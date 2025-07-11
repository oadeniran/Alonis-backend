from langchain.docstore.document import Document
import os
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_mongodb import MongoDBAtlasVectorSearch
from db import ragEmbeddingsCollection,db

ATLAS_VECTOR_SEARCH_INDEX_NAME = "langchain-index-vectorstores"

def create_docs(context, curr_session_id):
    docs = []
    if len(context) == 0:
        return docs
    
    if isinstance(context, str):
        context = { "Text Context" : {"content": context, "metadata": {}} }
    for title, context_details in context.get('context', {}).items():
        print("Creating document for title:", title)
        print("Context details:", context_details)
        meta_data = context_details.get("metadata", {})
        meta_data["curr_session_id"] = curr_session_id
        doc = Document(
            page_content=title + "\n" + context_details["content"],
            metadata=meta_data
        )
        docs.append(doc)
    return docs

def create_update_embeddings_for_user(docs, api_key, user_id):

    userRagEmbeddingsCollection = db[user_id]
    if len(docs) > 0:
        ids = [user_id + f"_{i}" for i in range(len(docs))]
    
    # Split documents
    #text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    #splits = text_splitter.split_documents(docs)
    #ids = [user_id + f"_{i}" for i in range(len(splits))]
    
    # Create embeddings and persist them
    #vectorstore = Chroma.from_documents(documents=splits, persist_directory=persist_dir, embedding=OpenAIEmbeddings(api_key=api_key))
    vectorstore = MongoDBAtlasVectorSearch(
            collection=userRagEmbeddingsCollection,
            embedding=OpenAIEmbeddings(api_key=api_key),
            index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
            relevance_score_fn="cosine"
        )
    
    if len(docs) > 0:
        vectorstore.add_documents(documents=docs, ids=ids)

    vectorstore.create_vector_search_index(dimensions=1536)
    
    return "done"


def create_retriever(api_key, context_doc_list):
    if len(context_doc_list) == 0:
        return MongoDBAtlasVectorSearch(
            collection=ragEmbeddingsCollection,
            embedding=OpenAIEmbeddings(api_key=api_key),
            index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
            relevance_score_fn="cosine"
        ).as_retriever()
    vstore = MongoDBAtlasVectorSearch.from_documents(
    documents=context_doc_list,
    embedding=OpenAIEmbeddings(api_key=api_key, disallowed_special=()), 
    collection=ragEmbeddingsCollection, 
    index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME
    )

    return vstore.as_retriever()

def load_model(api_key, retriever, chat_history):
    llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")

    system_prompt = (
    "You are a compassionate therapist, helping users talk about their emotions and providing support to help them feel better. "
    "You have access to the user's previous tests and can remember past conversations to provide more personalized guidance. "
    "When responding, acknowledge the user's feelings and offer thoughtful, emotionally supportive responses. "
    "If you feel the context is unclear, ask gentle, open-ended questions to better understand the user. "
    "Keep your tone empathetic and aim to help the user feel heard and understood."
    "When there is no message from the user and no chat history, Greet the user and wwelcome the user to the session and ask what is on their mind."
    "\n\n"
    "{context}"
    "\n\n"
    "Chat History"
    f"{chat_history}"
)


    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    return rag_chain
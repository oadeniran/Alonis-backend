from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_mongodb import MongoDBAtlasVectorSearch
from db import ragEmbeddingsCollection
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
import os
from uuid import uuid4
from core.userActions import build_context_for_user

from config import EMBEDDINGS_DIR, OPENAI_API_KEY
# Shared splitter & embedder
SPLITTER  = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
EMBEDDING = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

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

def _get_store(user_id: str):
    """Return a (persisted) Chroma collection for this user."""
    return Chroma(
        persist_directory=os.path.join(EMBEDDINGS_DIR, user_id),
        embedding=EMBEDDING
    )

def create_embeddings_for_user(docs, user_id: str) -> str:
    """Create a fresh store (overwrites any existing one)."""
    splits = SPLITTER.split_documents(docs)

    # Generate truly unique ids per split to avoid future collisions
    ids = [f"{user_id}_{uuid4().hex}" for _ in splits]

    store = Chroma.from_documents(
        documents=splits,
        ids=ids,
        persist_directory=os.path.join(EMBEDDINGS_DIR, user_id),
        embedding=EMBEDDING
    )
    store.persist()          # flush to disk
    return "done"

def update_embeddings_for_user(docs, user_id: str) -> str:
    """Append new docs to an existing user store (creates one if absent)."""
    if not os.path.exists(os.path.join(EMBEDDINGS_DIR, user_id)):
        # No store yet → just create
        # Create with context that is built from user data
        user_context = build_context_for_user(user_id)
        user_context_docs = create_docs(user_context, "")
        return create_embeddings_for_user(user_context_docs, user_id)

    store  = _get_store(user_id)

    splits = SPLITTER.split_documents(docs)
    ids    = [f"{user_id}_{uuid4().hex}" for _ in splits]  # unique ids

    store.add_documents(documents=splits, ids=ids)
    store.persist()          # make sure it survives restarts
    return "done"

def load_user_retriever(user_id: str):
    """
    Load a retriever for a given user's vectorstore.

    Args:
        user_id (str): The user ID whose retriever you want to load.

    Returns:
        VectorStoreRetriever: A retriever instance ready to use.
    """
    store = _get_store(user_id)
    return store.as_retriever()


def create_retriever(context_doc_list):
    if len(context_doc_list) == 0:
        return MongoDBAtlasVectorSearch(
            collection=ragEmbeddingsCollection,
            embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY),
            index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
            relevance_score_fn="cosine"
        ).as_retriever()
    vstore = MongoDBAtlasVectorSearch.from_documents(
    documents=context_doc_list,
    embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY, disallowed_special=()), 
    collection=ragEmbeddingsCollection, 
    index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME
    )

    return vstore.as_retriever()

def load_model(retriever, chat_history):
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o-mini")

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
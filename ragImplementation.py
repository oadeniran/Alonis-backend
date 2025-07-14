from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_mongodb import MongoDBAtlasVectorSearch
from db import ragEmbeddingsCollection
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
import os
from uuid import uuid4
from core.userActions import build_context_for_user
from config import EMBEDDINGS_DIR, OPENAI_API_KEY
from utils import upload_file_bytes, download_file_bytes
from pathlib import Path
import shutil
import zipfile

# Shared splitter & embedder
SPLITTER  = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
EMBEDDING = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
EMBEDDING_DIR_PATH = Path(EMBEDDINGS_DIR)

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
            page_content=title + "\n" + context_details.get("content", ""),
            metadata=meta_data
        )
        docs.append(doc)
    return docs

def _get_store(user_id: str):
    """Return a (persisted) Chroma collection for this user."""
    return Chroma(
        persist_directory=os.path.join(EMBEDDINGS_DIR, user_id),
        embedding_function=EMBEDDING
    )

def upload_embeddings_to_azure(user_id: str):
    """
    Upload the embeddings for a user to Azure Blob Storage.
    This is useful for backup and loading the embeddings later.
    """
    user_folder = EMBEDDING_DIR_PATH / user_id
    zip_path = EMBEDDING_DIR_PATH / f"{user_id}_chroma.zip"

    if not user_folder.exists():
        return "No embeddings created, user folder does not exist."

    # Zip the folder
    shutil.make_archive(str(zip_path).replace(".zip", ""), 'zip', user_folder)

    # Read and upload
    file_bytes = zip_path.read_bytes()
    upload_file_bytes(zip_path.name, file_bytes)

    # Clean up the zip file
    zip_path.unlink()
    return "done"

def download_and_restore_user_embeddings(user_id: str):
    """
    Downloads a zipped Chroma embedding folder for a user,
    unzips it into the correct location, and deletes the zip.

    Args:
        user_id (str): User ID to restore embeddings for.
        EMBEDDING_DIR_PATH (Path): Root directory where embeddings live.
        download_file_bytes (function): Function that takes filename and returns file bytes.
    """
    zip_filename = f"{user_id}_chroma.zip"
    zip_path = EMBEDDING_DIR_PATH / zip_filename

    # Download zip bytes
    file_bytes = download_file_bytes(zip_filename)
    if not file_bytes:
        print(f"No zip found for user {user_id}")
        return

    # Save zip file temporarily
    with open(zip_path, "wb") as f:
        f.write(file_bytes)

    # Extract zip contents to EMBEDDING_DIR_PATH / user_id
    extract_path = EMBEDDING_DIR_PATH / user_id
    extract_path.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    # Clean up zip file
    zip_path.unlink()
    return "done"

def create_embeddings_for_user(docs, user_id: str) -> str:
    """Create a fresh store (overwrites any existing one)."""
    splits = SPLITTER.split_documents(docs)

    # Generate truly unique ids per split to avoid future collisions
    ids = [f"{user_id}_{uuid4().hex}" for _ in splits]

    Chroma.from_documents(
        documents=splits,
        ids=ids,
        persist_directory=os.path.join(EMBEDDINGS_DIR, user_id),
        embedding=EMBEDDING
    )

    # Upload the embeddings to Azure Blob Storage for backup and loading
    upload_embeddings_to_azure(user_id)
    return "done"

def update_embeddings_for_user(docs, user_id: str) -> str:
    """Append new docs to an existing user store (creates one if absent)."""
    if not os.path.exists(os.path.join(EMBEDDINGS_DIR, user_id)):
        # No store yet → Try loading from azure Blob Storage and if still not there then build context from user data
        try:
            res = download_and_restore_user_embeddings(user_id)
        except Exception as e:
            res = None # If the file doesn't exist, then just create an empty store
        if res is None:
            # Create with context that is built from user data
            user_context = build_context_for_user(user_id)
            user_context_docs = create_docs(user_context, "")
            create_embeddings_for_user(user_context_docs, user_id)

    store  = _get_store(user_id)

    splits = SPLITTER.split_documents(docs)
    ids    = [f"{user_id}_{uuid4().hex}" for _ in splits]  # unique ids

    store.add_documents(documents=splits, ids=ids)

    # Upload the embeddings to Azure Blob Storage for backup and loading
    upload_embeddings_to_azure(user_id)
    return "done"

def load_user_retriever(user_id: str):
    """
    Load a retriever for a given user's vectorstore.

    Args:
        user_id (str): The user ID whose retriever you want to load.

    Returns:
        VectorStoreRetriever: A retriever instance ready to use.
    """
    if not os.path.exists(os.path.join(EMBEDDINGS_DIR, user_id)):
        # No store yet → Try loading from azure Blob Storage and if still not there then build context from user data
        try:
            res = download_and_restore_user_embeddings(user_id)
        except Exception as e:
            res = None # If the file doesn't exist, then just create an empty store
        if res is None:
            # Create with context that is built from user data
            user_context = build_context_for_user(user_id)
            print("user_context===", user_context)
            user_context_docs = create_docs(user_context, "")
            create_embeddings_for_user(user_context_docs, user_id)
        
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

def load_model(retriever, chat_history, quote_flow=False, current_quote=None, recommendation_flow=False, recommendation_context=None):
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o-mini")

    if quote_flow:
        print("Loading model for quote flow")
        system_prompt = f"""
        You are ALONIS, a personalized AI that provides users with daily personalized quotes based on their data and past interactions.
        The context you have access to include the user's data, past interactions, goals and random notes,past assessments chats and reports 
        You have access to the user's context and can use it to provide quotes that matches the user's personality.If you do not have enough context to provide a personalized quote, then return a radom quote

        The current quote seen by the user for previous day is:
        
        {current_quote}

        YOU MUST RETURN A NEW QUOTE DIFFERENT FROM THE CURRENT QUOTE THAT THE USERE IS SEEING USING YOUR KNOWLEDGE BASE.
        \n\n
        """ + """Your are to return the quote in the following format:

        {{"quote": "The quote here", "author": "The author of the quote here"}}

        \n\n
        {context}

        """

        model_contexts = [
            ("system", system_prompt)
        ]
    elif recommendation_flow:
        
        system_prompt = f"""
        You are ALONIS, a personalized AI that provides users with personalized recommendations based on their data and past interactions.

        The context you have access to include the user's data, past interactions, goals and random notes,past assessments chats and reports

        You have access to the user's context and can use it to provide recommendations that matches the user's personality.

        The current recommendations seen by the user are:

        {recommendation_context}

        Your are to return a new list of recommendations based on the user's updated context that you have and these recommendations should definitely be different from the current recommendations that the user is seeing.

        """ + """
        You are to return the recommendations in the following format:

        [{{"title": "Title of the recommendation", "description": "Description of the recommendation including why this is being recommended to the user""}}]

        Return the recommendations in safe format for JSON and ensure that it follows the format above exactly without any extra text or explanation.

        \n\n
        {context}
        """
        model_contexts = [
            ("system", system_prompt)
        ]
    else:
        system_prompt = (
        "You are ALONIS, a compassionate perosnalized AI talsking to users about anything on their mind and  helping users talk about their emotions and providing support to help them feel better. "
        "You have access and context of everything the user has talked about in the past, every interaction they have had with you  and you can use this context to provide personalized responses. "
        "The context you have access to include the user's data, past interactions, goals and random notes,past assessments chats and reports"
        "When responding to user, yopu are fully aware of the context of what is being spoken about therefore if a context is based on the Notes or Goals the user has added, your responses reflcet that you aware its a note or goal and you are aware of the details of the note or goal. If its about a previous assessment, you are aware of the details of the assessment and you are aware of the context of the assessment."
        "Since the user is aware that you have context of every of their data, its possible for them to ask you about anything they have said in the past, any goal they have added, any note they have added, any assessment they have done and you are aware of the details of that data, you are to ensure that you try your best as muchj as possible to provide a helpful response based on the context of the data and the context of the conversation. "
        "The context you have access to is always up to date, so you need to esnure that you always use the context to provide personalized responses that will be very helpful to the user as an anwser to their question or as a response to their message. "
        "When responding, acknowledge the user's feelings and offer thoughtful, emotionally supportive responses. "
        "If you feel the context is unclear, ask gentle, open-ended questions to better understand the user. "
        "Keep your tone empathetic and aim to help the user feel heard and understood."
        "When there is no message from the user and no chat history, Greet the user, welcome the user to the session, ask what's on their mind and suggest possible things that they can talk about based on context of their data and past interactions with you. Thes posible things should be very specific and tailored to the user. for example a goal they added recently or something they said in a prevuious assessment etc"
        "\n\n"
        "{context}"
        "\n\n"
        "Chat History"
        f"{chat_history}"
        )
        model_contexts = [
            ("system", system_prompt),
            ("human", "{input}"),
        ]


    prompt = ChatPromptTemplate.from_messages(
        model_contexts
    )

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    return rag_chain
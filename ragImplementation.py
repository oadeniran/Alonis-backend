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
from locks import chroma_guard, zip_file_upload_guard
import asyncio
import model_prompts

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
        #print("Context details:", context_details)
        meta_data = context_details.get("metadata", {})
        meta_data["curr_session_id"] = curr_session_id
        doc = Document(
            page_content=title + "\n" + context_details.get("content", ""),
            metadata=meta_data
        )
        docs.append(doc)
    print("Created documents:", len(docs))
    return docs

def _get_store(user_id: str):
    """Return a (persisted) Chroma collection for this user."""
    return Chroma(
        persist_directory=os.path.join(EMBEDDINGS_DIR, user_id),
        embedding_function=EMBEDDING
    )

async def upload_embeddings_to_azure(user_id: str):
    """
    Upload the embeddings for a user to Azure Blob Storage.
    This is useful for backup and loading the embeddings later.
    """
    user_folder = EMBEDDING_DIR_PATH / user_id
    zip_path = EMBEDDING_DIR_PATH / f"{user_id}_chroma.zip"

    if not user_folder.exists():
        return "No embeddings created, user folder does not exist."

    # Zip the folder
    async with zip_file_upload_guard(user_id):
        await asyncio.to_thread(shutil.make_archive, str(zip_path).replace(".zip", ""), 'zip', user_folder)

        # Read and upload
        file_bytes = zip_path.read_bytes()
        await asyncio.to_thread(upload_file_bytes, zip_path.name, file_bytes)

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

async def create_embeddings_for_user(docs, user_id: str) -> str:
    """Create a fresh store (overwrites any existing one)."""
    splits = SPLITTER.split_documents(docs)

    # Generate truly unique ids per split to avoid future collisions
    ids = [f"{user_id}_{uuid4().hex}" for _ in splits]

    # Create the store and add documents. Use async context manager to ensure the lock is acquired and released properly. This way we can ensure that no other process is trying to write to the same user's store at the same time.
    async with chroma_guard(user_id):
        Chroma.from_documents(
            documents=splits,
            ids=ids,
            persist_directory=os.path.join(EMBEDDINGS_DIR, user_id),
            embedding=EMBEDDING
        )
    print(f"Created embeddings for user {user_id} with {len(splits)} documents.")

    # Upload the embeddings to Azure Blob Storage for backup and loading
    asyncio.create_task(upload_embeddings_to_azure(user_id))
    return "done"

async def update_embeddings_for_user(docs, user_id: str) -> str:
    """Append new docs to an existing user store (creates one if absent)."""
    if not os.path.exists(os.path.join(EMBEDDINGS_DIR, user_id)):
        # No store yet → Try loading from azure Blob Storage and if still not there then build context from user data
        try:
            async with chroma_guard(user_id):
                # Attempt to download and restore user embeddings
                res = download_and_restore_user_embeddings(user_id)
        except Exception as e:
            print(f"Error restoring user embeddings for {user_id}: {e}")
            res = None # If the file doesn't exist, then just create an empty store
        if res is None:
            # Create with context that is built from user data
            user_context = build_context_for_user(user_id)
            user_context_docs = create_docs(user_context, "")
            await create_embeddings_for_user(user_context_docs, user_id)

    async with chroma_guard(user_id):
        store  = _get_store(user_id)

        splits = SPLITTER.split_documents(docs)
        ids    = [f"{user_id}_{uuid4().hex}" for _ in splits]  # unique ids

        store.add_documents(documents=splits, ids=ids)

    # Upload the embeddings to Azure Blob Storage for backup and loading
    asyncio.create_task(upload_embeddings_to_azure(user_id))
    return "done"

async def load_user_retriever(user_id: str):
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
            async with chroma_guard(user_id):
                # Attempt to download and restore user embeddings
                res = download_and_restore_user_embeddings(user_id)
        except Exception as e:
            res = None # If the file doesn't exist, then just create an empty store
        if res is None:
            # Create with context that is built from user data
            user_context = build_context_for_user(user_id)
            print("user_context===", user_context)
            user_context_docs = create_docs(user_context, "")
            await create_embeddings_for_user(user_context_docs, user_id)
    async with chroma_guard(user_id):
        # Load the store - since we are using chroma_guard, we can be sure that no other process is trying to write to the same user's store at the same time
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

def load_model(retriever, chat_history=[], flow={}):
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o-mini")

    if flow.get('name', '') == 'quote_flow':
        print("Loading model for quote flow")
        system_prompt = model_prompts.QUOTE_MODEL_PROMPT + '\n' + flow.get('context', '')

        model_contexts = [
            ("system", system_prompt)
        ]
    elif flow.get('name', '') == 'recommendation_flow':
        print("Loading model for recommendation flow")
        system_prompt = model_prompts.RECCOMMENDATION_MODEL_PROMPT + '\n' + flow.get('context', '')
        model_contexts = [
            ("system", system_prompt)
        ]
    elif flow.get('name', '') == 'tag_selection_flow':
        print("Loading model for tag selection flow")
        system_prompt = model_prompts.TAG_SELECTION_MODEL_PROMPT + '\n' + flow.get('context', '')
        model_contexts = [
            ("system", system_prompt)
        ]
    elif flow.get('name', '') == 'recommendation_context_flow':
        print("Loading model for recommendation context flow")
        system_prompt = model_prompts.RECOMMENDATION_CONTEXT_MODEL_PROMPT + '\n' + flow.get('context', '')
        model_contexts = [
            ("system", system_prompt)
        ]
    elif flow.get('name', '') == 'daily_story_flow':
        print("Loading model for story flow")
        system_prompt = model_prompts.DAILY_STORY_MODEL_PROMPT + '\n' + flow.get('context', '')
        model_contexts = [
            ("system", system_prompt)
        ]
    else:
        system_prompt = model_prompts.TALK_MODEL_PROMPT + f"{chat_history}"
        
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
from dotenv import load_dotenv
import os
import pickle

load_dotenv()

# Load environment variables
OPENAI_API_KEY = os.getenv("OAI_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
EMBED_PATH = os.getenv("EMBED_PATH", "embeddings")
appENV = os.getenv("APP_ENV", "local")  # Default to 'local' if not set
PORT = int(os.getenv("PORT", 80))  # Default to 8000 if not set
EMBEDDINGS_DIR = os.getenv("EMBEDDINGS_DIR", "embeddings")

AZURE_BLOB_CONNECTION_STR = os.getenv("BLOB_CONNECTION_STR", "")
EMBEDDINGS_CONTAINER_NAME = os.getenv("EMBEDDINGS_CONTAINER_NAME", "embeddings")

# Load in ML Models
mentalHealthModel =  pickle.load(open("model_data/mental_model-n.sav", 'rb'))

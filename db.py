from pymongo import MongoClient

from config import DATABASE_URL 

# Connect to MongoDB
client = MongoClient(DATABASE_URL )
db = client["mindwave_db"]

usersCollection = db["users"]
messageCollection = db["messages"]
extractedDataCollection = db["extractedData"]
reportsCollection = db["reports"]
rantMessagesCollection = db["rantMessages"]
ragEmbeddingsCollection = db["ragEmbeddings"]
sessionsCollection = db["sessions"]

# Define DB actions
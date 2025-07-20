from pymongo import MongoClient
from pymongo.errors import BulkWriteError

from config import DATABASE_URL 

# Connect to MongoDB
client = MongoClient(DATABASE_URL )
db = client["mindwave_db"]

usersCollection = db["users"]
messageCollection = db["messages"]
extractedDataCollection = db["extractedData"]
reportsCollection = db["reports"]
rantMessagesCollection = db["rantMessages"]
talksMessagesCollection = db["talksMessages"]
ragEmbeddingsCollection = db["ragEmbeddings"]
sessionsCollection = db["sessions"]
notes_and_goalsCollection = db["notes_and_goals"]
dailyQuotesCollection = db['dailyQuotes']
recommendationsCollection = db['recommendations']
qlooRecommendationsPageTrackingCollection = db['qlooRecommendationsPageTracking']

# Define DB actions
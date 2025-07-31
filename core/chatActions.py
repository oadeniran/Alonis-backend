from db import messageCollection, sessionsCollection, talksMessagesCollection
from datetime import datetime
    
def add_chat_to_db(uid, session_id:str,type:str,message:str, clean_message = "", extra_info={}, talks_session=False):
    if clean_message == "":
        clean_message = message
    document = {
        "uid":uid,
        "session_id":session_id,
        "type":type,
        "message":message,
        "clean_message": clean_message,
        "date":datetime.now(),
    }
    if extra_info:
        document.update(extra_info)
    if talks_session:
        talksMessagesCollection.insert_one(document)
    else:
        messageCollection.insert_one(document)
    
    # Lets also update the session to increase the message count or initialze the variable to 1 if it doesn't exist
    sessionsCollection.find_one_and_update(
        {"uid": uid, "session_id": session_id},
        {"$inc": {"message_count": 1}},
        upsert=True  # Create the session if it doesn't exist 
    )
    
def get_chat_from_db(uid, session_id, talks_session=False, getCount = False):
    if talks_session:
        try:
            chats = talksMessagesCollection.find({"uid":uid, "session_id": session_id}, {"_id": 0})
            if getCount:
                count = talksMessagesCollection.count_documents({"uid":uid, "session_id": session_id})
                return list(chats), count
            else:
                return	chats, None
        except Exception as e:
            print(e)
            return "Error with chat retrieval", None
    else:
        try:
            chats = messageCollection.find({"uid":uid, "session_id": session_id}, {"_id": 0})
            if getCount:
                count = messageCollection.count_documents({"uid":uid, "session_id": session_id})
                return list(chats), count
            else:
                return chats, None
        except Exception as e:
            print(e)
            return "Error with chat retrieval", None
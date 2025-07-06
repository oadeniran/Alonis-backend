from db import messageCollection, rantMessagesCollection
from datetime import datetime
    
def add_chat_to_db(uid, session_id:str,type:str,message:str, extra_info:dict, rant=False):
    document = {
        "uid":uid,
        "session_id":session_id,
        "type":type,
        "message":message,
        "date":datetime.now(),
    }
    if extra_info:
        document.update(extra_info)
    if rant:
        rantMessagesCollection.insert_one(document)
    else:
        messageCollection.insert_one(document)
    
def get_chat_from_db(uid, session_id, rant=False, getCount = False):
    if rant:
        try:
            chats = rantMessagesCollection.find({"uid":uid, "session_id": session_id})
            if getCount:
                count = rantMessagesCollection.count_documents({"uid":uid, "session_id": session_id})
                return chats, count
            else:
                return	chats
        except Exception as e:
            print(e)
            return "Error with chat retrieval"
    else:
        try:
            chats = messageCollection.find({"uid":uid, "session_id": session_id})
            if getCount:
                count = messageCollection.count_documents({"uid":uid, "session_id": session_id})
                return chats, count
            else:
                return chats
        except Exception as e:
            print(e)
            return "Error with chat retrieval"
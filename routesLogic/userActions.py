from core import userActions, chatActions
import utils
from config import OPENAI_API_KEY

def signup_user(username: str, password: str):
    if not username or not password:
        return {"error": "Username and password are required"}
    
    
    resp = userActions.signup({"username": username, "password": password, "sessions": []})
    if resp["status_code"] == 200:
        return resp

def login_user(username: str, password: str):
    if not username or not password:
        return {"error": "Username and password are required"}
    
    resp = userActions.login({"username": username, "password": password})
    if resp["status_code"] == 200:
        return resp
    else:
        return {"error": resp["message"]}

async def get_all_sessions(uid: str):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    userSessions = userActions.get_all_user_sessions(uid)
    if not userSessions:
        return {"error": "No sessions found for this user"}
    
    return userSessions

async def get_session_chats(uid: str, session_id: str, rant: bool = False):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    chats, count = chatActions.get_chat_from_db(uid=uid, session_id=session_id, rant=rant, getCount=True)
    if count == 0:
        return {"error": "No messages for this session yet"}
    
    return {"chats": chats, "count": count}

async def get_user_reports(uid: str):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    all_reports = userActions.get_user_reports(uid)
    if not all_reports:
        return {"error": "No reports found for this user"}
    
    return all_reports
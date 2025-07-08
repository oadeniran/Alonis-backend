from core import userActions, chatActions
import utils
from config import OPENAI_API_KEY

def signup_user(user_details: dict):
    username = user_details.get("username")
    password = user_details.get("password")
    if not username or not password:
        return {"error": "Username and password are required"}
    
    if not password or len(password) < 8:
        return {"error": "Password must be at least 8 characters long"}
    
    
    resp = userActions.signup(user_details)
    if resp["status_code"] == 200:
        return resp
    else:        
        return {"error": resp["message"]}

def login_user(login_cred):
    username = login_cred.get("username")
    password = login_cred.get("password")
    email = login_cred.get("email", "")
    if not username:
        if not email:
            return {"error": "Either username or email is required for login"}
    
    if not password:
        return {"error": "Password is required for login"}
    
    resp = userActions.login(login_cred)
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
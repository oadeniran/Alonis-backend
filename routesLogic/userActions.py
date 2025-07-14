from core import userActions, chatActions, background_tasks
import asyncio
from datetime import datetime

async def signup_user(user_details: dict):
    username = user_details.get("username")
    password = user_details.get("password")
    if not username or not password:
        return {"error": "Username and password are required"}
    
    if not password or len(password) < 8:
        return {"error": "Password must be at least 8 characters long"}
    
    user_details['signup_date'] = datetime.now()
    
    resp = userActions.signup(user_details)
    if resp["status_code"] == 200:
        user_details['uid'] = resp.get("uid")
        asyncio.create_task(background_tasks.init_user_embeddings(user_details))
        return resp
    else:        
        return {"error": resp["message"]}

async def login_user(login_cred):
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
        # Start a background task to update user embeddings with login details
        asyncio.create_task(background_tasks.run_sequenced_user_login_tasks(
            uid=resp.get("uid", "default_user"),
            username=username 
        ))
        return resp
    else:
        return {"error": resp["message"]}

async def get_all_sessions(uid: str):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    resp = userActions.get_all_user_sessions(uid)

    if resp["status_code"] != 200:
        return {"error": resp["message"]}
    
    return resp

async def get_user_session_chats(uid: str, session_id: str, is_talk_session: bool = False):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    chats, count = chatActions.get_chat_from_db(uid=uid, session_id=session_id, talks_session=is_talk_session, getCount=True)
    if count and count == 0:
        return {"error": "No messages for this session yet"}
    
    return {"messages": chats, "count": count, 'status_code': 200}

async def get_user_reports(uid: str):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    all_reports = userActions.get_user_reports(uid)
    if not all_reports:
        return {"error": "No reports found for this user"}
    
    return all_reports

async def get_user_session_report(uid: str, session_id: str):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    if not session_id or session_id == "":
        return {"error": "Session ID is required"}
    
    report = userActions.get_user_session_report(uid, session_id)
    if not report:
        return {"error": "No report found for this session"}
    
    return report

async def add_user_note_or_goal(uid: str, note_details: dict):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    if not note_details or not isinstance(note_details, dict):
        return {"error": "Note details are required"}
    
    resp = userActions.add_note_or_goal_for_user(uid, note_details)

    print(resp)
    if resp.get("status_code", 200) == 200:
        asyncio.create_task(background_tasks.update_user_embeddings(
            note_details,
            uid,
            meta_data={"note_added": datetime.now().isoformat()},
            title="User Note/Goal Addition"
        ))
        return resp
    else:
        return {"error": resp["message"]}
    
async def get_user_notes_and_goals(uid, page = 1):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    notes_and_goals = userActions.get_user_notes_and_goals(uid, page)

    if not notes_and_goals:
        return {"error": "No notes or goals found for this user"}
    
    return notes_and_goals

async def delete_note_or_goal(uid, note_id):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    if not note_id or note_id == "":
        return {"error": "Note ID is required"}
    
    resp = userActions.delete_note_or_goal(uid, note_id)

    if resp["status_code"] != 200:
        return {"error": resp["message"]}
    
    return resp

async def mark_goal_as_achieved(uid: str, note_id: str):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    if not note_id or note_id == "":
        return {"error": "Note ID is required"}
    
    try:
        result = userActions.mark_goal_as_achieved(uid, note_id)
        asyncio.create_task(background_tasks.update_user_embeddings(
            {"note_id": note_id, "status": "achieved"},
            uid,
            meta_data={"goal_achieved": datetime.now().isoformat()},
            title="Goal Marked as Achieved"
        ))
        return result   
    except Exception as e:
        print(e)
        return {"error": "Error marking note as achieved", "status_code": 400}
    
async def get_alonis_recommendations(uid: str, rec_type = 'alonis_recommendation', page: int = 1):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    recommendations = None
    
    if rec_type == 'alonis_recommendation':
        recommendations = userActions.get_current_alonis_recommendations(uid, rec_type=rec_type, page = page)

    if not recommendations:
        return {"error": "No Alonis recommendations found for this user"}
    
    return recommendations

async def mark_interaction_with_recommendation(uid: str, rec_id: str):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    if not rec_id or rec_id == "":
        return {"error": "Recommendation ID is required"}
    
    resp = userActions.mark_interaction_with_recommendation(uid, rec_id)

    if resp["status_code"] != 200:
        return {"error": resp["message"]}
    print(resp)
    asyncio.create_task(background_tasks.update_user_embeddings(
        {'good thing to note': 'user interacted with a recommendation',
         'recommendation details': resp.get('result', {})},
        uid,
        meta_data={"interaction_with_rec": datetime.now().isoformat()},
        title=f"User Interacted with Recommendation titlled : {resp.get('result', {}).get('title', 'Unknown')}"
    ))
    
    return resp
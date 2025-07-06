import random
from core import rantSessions, userActions
import utils
import uuid
from config import OPENAI_API_KEY

async def mindwave_talk_session(uid: str, session_id: str, user_input: str = ""):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}

    if not session_id or session_id == "":
        session_id = str(uuid.uuid4())
        
    userActions.add_user_session(uid, session_id, "Talk_session", {})
    
    reports_doc_list = rantSessions.get_reports_doc_list(userActions.get_user_reports(uid), session_id)

    output = rantSessions.talkToMe(uid, session_id, user_input, OPENAI_API_KEY, reports_doc_list=reports_doc_list)

    utils.remove_embedded_data(session_id)

    return {"response": output, "session_id": session_id, "uid": uid}
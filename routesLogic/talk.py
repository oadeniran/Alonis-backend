import random
from core import talksSessions, userActions
import utils
import uuid
from config import OPENAI_API_KEY

async def mindwave_talk_session(uid: str, session_id: str, user_input: str = ""):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}

    if not session_id or session_id == "":
        session_id = str(uuid.uuid4())
        
    userActions.add_user_session(uid, session_id, "talk_session", {})
    
    context_doc_list = talksSessions.get_context_doc_list(userActions.build_context_for_user(uid), session_id)

    output = talksSessions.talkToMe(uid, session_id, user_input, OPENAI_API_KEY, context_doc_list=context_doc_list)

    utils.remove_embedded_data(session_id)

    return {"response": output, "session_id": session_id, "uid": uid}

async def get_personalized_quote(uid: str):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}

    quotes = []
    if not quotes:
        return {"error": "No quotes available at the moment"}

    random_quote = random.choice(quotes)
    
    return {"quote": random_quote, "uid": uid}
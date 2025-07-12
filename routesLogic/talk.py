from core import talksSessions, userActions,background_tasks
import utils
import uuid
from config import OPENAI_API_KEY
from datetime import datetime
import asyncio

async def mindwave_talk_session(uid: str, session_id: str, user_input: str = ""):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}

    if not session_id or session_id == "":
        session_id = str(uuid.uuid4())
        
    userActions.add_user_session(uid, session_id, "talk_session", {})
    
    context_doc_list = None # talksSessions.get_context_doc_list(userActions.build_context_for_user(uid), session_id)

    output = talksSessions.talkToMe(uid, session_id, user_input, context_doc_list=context_doc_list)

    if context_doc_list is not None:
        # Then remove the embedding from mongo since its what we used to create the context
        utils.remove_embedded_data(session_id)

    asyncio.create_task(background_tasks.update_user_embeddings(
        {"user_input": user_input, "response": output},
        uid,
        meta_data={"talk session date": datetime.now().isoformat()},
        session_id=session_id,
        title="Talk Session Data"
    ))

    return {"response": output, "session_id": session_id, "uid": uid}

async def get_personalized_quote(uid: str):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    user_quote = userActions.get_user_quote_for_today(uid)

    if user_quote and user_quote.get('date', '') == datetime.now().strftime('%Y-%m-%d'):
        user_quote.pop('_id', None)  # Remove MongoDB ObjectId if present
        return {'quote' : user_quote}
    
    # If no quote for today, generate a new one
    previous_quote = userActions.get_previous_quote(uid)
    previous_quote = previous_quote.get('quote', "No previous quote seen by user")  # Ensure we have a quote to work with

    quote = talksSessions.giveMeAQuoute(uid, previous_quote)
    if not quote:
        return {"error": "No quotes available at the moment"}

    #  Add the quote to the database for the user
    userActions.add_daily_quote(uid, quote['quote'])
    
    return quote
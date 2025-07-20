from core import talksSessions, userActions,background_tasks
import utils
import uuid
from datetime import datetime
import asyncio

async def mindwave_talk_session(uid: str, session_id: str, user_input: str = ""):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}

    if not session_id or session_id == "":
        session_id = str(uuid.uuid4())
        
    userActions.add_user_session(uid, session_id, "talk_session", {})
    
    context_doc_list = None # talksSessions.get_context_doc_list(userActions.build_context_for_user(uid), session_id)

    output = await talksSessions.talkToMe(uid, session_id, user_input, context_doc_list=context_doc_list)

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
    previous_quote = userActions.get_previous_quotes(uid)
    if previous_quote.get('count', 0) > 0:
        previous_quotes  = [utils.dict_to_string(prev_quote) for prev_quote in previous_quote.get('quotes', [])]
        previous_quotes = "\n".join(previous_quotes)
    else:
        previous_quotes = "No previous quotes available."

    quote = await talksSessions.giveMeAQuoute(uid, previous_quotes)
    if not quote:
        return {"error": "No quotes available at the moment"}

    #  Add the quote to the database for the user
    userActions.add_daily_quote(uid, quote['quote'])
    
    return quote

async def get_daily_story(uid: str):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    user_story = userActions.get_user_story_for_today(uid)

    if user_story and user_story.get('date', '') == datetime.now().strftime('%Y-%m-%d'):
        user_story.pop('_id', None)  # Remove MongoDB ObjectId if present
        return  user_story
    
    # If no story for today, generate a new one
    previous_stories = userActions.get_previous_stories(uid)
    if previous_stories.get('count', 0) > 0:
        previous_stories_list = [utils.dict_to_string(prev_story) for prev_story in previous_stories.get('stories', [])]
        previous_stories_text = "\n".join(previous_stories_list)
    else:
        previous_stories_text = "No previous stories available."

    story = await talksSessions.giveMeAStory(uid, previous_stories_text)
    if not story:
        return {"error": "No stories available at the moment"}

    # Add the story to the database for the user
    userActions.add_daily_story(uid, story.get('story'))
    
    return story
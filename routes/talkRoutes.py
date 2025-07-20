from fastapi import APIRouter
from routesLogic import talk
from dtos.talk_dto import TalkDTO

router = APIRouter()

@router.post("/talk-session")
async def talk_session_route(talk_data: TalkDTO):
    """
    Endpoint to handle talk session requests.
    
    Args:
        talk_data (TalkDTO): Data transfer object containing user_id, session_id, and user_input.
    Returns:
        JSON response from the talk session logic.
    """
    uid = talk_data.user_id
    session_id = talk_data.session_id
    user_input = talk_data.user_input if talk_data.user_input else ""
    return await talk.mindwave_talk_session(uid, session_id, user_input)

@router.get("/{uid}/personalized-quote")
async def personalized_quote(uid: str):
    """
    Endpoint to retrieve a personalized quote for a user.
    
    Args:
        uid (str): User ID.
    Returns:
        JSON response containing a personalized quote.
    """
    return await talk.get_personalized_quote(uid)

@router.get("/{uid}/daily-story")
async def daily_story(uid: str):
    """
    Endpoint to retrieve a daily story for a user.
    
    Args:
        uid (str): User ID.
    Returns:
        JSON response containing a daily story.
    """
    return await talk.get_daily_story(uid)
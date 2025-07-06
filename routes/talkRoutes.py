from fastapi import APIRouter
from routesLogic import talk

router = APIRouter()

@router.post("/talk-session")
async def talk_session_route(uid: str, session_id: str, user_input: str = ""):
    """
    Endpoint to handle talk session requests.
    
    Args:
        uid (str): User ID.
        session_id (str): Session ID.
        user_input (str): User input for the talk session.
    
    Returns:
        dict: A dictionary containing the response from the talk session.
    """
    return await talk.mindwave_talk_session(uid, session_id, user_input)
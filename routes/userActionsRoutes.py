from fastapi import APIRouter
from routesLogic import userActions
router = APIRouter()

@router.post("/sign-up")
async def sign_up(user_name, password):
    """
    Endpoint to sign up a new user.
    
    Args:
        uid (str): User ID.
    
    Returns:
        dict: A dictionary containing a success message or an error message.
    """
    return userActions.signup_user(user_name, password)

@router.post("/sign-in")
async def sign_in(user_name, password):
    """
    Endpoint to sign in an existing user.
    
    Args:
        user_name (str): Username of the user.
        password (str): Password of the user.
    
    Returns:
        dict: A dictionary containing a success message or an error message.
    """
    return userActions.login_user(username = user_name,password = password)

@router.get("/get-all-sessions")
async def get_all_sessions(uid: str):
    """
    Endpoint to retrieve all user sessions.
    
    Args:
        uid (str): User ID.
    
    Returns:
        dict: A dictionary containing all user sessions or an error message.
    """
    return await userActions.get_all_sessions(uid)

@router.get("/get-session-chats")
async def get_session_chats(uid: str, session_id: str, rant: bool = False):
    """
    Endpoint to retrieve chats for a specific user session.
    
    Args:
        uid (str): User ID.
        session_id (str): Session ID.
        rant (bool): Flag to indicate if the session is a rant session.
    
    Returns:
        dict: A dictionary containing the chats for the session or an error message.
    """
    return await userActions.get_session_chats(uid, session_id, rant)

@router.get("/get-user-reports")
async def get_user_reports(uid: str):
    """
    Endpoint to retrieve all reports for a user.
    
    Args:
        uid (str): User ID.
    
    Returns:
        dict: A dictionary containing all user reports or an error message.
    """
    return await userActions.get_user_reports(uid)
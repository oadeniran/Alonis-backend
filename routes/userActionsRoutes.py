from fastapi import APIRouter
from routesLogic import userActions
router = APIRouter()
from dtos.user_dto import UserDTO, UserLoginDTO
from dtos.notes_dto import Note_AND_GOAL

@router.post("/sign-up")
async def sign_up(user_details: UserDTO):
    """
    Endpoint to sign up a new user.
    
    Args:
        uid (str): User ID.
    
    Returns:
        dict: A dictionary containing a success message or an error message.
    """
    return await userActions.signup_user(user_details.model_dump())

@router.post("/sign-in")
async def sign_in(login_cred: UserLoginDTO):
    """
    Endpoint to sign in an existing user.
    
    Args:
        user_name (str): Username of the user.
        password (str): Password of the user.
    
    Returns:
        dict: A dictionary containing a success message or an error message.
    """
    return await userActions.login_user(login_cred.model_dump())

@router.get("/{uid}/sessions")
async def get_user_sessions(uid: str):
    """
    Endpoint to retrieve all user sessions.
    
    Args:
        uid (str): User ID.
    
    Returns:
        dict: A dictionary containing all user sessions or an error message.
    """
    return await userActions.get_all_sessions(uid)

@router.get("/{uid}/{session_id}/session-chats")
async def get_user_session_chats(uid: str, session_id: str, is_talk_session: bool = False):
    """
    Endpoint to retrieve chats for a specific user session.
    
    Args:
        uid (str): User ID.
        session_id (str): Session ID.
        is_talk_session (bool): Flag to indicate if the session is a talk session.
    
    Returns:
        dict: A dictionary containing the chats for the session or an error message.
    """
    return await userActions.get_user_session_chats(uid, session_id, is_talk_session)

@router.get("/{uid}/{session_id}/session-report")
async def get_user_session_report(uid: str, session_id: str):
    """
    Endpoint to retrieve user session report.
    
    Args:
        uid (str): User ID.
        session_id (str): Session ID.
    
    Returns:
        dict: The session report data or an error message.
    """
    return await userActions.get_user_session_report(uid, session_id)

@router.post('/add-note-or-goal')
async def add_note_or_goal(note_details: Note_AND_GOAL):
    """
    Endpoint to add a note or goal for a user.
    
    Args:
        note_details (Note_AND_GOAL): Details of the note or goal to be added.
    
    Returns:
        dict: A dictionary containing a success message or an error message.
    """
    return await userActions.add_user_note_or_goal(note_details.uid, note_details.model_dump())

@router.get("/{uid}/get-notes-and-goals")
async def get_user_notes_and_goals(uid: str):
    """
    Endpoint to retrieve all notes and goals for a user.
    
    Args:
        uid (str): User ID.
    
    Returns:
        dict: A dictionary containing all notes and goals or an error message.
    """
    return await userActions.get_user_notes_and_goals(uid)

@router.post("/{uid}/mark-goal-as-achieved/{note_id}")
async def mark_goal_as_achieved(uid: str, note_id: str):
    """
    Endpoint to mark a note as achieved for a user.
    
    Args:
        uid (str): User ID.
        note_id (str): Note ID to be marked as achieved.
    
    Returns:
        dict: A dictionary containing a success message or an error message.
    """
    return await userActions.mark_goal_as_achieved(uid, note_id)

@router.delete("/{uid}/delete-note-or-goal/{note_id}")
async def delete_note_or_goal(uid: str, note_id: str):
    """
    Endpoint to delete a note or goal for a user.
    
    Args:
        uid (str): User ID.
        note_id (str): Note or goal ID to be deleted.
    
    Returns:
        dict: A dictionary containing a success message or an error message.
    """
    return await userActions.delete_note_or_goal(uid, note_id)
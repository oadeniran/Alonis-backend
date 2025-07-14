from fastapi import APIRouter
from routesLogic import userActions
from typing import Literal
from dtos.user_dto import UserDTO, UserLoginDTO
from dtos.notes_dto import Note_AND_GOAL

router = APIRouter()
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
async def get_user_notes_and_goals(uid: str, page: int = 1):
    """
    Endpoint to retrieve paginated notes and goals for a user.
    
    Args:
        uid (str): User ID.
        page (int): Page number (default = 1).
    
    Returns:
        dict: Notes and goals with pagination.
    """
    return await userActions.get_user_notes_and_goals(uid, page)

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

@router.get("/{uid}/alonis-recommendations/{rec_type}")
async def get_alonis_recommendations(
    uid: str,
    rec_type: Literal['alonis_recommendation', 'alonis_recommendation_movies', 'alonis_recommendation_songs'] = 'alonis_recommendation',
    page: int = None
):
    """
    Endpoint to retrieve personalized Alonis recommendations for a user.
    
    Args:
        uid (str): User ID.
        limit (int): Number of recommendations to retrieve.
    
    Returns:
        dict: A dictionary containing the recommendations or an error message.
    """
    return await userActions.get_alonis_recommendations(uid, rec_type, page)

@router.post("/{uid}/mark-interaction-with-recommendation/{rec_id}")
async def mark_interaction_with_recommendation(uid: str, rec_id: str):
    """
    Endpoint to mark an interaction with a recommendation for a user.
    
    Args:
        uid (str): User ID.
        rec_id (str): Recommendation ID to be marked.
    
    Returns:
        dict: A dictionary containing a success message or an error message.
    """
    return await userActions.mark_interaction_with_recommendation(uid, rec_id)
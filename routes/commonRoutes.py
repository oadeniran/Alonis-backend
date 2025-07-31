
import uuid
from fastapi import APIRouter

router = APIRouter()


@router.get("/generate-session-id")
async def generate_session_id():
    """
    Endpoint to generate a new session ID.
    
    Returns:
        dict: A dictionary containing the generated session ID.
    """
    return {"session_id": str(uuid.uuid4())}
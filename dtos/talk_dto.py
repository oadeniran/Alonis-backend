from pydantic import BaseModel
from typing import Optional, List

class TalkDTO(BaseModel):
    user_id: str
    session_id: str
    user_input: Optional[str] = ""
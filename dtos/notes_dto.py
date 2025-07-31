from pydantic import BaseModel, Field
from typing import Optional, List

class Note_AND_GOAL(BaseModel):
    uid: str
    title: str
    details: str
    is_goal: bool = Field(default=False, description="Indicates if the note is a goal")
    
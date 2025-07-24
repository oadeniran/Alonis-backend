
from pydantic import BaseModel
from typing import Optional

class UserDTO(BaseModel):
    username: str
    email: str
    password: str
    alonis_verbosity: int = 0  # Default verbosity level is set to 0
    short_bio: str = ""  # Default short bio is an empty string

class UserLoginDTO(BaseModel):
    username: Optional[str] = None  # Optional username field for login
    password: str
    email: Optional[str] = None  # Optional email field for login
    is_email_login: bool = False

class HackathonAuthDTO(BaseModel):
    username: str
    short_bio: Optional[str] = ""  # Optional short bio for hackathon authentication
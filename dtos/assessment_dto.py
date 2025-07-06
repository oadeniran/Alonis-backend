from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum

# Enum for test types
class TestType(Enum):
    personality_test = "Personality Test"
    mental_health_test = "Mental Health"


class AssessmentDTO(BaseModel):
    user_id: str
    user_input: str
    test_type: TestType
    session_id: str

class AssessmenPredictionDTO(BaseModel):
    user_id: str
    session_id: str
    test_type: TestType
    data_extracted: Optional[Dict[str, Any]] = None
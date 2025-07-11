from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

# Enum for test types
class TestType(Enum):
    personality_test = "personality_test"
    mental_health_test = "mindlab"


class AssessmentDTO(BaseModel):
    user_id: str
    user_input: str
    test_type: TestType = Field(..., description="Type of the test being taken")
    session_id: str

class AssessmenPredictionDTO(BaseModel):
    user_id: str
    session_id: str
    test_type: TestType
    data_extracted: Optional[Dict[str, Any]] = None
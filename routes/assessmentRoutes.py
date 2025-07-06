from fastapi import APIRouter
from dtos.assessment_dto import AssessmentDTO, AssessmenPredictionDTO
from routesLogic import assessment
import uuid

router = APIRouter()

@router.post("/assessment")
async def assessment_route(assessment_details: AssessmentDTO):
    """
    Endpoint to handle assessment requests.
    
    Args:
        assessment_details (AssessmentDTO): Data Transfer Object containing user input, test type, and session ID.
    
    Returns:
        dict: A dictionary containing the response message and any additional data.
    """
    return await assessment.assessment_logic(assessment_details)

@router.post("/assessment-result")
async def assessment_result_route(assessment_data_for_prediction: AssessmenPredictionDTO):
    """
    Endpoint to handle assessment result requests.
    
    Args:
        assessment_data_for_prediction (AssessmenPredictionDTO): Data Transfer Object containing session ID, test type, and extracted data.
    
    Returns:
        dict: A dictionary containing the response message or extracted data.
    """
    return await assessment.asessment_result_logic(assessment_data_for_prediction)

@router.get("/generate-session-id")
async def generate_session_id():
    """
    Endpoint to generate a new session ID.
    
    Returns:
        dict: A dictionary containing the generated session ID.
    """
    return {"session_id": str(uuid.uuid4())}
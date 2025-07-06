import utils
import chatbot
from dtos.assessment_dto import AssessmentDTO, AssessmenPredictionDTO
from core import userActions
import uuid

async def assessment_logic(assessment_details: AssessmentDTO):
    """
    Logic for handling assessment requests.
    
    Args:
        assessment_dto (AssessmentDTO): Data Transfer Object containing user input, test type, and session ID.
    
    Returns:
        dict: A dictionary containing the response message and any additional data.
    """
    assessment_details_dict = assessment_details.model_dump()
    test_option = assessment_details_dict.get("test_type")
    user_id = assessment_details_dict.get("user_id")
    session_id = assessment_details_dict.get("session_id")
    user_input = assessment_details_dict.get("user_input")
    
    input_info = utils.get_input_format(test_option)
    output_info = utils.get_output_format(test_option)
    verbosity = 2 # Default verbosity level for Now
    sys_template = utils.get_system_template(test_option, output_info, input_info, verbosity)

    test_config = {
                "uid" : user_id,
                "session_id" : session_id,
                "test_option" : test_option,
                "verbosity" : verbosity,
                "input_info" : input_info,
                "output_info" : output_info,
                "system_template" : sys_template
            }

    # Initialize session state if not already set
    userActions.add_user_session(user_id, session_id, test_option,test_config)

    output = chatbot.MindWavebot(uid = user_id, session_id = session_id, message = user_input, system_template=sys_template)

    return output

async def asessment_result_logic(assessment_data_for_prediction: AssessmenPredictionDTO):
    """
    Logic for handling assessment result requests.
    Args:
        assessment_data_for_prediction (AssessmenPredictionDTO): Data Transfer Object containing session ID, test type, and extracted data.
    Returns:
        dict: A dictionary containing the response message or extracted data.
    """
    assessment_data_dict = assessment_data_for_prediction.model_dump()
    session_id = assessment_data_dict.get("session_id")
    test_option = assessment_data_dict.get("test_type")
    data_extracted = assessment_data_dict.get("data_extracted")
    input_info = utils.get_input_format(test_option)
    user_id = assessment_data_dict.get("user_id")

    df_d = utils.convert_dict_to_df(data_extracted)
    prediction = utils.get_prediction(test_option, df_d)
    print("prediction===", prediction)
    report = chatbot.MindwaveReportBot(uid = user_id, session_id = session_id, prediction = prediction, required_info = input_info, curr_test=test_option)
    utils.add_report_to_db(user_id,test_option, session_id, report)
    
    return {"message": "No data extracted for report generation."}
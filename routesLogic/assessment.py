import utils
import chatbot
from dtos.assessment_dto import AssessmentDTO, AssessmenPredictionDTO
from core import userActions, background_tasks
from datetime import datetime
import uuid
import asyncio

async def assessment_logic(assessment_details: AssessmentDTO):
    """
    Logic for handling assessment requests.
    
    Args:
        assessment_dto (AssessmentDTO): Data Transfer Object containing user input, test type, and session ID.
    
    Returns:
        dict: A dictionary containing the response message and any additional data.
    """
    assessment_details_dict = assessment_details.model_dump(mode="json")

    print("assessment_details_dict===", assessment_details_dict)

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
    userActions.add_user_session(user_id, session_id, "assessment_"+test_option,test_config)

    output = chatbot.MindWavebot(uid = user_id, session_id = session_id, message = user_input, system_template=sys_template)

    asyncio.create_task(background_tasks.update_user_embeddings(
        {"user_input": user_input, "response": output},
        user_id,
        meta_data={"assessment_date": datetime.now().isoformat(), "assessment_type": test_option},
        session_id=session_id,
        title="Assessment Information"
    ))

    return output

async def asessment_result_logic(assessment_data_for_prediction: AssessmenPredictionDTO):
    """
    Logic for handling assessment result requests.
    Args:
        assessment_data_for_prediction (AssessmenPredictionDTO): Data Transfer Object containing session ID, test type, and extracted data.
    Returns:
        dict: A dictionary containing the response message or extracted data.
    """
    assessment_data_dict = assessment_data_for_prediction.model_dump(mode="json")

    print("assessment_data_dict===", assessment_data_dict)

    user_id = assessment_data_dict.get("user_id")
    session_id = assessment_data_dict.get("session_id")
    test_option = assessment_data_dict.get("test_type")
    data_extracted = assessment_data_dict.get("data_extracted")

    if data_extracted == {} or data_extracted is None:
        # If no data is extracted, try to fetch it from the database
        data_extracted = userActions.get_extracted_data(user_id, session_id)
        if data_extracted is None:
            return {'message': "No data extracted for this session", 'status_code': 404}
    input_info = utils.get_input_format(test_option)
    

    df_d = utils.convert_dict_to_df(data_extracted)
    prediction = utils.get_prediction(test_option, df_d)
    print("prediction===", prediction)

    # Get the previous report if it exists
    previous_report = userActions.get_last_report_for_assessment_type(user_id, test_option)

    data_extracted_str = utils.dict_to_string(data_extracted)

    report = chatbot.MindwaveReportBot(uid = user_id, session_id = session_id, prediction = prediction, required_info = input_info, curr_test=test_option, data_extracted=data_extracted_str, previous_report=previous_report)
    userActions.add_report_to_db(user_id,test_option, session_id, report)

    asyncio.create_task(background_tasks.update_user_embeddings(
        {"data_extracted": data_extracted, "prediction": prediction, 
         "report": report},
        user_id,
        meta_data={"assessment_date": datetime.now().isoformat(), "assessment_type": test_option},
        session_id=session_id,
        title="Assessment Result"
    ))
    
    return {'report': report, 'status_code' : 200}
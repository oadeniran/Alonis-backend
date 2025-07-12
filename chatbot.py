from langchain_core.messages import  HumanMessage
from langchain_openai import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
)
import re
import json
from openai import OpenAI
from datetime import datetime


from utils import dict_to_string, add_extracted_data_to_db, remove_stage_from_message, extract_dictionary_from_string, clean_and_parse_json
from core.chatActions import add_chat_to_db, get_chat_from_db
from config import OPENAI_API_KEY

def get_todays_date_formatted():
    return datetime.today().strftime('%Y-%m-%d')

LLM = ChatOpenAI(api_key=OPENAI_API_KEY, model_name="gpt-4o-mini", temperature=0.0)

def get_chat_history_for_ai(uid, session_id):
    chat_history, count = get_chat_from_db(uid, session_id)
    new_messages = []
    if not chat_history or count == 0:
        return new_messages
    else:
        for message in chat_history:
            if message['type'] == 'human':
                temp_message = message['message']
                new_messages.append(HumanMessage(content=temp_message))
            else:
                # message = message['message']
                temp_message = message['message']
                new_messages.append(temp_message)

        return new_messages


def extract_stage_from_message(message):
    stage_pattern = re.compile(r'CURRENT_STAGE:\s*(\d+)', re.DOTALL)
    match = stage_pattern.search(message)
    if match:
        curr_stage = match.group(0)
        print("Current stage:", curr_stage)
        return curr_stage
    else:
        print("Error: No stage found in the input string.")
        return None

def MindWavebot(uid, session_id:str, message:str, system_template, verbosity=1):
    add_chat_to_db(uid, session_id, "user", message, message, {})
    
    sys_message = SystemMessagePromptTemplate.from_template(system_template)
    #print(sys_message)

    chat_prompts = ChatPromptTemplate.from_messages(
        [sys_message, MessagesPlaceholder("chat_history"), ("human", "{input}")]
    )

    #print("Chat prompts:", chat_prompts)
    
    chain = chat_prompts | LLM
    
    session_chat_history = get_chat_history_for_ai(uid, session_id)

    # print("Session chat history:", session_chat_history)

    model_response = chain.invoke(
            {"input": message, "chat_history": session_chat_history}
        )
    #print("Model response:", model_response.content)
    #print("Extracting dictionary from diana_response.content 1")
    dictionary_response = extract_dictionary_from_string(model_response.content)
    if not dictionary_response:
        print("Extracting dictionary from diana_response.content 2")
        dictionary_response = clean_and_parse_json(model_response.content)
    
    if dictionary_response:

        print("Extracted dictionary:", dictionary_response)
        
        add_chat_to_db(uid, session_id, "system", model_response.content,"I think I've gotten enough data",{"details_completed":True},)
        print("Added chat to DB with session_id:", session_id)
        add_extracted_data_to_db(uid, session_id, dictionary_response)
        return {
            "message": "I think I've gotten enough data",
            "type" : "system",
            "session_id": session_id,
            "stages" : "completed",
            "dictionary_data": dictionary_response
        }
    else:
        stages = extract_stage_from_message(model_response.content)
        # print("Extracted stages:", stages)
        print(1)
        print("Extracted stages:", stages)
        # print("Extracted stage:", stage)
        output = {}
        output["message"] = remove_stage_from_message(model_response.content)
        output["session_id"] = session_id
        output["type"] = "system"
        output["stages"] = stages

        add_chat_to_db(uid, session_id, "system", model_response.content, output["message"], {'stages': stages, 'details_completed': False})
        return output

def MindwaveReportBot(uid, session_id:str, prediction:str, required_info:str, curr_test,data_extracted=None, previous_report=None):
    
    required_info_s = required_info
  
    system_template = f"""

    You are ALONIS a persoanlized AI and you are very good at evaluating the mental profile or psychological state of your users. 
    
    A {curr_test} assessment was conducted by this user

    The information about the assessment is as follows: {required_info_s}

    The following information was collected from the user based on their assessment: {data_extracted if data_extracted else "Not available"}

    Based on this it has been predicted that the user is {prediction}.

    Also the previous report for this user is as follows: {previous_report if previous_report else "No previous report available"}

    Generate an extensive report based on the information collected and the prediction made by the ML model. You have access to all the information collected from the user and you can use this information to generate the report.

    The report should be detailed and contain the following sections:
    - Assessment Summary (Including comparison with previous reports if available)
    -  Prediction Analysis
    - Behavioral Indicators
    - Comparative Analysis with previous analysis result(if previous report is available)
    - Actionable Recommendations

    ON NO ACCOUNT SHOULD YOU LEAK YOUR GOAL OR MAKE ANY MENTION OF DICTIONARY OR JSON OR ANYTHING THAT WILL GIVE AWAY THE FACT THAT YOU ARE AN AI.

    ** MUST**
    - Speak in a preofessional tone and first person language
    - Use markdown format for the report
    - Do not mention that you are an AI or a bot
    - Do not mention that you are a mental health professional and do not give any medical advice
    - Do not mention that you are a psychologist or a psychiatrist and end the report with a disclaimer that the report is for informational purposes only and should not be used as a substitute for professional medical advice, diagnosis, or treatment.

    RETURN THE REPORT PROPERLY FORMATTE IN MARKDOWN FORMAT.
 
    """

    sys_message = SystemMessagePromptTemplate.from_template(system_template)
    #print(sys_message)

    chat_prompts = ChatPromptTemplate.from_messages(
        [sys_message, MessagesPlaceholder("chat_history")]
    )
    
    chain = chat_prompts | LLM
    
    session_chat_history = get_chat_history_for_ai(uid, session_id)

    model_response = chain.invoke(
            {"chat_history": session_chat_history}
        )
    
    return model_response.content
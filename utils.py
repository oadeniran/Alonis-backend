from db import ragEmbeddingsCollection, extractedDataCollection, reportsCollection, sessionsCollection
from datetime import datetime
from core import chatActions, mental_prediction, big5_personality
import pandas as pd
import re
import json
from azure.storage.blob import BlobServiceClient, ContentSettings
from config import AZURE_BLOB_CONNECTION_STR, EMBEDDINGS_CONTAINER_NAME

POSSIBLE_SELECTIONS = {
    "mindlab": mental_prediction,
    "personality_test": big5_personality
}

VERBOSITY_LEVEL = {
    1: "Direct and concise. Ask straightforward questions with minimal elaboration.",
    2: "Moderate verbosity. Ask questions with some detail and context, providing a bit of expressiveness and guidance.",
    3: "High verbosity and expressiveness. Present scenarios or hypothetical situations and ask questions about how the user would respond to these situations, using their responses to assess and score."
}

def extract_dictionary_from_string(input_string):
    # Regular expression to find dictionary-like structure in the string
    dict_pattern = re.compile(r'\{.*?\}', re.DOTALL)
    
    # Search for the dictionary-like structure
    match = dict_pattern.search(input_string)
    
    if match:
        dict_string = match.group(0)
        
        # Attempt parsing the string to JSON
        dictionary = clean_and_parse_json(dict_string)
        return dictionary
    else:
        print("Error: No dictionary-like structure found in the input string.")
        return None

def clean_and_parse_json(input_string):
    # Step 1: Clean input by removing newline characters and excessive whitespace
    cleaned_string = re.sub(r'[\n\t]', '', input_string).strip()
    
    # Step 2: Convert single quotes to double quotes if needed
    cleaned_string = cleaned_string.replace("'", '"')
    
    # Step 3: Handle any trailing commas inside the dictionary
    cleaned_string = re.sub(r',(\s*[\}\]])', r'\1', cleaned_string)
    
    # Step 4: Try to parse the cleaned string into a JSON object
    try:
        dictionary = json.loads(cleaned_string)
        return dictionary
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

def dict_to_string(d, explanations=None):
    #i = 1
    result = []
    if explanations and len(explanations) > 0:
        for key, value in d.items():
            if isinstance(value, dict):
                value_str = ', '.join(f'{k}: {v}' for k, v in value.items())
                result.append(f'{key}: {explanations[key]}: value(numeric) can be {value_str}')
            elif isinstance(value, range):
                value_str = f'{value.start} to {value.stop - 1}'
                result.append(f'{key}: {explanations[key]}: score user with a numeric value between {value_str}')
            else:
                result.append(f'{key}: {value}')
        
        #i+=1
    else:
        for key, value in d.items():
            if isinstance(value, dict):
                value_str = ', '.join(f'{k}: {v}' for k, v in value.items())
                result.append(f'{key}: {value_str}')
            elif isinstance(value, range):
                value_str = f'{value.start} to {value.stop - 1}'
                result.append(f'{key}: {value_str}')
            else:
                result.append(f'{key}: {value}')
            
            #i+=1

    return '\n'.join(result)

def remove_stage_from_message(message):
    pattern = r'CURRENT_STAGE:\s*\d+'

    # Replace the CURRENT_STAGE part with an empty string
    cleaned_message = re.sub(pattern, '', message)

    return cleaned_message

def get_input_format(selection):
    d = POSSIBLE_SELECTIONS[selection].MAPPINGS
    explanations = POSSIBLE_SELECTIONS[selection].EXPLANATIONS
    return dict_to_string(d, explanations)

def get_output_format(selection):
    output_format = dict_to_string(POSSIBLE_SELECTIONS[selection].OUTPUT_FORMAT)
    return output_format

def get_system_template(selection,output_format, required_info_s ,verbosity):

    sys_template = POSSIBLE_SELECTIONS[selection].get_sys_template(output_format, required_info_s, verbosity)

    return sys_template

def convert_dict_to_df(d):
  df = pd.DataFrame(columns=d.keys())
  df.loc[0] = d.values()
  return df

def get_prediction(selection, data):
    return POSSIBLE_SELECTIONS[selection].get_prediction(data)

def add_extracted_data_to_db(uid, session_id:str, data:dict):
    document = {
        "uid":uid,
        "session_id":session_id,
        "data":data,
        "date":datetime.now(),
    }
    extractedDataCollection.insert_one(document)

def remove_embedded_data(session_id:str):
    print("Removing embedded data for session_id:", session_id)
    ragEmbeddingsCollection.delete_many({"current_session_id":session_id})
    print("Removed embedded data for session_id:", session_id)

def upload_file_bytes(blob_name, file_bytes, content_type="application/octet-stream", container_name=EMBEDDINGS_CONTAINER_NAME,):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            AZURE_BLOB_CONNECTION_STR
        )
        
        container_client = blob_service_client.get_container_client(
            container_name
        )

        blob_client = container_client.get_blob_client(blob_name)

        # Explicitly delete if exists
        if blob_client.exists():
            blob_client.delete_blob()

        content_settings = ContentSettings(
            content_type=content_type,
            content_disposition="inline",
        )

        blob_client.upload_blob(
            file_bytes,
            overwrite=True,
            blob_type="BlockBlob",
            content_settings=content_settings,
        )

        print(f"File {blob_name} uploaded successfully.")
        return blob_client.url

    except Exception as ex:
        print(f"Error during file upload: {ex}")
        raise

def download_file_bytes(blob_name, container_name=EMBEDDINGS_CONTAINER_NAME):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            AZURE_BLOB_CONNECTION_STR
        )
        
        container_client = blob_service_client.get_container_client(
            container_name
        )

        blob_client = container_client.get_blob_client(blob_name)

        if not blob_client.exists():
            print(f"Blob {blob_name} does not exist.")
            return None

        file_bytes = blob_client.download_blob().readall()
        print(f"File {blob_name} downloaded successfully.")
        return file_bytes

    except Exception as ex:
        print(f"Error during file download: {ex}")
        raise

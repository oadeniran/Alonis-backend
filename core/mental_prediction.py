from config import mentalHealthModel
import os
import re
import json
from openai import OpenAI
from datetime import datetime
from datetime import datetime

def get_todays_date_formatted():
    return datetime.today().strftime('%Y-%m-%d')

VERBOSITY_LEVEL = {
    1: "Direct and concise. Ask straightforward questions with minimal elaboration.",
    2: "Moderate verbosity. Ask questions with some detail and context, providing a bit of expressiveness and guidance.",
    3: "High verbosity and expressiveness. Present scenarios or hypothetical situations and ask questions about how the user would respond to these situations, using their responses to assess and score."
}


MAPPINGS = {
    'Admit Mistakes': {'NO': 0, 'YES': 1},
    'Aggressive Response': {'NO': 0, 'YES': 1},
    'Anorxia': {'NO': 0, 'YES': 1},
    'Authority Respect': {'NO': 0, 'YES': 1},
    'Concentration': range(1, 11),
    'Euphoric': {'Most-Often': 10, 'Seldom': 1, 'Sometimes': 4, 'Usually': 6},
    'Exhausted': {'Most-Often': 10, 'Seldom': 1, 'Sometimes': 4, 'Usually': 6},
    'Ignore & Move-On': {'NO': 0, 'YES': 1},
    'Mood Swing': {'NO': 0, 'YES': 1},
    'Nervous Break-down': {'NO': 0, 'YES': 1},
    'Optimisim': range(1, 11),
    'Overthinking': {'NO': 0, 'YES': 1},
    'Sadness': {'Most-Often': 10, 'Seldom': 1, 'Sometimes': 4, 'Usually': 6},
    'Sexual Activity': range(1, 11),
    'Sleep dissorder': {'Most-Often': 10, 'Seldom': 1, 'Sometimes': 4, 'Usually': 6},
    'Suicidal thoughts': {'NO': 0, 'YES': 1, 'YES ': 1},
    'Try-Explanation': {'NO': 0, 'YES': 1}
}




EXPLANATIONS = {
    'Admit Mistakes': 'The act of acknowledging errors or faults and accepting responsibility for them.',
    'Aggressive Response': 'A reaction marked by hostility or anger, often in response to a perceived threat or challenge.',
    'Anorxia': 'An eating disorder characterized by an intense fear of gaining weight, leading to restricted eating and extreme weight loss.',
    'Authority Respect': 'An attitude or behavior of showing deference and acknowledgment towards figures of authority or power.',
    'Concentration': 'The mental ability to focus attention and effort on a specific task or activity.',
    'Euphoric': 'An intense feeling of excitement or happiness, often associated with an overwhelming sense of well-being.',
    'Exhausted': 'A physical or mental state of extreme tiredness or fatigue, often resulting from prolonged stress or activity.',
    'Ignore & Move-On': 'A coping mechanism where one chooses to overlook or dismiss a situation and continue forward without addressing it.',
    'Mood Swing': 'An abrupt change in emotional state, typically ranging from extreme highs to extreme lows.',
    'Nervous Break-down': 'A state of acute mental or emotional stress that leads to a temporary inability to function normally.',
    'Optimisim': 'A general attitude of hopefulness or positivity, often expecting favorable outcomes.',
    'Overthinking': 'The act of dwelling on a problem or situation excessively, often leading to increased anxiety and indecision.',
    'Sadness': 'A state of feeling sorrowful or unhappy, often associated with loss or disappointment.',
    'Sexual Activity': 'Physical acts of intimacy or sexual engagement between individuals.',
    'Sleep dissorder': 'A condition that impairs sleep patterns, leading to difficulty falling asleep, staying asleep, or restful sleep.',
    'Suicidal thoughts': 'Persistent thoughts or considerations about ending one’s own life, often stemming from deep emotional pain or despair.',
    'Try-Explanation': 'The act of attempting to provide clarification or reasoning for a particular behavior, decision, or event.'
}


OUTPUT_FORMAT = {
    'Admit Mistakes': 'binary, 0 or 1',
    'Aggressive Response': 'binary, 0 or 1',
    'Anorxia': 'binary, 0 or 1',
    'Authority Respect': 'binary, 0 or 1',
    'Concentration': 'score from 1 to 10',
    'Euphoric': 'score from 1 to 10',
    'Exhausted': 'score from 1 to 10',
    'Ignore & Move-On': 'binary, 0 or 1',
    'Mood Swing': 'binary, 0 or 1',
    'Nervous Break-down': 'binary, 0 or 1',
    'Optimism': 'score from 1 to 10',
    'Overthinking': 'binary, 0 or 1',
    'Sadness': 'score from 1 to 10',
    'Sexual Activity': 'score from 1 to 10',
    'Sleep dissorder': 'score from 1 to 10',
    'Suicidal thoughts': 'binary, 0 or 1',
    'Try-Explanation': 'binary, 0 or 1'
}


TARGET_MAPPING = {0: 'Bipolar Type-1', 1: 'Bipolar Type-2', 2: 'Depression', 3: 'Normal'}

def get_sys_template(output_format, required_info_s, verbosity):

    sys_template = f"""

    You are a psychology expert and you are very good at evaluating the mental profile or psychological state of a person. Some information needs to be extracted and you can come up with scenarios and real world situsations where the user's response can be used to score the user for that information.
    You Love your job and you are very good at it. You are also a very very jovial person and you are good with words. A little information for you though, the current year is 2024 and today's date is {get_todays_date_formatted()}.
    You are to extract the following information from the user:

    {required_info_s}

    However, you do not want to explicitly ask the user for this information. You want to extract this information from the user's responses to your questions. You should ask questions that will help you deduce the information you need.

    When there is no user input, you should prompt the user for the information you need to extract.

    Your verbosity level is set to {verbosity} and that means you {VERBOSITY_LEVEL[verbosity]}.

    ON NO ACCOUNT SHOULD YOU LEAK YOUR GOAL OR MAKE ANY MENTION OF DICTIONARY OR JSON OR ANYTHING THAT WILL GIVE AWAY THE FACT THAT YOU ARE AN AI.

    While collecting information, end the message with excatly this text: CURRENT_STAGE: <Ind> where Ind is the index of the input being collected to indicate that you are currently collecting the information for that stage.

    When you have all the information ready, return the dictionary and DO NOT add any preambles or postambles or summary to the dictionary OUTPUT and Always output a dictionary in this format (field name as key and score as value) ONLY WHEN YOU HAVE ALL THE INFORMATION {output_format}.DO NOT add any preambles or postambles or summary to the dictionary OUTPUT. 

    As long as you can deduce that all information is collected from chat history, return the dictionary ONLY regardless of input from user.
    """

    return sys_template



def get_prediction(data):
  predicted_proba = mentalHealthModel.predict_proba(data.values)
  predicted_class = mentalHealthModel.predict(data.values)
  return f"User is predicted to be {TARGET_MAPPING[predicted_class[0]]} with a probability of {max(predicted_proba[0])}", 
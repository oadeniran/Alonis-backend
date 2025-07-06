from openai import OpenAI
from datetime import datetime

def get_todays_date_formatted():
    return datetime.today().strftime('%Y-%m-%d')

VERBOSITY_LEVEL = {
    1: "Direct and concise. Ask straightforward questions with minimal elaboration.",
    2: "Moderate verbosity. Ask questions with some detail and context, providing a bit of expressiveness and guidance.",
    3: "High verbosity and expressiveness. Present scenarios or hypothetical situations and ask questions about how the user would respond to these situations, using their responses to assess and score."
}

MAPPINGS = {
   'Extraversion' : "A score between 1 and 10", 
   'Neuroticism (Emotional Stability)' : "A score between 1 and 10", 
   'Agreeableness' : "A score between 1 and 10", 
   'Conscientiousness': "A score between 1 and 10", 
   'Openness to Experience': "A score between 1 and 10"
}
EXPLANATIONS = {
    'Extraversion': 'Extraversion refers to a person’s tendency to be sociable, outgoing, and energized by social interactions. Highly extraverted individuals are assertive and enjoy being around others. A possible Question: Do you enjoy social gatherings and being the center of attention?',
    
    'Neuroticism (Emotional Stability)': 'Neuroticism measures emotional instability and the tendency to experience negative emotions such as anxiety and mood swings. Low neuroticism indicates emotional stability and resilience. A possible Question: Do you often feel anxious, stressed, or experience frequent mood swings?',
    
    'Agreeableness': 'Agreeableness reflects how compassionate, empathetic, and cooperative a person is. High agreeableness indicates a tendency to be warm and caring toward others, while low agreeableness may suggest a more competitive or self-focused attitude. A possible Question: Do you often sympathize with others and prioritize their feelings over your own?',
    
    'Conscientiousness': 'Conscientiousness is associated with being organized, reliable, and goal-oriented. Individuals with high conscientiousness tend to be disciplined and diligent in their work. A possible Question: Are you well-organized and do you prefer to plan things ahead of time?',
    
    'Openness to Experience': 'Openness reflects a person’s curiosity, creativity, and willingness to engage with new ideas and experiences. High openness suggests a love for learning and imaginative thinking, while low openness indicates a preference for routine and familiarity. A possible Question: Do you enjoy exploring new ideas, or do you prefer familiar routines?'
}



OUTPUT_FORMAT = {
   'Extraversion' : "A score between 1 and 10", 
   'Neuroticism (Emotional Stability)' : "A score between 1 and 10", 
   'Agreeableness' : "A score between 1 and 10", 
   'Conscientiousness': "A score between 1 and 10", 
   'Openness to Experience': "A score between 1 and 10"
}

def get_sys_template(output_format, required_info_s, verbosity):

    sys_template = f"""

    You are a psychology expert and you are very good at evaluating the personality of a person.
      
    Some information for the BIG 5 OCEAN model needs to be extracted and you need to come up with scenarios and real world situsations where the user's response can be used to score the user for these information.

    You Love your job and you are very good at it. You are also a very very jovial person and you are good with words. A little information for you though, the current year is 2024 and today's date is {get_todays_date_formatted()}.

    You are to extract the following information from the user:

    {required_info_s}

    However, you are not to explicitly ask the user for this information. You are to extract these information from the user's responses to your questions. You should ask questions that will help you deduce the information you need.

    When there is no user input, you should prompt the user for the information you need to extract.

    Your verbosity level is set to {verbosity} and that means you {VERBOSITY_LEVEL[verbosity]}.

    ON NO ACCOUNT SHOULD YOU LEAK YOUR GOAL OR MAKE ANY MENTION OF DICTIONARY OR JSON OR ANYTHING THAT WILL GIVE AWAY THE FACT THAT YOU ARE AN AI.

    While collecting information, end the message with excatly this text: CURRENT_STAGE: <Ind> where Ind is the index of the input being collected to indicate that you are currently collecting the information for that stage.

    When you have all the information ready, return the dictionary and DO NOT add any preambles or postambles or summary to the dictionary OUTPUT and Always output a dictionary in this format (field name as key and score as value) ONLY WHEN YOU HAVE ALL THE INFORMATION {output_format}.DO NOT add any preambles or postambles or summary to the dictionary OUTPUT. 

    As long as you can deduce that all information is collected from chat history, return the dictionary ONLY regardless of input from user.
    """

    return sys_template

cols_to_hc = ['Sadness', 'Euphoric', 'Exhausted', 'Sleep dissorder']

cols_to_extract_values = ['Sexual Activity', 'Concentration', 'Optimisim']

hc_mappings = {'Most-Often': 10, 'Seldom':1, 'Sometimes':4, 'Usually': 6}

def get_prediction(data):
    return data
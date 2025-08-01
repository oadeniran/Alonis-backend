import ragImplementation as rag
from core.chatActions import add_chat_to_db, get_chat_from_db
from langchain_core.messages import  HumanMessage
from utils import extract_dictionary_from_string, clean_and_parse_json

def get_chat_history_for_ai(uid, session_id):
    chat_history, count = get_chat_from_db(uid, session_id, talks_session=True)
    new_messages = []
    if not chat_history:
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

def get_context_doc_list(context, session_id):
    return rag.create_docs(context, session_id)

def save_session_embeddings(text, user_id, api_key):
    docs = rag.create_docs(text)
    rag.create_update_embeddings_for_user(docs, api_key, user_id)
    return "saved"

def create_retriever(context_docs):
    return rag.create_retriever(context_docs)

async def load_retriever(uid):
    return await rag.load_user_retriever(uid)

def load_model(retriever, uid, session_id,flow_name = None, flow_context = None):
    if flow_name is not None and flow_context is not None:
        return rag.load_model(retriever, [], flow = {'name': flow_name, 
                                                     'context' : flow_context,})
    else:
        # If not in quote flow, we can use the chat history for the session
        return rag.load_model(retriever, get_chat_history_for_ai(uid, session_id))

def letsTalk(message, model, uid, session_id):
    add_chat_to_db(uid, session_id, "user", message, {}, talks_session=True)
    response = model.invoke({"input": message})
    answer = response["answer"]
    print("Answer:", answer)
    add_chat_to_db(uid, session_id, "system", answer, {}, talks_session=True)
    return answer

def getQuote(model, uid):
    response = model.invoke({'input': "Give me a unique personalized quote for today"})
    quote_text = response["answer"]

    quote = extract_dictionary_from_string(quote_text)

    if not quote:
        print("Extracting dictionary from diana_response.content 2")
        quote = clean_and_parse_json(quote_text)
    print("Quote generated:", quote)
    return {
        "quote": quote,
        "uid": uid
    }

def getStory(model, uid):
    response = model.invoke({'input': "Give me a unique personalized story for today"})
    story_text = response["answer"]

    story = story_text.strip()

    print("Story generated:", story)
    return {
        "story": story,
        "uid": uid
    }

async def talkToMe(uid, session_id, message, context_doc_list= None):
    if context_doc_list is not None:
        retriever = create_retriever(context_doc_list)
    else:
        retriever = await load_retriever(uid)

    model = load_model(retriever, uid, session_id)
    return letsTalk(message, model, uid, session_id)

async def giveMeAQuoute(uid, previous_quotes=None):
    retriever = await load_retriever(uid)
    model = load_model(retriever, uid, None, flow_name='quote_flow', flow_context = f""" The past 10 previous quote seen by user are: 
                                                        {previous_quotes if previous_quotes else "No previous quotes available."}
                                                    """)
    return getQuote(model, uid)

async def giveMeAStory(uid, previous_stories_text):
    retriever = await load_retriever(uid)
    model = load_model(retriever, uid, None, flow_name='story_flow', flow_context=f""" The past 10 previous stories seen by user are: 
                                                        {previous_stories_text if previous_stories_text else "No previous stories available."}
                                                    """)
    return getStory(model, uid)
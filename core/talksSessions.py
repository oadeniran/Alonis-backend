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

def load_retriever(uid):
    return rag.load_user_retriever(uid)

def load_model(retriever, uid, session_id, quote_flow=False, current_quote=None):
    if quote_flow:
        return rag.load_model(retriever, [], quote_flow=True, current_quote=current_quote)
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

def talkToMe(uid, session_id, message, context_doc_list= None):
    if context_doc_list is not None:
        retriever = create_retriever(context_doc_list)
    else:
        retriever = load_retriever(uid)

    model = load_model(retriever, uid, session_id)
    return letsTalk(message, model, uid, session_id)

def giveMeAQuoute(uid, current_quote=None):
    retriever = load_retriever(uid)
    model = load_model(retriever, uid, None, quote_flow=True, current_quote=current_quote)
    return getQuote(model, uid)

    
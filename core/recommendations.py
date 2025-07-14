import requests
from config import QLOO_API_URL, QLOO_API_KEY
import ragImplementation as rag
from utils import extract_list_from_string, dict_to_string
from core.userActions import get_current_alonis_recommendations
from datetime import datetime

def get_alonis_recommendations(user_id, limit=10):
    """
    Get Pernaolized Alonis recommendations based on user data and interactions.
    """

    retriever = rag.load_user_retriever(user_id)

    current_user_recommendations = get_current_alonis_recommendations(user_id, limit)

    if current_user_recommendations:
        recommendation_context = dict_to_string(current_user_recommendations)
    else:
        recommendation_context = "No previous recommendations found."

    model = rag.load_model(retriever, [], recommendation_flow=True, recommendation_context=recommendation_context)

    recommendation_text  = model.invoke({"input": "Generate personalized recommendations based on the user's data and interactions."}).get("answer", "")

    new_recommendations = extract_list_from_string(recommendation_text)

    if isinstance(new_recommendations[0], list):
        return new_recommendations[0]
    else:
        print("No recommendations generated or the format is incorrect.")
        print("Recommendation text:", recommendation_text)
        print("New recommendations:", new_recommendations)






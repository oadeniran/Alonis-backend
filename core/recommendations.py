import ragImplementation as rag
from utils import extract_list_from_string, dict_to_string
from core.userActions import get_current_alonis_recommendations, get_user_page_for_qloo_recommendations, update_user_page_for_qloo_recommendations
import random
from core import qloo_core
import asyncio

async def get_alonis_recommendations(user_id, limit=10):
    """
    Get Pernaolized Alonis recommendations based on user data and interactions.
    """

    retriever = await rag.load_user_retriever(user_id)

    current_user_recommendations = get_current_alonis_recommendations(user_id, limit)

    if current_user_recommendations:
        recommendation_context = dict_to_string(current_user_recommendations)
    else:
        recommendation_context = "No previous recommendations found."

    model = await asyncio.to_thread(
        lambda: rag.load_model(retriever, [], flow={
            'name': 'recommendation_flow', 
            'context': f"""The current recommendations seen by user are: 
                {recommendation_context}
            """
        })
    )

    recommendation_text  = model.invoke({"input": "Generate personalized recommendations based on the user's data and interactions."}).get("answer", "")

    new_recommendations = await asyncio.to_thread(extract_list_from_string, recommendation_text)

    if isinstance(new_recommendations[0], list):
        return new_recommendations[0]
    else:
        print("No recommendations generated or the format is incorrect.")
        print("Recommendation text:", recommendation_text)
        print("New recommendations:", new_recommendations)

async def get_alonis_qloo_powered_recommendations(user_id, rec_type='alonis_recommendation_movies',):
    """
    Get Alonis recommendations powered by Qloo based on user preferences.
    """
    
    if not user_id or user_id == "":
        return {"error": "Please sign up/login to continue"}
    
    recommendations = None
    
    # Get current page for Qloo recommendations for user
    current_page = await asyncio.to_thread(get_user_page_for_qloo_recommendations,user_id)
    
    # Step is get all possible tags for movies and tv shows
    # Build Model to return list of tags to use based on user data
    # Use Qloo API to get recommendations based on tags and current page
    # Use model to add a context on how the recommendation is a good fit for the user
    recommendations_to_get = [rec_type]
    recommendations_result = []
    if rec_type == 'alonis_recommendation_movies':
        # We need to fetch both Tv series and movies if its alonis_recommendation_movies
        recommendations_to_get.append('alonis_recommendation_tv_shows')

    for rec_type in recommendations_to_get:
        # 1st get tags for movies and tv shows
        tags = await asyncio.to_thread(qloo_core.get_qloo_tags_to_select_from, rec_type.replace('alonis_recommendation_', ''))
        # 2nd Load the model to get tags based on user data
        retriever = await rag.load_user_retriever(user_id)
        model = await asyncio.to_thread(rag.load_model, retriever, [], flow = {
            'name': 'tag_selection_flow', 
            'context' : f""" The current tags that can be selected for {rec_type.replace('alonis_recommendation_', '')} are
                {dict_to_string(tags)}

            The recommendation tags including number of times that have been shown to user are {dict_to_string(current_page.get(rec_type, {})) if rec_type in current_page else "No previous tags shown to user."}
            """
        })
        selected_tags_str = model.invoke({"input": "Select the tags that are appropriate for the user based on their data and past interactions."}).get("answer", "")
        selected_tags = selected_tags_str.split(",") if selected_tags_str else []
        if selected_tags:
            selected_tags = [tag.strip() for tag in selected_tags if tag.strip().isdigit()]
            selected_tags = [int(tag) for tag in selected_tags]
            print(f"Selected tags for {rec_type}: {selected_tags} by model")
            final_tags = {k: v for k, v in tags.items() if k in selected_tags}
        else:
            selected_tags = random.sample(list(tags.keys()), 3)  # Fallback to random selection if no tags are selected
            print(f"Selected tags for {rec_type}: {selected_tags} by random selection")
            final_tags = {k: v for k, v in tags.items() if k in selected_tags}
        
        # update the page for each tags selecetd and create if not exists
        for _, tag in final_tags.items():
            tag_id = tag.get("id")
            if tag_id is None:
                print(f"Skipping tag {tag} as it has no ID")
                continue
            if rec_type not in current_page:
                current_page[rec_type] = {}

            if tag_id not in current_page.get(rec_type, {}):
                current_page[rec_type][tag_id] = 1
            else:
                current_page[rec_type][tag_id] += 1
        
        #page to use is the updated rec_type in current_page
        page_to_use = current_page.get(rec_type, {})
        
        # 3rd get recommendations from Qloo API based on selected tags and current page
        recommendations = await asyncio.to_thread(qloo_core.get_qloo_recommendations, rec_type.replace('alonis_recommendation_', ''), final_tags, page=page_to_use)

        # Get the model to generate context for the recommendations
        # for rec in recommendations:
        #     model = rag.load_model(retriever, [], flow = {
        #     'name': 'recommendation_context_flow', 
        #     'context' : f""" The current recommendation is  
        #         {dict_to_string(rec)}
        #     """
        #     })
        #     context_text = model.invoke({"input": "Generate a context for this recommendation based on the user's data and interactions."}).get("answer", "")
        #     rec['context'] = context_text
        #     rec['extra_data_string'] = dict_to_string(rec.get('extra_data', {}))
        def enrich_recommendation(rec):
            # copy the recommendation to avoid modifying the original
            rec_ = rec.copy()
            rec_['tags_original'] = None
            model = rag.load_model(retriever, [], flow = {
                'name': 'recommendation_context_flow', 
                'context' : f""" The current recommendation is  
                    {dict_to_string(rec_)}
                """
            })
            context_text = model.invoke({"input": "Generate a context for this recommendation based on the user's data and interactions."}).get("answer", "")
            rec['context'] = context_text
            rec['extra_data_string'] = dict_to_string(rec.get('extra_data', {}), normalize_text=True)
            return rec
        
        recommendations = await asyncio.gather(*[
            asyncio.to_thread(enrich_recommendation, rec) for rec in recommendations
        ])

        # Update the user page for Qloo recommendations
        update_user_page_for_qloo_recommendations(user_id, current_page)

        recommendations_result += recommendations

        # print(f"Recommendations for {rec_type} on page {current_page}: {recommendations}")
    
    return recommendations_result if recommendations_result else {"error": "No recommendations found or an error occurred."}



from ragImplementation import create_embeddings_for_user, create_docs, update_embeddings_for_user
from core.userActions import add_recommendations, confirm_to_add_more_alonis_recommendations
from core.recommendations import get_alonis_recommendations, get_alonis_qloo_powered_recommendations
import asyncio
from datetime import datetime
import traceback as tb
from utils import dict_to_string
#Ide
def serialize_dict_to_text(data: dict, indent: int = 0) -> str:
    """
    Serialize a dictionary to a formatted string with indentation.
    
    Args:
        data (dict): The dictionary to serialize.
        indent (int): The number of spaces to use for indentation.
    
    Returns:
        str: A formatted string representation of the dictionary.
    """
    return dict_to_string(data, indent=indent)

async def init_user_embeddings(user_data: str):

   # Build the context from user data
    context = {
       'context': {
           'User Signup data': {'content': await asyncio.to_thread(serialize_dict_to_text, user_data, 2),
              'metadata': {
                'source': 'user_signup',
                'timestamp': datetime.now().isoformat(),
              }
           }
       },
    }

    # Create doc from context
    docs = await asyncio.to_thread(create_docs, context, "")

    # Extract user_id from user_data
    user_id = user_data.get('uid', 'default_user')

    # Create embeddings for the user
    await create_embeddings_for_user(docs, user_id)

async def update_user_embeddings(data, user_id: str, meta_data = {}, session_id = "", title = "Context Data"):
    """
    Update the embeddings for a user with new data.
    """
    # Build the context from user data
    context = {
        'context': {
            title: {"content" : await asyncio.to_thread(serialize_dict_to_text, data, 2) if isinstance(data, dict) else data,
                    'metadata': {
                        'source': 'user_update',
                        **meta_data
                    }
                }
            }
        }

    # Create doc from context
    docs = await asyncio.to_thread(create_docs, context, session_id)

    # Update embeddings for the user
    await update_embeddings_for_user(docs, user_id)

    await generate_alonis_recommendations_for_user(user_id)

async def generate_alonis_recommendations(user_id: str):
    """
    Generate personalized Alonis recommendations for a user.
    """

    if await asyncio.to_thread(confirm_to_add_more_alonis_recommendations, user_id, 'alonis_recommendation'):
        # Call the function to get Alonis recommendations
        recommendations = await get_alonis_recommendations(user_id)

        if recommendations:
            # Add the recommendations to the database
            resp = await asyncio.to_thread(add_recommendations, user_id, recommendations, rec_type='alonis_recommendation')
            print(f"Recommendations added for user {user_id}: {resp}")
            # Return a success message
            return {"message": "Recommendations added successfully", "status_code": 200}
        else:
            print(f"No recommendations generated for user {user_id}")
            return {"message": "No recommendations generated", "status_code": 404}
    else:
        print(f"User {user_id} does not need new recommendations for now.")
        return {"message": "Recommendations already generated for this user", "status_code": 200}
        
async def generate_alonis_recommendations_movies(user_id: str):
    """
    Generate personalized Alonis movie recommendations for a user.
    """
    if await asyncio.to_thread(confirm_to_add_more_alonis_recommendations, user_id, 'alonis_recommendation_movies'):
        recommendations = await get_alonis_qloo_powered_recommendations(user_id, rec_type='alonis_recommendation_movies')

        if recommendations:
            resp = await asyncio.to_thread(add_recommendations, user_id, recommendations, rec_type='alonis_recommendation_movies')
            print(f"Movie recommendations added for user {user_id}: {resp}")
            return {"message": "Movie recommendations added successfully", "status_code": 200}
        else:
            print(f"No movie recommendations generated for user {user_id}")
            return {"message": "No movie recommendations generated", "status_code": 404}
    else:
        print(f"User {user_id} does not need new movie recommendations for now.")
        return {"message": "Movie recommendations already generated for this user", "status_code": 200}
        
async def generate_alonis_recommendations_songs(user_id: str):
    """
    Generate personalized Alonis song recommendations for a user.
    """
    pass
    # if confirm_to_add_more_alonis_recommendations(user_id, 'alonis_recommendation_songs'):
    #     recommendations = await asyncio.to_thread(get_alonis_recommendations, user_id, rec_type='alonis_recommendation_songs')

    #     if recommendations:
    #         resp = await asyncio.to_thread(add_recommendations, user_id, recommendations, rec_type='alonis_recommendation_songs')
    #         print(f"Song recommendations added for user {user_id}: {resp}")
    #         return {"message": "Song recommendations added successfully", "status_code": 200}
    #     else:
    #         print(f"No song recommendations generated for user {user_id}")
    #         return {"message": "No song recommendations generated", "status_code": 404}

async def generate_alonis_recommendations_books(user_id: str):
    """
    Generate personalized Alonis book recommendations for a user.
    """
    if await asyncio.to_thread(confirm_to_add_more_alonis_recommendations, user_id, 'alonis_recommendation_books'):
        recommendations = await get_alonis_qloo_powered_recommendations(user_id, rec_type='alonis_recommendation_books')

        if recommendations:
            resp = await asyncio.to_thread(add_recommendations, user_id, recommendations, rec_type='alonis_recommendation_books')
            print(f"Book recommendations added for user {user_id}: {resp}")
            return {"message": "Book recommendations added successfully", "status_code": 200}
        else:
            print(f"No book recommendations generated for user {user_id}")
            return {"message": "No book recommendations generated", "status_code": 404}
    else:
        print(f"User {user_id} does not need new book recommendations for now.")
        return {"message": "Book recommendations already generated for this user", "status_code": 200}

async def generate_alonis_recommendations_news(user_id: str):
    """
    Generate personalized Alonis news recommendations for a user.
    """
    pass
    # if confirm_to_add_more_alonis_recommendations(user_id, 'alonis_recommendation_news'):
    #     recommendations = await asyncio.to_thread(get_alonis_recommendations, user_id, rec_type='alonis_recommendation_news')

    #     if recommendations:
    #         resp = await asyncio.to_thread(add_recommendations, user_id, recommendations, rec_type='alonis_recommendation_news')
    #         print(f"News recommendations added for user {user_id}: {resp}")
    #         return {"message": "News recommendations added successfully", "status_code": 200}
    #     else:
    #         print(f"No news recommendations generated for user {user_id}")
    #         return {"message": "No news recommendations generated", "status_code": 404}

async def generate_alonis_recommendations_for_user(user_id: str):
    """
    Generate all types of Alonis recommendations for a user.
    """
    try:
        await asyncio.gather(
            generate_alonis_recommendations(user_id),
            generate_alonis_recommendations_movies(user_id),
            generate_alonis_recommendations_books(user_id),
            generate_alonis_recommendations_songs(user_id),
            generate_alonis_recommendations_news(user_id)
        )
    except Exception as e:
        print(f"Error generating recommendations for user {user_id}: {e}")

async def run_sequenced_user_login_tasks(uid: str, username: str ,login_count: int):
    try:
        # Step 1: Update embeddings
        await update_user_embeddings(
            f"User {username} logged in at {datetime.now()}",
            uid,
            meta_data={"login_time": datetime.now().isoformat()},
            title="User Login"
        )

        # Step 2: Generate general recommendations

        # Step 3: Run books and movies recommendations in parallel
        if login_count > 1:
            await generate_alonis_recommendations_for_user(uid)

    except Exception as e:
        print(f"Error running sequenced tasks for user {uid}: {e}")
        print(tb.format_exc())
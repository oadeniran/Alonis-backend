from ragImplementation import create_embeddings_for_user, create_docs, update_embeddings_for_user
from core.userActions import add_recommendations, confirm_to_add_more_alonis_recommendations
from core.recommendations import get_alonis_recommendations
import asyncio
from datetime import datetime
def serialize_dict_to_text(data: dict, indent: int = 0) -> str:
    lines = []
    prefix = " " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(serialize_dict_to_text(value, indent + 2))
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    lines.append(serialize_dict_to_text(item, indent + 2))
                else:
                    lines.append(f"{' ' * (indent + 2)}- {item}")
        else:
            lines.append(f"{prefix}{key}: {value}")
    return "\n".join(lines)

async def init_user_embeddings(user_data: str):

   # Build the context from user data
    context = {
       'context': {
           'User Signup data': await asyncio.to_thread(serialize_dict_to_text, user_data, 2)
       },
       'metadata': {
           'source': 'user_signup'
       }
    }

    # Create doc from context
    docs = await asyncio.to_thread(create_docs, context, "")

    # Extract user_id from user_data
    user_id = user_data.get('uid', 'default_user')

    # Create embeddings for the user
    await asyncio.to_thread(create_embeddings_for_user, docs, user_id)

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
    await asyncio.to_thread(update_embeddings_for_user, docs, user_id)

async def generate_alonis_recommendations(user_id: str):
    """
    Generate personalized Alonis recommendations for a user.
    """

    if confirm_to_add_more_alonis_recommendations(user_id, 'alonis_recommendation'):
        # Call the function to get Alonis recommendations
        recommendations = await asyncio.to_thread(get_alonis_recommendations, user_id)

        if recommendations:
            # Add the recommendations to the database
            resp = await asyncio.to_thread(add_recommendations, user_id, recommendations, rec_type='alonis_recommendation')
            print(f"Recommendations added for user {user_id}: {resp}")
            # Return a success message
            return {"message": "Recommendations added successfully", "status_code": 200}
        else:
            print(f"No recommendations generated for user {user_id}")
            return {"message": "No recommendations generated", "status_code": 404}
        
async def generate_alonis_recommendations_movies(user_id: str):
    """
    Generate personalized Alonis movie recommendations for a user.
    """
    if confirm_to_add_more_alonis_recommendations(user_id, 'alonis_recommendation_movies'):
        recommendations = await asyncio.to_thread(get_alonis_recommendations, user_id, rec_type='alonis_recommendation_movies')

        if recommendations:
            resp = await asyncio.to_thread(add_recommendations, user_id, recommendations, rec_type='alonis_recommendation_movies')
            print(f"Movie recommendations added for user {user_id}: {resp}")
            return {"message": "Movie recommendations added successfully", "status_code": 200}
        else:
            print(f"No movie recommendations generated for user {user_id}")
            return {"message": "No movie recommendations generated", "status_code": 404}
        
async def generate_alonis_recommendations_songs(user_id: str):
    """
    Generate personalized Alonis song recommendations for a user.
    """
    if confirm_to_add_more_alonis_recommendations(user_id, 'alonis_recommendation_songs'):
        recommendations = await asyncio.to_thread(get_alonis_recommendations, user_id, rec_type='alonis_recommendation_songs')

        if recommendations:
            resp = await asyncio.to_thread(add_recommendations, user_id, recommendations, rec_type='alonis_recommendation_songs')
            print(f"Song recommendations added for user {user_id}: {resp}")
            return {"message": "Song recommendations added successfully", "status_code": 200}
        else:
            print(f"No song recommendations generated for user {user_id}")
            return {"message": "No song recommendations generated", "status_code": 404}

async def generate_alonis_recommendations_books(user_id: str):
    """
    Generate personalized Alonis book recommendations for a user.
    """
    if confirm_to_add_more_alonis_recommendations(user_id, 'alonis_recommendation_books'):
        recommendations = await asyncio.to_thread(get_alonis_recommendations, user_id, rec_type='alonis_recommendation_books')

        if recommendations:
            resp = await asyncio.to_thread(add_recommendations, user_id, recommendations, rec_type='alonis_recommendation_books')
            print(f"Book recommendations added for user {user_id}: {resp}")
            return {"message": "Book recommendations added successfully", "status_code": 200}
        else:
            print(f"No book recommendations generated for user {user_id}")
            return {"message": "No book recommendations generated", "status_code": 404}

async def generate_alonis_recommendations_news(user_id: str):
    """
    Generate personalized Alonis news recommendations for a user.
    """
    if confirm_to_add_more_alonis_recommendations(user_id, 'alonis_recommendation_news'):
        recommendations = await asyncio.to_thread(get_alonis_recommendations, user_id, rec_type='alonis_recommendation_news')

        if recommendations:
            resp = await asyncio.to_thread(add_recommendations, user_id, recommendations, rec_type='alonis_recommendation_news')
            print(f"News recommendations added for user {user_id}: {resp}")
            return {"message": "News recommendations added successfully", "status_code": 200}
        else:
            print(f"No news recommendations generated for user {user_id}")
            return {"message": "No news recommendations generated", "status_code": 404}

async def run_sequenced_user_login_tasks(uid: str, username: str):
    try:
        # Step 1: Update embeddings
        await update_user_embeddings(
            f"User {username} logged in at {datetime.now()}",
            uid,
            meta_data={"login_time": datetime.now().isoformat()},
            title="User Login"
        )

        # Step 2: Generate recommendations after embeddings update
        await generate_alonis_recommendations(uid)

    except Exception as e:
        print(f"Error running sequenced tasks for user {uid}: {e}")
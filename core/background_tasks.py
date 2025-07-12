from ragImplementation import create_embeddings_for_user, create_docs, update_embeddings_for_user

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
           'User Signup data': serialize_dict_to_text(user_data, indent=2)
       },
       'metadata': {
           'source': 'user_signup'
       }
    }

    # Create doc from context
    docs = create_docs(context, "")

    # Extract user_id from user_data
    user_id = user_data.get('uid', 'default_user')

    # Create embeddings for the user
    create_embeddings_for_user(docs, user_id)

async def update_user_embeddings(data, user_id: str, meta_data = {}, session_id = "", title = "Context Data"):
    """
    Update the embeddings for a user with new data.
    """
    # Build the context from user data
    context = {
        'context': {
            title: {"content" : serialize_dict_to_text(data, indent=2) if isinstance(data, dict) else data,
                    'metadata': {
                        'source': 'user_update',
                        **meta_data
                    }
                }
            }
        }

    # Create doc from context
    docs = create_docs(context, session_id)

    # Update embeddings for the user
    update_embeddings_for_user(docs, user_id)
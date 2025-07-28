from config import QLOO_API_URL, QLOO_API_KEY
import requests
import re
from bs4 import BeautifulSoup

ENTITIES= {
    "movies": "urn:entity:movie",
    "tv_shows": "urn:entity:tv_show",
    'books': "urn:entity:book",
}

QLOO_HEADER = {
    'X-Api-Key': QLOO_API_KEY,
    'accept': 'application/json'
}

def get_qloo_rec_endpoint(entity, tags, page):
    year_limit = ""
    if entity in ["movies", "tv_shows"]:
        year_limit = "&filter.release_year.min=2000"
    elif entity == "books":
        year_limit = "&filter.publication_year.min=2000"
    return f"{QLOO_API_URL}v2/insights?filter.type={entity}&filter.tags={tags}&page={page}{year_limit}"

def get_qloo_tags_endpoint(entity):
    return f"{QLOO_API_URL}v2/tags?feature.typo_tolerance=false&filter.parents.types={entity}"

def make_qloo_request(endpoint):
    response = requests.get(endpoint, headers=QLOO_HEADER)
    if response.status_code != 200:
        raise Exception(f"Error fetching data from Qloo API: {response.status_code} - {response.text}")
    return response.json()

def get_qloo_tags_to_select_from(entity_name):
    qloo_enity = ENTITIES.get(entity_name)
    if not qloo_enity:
        raise ValueError(f"Invalid entity name: {entity_name}")
    endpoint = get_qloo_tags_endpoint(qloo_enity)
    data = make_qloo_request(endpoint)
    tags_object = {
    i + 1: {
        "id": r.get("id"),
        "name": r.get("name"),
        "description": r.get("properties", {}).get("description"),
    }
    for i, r in enumerate(data.get("results", {}).get("tags", []))
    }
    return tags_object

def clean_html_text(html_text):
    # Define tags whose entire content should be removed
    remove_content_tags = ['i', 'em', 'script', 'style']

    soup = BeautifulSoup(html_text, "html.parser")

    # Remove specified tags and their content
    for tag in soup.find_all(remove_content_tags):
        tag.decompose()

    # Get remaining text
    cleaned_text = soup.get_text(separator=' ', strip=True)

    return cleaned_text

def transform_movie_entity(entity):
    """
    Transforms a single entity with improved tag filtering and 'where_to_watch' extraction.
    """
    # --- 1. Process all tag logic in a single, efficient loop ---
    filtered_tags = []
    where_to_watch_list = []
    original_tags = entity.get('tags', [])

    first_genre = None
    for tag in original_tags:
        tag_name = tag.get('name')
        tag_type = tag.get('type')

        # Skip any tag that is missing essential info
        if not tag_name or not tag_type:
            continue

        # Rule 1: Extract streaming services for 'extra_data'
        if 'streaming_service' in tag_type:
            where_to_watch_list.append(tag_name)

        # Rule 2: Add all genres to the final 'tags' list
        elif 'genre' in tag_type:
            filtered_tags.append(tag_name)
            if not first_genre:
                first_genre = tag_name

        # Rule 3: Add single-word keywords to the final 'tags' list
        elif 'keyword' in tag_type and ' ' not in tag_name.strip():
            filtered_tags.append(tag_name)

    # --- 2. Create and populate the 'extra_data' dictionary ---
    extra_data = {
        'duration': entity.get('properties', {}).get('duration'),
        'content_rating': entity.get('properties', {}).get('content_rating'),
        'popularity': entity.get('popularity'),
    }

    # Process external source data
    source_external = entity.get('external', {})
    if source_external:
        for key, value_list in source_external.items():
            if isinstance(value_list, list) and value_list and isinstance(value_list[0], dict):
                first_item = value_list[0]
                extra_data[key] = {k: v for k, v in first_item.items() if k != 'id'}
    extra_data['where_to_watch'] = where_to_watch_list

    # --- 3. Assemble and return the final dictionary ---
    return {
        'title': entity.get('name'),
        'id': entity.get('id') or entity.get('entity_id'),
        'release_date': entity.get('properties', {}).get('release_date'),
        'description': clean_html_text(entity.get('properties', {}).get('description')),
        'genre': first_genre,
        'image': entity.get('properties', {}).get('image'),
        # Clean the final extra_data to remove empty values (e.g., if where_to_watch is empty)
        'extra_data': {k: v for k, v in extra_data.items() if v},
        'tags': filtered_tags,
        'tags_original': original_tags,
    }

def transform_book_entity(entity):
    """
    Transforms a single book entity, including filtered tags.
    """

    # helper to clean author
    def clean_author(author_str: str) -> str:
        match = re.match(r"^\d{4},\s*(.*)", author_str)
        return match.group(1) if match else author_str
    
    # Get the nested properties dictionary once
    properties = entity.get('properties', {})

    # --- 1. Process tags for genres and keywords ---
    filtered_tags = []
    original_tags = entity.get('tags', [])

    for tag in original_tags:
        tag_name = tag.get('name')
        tag_type = tag.get('type')

        # Skip any tag that is missing essential info
        if not tag_name or not tag_type:
            continue

        # Add tag if its type is 'genre' OR 'keyword'
        if 'genre' in tag_type or 'keyword' in tag_type:
            filtered_tags.append(tag_name)

    # --- 2. Create and populate the 'extra_data' dictionary ---
    extra_data = {
        'publisher': properties.get('publisher'),
        'page_count': properties.get('page_count'),
        'popularity': entity.get('popularity')
    }

    # Process external data from other sources
    source_external = entity.get('external', {})
    if source_external:
        for key, value_list in source_external.items():
            if isinstance(value_list, list) and value_list and isinstance(value_list[0], dict):
                first_item = value_list[0]
                extra_data[key] = {k: v for k, v in first_item.items() if k != 'id'}

    # --- 3. Assemble and return the final dictionary ---
    return {
        'title': entity.get('name'),
        'id': entity.get('id') or entity.get('entity_id'),
        'author': clean_author(entity.get('disambiguation')) if entity.get('disambiguation') else None,
        'publication_date': properties.get('publication_date'),
        'image': properties.get('image'),
        'description': clean_html_text(properties.get('description')),
        'extra_data': {k: v for k, v in extra_data.items() if v},
        'tags': filtered_tags,
        'tags_original': original_tags,
    }

def get_qloo_recommendations(entity_name, tags, page=1):
    qloo_entity = ENTITIES.get(entity_name)
    if not qloo_entity:
        raise ValueError(f"Invalid entity name: {entity_name}")
    
    recommendation_entities = []
    for _, tag in tags.items():
        try:
            tag_id = tag.get("id")
            if tag_id is None:
                print(f"Skipping tag {tag} as it has no ID")
                continue
            endpoint = get_qloo_rec_endpoint(qloo_entity, tag_id, page.get(tag_id, 1))
            print(f"Fetching recommendations from Qloo API for {entity_name} with tag {tag} on page {page} with endpoint {endpoint}")
            data = make_qloo_request(endpoint)
            if entity_name in ["movies", "tv_shows"]:
                recommendation_entities += [
                transform_movie_entity(entity)
                for entity in data.get("results", {}).get("entities", [])
                ]
            elif entity_name == "books":
                recommendation_entities += [
                transform_book_entity(entity)
                for entity in data.get("results", {}).get("entities", [])
                ]
        except Exception as e:
            print(f"Error fetching recommendations for {entity_name} with tag {tag}: {e}")
            continue
    
    return recommendation_entities

from config import QLOO_API_URL, QLOO_API_KEY
import requests

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
    return f"{QLOO_API_URL}/v2/insights?filter.type={entity}&filter.tags={tags}&page={page}"

def get_qloo_tags_endpoint(entity):
    return f"{QLOO_API_URL}/v2/tags?feature.typo_tolerance=false&filter.parents.types={entity}"

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

def get_qloo_recommendations(entity_name, tags, page=1):
    qloo_entity = ENTITIES.get(entity_name)
    if not qloo_entity:
        raise ValueError(f"Invalid entity name: {entity_name}")
    endpoint = get_qloo_rec_endpoint(qloo_entity, tags, page)
    data = make_qloo_request(endpoint)
    recommendation_entities = []
    if entity_name in ["movies", "tv_shows",]:
        recommendation_entities = [
        {
            "name": entity.get("name"),
            "id": entity.get("id") or entity.get('entity_id'),
            "release_date": entity.get("properties", {}).get("release_date"),
            "description": entity.get("properties", {}).get("description"),
            "image": entity.get("properties", {}).get("image"),
            "external_data": entity.get("external", {})
        }
        for entity in data.get("results", {}).get("entities", [])
        ]
    elif entity_name == "books":
        recommendation_entities = [
        {
            "name" : entity.get('name'),
            "id" : entity.get('id') or entity.get('entity_id'),
            "description" : entity.get('properties', {}).get('description'),
            'publication_date' : entity.get('properties', {}).get('publication_date'),
            'page_count' : entity.get('properties', {}).get('page_count'),
            "image" : entity.get('properties', {}).get('image'),
            'popularity': entity.get('popularity'),
            'tags' : entity.get('tags'),
            "external_data" : entity.get('external', {})
        }
        for entity in data.get("results", {}).get("entities", [])
        ]
    
    return recommendation_entities

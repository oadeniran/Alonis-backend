from db import notes_and_goalsCollection
from datetime import datetime
from bson import ObjectId
from config import NOTES_PER_PAGE

def add_notes(uid, notes_details):
    try:
        note_or_goal_data = {
            "uid": uid,
            "title": notes_details["title"],
            "details": notes_details["details"],
            "is_goal": notes_details.get("is_goal", False),
            'is_achieved': notes_details.get("is_achieved", False),
            "is_archived": notes_details.get("is_archived", False),
            "date": datetime.now(),
        }
        notes_and_goalsCollection.insert_one(note_or_goal_data)
        # Convert ObjectId to string for JSON serialization
        note_or_goal_data['_id'] = str(note_or_goal_data['_id'])
        note_or_goal_data['date'] = note_or_goal_data['date'].strftime('%Y-%m-%d %H:%M:%S')  # Format date for better readability
        return {
            "message": "Note added successfully",
            "status_code": 200,
            'note': note_or_goal_data
        }
    except Exception as e:
        print(e)
        return {
            "message": "Error adding note",
            "status_code": 400
        }

def set_goal_as_achieved(uid, note_id):
    try:
        result = notes_and_goalsCollection.update_one(
            {"uid": uid, "_id": ObjectId(note_id)},
            {"$set": {"is_achieved": True}}
        )
        if result.modified_count > 0:
            return {
                "message": "Note marked as achieved",
                "status_code": 200
            }
        else:
            return {
                "message": "Note not found or already marked as achieved",
                "status_code": 404
            }
    except Exception as e:
        print(e)
        return {
            "message": "Error marking note as achieved",
            "status_code": 400
        }

def mark_note_as_archived(uid, note_id):
    try:
        result = notes_and_goalsCollection.update_one(
            {"uid": uid, "_id": ObjectId(note_id)},
            {"$set": {"is_archived": True}}
        )
        if result.modified_count > 0:
            return {
                "message": "Note marked as archived",
                "status_code": 200
            }
        else:
            return {
                "message": "Note not found or already archived",
                "status_code": 404
            }
    except Exception as e:
        print(e)
        return {
            "message": "Error archiving note",
            "status_code": 400
        }

def get_user_notes_and_goals(uid, page: int = 1):
    try:
        per_page = NOTES_PER_PAGE
        skip = (page - 1) * per_page

        cursor = (
            notes_and_goalsCollection
            .find({"uid": uid, 'is_archived': False})
            .sort("date", -1)
            .skip(skip)
            .limit(per_page)  # Custom rule: 12 * page
        )

        total = notes_and_goalsCollection.count_documents({"uid": uid, 'is_archived': False})

        notes_list = []
        for note in cursor:
            note['_id'] = str(note['_id'])
            note['date'] = note['date'].strftime('%Y-%m-%d %H:%M:%S')
            notes_list.append(note)

        return {
            "notes_and_goals": notes_list,
            "page": page,
            "count": len(notes_list),
            'has_next_page': (page * per_page) < total,
            'status_code': 200
        }

    except Exception as e:
        print(e)
        return {
            "message": "Error fetching notes",
            "status_code": 400
        }
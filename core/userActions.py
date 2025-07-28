from db import usersCollection, reportsCollection, sessionsCollection, dailyQuotesCollection, extractedDataCollection, recommendationsCollection, qlooRecommendationsPageTrackingCollection, dailyStoriesCollection, BulkWriteError
from bson import ObjectId
import bcrypt
from datetime import datetime
from core.notesActions import get_user_notes_and_goals, add_notes, set_goal_as_achieved, mark_note_as_archived
from config import RECOMMENDATIONS_PER_PAGE
import random


def encrypt_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
def signup(signUp_det):
    try:
        details = usersCollection.find_one({"username" : signUp_det["username"]})
    except:
        return {
                    "message" : "Error in signup, please try again",
                    "status_code" : 404
                    }
    if details:
        return {
                    "message" : "Username is taken, please use another",
                    "status_code" : 400}
    try:
        signUp_det["password"] = encrypt_password(signUp_det["password"])
        uid = usersCollection.insert_one(signUp_det)
    except Exception as e:
        print(e)
        return {
                    "message" : "Error with signup",
                    "status_code" : 400}
    return {
    "message" : "Sign Up successful",
    "uid" : str(uid.inserted_id),
    "status_code" : 200}

def login(login_det):

    try:
        if login_det["is_email_login"]:
            details = usersCollection.find_one({"email" : login_det["email"]})
        else:
            # If not email login, use username
            details = usersCollection.find_one({"username" : login_det["username"]})
    except:
        return {
                    "message" : "Error with DB",
                    "status_code" : 404
                    }
    
    if details:
        print(str(details["_id"]))
        if check_password(login_det["password"], details["password"]):
            # Increment the login count
            usersCollection.update_one({"_id": ObjectId(details["_id"])}, {"$inc": {"login_count": 1}})
            return {
                    "message" : "Sign In successful",
                    "status_code" : 200,
                    "uid" : str(details["_id"]),
                    "username" : details["username"],
                    "email" : details["email"],
                    "alonis_verbosity" : details["alonis_verbosity"],
                    "short_bio" : details["short_bio"],
                    "login_count": details.get("login_count", 0) + 1
                    }
        else:
            return {
            "message" : "Wrong Password",
            "status_code" : 400}
    else:
        return {
                    "message" : "User not found",
                    "status_code" : 404
                    }

def hackathon_username_only_authentication(username, short_bio=""):
    try:
        details = usersCollection.find_one({"username": username})
    except:
        return {
                    "message": "Error with DB",
                    "status_code": 404
                }
    
    if details:
        # Treat this as login for hackathon auth
        print(str(details["_id"]))
        usersCollection.update_one({"_id": ObjectId(details["_id"])}, {"$inc": {"login_count": 1}})
        return {
            "message": "Hackathon auth successful",
            "status_code": 200,
            "uid": str(details["_id"]),
            "username": details["username"],
            "email": details.get("email", ""),
            "alonis_verbosity": details.get("alonis_verbosity", "normal"),
            "short_bio": details.get("short_bio", ""),
            "login_count": details.get("login_count", 1)  # Default to 1 if not present
        }
    
    user_details = {
        "username": username,
        "short_bio": short_bio,
        "alonis_verbosity": "normal",  # Default verbosity level
        "email": "",  # No email provided in this case
        "password": encrypt_password("default_password"),  # Default password for hackathon auth
        "login_count": 1,  # Initial login count
        "is_hackathon_user": True  # Flag to indicate hackathon user
    }
    
    try:
        uid = usersCollection.insert_one(user_details)
    except Exception as e:
        print(e)
        return {
                    "message": "Error with signup",
                    "status_code": 400
                }
    # Return the new user details
    user_details['uid'] = str(uid.inserted_id)
    
    return {
        "message": "Sign Up successful",
        "uid": str(uid.inserted_id),
        "username": username,
        "email": "",
        "alonis_verbosity": "normal",
        "short_bio": short_bio,
        "login_count": 1,
        "status_code": 200,
        'user_details': user_details
    }

def add_user_session(uid, session_id, session_type, session_info):
    try:
        #usersCollection.update_one({"_id":ObjectId(uid)}, {"$push": {"sessions": {"session_id": session_id, "session_type": session_type, "session_info": session_info}}})
        # Update the sessions collection with the new session or upsert if it doesn't exist
        existing = sessionsCollection.find_one({
        "uid": uid,
        "session_id": session_id
        })

        if not existing:
            sessionsCollection.insert_one({
                "uid": uid,
                "session_id": session_id,
                "session_type": session_type,
                "session_info": session_info,
                'is_archived': False,  # Default value for is_archived
                "date": datetime.now()
            })
    except:
        return {
                    "message" : "Error with DB",
                    "status_code" : 404
                    }
    return {
    "message" : "Session added successfully",
    "status_code" : 200}

def get_all_user_sessions(uid):
    try:
        print(uid)
        #users = usersCollection.find({"_id":ObjectId(uid)})
        sessions = sessionsCollection.find({
            "uid": uid,
            "$or": [
                {"is_archived": False},
                {"is_archived": {"$exists": False}}
            ]
        }).sort("date", -1)  # Sort by date in descending order

        sessions = list(sessions)  # Convert cursor to list for easier processing
        # print(sessions)

        # Convert _id and uid to string for JSON serialization
        final_sessions_obj = {}

        final_sessions_obj['assessments'] = [{
            "session_id": str(session["session_id"]),
            "session_type": session["session_type"],
            "session_info": session["session_info"],
            "date": session["date"].strftime("%Y-%m-%d %H:%M:%S") if "date" in session else None,
            "has_report": session.get("has_report", False)
        } for session in sessions if "assessment_" in session.get("session_type") or "personality_" in session.get("session_type") or "mind" in session.get("session_type")]

        final_sessions_obj['talk_sessions'] = [{
            "session_id": str(session["session_id"]),
            "session_type": session["session_type"],
            "session_info": session["session_info"],
            "date": session["date"].strftime("%Y-%m-%d %H:%M:%S") if "date" in session else None
        } for session in sessions if session.get("session_type") == "talk_session" and session.get('message_count', 0) > 2]
    except:
        return {
                    "message" : "Error with DB",
                    "status_code" : 404
                    }
    #print(list(users))
    return {"sessions": final_sessions_obj, "status_code": 200}

def add_doc_ids(uid, ids):
    try:
        print(uid)
        user = usersCollection.find({"_id":ObjectId(uid)})
    except:
        return {
                    "message" : "Error with DB",
                    "status_code" : 404
                    }
    #print(list(users))
    new_ids = user["docIds"] + ids
    user["docIds"] = new_ids

    try:
        usersCollection.find_one_and_update({"_id":ObjectId(uid)}, {"docIds" : new_ids})
    except:
        return {
                    "message" : "Error with DB",
                    "status_code" : 404
                    }
    return "updated"

def get_user_reports(uid):
    try:
        reports = reportsCollection.find({"uid":uid,
                                          "$or": [
                                            {"is_archived": False},
                                            {"is_archived": {"$exists": False}}
                                          ]}).sort("date", -1)  # Sort by date in descending order
    except:
        return {
                    "message" : "Error with DB",
                    "status_code" : 404
                    }
    if reports == None:
        return {}
    reports_formatted = {report['session_id']: {"session_type": report['session_type'], "report_data": report['report']} for report in reports}
    #print(reports_formatted)
    return reports_formatted

def get_extracted_data(uid, session_id:str):
    extracted_data = extractedDataCollection.find_one({"uid": uid, "session_id": session_id})
    if extracted_data:
        return extracted_data["data"]
    else:
        return None

def add_report_to_db(uid, session_type, session_id:str, report:str):
    document = {
        "uid":uid,
        "session_id":session_id,
        "session_type":session_type,
        "report":report,
        "date":datetime.now(),
        "is_archived" : False
    }
    reportsCollection.insert_one(document)

    # Update the session to mark it as having a report
    sessionsCollection.find_one_and_update(
        {"uid": uid, "session_id": session_id},
        {"$set": {"has_report": True}}
    )

    # Update the user to increment the report count
    usersCollection.find_one_and_update(
        {"_id": ObjectId(uid)},
        {"$inc": {"report_count": 1}}
    )

def update_report_save_status(uid, session_id:str):
    reportsCollection.find_one_and_update({"uid":uid, "session_id":session_id}, {"$set": {"saved": True}})

def get_last_report_for_assessment_type(uid, assessment_type):
    report = reportsCollection.find_one(
        {"uid": uid, "session_type": assessment_type},
        sort=[("date", -1)]
    )
    if report:
        return report.get("report", None)
    else:
        return "No previous report found for this assessment type"

def build_context_for_user(uid):
    context = {}
    try:
        user = usersCollection.find_one({"_id":ObjectId(uid)})
    except:
        return {
                    "message" : "Error with DB",
                    "status_code" : 404
                    }
    if user == None:
        return {"message": "User not found", "status_code": 404}
    
    # Add the user data to the context
    context['user_data'] = {
        "content" : user.get("short_bio", ""),
        "metadata" : {
            "source" : "user_data",
            "uid": uid,
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "alonis_verbosity": user.get("alonis_verbosity", "")
        }
    }

    # Add the Assessment reports to the context
    assessment_reports = get_user_reports(uid)
    for session_id, report_details in assessment_reports.items():
        context[f'assessment_report for session {session_id}'] = {
            "content": report_details["report_data"],
            "metadata": {
                "source": "assessment_report",
                "session_id": session_id,
                "session_type": report_details["session_type"]
            }
        }
    
    # Add the user Notes and Goals to the context
    user_notes_and_goals = get_user_notes_and_goals(uid)
    if user_notes_and_goals:
        for note_or_goal in user_notes_and_goals.get("notes_and_goals", []):
            if note_or_goal.get("is_goal", False) == True:
                context[f'A goal provided_by user titled {note_or_goal["title"]}'] = {
                    "content": note_or_goal["title"] + " : " + 'Created on' + note_or_goal['date'] + note_or_goal["details"] + "\n" + ("Achieved" if note_or_goal.get("is_achieved", False) else "Not Achieved"),
                    "metadata": {
                        "source": "user_goal",
                        "title": note_or_goal["title"],
                        "is_achieved": note_or_goal.get("is_achieved", False)
                    }
                }
            else:
                context[f'A note provided_by_user titled {note_or_goal["title"]}'] = {
                    "content": note_or_goal["title"] + ' : ' + note_or_goal["details"],
                    "metadata": {
                        "source": "user_note",
                        "title": note_or_goal["title"]
                    }
                }
    
    return {"context": context, "status_code": 200}

def get_user_session_report(uid, session_id):
    try:
        report = reportsCollection.find_one({"uid":uid, "session_id":session_id})
    except:
        return {
                    "message" : "Error with DB",
                    "status_code" : 404
                    }
    if report == None:
        return {"message": "No report found for this session", "status_code": 404}
    
    return {"report_data": report["report"], "session_type": report["session_type"], "is_saved": report.get("saved", False), "status_code": 200}

def add_note_or_goal_for_user(uid, note_details):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    if not note_details.get("title") or not note_details.get("details"):
        return {"error": "Title and content are required for the note/goal"}
    
    resp = add_notes(uid, note_details)

    # If the note/goal was added successfully, update note count by 1
    if resp["status_code"] == 200:
        usersCollection.find_one_and_update(
            {"_id": ObjectId(uid)},
            {"$inc": {"note_count": 1}}
        )

    print(resp)
    
    if resp["status_code"] != 200:
        return {"error": resp["message"], "status_code": resp["status_code"]}
    
    return resp

def delete_note_or_goal(uid, note_id):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    if not note_id or note_id == "":
        return {"error": "Note ID is required"}
    
    try:
        result = mark_note_as_archived(uid, note_id)

        # If the note/goal was archived successfully, update note count by -1
        usersCollection.find_one_and_update(
            {"_id": ObjectId(uid)},
            {"$inc": {"note_count": -1}}
        )
        return result   
    except Exception as e:
        print(e)
        return {"error": "Error deleting note/goal", "status_code": 400}

def mark_goal_as_achieved(uid, note_id):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    if not note_id or note_id == "":
        return {"error": "Note ID is required"}
    
    try:
        result = set_goal_as_achieved(uid, note_id)
        return result   
    except Exception as e:
        print(e)
        return {"error": "Error marking note as achieved", "status_code": 400}
    
def add_daily_quote(uid, quote):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    if not quote or quote == "":
        return {"error": "Quote is required"}
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    dailyQuotesCollection.update_one(
        {"uid": uid, "date": today},
        {"$set": quote},
        upsert=True
    )
    
    return {"message": "Quote added successfully", "status_code": 200}

def add_daily_story(uid, story):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    if not story or story == "":
        return {"error": "Story is required"}
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    dailyStoriesCollection.update_one(
        {"uid": uid, "date": today},
        {"$set": {"story": story}},
        upsert=True
    )
    
    return {"message": "Story added successfully", "status_code": 200}

def get_user_quote_for_today(uid):

    user_quote_for_day = dailyQuotesCollection.find_one({
        'uid': uid,
        'date' : datetime.now().strftime( "%Y-%m-%d")
    })

    return user_quote_for_day

def get_user_story_for_today(uid):
    user_story_for_day = dailyStoriesCollection.find_one({
        'uid': uid,
        'date' : datetime.now().strftime( "%Y-%m-%d")
    })

    return user_story_for_day

def get_previous_quote(uid):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    prev_user_quote = dailyQuotesCollection.find_one({
        'uid': uid,
        'date': {"$lt": datetime.now().strftime("%Y-%m-%d")} # Get the most recent quote before today
    }, sort=[("date", -1)])  # Sort by date in descending order to get the most recent quote

    return prev_user_quote if prev_user_quote else {"message": "No previous quote found"}

def get_previous_quotes(uid, limit=10):
    if not uid:
        return {"error": "Please sign up/login to continue"}

    try:
        # Query all quotes before today, sorted by date descending, limited to 10
        previous_quotes_cursor = dailyQuotesCollection.find(
            {
                'uid': uid,
                'date': {"$lt": datetime.now().strftime("%Y-%m-%d")}
            },
            {
                "_id": 0  # Exclude the _id field
            }
        ).sort("date", -1).limit(limit)

        quotes = list(previous_quotes_cursor)

        if quotes:
            return {"quotes": quotes, "count": len(quotes)}
        else:
            return {"message": "No previous quotes found", "quotes": []}

    except Exception as e:
        print(f"Error retrieving previous quotes: {e}")
        return {"error": "Something went wrong retrieving previous quotes"}

def get_previous_stories(uid, limit=10):
    if not uid:
        return {"error": "Please sign up/login to continue"}

    try:
        # Query all stories before today, sorted by date descending, limited to 10
        previous_stories_cursor = dailyStoriesCollection.find(
            {
                'uid': uid,
                'date': {"$lt": datetime.now().strftime("%Y-%m-%d")}
            },
            {
                "_id": 0  # Exclude the _id field
            }
        ).sort("date", -1).limit(limit)

        stories = list(previous_stories_cursor)

        if stories:
            return {"stories": stories, "count": len(stories)}
        else:
            return {"message": "No previous stories found", "stories": []}

    except Exception as e:
        print(f"Error retrieving previous stories: {e}")
        return {"error": "Something went wrong retrieving previous stories"}


def add_recommendations(uid, recommendations, rec_type='alonis_recommendation'):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    if not recommendations or not isinstance(recommendations, list):
        return {"error": "Recommendations must be a list"}
    
    ACTIONS_DICT = {
        'alonis_recommendation': None,
        'alonis_recommendation_movies': {"name" : "Watched this movie", "status": False},
        'alonis_recommendation_songs': {"name" : "Listened to this song", "status": False},
        'alonis_recommendation_books': {"name" : "Read this book", "status": False},
        'alonis_recommendation_news': None
    }
    
    recommendations_to_insert = [
    {
        **new_recommendation,
        "uid": uid,
        "date": datetime.now(),
        "type": rec_type,
        "is_read_by_user": False,
        **({"action": action} if (action := ACTIONS_DICT.get(rec_type)) is not None else {})
    }
    for new_recommendation in recommendations
    ]
    
    try:
        recommendationsCollection.insert_many(recommendations_to_insert, ordered=False)
        return {"message": "Recommendations added successfully", "status_code": 200}
    except BulkWriteError as bwe:
        # Handle duplicate key errors or other bulk write errors
        print(f"Bulk write error: {bwe.details}")
    except Exception as e:
        print(e)
        return {"error": "Error adding recommendations", "status_code": 400}

def get_current_alonis_recommendations(uid, rec_type='alonis_recommendation', page=None):
    """
    Get personalized Alonis recommendations based on user data and interactions.
    
    Args:
        uid (str): User ID.
        rec_type (str): Type of recommendation.
        page (int or None): If provided, enables pagination (20 * page).
        
    Returns:
        dict: Recommendations and status.
    """
    try:
        query = {
            "uid": uid,
            "type": rec_type,
            "$or": [
                {"action": {"$exists": False}},                      # No action field
                {"action.status": {"$ne": True}}                    # action exists, but status is not True
            ]
        }
        cursor = recommendationsCollection.find(query).sort([("is_read_by_user", 1), ("date", -1), ("_id", -1)])  # Sort by date and then by _id in descending order

        if page is not None:
            skip = (page - 1) * RECOMMENDATIONS_PER_PAGE
            cursor = cursor.skip(skip)
            cursor = cursor.limit(RECOMMENDATIONS_PER_PAGE)

        recommendations = list(cursor)

        for rec in recommendations:
            rec['id'] = str(rec['_id'])
            del rec['_id']
            if 'date' in rec:
                rec['date'] = rec['date'].strftime("%Y-%m-%d %H:%M:%S")
        
        # # Shuffle the recommendations to provide a varied experience
        # random.shuffle(recommendations)
        
        total_recommendations = recommendationsCollection.count_documents(query)

        return {
            "recommendations": [{k:v for k, v in recommendation.items() if k != 'tags_original'} for recommendation in recommendations],
            "count": len(recommendations),
            "page": page,
            'has_next_page': (page is not None and (RECOMMENDATIONS_PER_PAGE * int(page)) < total_recommendations),
            "status_code": 200
        }

    except Exception as e:
        print(f"Error fetching recommendations: {e}")
        return 
    
def confirm_user_has_performed_enough_actions(uid):
    user_data = usersCollection.find_one({"_id": ObjectId(uid)})
    if user_data:
        has_report = reportsCollection.count_documents({"uid": uid}) > 0
        has_note = usersCollection.find_one({"_id": ObjectId(uid), "note_count": {"$gt": 2}}) is not None
        has_session_with_messages = sessionsCollection.count_documents({"uid": uid, 'session_type' : 'talk_session', "message_count": {"$gt": 6}}) > 0
        
        if has_report or has_note or has_session_with_messages:
            return True
    
    return False
            
def confirm_to_add_more_alonis_recommendations(uid, rec_type='alonis_recommendation'):
    try:
        match_query = {"uid": uid, "type": rec_type}

        total = recommendationsCollection.count_documents(match_query)
        read = recommendationsCollection.count_documents({**match_query, "is_read_by_user": True})
        
        if total > 0 and (read / total) > 0.6:
            return True

        # Aggregate to count how many recs have at least one action.status == True
        if total > 0:
            pipeline = [
                {"$match": {**match_query, "actions.status": True}},
                {"$count": "count_with_true_actions"}
            ]
            result = list(recommendationsCollection.aggregate(pipeline))
            count_with_true_actions = result[0]["count_with_true_actions"] if result else 0

            total_with_actions = recommendationsCollection.count_documents({**match_query, "actions": {"$exists": True, "$ne": []}})

            
            
            if total_with_actions > 0 and (count_with_true_actions / total_with_actions) > 0.6:
                return True
        else:
            if rec_type == 'alonis_recommendation':
                # If no recommendations exist, but is alonis_recommendations type then we can generate some
                return True

            return confirm_user_has_performed_enough_actions(uid)

    except Exception as e:
        print(f"Error confirming recommendations: {e}")
        return False

def mark_interaction_with_recommendation(uid, rec_id):
    """
    Mark an interaction with a recommendation for a user.
    
    Args:
        uid (str): User ID.
        rec_id (str): Recommendation ID.
        
    Returns:
        dict: Success or error message.
    """
    try:
        result = recommendationsCollection.find_one_and_update(
            {"uid": uid, "_id": ObjectId(rec_id)},
            {"$set": {"is_read_by_user": True}},
            return_document=True
        )
        del result['_id']  # Remove the ObjectId for JSON serialization
        
        if result:
            return {"message": "Interaction marked successfully", "status_code": 200, "result": result}
        else:
            return {"error": "Recommendation not found", "status_code": 404}
    except Exception as e:
        print(f"Error marking interaction: {e}")
        return {"error": "Error marking interaction", "status_code": 400}

def mark_recommendation_as_completed(uid, rec_id):
    """
    Mark a recommendation as completed for a user.
    
    Args:
        uid (str): User ID.
        rec_id (str): Recommendation ID.
        
    Returns:
        dict: Success or error message.
    """
    try:
        result = recommendationsCollection.find_one_and_update(
            {"uid": uid, "_id": ObjectId(rec_id)},
            {"$set": {"action.status": True}},
            return_document=True
        )
        
        if result:
            del result['_id']  # Remove the ObjectId for JSON serialization
            return {"message": "Recommendation marked as completed", "status_code": 200, "result": result}
        else:
            return {"error": "Recommendation not found", "status_code": 404}
    except Exception as e:
        print(f"Error marking recommendation as completed: {e}")
        return {"error": "Error marking recommendation as completed", "status_code": 400}

def get_user_page_for_qloo_recommendations(uid):
    """
    Get the page number for Qloo recommendations for a user.
    
    Args:
        uid (str): User ID.
        rec_type (str): Type of recommendation.
        
    Returns:
        dict: Page number
    """
    try:
        page_tracking = qlooRecommendationsPageTrackingCollection.find_one({"uid": uid})
        
        if page_tracking:
            return page_tracking
        else:
            return {}
    except Exception as e:
        print(f"Error fetching Qloo recommendations page: {e}")
        return {"error": "Error fetching Qloo recommendations page", "status_code": 400}

def update_user_page_for_qloo_recommendations(uid, page_obj={}):
    """
    Update the page number for Qloo recommendations for a user.
    
    Args:
        uid (str): User ID.
        rec_type (str): Type of recommendation.
        page (int): Page number to update.
        
    Returns:
        dict: Success or error message.
    """
    try:
        qlooRecommendationsPageTrackingCollection.update_one(
            {"uid": uid},
            {"$set": page_obj},
            upsert=True
        )
        return {"message": "Page updated successfully", "status_code": 200}
    except Exception as e:
        print(f"Error updating Qloo recommendations page: {e}")
        return {"error": "Error updating Qloo recommendations page", "status_code": 400}

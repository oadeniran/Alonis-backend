from db import usersCollection, reportsCollection, sessionsCollection, dailyQuotesCollection, extractedDataCollection
from bson import ObjectId
import bcrypt
from datetime import datetime
from core.notesActions import get_user_notes_and_goals, add_notes, set_goal_as_achieved, mark_note_as_archived

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
            return {
                    "message" : "Sign In successful",
                    "status_code" : 200,
                    "uid" : str(details["_id"]),
                    "username" : details["username"],
                    "email" : details["email"],
                    "alonis_verbosity" : details["alonis_verbosity"],
                    "short_bio" : details["short_bio"]}
        else:
            return {
            "message" : "Wrong Password",
            "status_code" : 400}
    else:
        return {
                    "message" : "User not found",
                    "status_code" : 404
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
        for note_or_goal in user_notes_and_goals:
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

def get_user_quote_for_today(uid):

    user_quote_for_day = dailyQuotesCollection.find_one({
        'uid': uid,
        'date' : datetime.now().strftime( "%Y-%m-%d")
    })

    return user_quote_for_day

def get_previous_quote(uid):
    if not uid or uid == "":
        return {"error": "Please sign up/login to continue"}
    
    prev_user_quote = dailyQuotesCollection.find_one({
        'uid': uid,
        'date': {"$lt": datetime.now().strftime("%Y-%m-%d")} # Get the most recent quote before today
    }, sort=[("date", -1)])  # Sort by date in descending order to get the most recent quote

    return prev_user_quote if prev_user_quote else {"message": "No previous quote found"}

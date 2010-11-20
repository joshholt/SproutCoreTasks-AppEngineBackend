""" This module provdes helpers.
  Author: Joshua Holt 
  Author: Suvajit Gupta 
"""

import time,datetime,hashlib,models
from google.appengine.ext import db
from models import User, Task, Project, Watch, Comment
from django.utils import simplejson

# Global constants
MAX_RESULTS = 10000000
MONTH_MILLISECONDS = 30*24*60*60*1000

def purge_soft_deleted_records(list, cutoff):
  list.filter("status =", "deleted")
  list.filter("updatedAt <", cutoff)
  records_to_delete = list.fetch(MAX_RESULTS)
  db.delete(records_to_delete)
  return records_to_delete

def extract_record_ids(list):
  record_ids = []
  for record in list:
    if record.status != 'deleted':
      record_ids.append(record.key().id_or_name())
  return record_ids
  
#-----------------------------------------------------------------------------
# GENERAL JSON HELPERS
#-----------------------------------------------------------------------------
def apply_json_to_model_instance(model, jobj):
  """This is the generic method to apply the given json to the given model"""
  for key in model.properties():
    setattr(model, key, jobj[key] if jobj.has_key(key) else None)
  return model  

def generate_auth_token():
  """This method generates the authToken for a user every time they login"""
  return hashlib.sha1("This--is--the--authToken--%s" % time.mktime(datetime.datetime.utcnow().timetuple())).hexdigest()

def is_login_name_valid(login_name, current_user):
  if login_name.lower() == 'none':
    return False;
  login_name = login_name.strip().replace("\'","")
  current_user_id = None
  if current_user != None:
    current_user_id = current_user.key().id_or_name()
  users = User.all()
  for user in users:
    if user.status != 'deleted' and user.key().id_or_name() != current_user_id and user.loginName == login_name:
      return False;
  return True;

def create_user(request, response, signup):
  response.headers['Content-Type'] = 'application/json'
  user_json = simplejson.loads(request.body)
  if is_login_name_valid(user_json['loginName'], None):
    user = apply_json_to_model_instance(User(), user_json)
    if signup:
      user.role = "_Guest"
      user.authToken = generate_auth_token()
    user.put()
    guid = user.key().id_or_name()
    new_url = "/tasks-server/user/%s" % guid
    user_json["id"] = guid
    response.set_status(201, "User created")
    response.headers['Location'] = new_url
    response.out.write(simplejson.dumps(user_json))
  else:
    report_invalid_login_name(response)

def build_user_json(user, send_auth_token):
  user_json = {
    "id": "%s" % user.key().id_or_name(),
    "name": user.name,
    "loginName": user.loginName,
    "role": user.role,
    "preferences": {},
    "email": user.email, 
    "password": "password" if user.password != None and len(user.password) != 0 else "",
    "status": user.status, 
    "createdAt": user.createdAt, 
    "updatedAt": user.updatedAt
  }
  if send_auth_token:
    user_json["authToken"] = user.authToken if user.authToken != None else ""
  return user_json

def build_user_list_json(list, current_user_id):
  users_json = []
  for user in list:
    send_auth_token = False;
    if current_user_id != None and user.key().id_or_name() == current_user_id:
      send_auth_token = True
    users_json.append(build_user_json(user, send_auth_token))
  return users_json

def build_project_list_json(list):
  projects_json = []
  for project in list:
    project_json = {
      "id": "%s" % project.key().id_or_name(),
      "name": project.name,
      "description": project.description,
      "timeLeft": project.timeLeft,
      "developmentStatus": project.developmentStatus,
      "activatedAt": project.activatedAt,
      "status": project.status, 
      "createdAt": project.createdAt,
      "updatedAt": project.updatedAt
    }
    projects_json.append(project_json)
  return projects_json

def build_task_list_json(list):
  tasks_json = []
  for task in list:
    task_json = {
      "id": "%s" % task.key().id_or_name(),
      "name": task.name,
      "priority": task.priority,
      "description": task.description,
      "projectId": task.projectId,
      "effort": task.effort,
      "submitterId": task.submitterId,
      "assigneeId": task.assigneeId,
      "type": task.type, 
      "developmentStatus": task.developmentStatus,
      "validation": task.validation,
      "status": task.status, 
      "createdAt": task.createdAt,
      "updatedAt": task.updatedAt
    }
    tasks_json.append(task_json)
  return tasks_json

def build_watch_list_json(list):
  watches_json = []
  for watch in list:
    watch_json = {
      "id": "%s" % watch.key().id_or_name(),
      "taskId": watch.taskId,
      "userId": watch.userId,
      "status": watch.status, 
      "createdAt": watch.createdAt,
      "updatedAt": watch.updatedAt
    }
    watches_json.append(watch_json)
  return watches_json

def build_comment_list_json(list):
  comments_json = []
  for comment in list:
    comment_json = {
      "id": "%s" % comment.key().id_or_name(),
      "description": comment.description,
      "taskId": comment.taskId,
      "userId": comment.userId,
      "status": comment.status, 
      "createdAt": comment.createdAt,
      "updatedAt": comment.updatedAt
    }
    comments_json.append(comment_json)
  return comments_json

#-----------------------------------------------------------------------------
# AUTHORIZATION
#-----------------------------------------------------------------------------
# TODO: tighten up control to match GUI - Guests can only delete tasks they submitted
def authorized(userId, authToken, action):
  """This method checks the user's authToken against what's stored in the DB"""
  key = db.Key.from_path('User', int(userId))
  user = db.get(key)
  retVal = False
  if not user == None:
    if user.authToken == authToken:
      retVal = {
      "getRecords": lambda role: True if not role == "None" else False,
      "createUser": lambda role: True if role == "_Manager" else False,
      "updateUser": lambda role: True if not role == "None" else False,
      "deleteUser": lambda role: True if role == "_Manager" else False,
      "createProject": lambda role: True if role == "_Manager" else False,
      "updateProject": lambda role: True if role == "_Manager" else False,
      "deleteProject": lambda role: True if role == "_Manager" else False,
      "createTask": lambda role: True if not role == "None" else False,
      "updateTask": lambda role: True if not role == "None" else False,
      "deleteTask": lambda role: True if not role == "None" else False,
      "createWatch": lambda role: True if not role == "None" else False,
      "updateWatch": lambda role: True if not role == "None" else False,
      "deleteWatch": lambda role: True if not role == "None" else False,
      "createComment": lambda role: True if not role == "None" else False,
      "updateComment": lambda role: True if not role == "None" else False,
      "deleteComment": lambda role: True if not role == "None" else False,
      "cleanup": lambda role: True if role == "_Manager" else False
      }[action](str(user.role))
    else:
      retVal = False
  else:
    retVal = False
  return retVal

def report_unauthorized_access(response):
  response.set_status(401, "Unauthorized")
  response.out.write(simplejson.dumps({ "message": 'Access denied'}))

def report_missing_record(response):
  response.set_status(404, "Missing Record")
  response.out.write(simplejson.dumps({ "message": 'Cannot find record with given id'}))

def report_invalid_login_name(response):
  response.set_status(409, "Invalid login name")
  response.out.write(simplejson.dumps({ "message": 'This loginName is reserved or in use'}))
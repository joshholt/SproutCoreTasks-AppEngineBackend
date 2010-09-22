""" This module provdes helpers.
  Author: Joshua Holt 
  Date: 09-30-2009
  Last Modified: 02-14-2010
"""

import time,datetime,hashlib,models
from google.appengine.ext import db
from models import User, Task, Project

#-----------------------------------------------------------------------------
# GENERAL JSON HELPERS
#-----------------------------------------------------------------------------
def apply_json_to_model_instance(model, jobj):
  """This is the generic method to apply the given json to the given model"""
  for key in model.properties():
    setattr(model, key, jobj[key] if jobj.has_key(key) else None)
  
  return model  

def build_user_json(user, send_auth_token):
  user_json = { "id": "%s" % user.key().id_or_name(),
    "name": user.name,
    "loginName": user.loginName,
    "role": user.role,
    "preferences": {},
    "email": user.email, 
    "password": "password" if user.password != None and len(user.password) != 0 else "",
    "status": user.status, 
    "createdAt": user.createdAt, 
    "updatedAt": user.updatedAt }
  if send_auth_token:
    user_json["authToken"] = user.authToken if user.authToken != None else ""
  return user_json

def build_user_list_json(list):
  users_json = []
  for user in list:
    users_json.append(build_user_json(user, False))
  return users_json

def build_task_list_json(list):
  tasks_json = []
  for task in list:
    task_json = { "id": "%s" % task.key().id_or_name(),
      "name": task.name, "priority": task.priority,
      "projectId": task.projectId,
      "effort": task.effort, "submitterId": task.submitterId,
      "assigneeId": task.assigneeId, "type": task.type, "developmentStatus": task.developmentStatus,
      "validation": task.validation, "description": task.description,
      "status": task.status, 
      "createdAt": task.createdAt,
      "updatedAt": task.updatedAt }
    
    tasks_json.append(task_json)
  return tasks_json

def build_project_list_json(list):
  projects_json = []
  for project in list:
    project_json = { "id": "%s" % project.key().id_or_name(),
      "name": project.name,
      "description": project.description,
      "timeLeft": project.timeLeft,
      "developmentStatus": project.developmentStatus,
      "activatedAt": project.activatedAt,
      "status": project.status, 
      "createdAt": project.createdAt,
      "updatedAt": project.updatedAt }
    
    projects_json.append(project_json)
  return projects_json

def build_watch_list_json(list):
  watches_json = []
  for watch in list:
    watch_json = { "id": "%s" % watch.key().id_or_name(),
      "taskId": watch.taskId,
      "userId": watch.userId,
      "status": watch.status, 
      "createdAt": watch.createdAt,
      "updatedAt": watch.updatedAt }
    
    watches_json.append(watch_json)
  return watches_json

def generateAuthToken():
  """This method generates the authToken for a user every time they login"""
  return hashlib.sha1("This--is--the--authToken--%s" % time.mktime(datetime.datetime.utcnow().timetuple())).hexdigest()

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
      "createProject": lambda role: True if role == "_Manager" else False,
      "updateProject": lambda role: True if role == "_Manager" else False,
      "deleteProject": lambda role: True if role == "_Manager" else False,
      "createTask": True,
      "updateTask": True,
      "deleteTask": lambda role: True if not role == "None" else False,
      "createUser": lambda role: True if role == "_Manager" else False,
      "updateUser": True,
      "deleteUser": lambda role: True if role == "_Manager" else False,
      "createWatch": True,
      "deleteWatch": True
      }[action](str(user.role))
    else:
      retVal = False
  else:
    retVal = False
  return retVal

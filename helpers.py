""" This module provdes helpers for dealing with the json and model objects.
  Author: Joshua Holt 
  Date: 09-30-2009
  Last Modified: 10-03-2009
"""

import time,datetime,hashlib,models
from google.appengine.ext import db
from models import User

#-----------------------------------------------------------------------------
# GENERAL HELPERS
#-----------------------------------------------------------------------------
def apply_json_to_model_instance(model, jobj):
  """This is the generic method to apply the given json to the given model"""
  for key in model.properties():
    setattr(model, key, jobj[key] if jobj.has_key(key) else None)
  
  return model  


def build_list_json(list):
  """This method will build the users list in JSON"""
  users_json = []
  for user in list:
    user_json = { "id": "%s" % user.key().id_or_name(),
      "name": user.name,
      "loginName": user.loginName, "role": user.role,
      "preferences": {}, "email": user.email, "authToken": user.authToken if user.authToken != None else "", 
      "password": "password" if user.password != None and len(user.password) != 0 else "",
      "createdAt": user.createdAt if user.createdAt != None else 0, 
      "updatedAt": user.updatedAt if user.updatedAt != None else 0 }
  
    users_json.append(user_json)
  return users_json

def generateAuthToken():
  """This method generates the authToken for a user every time they login"""
  return hashlib.sha1("This--is--the--authToken--%s" % time.mktime(datetime.datetime.utcnow().timetuple())).hexdigest()

#-----------------------------------------------------------------------------
# AUTHORIZATION
#-----------------------------------------------------------------------------
def authorized(userID, authToken, action):
  """This method checks the user's authToken against what's stored in the DB"""
  key = db.Key.from_path('User', int(userID))
  user = db.get(key)
  retVal = False
  if not user == None:
    if user.authToken == authToken:
      retVal = {
      "createProject": lambda role: True if role == "_Manager" else False,
      "updateProject": lambda role: True if role == "_Manager" else False,
      "deleteProject": lambda role: True if role == "_Manager" else False,
      "createTask": True,
      "updateTask": True,
      "deleteTask": lambda role: True if  not role == "_Guest" else False,
      "createUser": lambda role: True if  role == "_Manager" else False,
      "updateUser": True,
      "deleteUser": lambda role: True if  role == "_Manager" else False
      }[action](str(user.role))
    else:
      retVal = False
  else:
    retVal = False
  return retVal

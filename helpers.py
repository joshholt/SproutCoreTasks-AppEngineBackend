""" This module provdes helpers for dealing with the json and model objects.
  Author: Joshua Holt 
  Date: 09-30-2009
  Last Modified: 10-03-2009
"""

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
      "preferences": {}, "email": user.email, "authToken": "", 
      "password": "password" if user.password != None and len(user.password) != 0 else "",
      "createdAt": user.createdAt if user.createdAt != None else 0, 
      "updatedAt": user.updatedAt if user.updatedAt != None else 0 }
  
    users_json.append(user_json)
  return users_json
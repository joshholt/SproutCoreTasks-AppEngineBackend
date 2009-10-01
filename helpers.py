""" This module provdes helpers for dealing with the json and model objects.
  Author: Joshua Holt 
  Date: 09-30-2009
  Last Modified: 09-30-2009
"""

def apply_json_to_user(model, jobj):
  """This method will apply the given json to the given model object"""
  
  # Take care of the required properties fist by setting a generic value
  # if no value is provided
  model.name        = jobj['name']        if jobj.has_key('name')         else "(No Name)"
  model.loginName   = jobj['loginName']   if jobj.has_key('loginName')    else "NA"
  model.role        = jobj['role']        if jobj.has_key('role')         else "_Developer"
  
  # Then take care of the optional properties  
  model.preferences = jobj['preferences'] if jobj.has_key('preferences')  else None
  model.authToken   = jobj['authToken']   if jobj.has_key('authToken')    else None
  
  return model

  
def apply_json_to_task(model, jobj):
  """This method will apply the given json to the given task model object"""
  
  # Take care of the required properties fist by setting a generic value
  # if no value is provided
  model.name        = jobj['name']        if jobj.has_key('name')         else "(No Name Task)"
  
  # Then take care of the optional properties
  model.priority    = jobj['priority']    if jobj.has_key('priority')     else None
  model.effort      = jobj['effort']      if jobj.has_key('effort')       else None
  model.submitter   = jobj['submitter']   if jobj.has_key('submitter')    else None
  model.assignee    = jobj['assignee']    if jobj.has_key('assignee')     else None
  model.type        = jobj['type']        if jobj.has_key('type')         else None
  model.status      = jobj['status']      if jobj.has_key('status')       else None
  model.validation  = jobj['validation']  if jobj.has_key('validation')   else None
  model.description = jobj['description'] if jobj.has_key('description')  else None
  
  return model
  


def apply_json_to_project(model, jobj):
  """This method will apply the given json to the given project model object"""
  
  # Take care of the required properties fist by setting a generic value
  # if no value is provided
  model.name      = jobj['name']      if jobj.has_key('name')     else "(No Name Project)"
  
  # Then take care of the optional properties  
  model.timeLeft  = jobj['timeLeft']  if jobj.has_key('timeLeft') else None
  model.tasks     = jobj['tasks']     if jobj.has_key('tasks')    else None
  
  return model
  

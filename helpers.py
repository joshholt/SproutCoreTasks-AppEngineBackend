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

#!/usr/bin/env python
#
# Author: Joshua Holt
# Date: 09-29-2009

""" Prupose: To serve tasks & project to SG's Sproutcore Tasks application.
    ********* NOTE ***************
    This Code is not DRY is has been years since I've touched python
     ruby spoiled me :)
     
     Trying figure out a way to loop through model_instance.properties()
     and actually be able to use that to set the  model instance attrs
     
     Currently I am only able to do the 1/2 of the DRYing up that I want
     to do.
     
     This is what I am trying to do in my helpers module:
     
     def apply_json_to_model_instance(model, json):
       props = model.properties()
       for key in props:
         if json.has_key(key):
           model.key = json[key]
        
        model.put()
        
     
     But it seems that you cannot do this b/c I remember that you cannot
     specify an object's attribute as a string and model instances are not
     subscriptable.
     
     If anyone has any tips I am open for suggestions.
     
     thanks,
     Joshua Holt
"""

# App Engine Imports
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db
from django.utils import simplejson

# Data Model Imports
import models
from models import User
from models import Task
from models import Project

# Helper Imports
import helpers

class UsersHandler(webapp.RequestHandler):
  
  # Retrieve a list of all the Users.
  def get(self):
    
    # collect saved tasks
    users_json = []
    for user in User.all():
      user_json = { "id": "user/%s" % user.key().id_or_name(),
        "name": user.name,
        "loginName": user.loginName, "role": user.role,
        "preferences": {}, "authToken": " " }
      
      users_json.append(user_json)
    
    # Set the response content type and dump the json
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(users_json))
  
  # Create a new User
  def post(self):
    
    # collect the data from the record
    user_json = simplejson.loads(self.request.body)
    
    # create a user
    user = helpers.apply_json_to_user(User(), user_json)
    # save the new user
    user.put()
    
    guid = user.key().id_or_name()
    new_url = "/tasks-server/user/%s" % guid
    user_json["id"] = guid
    
    self.response.set_status(201, "User created")
    self.response.headers['Location'] = new_url
    self.response.headers['Content-Type'] = 'text/json'
    self.response.out.write(simplejson.dumps(user_json))


class UserHandler(webapp.RequestHandler):
  # retrieve the task with a given id
  def get(self, guid):
    
    # find the matching task
    key = db.Key.from_path('User', int(guid))
    user = db.get(key)
    if not user == None:
      guid = "user/%s" % user.key().id_or_name()
      
      user_json = { "id": "%s" % guid,
        "name": user.name,
        "loginName": user.loginName, "role": user.role,
        "preferences": user.preferences if user.preferences != None else {},
        "authToken": user.authToken if user.authToken != None else "" }
      
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(user_json))
    
    else:
      self.response.set_status(404, "User not found")
  
  # Update an existing record
  def put(self, guid):
    
    # find the matching user
    key = db.Key.from_path('User', int(guid))
    user = db.get(key)
    if not user == None:
      
      # collect the data from the record
      user_json = simplejson.loads(self.request.body)
      # update the record
      user = helpers.apply_json_to_user(user, user_json)
      # save the record
      user.put()
      # return the same record...
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(user_json))
    
    else:
      self.response.set_status(404, "User not found")
  
  # delete the user with a given id
  def delete(self, guid):
    
    # find the matching task and delete it if found
    key = db.Key.from_path('User', int(guid))
    user = db.get(key)
    if not user == None:
      user.delete()
  


class TasksHandler(webapp.RequestHandler):
  # Retrieve a list of all the Users.
  def get(self):
    # collect saved tasks
    tasks_json = []
    for task in Task.all():
      task_json = { "id": "task/%s" % task.key().id_or_name(),
        "name": task.name, "priority": task.priority,
        "effort": task.effort, "submitter": task.submitter,
        "assignee": task.assignee, "type": task.type, "status": task.status,
        "validation": task.validation, "description": task.description }
      
      tasks_json.append(task_json)
    
    # Set the response content type and dump the json
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(tasks_json))
  
  # Create a new Task
  def post(self):
    
    # collect the data from the record
    task_json = simplejson.loads(self.request.body)
    # create a new taks with the passed in json
    task = helpers.apply_json_to_task(Task(),task_json)
    # save task
    task.put()
        
    guid = task.key().id_or_name()
    new_url = "/tasks-server/task/%s" % guid
    task_json["id"] = guid
    
    self.response.set_status(201, "Task created")
    self.response.headers['Location'] = new_url
    self.response.headers['Content-Type'] = 'text/json'
    self.response.out.write(simplejson.dumps(task_json))
  


class TaskHandler(webapp.RequestHandler):
  """Deals with a single Task item""" 
  def get(self, guid):
    """Retrieves a single task record and returns the JSON"""
    key = db.Key.from_path('Task', int(guid))
    task = db.get(key)
    if not task == None:
      guid = "task/%s" % task.key().id_or_name()
      task_json = { "id": "%s" % guid, "name": task.name, 
        "priority": task.priority, "effort": task.effort, 
        "submitter": task.submitter, "assignee": task.assignee, 
        "type": task.type, "status": task.status,
        "validation": task.validation, "description": task.description }
        
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(task_json))
    else:
      self.response.set_status(404, "Task not found")
  
  def put(self, guid):
    """Update the task with the given id"""
    key = db.Key.from_path('Task', int(guid))
    task = db.get(key)
    if not task == None:
      # collect the json from the request
      task_json = simplejson.loads(self.request.body)
      # update the project record
      task = apply_json_to_project(task, task_json)
      # save the updated data
      task.put()
      # return the same record...
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(task_json))
    else:
      self.response.set_status(404, "Task not found")
  
  def delete(self, guid):
    """Delete the task with the given id"""
    # search for the Project and delete if found
    key = db.Key.from_path('Task', int(guid))
    task = db.get(key)
    if not task == None:
      task.delete()
  


class ProjectsHandler(webapp.RequestHandler):
  # Retrieve a list of all the Users.
  def get(self):
    # collect saved tasks
    projects_json = []
    for project in Project.all():
      project_json = { "id": "project/%s" % project.key().id_or_name(),
        "name": project.name,
        "timeLeft": project.timeLeft,
        "tasks": project.tasks }
      
      projects_json.append(project_json)
    
    # Set the response content type and dump the json
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(projects_json))
  
  # Create a new User
  def post(self):
    # collect the data from the record
    project_json = simplejson.loads(self.request.body)
    
    # create a new project
    project = apply_json_to_project(Project(), project_json)
    # save project
    project.save()
    
    guid = project.key().id_or_name()
    new_url = "/tasks-server/project/%s" % guid
    project_json["id"] = guid
    
    self.response.set_status(201, "Project created")
    self.response.headers['Location'] = new_url
    self.response.headers['Content-Type'] = 'text/json'
    self.response.out.write(simplejson.dumps(project_json))
  


class ProjectHandler(webapp.RequestHandler):
  """Deals with a single project item"""
    
  # Retrieve a single project record
  def get(self, guid):
    """Retrieves a single project record and returns the JSON"""
    key = db.Key.from_path('Project', int(guid))
    project = db.get(key)
    if not project == None:
      guid = "project/%s" % project.key().id_or_name()
      
      project_json = { "id": "%s" % guid, "name": project.timeLeft,
        "tasks": project.tasks }
      
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(project_json))
    
    else:
      self.response.set_status(404, "Project not found")
  
  def put(self, guid):
    """Update the project with the given id"""
    key = db.Key.from_path('Project', int(guid))
    project = db.get(key)
    if not project == None:
      # collect the json from the request
      project_json = simplejson.loads(self.request.body)
      # update the project record
      project = apply_json_to_project(project, project_json)
      # save the updated data
      project.put()
      
      # return the same record...
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(project_json))
      
    else:
      self.response.set_status(404, "Project not found")
  
  def delete(self, guid):
    """Delete the project with the given id"""
    
    # search for the Project and delete if found
    key = db.Key.from_path('Project', int(guid))
    project = db.get(key)
    if not project == None:
      project.delete()
  


def main():
  application = webapp.WSGIApplication([(r'/tasks-server/user?$', UsersHandler),
    (r'/tasks-server/project?$', ProjectsHandler),
    (r'/tasks-server/task?$', TasksHandler),
    (r'/tasks/([^\.]+)(\.json)?$', UserHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
#!/usr/bin/env python
# 
# Author: Joshua Holt
# Date: 09-29-2009

##############################################################################
# 
#   Prupose: To serve tasks & project to SG's Sproutcore Tasks application.
#
##############################################################################

import wsgiref.handlers
from django.utils import simplejson

from google.appengine.ext import webapp
from google.appengine.ext import db

class User(db.Model):
  name = db.StringProperty(required=True)
  loginName = db.StringProperty(required=True)
  role = db.StringProperty(required=True)
  preferences = db.TextProperty()
  authToken = db.StringProperty()

class Project(db.Model):
  name = db.StringProperty(required=True)
  timeLeft = db.StringProperty()
  tasks = db.ListProperty(str)

class Task(db.Model):
  name = db.StringProperty(required=True)
  priority = db.StringProperty()
  effort = db.StringProperty()
  submitter = db.StringProperty()
  assignee = db.StringProperty()
  type = db.StringProperty()
  status = db.StringProperty()
  validation = db.StringProperty()
  description = db.TextProperty()

class UsersHandler(webapp.RequestHandler):
  
  # Retrieve a list of all the Users.
  def get(self):
    
    # collect saved tasks
    users_json = []
    for user in User.all():
      user_json = { "id": "user/%s" % user.key().id_or_name(), "name": user.name, "loginName": user.loginName, "role": user.role, "preferences": {}, "authToken": " " }
      users_json.append(user_json)
    
    # Set the response content type and dump the json
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(users_json))
  
  # Create a new User
  def post(self):
    # This normalized dict for the incomming json
    incomming = dict()
    
    # collect the data from the record
    user_json = simplejson.loads(self.request.body)
    
    #Make sure we have all the required params
    if user_json.has_key('name') == False:
      user_json['name'] = '(No Name)'
    
    if user_json.has_key('loginName') == False:
      user_json['loginName'] = 'NA'
    
    if user_json.has_key('role') == False:
      user_json['role'] = 'Developer'
    
    user = User(name=user_json["name"], loginName=user_json["loginName"], role=user_json["role"])
    user.put() # save
    
    guid = user.key().id_or_name()
    new_url = "/tasks/%s.json" % guid
    user_json["id"] = guid
    
    self.response.set_status(201, "User created")
    self.response.headers['Location'] = new_url
    self.response.headers['Content-Type'] = 'text/json'
    self.response.out.write(simplejson.dumps(user_json))


class UserHandler(webapp.RequestHandler):
  # retrieve the task with a given id
  def get(self, guid, ext):
    
    # find the matching task
    key = db.Key.from_path('Task', int(guid))
    task = db.get(key)
    if not task == None:
      guid = "/tasks/%s.json" % task.key().id_or_name()
      task_json = { "guid": guid, "order": task.order, "title": task.title, "isDone": task.is_done, "type": "Task" }
      
      rec = { "content": task_json, "self": guid }
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(rec))
    
    else:
      self.response.set_status(404, "Task not found")
  
  # Update an existing record
  def put(self, guid, ext):
    
    # find the matching task
    key = db.Key.from_path('Task', int(guid))
    task = db.get(key)
    if not task == None:
      
      # collect the data from the record
      rec = simplejson.loads(self.request.body)
      if rec.has_key('content'):
        
        # update record with passed data.
        task_json = rec["content"]
        did_change = False
        
        if task_json.has_key('title'):
          task.title = task_json['title']
          did_change = True
        
        if task_json.has_key('order'):
          task.order = task_json['order']
          did_change = True
        
        if task_json.has_key('isDone'):
          task.is_done = task_json['isDone']
          did_change = True
        
        if did_change:
          task.put() # save
        
        # return the same record...
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps(rec))
      
      else:
        self.response.set_status(400, "content required")
    
    else:
      self.response.set_status(404, "Task not found")
  
  # delete the task with a given id
  def delete(self, guid, ext):
    
    # find the matching task and delete it if found
    key = db.Key.from_path('Task', int(guid))
    task = db.get(key)
    if not task == None:
      task.delete()


class TasksHandler(webapp.RequestHandler):
  # Retrieve a list of all the Users.
  def get(self):
    # collect saved tasks
    tasks_json = []
    for task in Task.all():
      task_json = { "id": "user/%s" % task.key().id_or_name(),
        "name": task.name, "priority": task.priority, 
        "effort": task.effort, "submitter": task.submitter,
        "assignee": task.assignee, "type": task.type, "status": task.status,
        "validation": task.validation, "description": task.description }
      tasks_json.append(task_json)
    # Set the response content type and dump the json
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(tasks_json))
  
  # Create a new User
  def post(self):
    # collect the data from the record
    user_json = simplejson.loads(self.request.body)
    #Make sure we have all the required params
    if user_json.has_key('name') == False:
      user_json['name'] = '(No Name)'
    if user_json.has_key('loginName') == False:
      user_json['loginName'] = 'NA'
    if user_json.has_key('role') == False:
      user_json['role'] = 'Developer'
    user = User(name=user_json["name"], loginName=user_json["loginName"], role=user_json["role"])
    user.put() # save
    guid = user.key().id_or_name()
    new_url = "/tasks/%s.json" % guid
    user_json["id"] = guid
    self.response.set_status(201, "User created")
    self.response.headers['Location'] = new_url
    self.response.headers['Content-Type'] = 'text/json'
    self.response.out.write(simplejson.dumps(user_json))  


class ProjectsHandler(webapp.RequestHandler):
  # Retrieve a list of all the Users.
  def get(self):
    # collect saved tasks
    projects_json = []
    for project in Project.all():
      project_json = { "id": "project/%s" % project.key().id_or_name(), "name": project.name, "timeLeft": project.timeLeft, "tasks": project.tasks }
      projects_json.append(project_json)
    # Set the response content type and dump the json
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(projects_json))
  
  # Create a new User
  def post(self):
    # collect the data from the record
    project_json = simplejson.loads(self.request.body)
    #Make sure we have all the required params
    if project_json.has_key('name') == False:
      project_json['name'] = '(No Name Project)'
    if project_json.has_key('timeLeft') == False:
      project_json['timeLeft'] = 0
    if project_json.has_key('tasks') == False:
      project_json['tasks'] = []
    project = Project(name=project_json["name"], timeLeft=project_json["timeLeft"], tasks=project_json["tasks"])
    project.put() # save
    guid = project.key().id_or_name()
    new_url = "/tasks-server/project/%s" % guid
    project_json["id"] = guid
    self.response.set_status(201, "Project created")
    self.response.headers['Location'] = new_url
    self.response.headers['Content-Type'] = 'text/json'
    self.response.out.write(simplejson.dumps(project_json))
  


def main():
  application = webapp.WSGIApplication([(r'/tasks-server/user?$', UsersHandler), 
    (r'/tasks-server/project?$', ProjectsHandler), 
    (r'/tasks-server/task?$', TasksHandler),
    (r'/tasks/([^\.]+)(\.json)?$', UserHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
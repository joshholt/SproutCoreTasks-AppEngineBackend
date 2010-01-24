#!/usr/bin/env python

""" Prupose: To serve tasks & project to SG's Sproutcore Tasks application.
    Author: Joshua Holt
    Date: 09-30-2009
    Last Modified: 01-10-2010
    
    ********* NOTE(2) ***********
    I added a nasty hack that I am not proud of on line #84
    
    ********* SOLVED *************
    
    I've solved the issue below.. I had forgotten that python and a builtin 
    function "setattr(obj, attr, val)". If you want to see how it DRYed up
    the code you can look through the commit log.
    
    
    ********* NOTE ***************
    This Code is not DRY it has been years since I've touched python
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
from google.appengine.api.labs import taskqueue

# Data Model Imports
import models
from models import User
from models import Task
from models import Project

# Helper Imports
import helpers,notification

class UsersHandler(webapp.RequestHandler):
  
  # Retrieve a list of all the Users.
  def get(self):
    if  len(self.request.params) == 0:
      users_json = helpers.build_list_json(User.all())
      # Set the response content type and dump the json
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(users_json))
    else:
      users_json = []
      if len(self.request.params) == 2:
        user = self.request.params['loginName']
        password = self.request.params['password']
        q = db.GqlQuery("SELECT * FROM User WHERE loginName = %s" % user)
        result = q.fetch(2)
        if len(result) == 0:
          users_json = []
        else:
          # This is really crappy, it works for now, but I'm not proud of it...
          if len(password.strip().replace("\'","")) == 0 or password == None:
            password = "'None'"
          if "'%s'" % result[0].password == password or (len(result[0].password) == 0 and password == "'None'"):
            result[0].authToken = helpers.generateAuthToken()
            result[0].put()
            users_json = helpers.build_list_json(User.all())
          else:
            users_json = []
      else:
        users_json = []
      # Set the response content type and dump the json
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(users_json))
  
  # Create a new User
  def post(self):
    if len(self.request.params) > 0:
      if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['role'], self.request.params['action']):
        # collect the data from the record
        user_json = simplejson.loads(self.request.body)
    
        # create a user
        user = helpers.apply_json_to_model_instance(User(), user_json)
        # save the new user
        user.put()
    
        guid = user.key().id_or_name()
        new_url = "/tasks-server/user/%s" % guid
        user_json["id"] = guid
    
        self.response.set_status(201, "User created")
        self.response.headers['Location'] = new_url
        self.response.headers['Content-Type'] = 'text/json'
        self.response.out.write(simplejson.dumps(user_json))
      else:
        self.response.set_status(401, "Not Authorized")
    else:
      user_json = simplejson.loads(self.request.body)
      user = helpers.apply_json_to_model_instance(User(), user_json)
      user.authToken = helpers.generateAuthToken()
      user.put()
      guid = user.key().id_or_name()
      new_url = "/tasks-server/user/%s" % guid
      user_json["id"] = guid
      self.response.set_status(201, "User created")
      self.response.headers['Location'] = new_url
      self.response.headers['Content-Type'] = 'text/json'
      self.response.out.write(simplejson.dumps(user_json))


class UserHandler(webapp.RequestHandler):
  # retrieve the user with a given id
  def get(self, guid):
    # find the matching user
    key = db.Key.from_path('User', int(guid))
    user = db.get(key)
    if not user == None:
      guid = "%s" % user.key().id_or_name()
      
      user_json = { "id": "%s" % guid,
        "name": user.name,
        "loginName": user.loginName, "role": user.role,
        "preferences": user.preferences if user.preferences != None else {},
        "authToken": user.authToken if user.authToken != None else "",
        "email": user.email if user.email != None else "",
        "createdAt": user.createdAt if user.createdAt != None else 0, 
        "updatedAt": user.updatedAt if user.updatedAt != None else 0 }
      
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(user_json))
    
    else:
      self.response.set_status(404, "User not found [%s]" % guid)
  
  # Update an existing record
  def put(self, guid):
    # find the matching user
    key = db.Key.from_path('User', int(guid))
    user = db.get(key)
    if not user == None:
    
      # collect the data from the record
      user_json = simplejson.loads(self.request.body)
      if str(user.role) == "_Guest":
        user_json['role'] = "_Guest"
      # update the record
      user = helpers.apply_json_to_model_instance(user, user_json)
      # save the record
      user.put()
      # return the same record...
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(user_json))
    else:
      self.response.set_status(404, "User not found")

  # delete the user with a given id
  def delete(self, guid):
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['role'], self.request.params['action']):
      # find the matching task and delete it if found
      key = db.Key.from_path('User', int(guid))
      user = db.get(key)
      if not user == None:
        user.delete()
        self.response.set_status(204, "Deleted")
      else:
        self.response.set_status(404, "Not Found")
    else:
      self.response.set_status(401, "Not Atuhorized")
  


class TasksHandler(webapp.RequestHandler):
  # Retrieve a list of all the Users.
  def get(self):
    # collect saved tasks
    tasks_json = []
    for task in Task.all():
      task_json = { "id": "%s" % task.key().id_or_name(),
        "name": task.name, "priority": task.priority,
        "projectId": task.projectId,
        "effort": task.effort, "submitterId": task.submitterId,
        "assigneeId": task.assigneeId, "type": task.type, "developmentStatus": task.developmentStatus,
        "validation": task.validation, "description": task.description,
        "createdAt": task.createdAt if task.createdAt != None else 0, 
        "updatedAt": task.updatedAt if task.updatedAt != None else 0 }
      
      tasks_json.append(task_json)
    
    # Set the response content type and dump the json
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(tasks_json))
  
  # Create a new Task
  def post(self):
    
    # collect the data from the record
    task_json = simplejson.loads(self.request.body)
    # create a new taks with the passed in json
    task = helpers.apply_json_to_model_instance(Task(),task_json)
    # save task
    task.put()
    guid = task.key().id_or_name()
    # Push notification email on the queue
    taskqueue.add(url='/mailer', params={'taskId': int(guid)})
    
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
      guid = "%s" % task.key().id_or_name()
      task_json = { "id": "%s" % guid, "name": task.name, 
        "priority": task.priority, "effort": task.effort,
        "projectId": task.projectId,
        "submitterId": task.submitterId, "assigneeId": task.assigneeId, 
        "type": task.type, "developmentStatus": task.developmentStatus,
        "validation": task.validation, "description": task.description,
        "createdAt": task.createdAt if task.createdAt != None else 0, 
        "updatedAt": task.updatedAt if task.updatedAt != None else 0 }
        
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
      task = helpers.apply_json_to_model_instance(task, task_json)
      # save the updated data
      task.put()
      # Push notification email on the queue
      taskqueue.add(url='/mailer', params={'taskId': int(guid)})
      # return the same record...
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(task_json))
    else:
      self.response.set_status(404, "Task not found")
  
  def delete(self, guid):
    """Delete the task with the given id"""
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['role'], self.request.params['action']):
      # search for the Project and delete if found
      key = db.Key.from_path('Task', int(guid))
      task = db.get(key)
      if not task == None:
        task.delete()
        self.response.set_status(204, "Deleted")
      else:
        self.response.set_status(404, "Not Found")
    else:
      self.response.set_status(401, "Not Authorized")
  


class ProjectsHandler(webapp.RequestHandler):
  # Retrieve a list of all the Users.
  def get(self):
    # collect saved tasks
    projects_json = []
    for project in Project.all():
      project_json = { "id": "%s" % project.key().id_or_name(),
        "name": project.name,
        "description": project.description,
        "timeLeft": project.timeLeft,
        "createdAt": project.createdAt if project.createdAt != None else 0, 
        "updatedAt": project.updatedAt if project.updatedAt != None else 0 }
      
      projects_json.append(project_json)
    
    # Set the response content type and dump the json
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(projects_json))
  
  # Create a new User
  def post(self):
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['role'], self.request.params['action']):
      # collect the data from the record
      project_json = simplejson.loads(self.request.body)
    
      # create a new project
      project = helpers.apply_json_to_model_instance(Project(), project_json)
      # save project
      project.save()
    
      guid = project.key().id_or_name()
      new_url = "/tasks-server/project/%s" % guid
      project_json["id"] = guid
    
      self.response.set_status(201, "Project created")
      self.response.headers['Location'] = new_url
      self.response.headers['Content-Type'] = 'text/json'
      self.response.out.write(simplejson.dumps(project_json))
    else:
      self.response.set_status(401, "Not Authorized")
  


class ProjectHandler(webapp.RequestHandler):
  """Deals with a single project item"""
    
  # Retrieve a single project record
  def get(self, guid):
    """Retrieves a single project record and returns the JSON"""
    key = db.Key.from_path('Project', int(guid))
    project = db.get(key)
    if not project == None:
      guid = "%s" % project.key().id_or_name()
      
      project_json = { "id": "%s" % guid, "name": project.timeLeft,
        "description": project.description,
        "createdAt": project.createdAt if project.createdAt != None else 0, 
        "updatedAt": project.updatedAt if project.updatedAt != None else 0 }
      
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(project_json))
    
    else:
      self.response.set_status(404, "Project not found")
  
  def put(self, guid):
    """Update the project with the given id"""
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['role'], self.request.params['action']):
      key = db.Key.from_path('Project', int(guid))
      project = db.get(key)
      if not project == None:
        # collect the json from the request
        project_json = simplejson.loads(self.request.body)
        # update the project record
        project = helpers.apply_json_to_model_instance(project, project_json)
        # save the updated data
        project.put()
      
        # return the same record...
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps(project_json))
      
      else:
        self.response.set_status(404, "Project not found")
    else:
      self.response.set_status(401, "Not Authorized")
  
  def delete(self, guid):
    """Delete the project with the given id"""
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['role'], self.request.params['action']):
      # search for the Project and delete if found
      key = db.Key.from_path('Project', int(guid))
      project = db.get(key)
      if not project == None:
        project.delete()
        self.response.set_status(204, "Deleted")
      else:
        self.response.set_status(404, "Not Found")
    else:
      self.response.set_status(401, "Not Authorized")

class MailWorker(webapp.RequestHandler):
  """The Mail worker works off the mail queue"""
  def post(self):
    notification.send_test_email(self.request.get('taskId'))
    

def main():
  application = webapp.WSGIApplication([(r'/tasks-server/user?$', UsersHandler),
    (r'/tasks-server/project?$', ProjectsHandler),
    (r'/tasks-server/task?$', TasksHandler),
    (r'/tasks-server/user/([^\.]+)?$', UserHandler),
    (r'/tasks-server/project/([^\.]+)?$', ProjectHandler),
    (r'/tasks-server/task/([^\.]+)?$', TaskHandler),
    (r'/mailer', MailWorker)],debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
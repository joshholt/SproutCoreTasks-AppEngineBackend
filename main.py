#!/usr/bin/env python

""" Prupose: To serve tasks & project to SG's Sproutcore Tasks application.
    Author: Joshua Holt
    Date: 09-30-2009
    Last Modified: 02-14-2010
    
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
import logging
import sys
import os
import datetime
import time
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
from models import Watch

# Helper Imports
import helpers,notification

max_results = 10000000
month_milliseconds = 30*24*60*60*1000

class RecordsHandler(webapp.RequestHandler):
  
  # Retrieve a list of all the Records.
  def get(self):
    
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
      lastRetrievedAt = ''
      if len(self.request.params) > 0:
        lastRetrievedAt = self.request.params['lastRetrievedAt']
    
      if lastRetrievedAt == '':
        users_json = helpers.build_user_list_json(User.all())
        tasks_json = helpers.build_task_list_json(Task.all())
        projects_json = helpers.build_project_list_json(Project.all())
        watches_json = helpers.build_watch_list_json(Watch.all())
      else:
        q = User.all()
        q.filter('updatedAt >', int(lastRetrievedAt))
        result = q.fetch(max_results)
        users_json = helpers.build_user_list_json(result)
        q = Task.all()
        q.filter('updatedAt >', int(lastRetrievedAt))
        result = q.fetch(max_results)
        tasks_json = helpers.build_task_list_json(result)
        q = Project.all()
        q.filter('updatedAt >', int(lastRetrievedAt))
        result = q.fetch(max_results)
        projects_json = helpers.build_project_list_json(result)
        q = Watch.all()
        q.filter('updatedAt >', int(lastRetrievedAt))
        result = q.fetch(max_results)
        watches_json = helpers.build_watch_list_json(result)
    
      result = {
       "users": users_json,
       "tasks": tasks_json,
       "projects": projects_json,
       "watches": watches_json
      }
    
      records_json = {
        "result": result
      }
    
      # Set the response content type and dump the json
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(records_json))
    else:
      self.response.set_status(401, "Not Authorized")

class UsersHandler(webapp.RequestHandler):
  
  # Retrieve a list of all the Users.
  def get(self):
    if  len(self.request.params) == 0:
      users_json = helpers.build_user_list_json(User.all())
      # Set the response content type and dump the json
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(users_json))
    else:
      users_json = []
      if len(self.request.params) == 2:
        loginName = self.request.params['loginName'].strip().replace("\'","")
        password = self.request.params['password'].strip().replace("\'","")
        q = User.all()
        q.filter('loginName =', loginName)
        result = q.fetch(1)
        if len(result) == 0:
          users_json = []
        else:
          if result[0].password == None or result[0].password == password:
            result[0].authToken = helpers.generateAuthToken()
            result[0].put()
            users_json = helpers.build_user_list_json([ result[0] ])
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
      if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
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
        self.response.headers['Content-Type'] = 'application/json'
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
      self.response.headers['Content-Type'] = 'application/json'
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
        "authToken": user.authToken if user.authToken != None else '',
        "email": user.email if user.email != '' else '',
        "createdAt": user.createdAt,
        "updatedAt": user.updatedAt }
      
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
      # The following keeps Guests and Developers and Testers from being able
      # to change their role.
      currentUserId = self.request.params['UUID']
      cukey = db.Key.from_path('User', int(currentUserId))
      cuser = db.get(cukey)
      if str(user.role) != user_json['role'] and str(cuser.role) != "_Manager":
        user_json['role'] = str(user.role)
        self.response.set_status(401, "Not Authorized")
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
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
      # find the matching user and delete it if found
      key = db.Key.from_path('User', int(guid))
      user = db.get(key)
      if not user == None:
        user.delete()
        self.response.set_status(204, "Deleted")
      else:
        self.response.set_status(404, "Not Found")
    else:
      self.response.set_status(401, "Not Authorized")


class TasksHandler(webapp.RequestHandler):
  # Retrieve a list of all the Tasks.
  def get(self):
    # collect saved tasks
    tasks_json = helpers.build_task_list_json(Task.all())
    
    # Set the response content type and dump the json
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(tasks_json))
  
  # Create a new Task
  def post(self):
    wantsNotifications = {"true": True, "false": False}.get(self.request.params['notify'].lower())
    # collect the data from the record
    task_json = simplejson.loads(self.request.body)
    logging.info(self.request.body)
    # if the user is a guest the project must be unallocated
    currentUserId = self.request.params['UUID']
    cukey = db.Key.from_path('User', int(currentUserId))
    user = db.get(cukey)
    if str(user.role) != '_Guest' or (task_json.has_key('projectId') == False or task_json['projectId'] == None):
      # create a new task with the passed in json
      task = helpers.apply_json_to_model_instance(Task(),task_json)
      # save task
      task.put()
      guid = task.key().id_or_name()
      # Push notification email on the queue if the task has some sort of status, etc..
      if notification.should_notify(currentUserId,task,"createTask", wantsNotifications):
        taskqueue.add(url='/mailer', params={'taskId': int(guid), 'currentUUID': self.request.params['UUID'], 'action': "createTask", 'name': "New Task"})
      new_url = "/tasks-server/task/%s" % guid
      task_json["id"] = guid
      self.response.set_status(201, "Task created")
      self.response.headers['Location'] = new_url
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(task_json))
    else:
      self.response.set_status(401, "Not Authorized")


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
        "createdAt": task.createdAt,
        "updatedAt": task.updatedAt }
      
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(task_json))
    else:
      self.response.set_status(404, "Task not found")
  
  def put(self, guid):
    """Update the task with the given id"""
    key = db.Key.from_path('Task', int(guid))
    task = db.get(key)
    if task != None:
      # cache current values before updates
      taskName = task.name
      taskType = task.type
      taskPriority = task.priority
      taskStatus = task.developmentStatus
      taskValidation = task.validation
      taskSubmitterId = task.submitterId
      taskAssigneeId = task.assigneeId
      taskEffort = task.effort
      taskProjectId = task.projectId
      taskDescription = task.description
      # collect the json from the request
      task_json = simplejson.loads(self.request.body)
      # if the user is a guest the project must be unallocated
      wantsNotifications = {"true": True, "false": False}.get(self.request.params['notify'].lower())
      currentUserId = self.request.params['UUID']
      cukey = db.Key.from_path('User', int(currentUserId))
      user = db.get(cukey)
      if str(user.role) != '_Guest' or (task_json.has_key('projectId') == False or task_json['projectId'] == None):
        # update the project record
        task = helpers.apply_json_to_model_instance(task, task_json)
        # save the updated data
        task.put()
        # Push notification email on the queue if we need to notify
        if notification.should_notify(currentUserId,task,"updateTask",wantsNotifications):
          taskqueue.add(url='/mailer', params={'taskId': int(guid), 'currentUUID': self.request.params['UUID'], 'action': "updateTask", 'name': taskName, 'type': taskType, 'priority': taskPriority, 'status': taskStatus, 'validation': taskValidation, 'submitterId': taskSubmitterId, 'assigneeId': taskAssigneeId, 'effort': taskEffort, 'projectId': taskProjectId, 'description': taskDescription})
        # return the same record...
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps(task_json))
      else:
        self.response.set_status(401, "Not Authorized")
    else:
      self.response.set_status(404, "Task not found")
  
  def delete(self, guid):
    """Delete the task with the given id"""
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
      # search for the Project and delete if found
      key = db.Key.from_path('Task', int(guid))
      task = db.get(key)
      wantsNotifications = {"true": True, "false": False}.get(self.request.params['notify'].lower())
      currentUserId = self.request.params['UUID']
      cukey = db.Key.from_path('User', int(currentUserId))
      user = db.get(cukey)
      if not task == None:
        # cache current values before updates
        taskName = task.name
        taskType = task.type
        taskPriority = task.priority
        taskStatus = task.developmentStatus
        taskValidation = task.validation
        taskSubmitterId = task.submitterId
        taskAssigneeId = task.assigneeId
        taskEffort = task.effort
        taskProjectId = task.projectId
        taskDescription = task.description
        # Push notification email on the queue if we need to notify
        if notification.should_notify(currentUserId,task,"deleteTask",wantsNotifications):
          taskqueue.add(url='/mailer', params={'taskId': int(guid), 'currentUUID': self.request.params['UUID'], 'action': "deleteTask", 'name': taskName, 'type': taskType, 'priority': taskPriority, 'status': taskStatus, 'validation': taskValidation, 'submitterId': taskSubmitterId, 'assigneeId': taskAssigneeId, 'effort': taskEffort, 'projectId': taskProjectId, 'description': taskDescription})
        task.delete()
        self.response.set_status(204, "Deleted")
      else:
        self.response.set_status(404, "Not Found")
    else:
      self.response.set_status(401, "Not Authorized")


class ProjectsHandler(webapp.RequestHandler):
  # Retrieve a list of all the Projects.
  def get(self):
    # collect saved tasks
    projects_json = helpers.build_project_list_json(Project.all())
    
    # Set the response content type and dump the json
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(projects_json))
  
  # Create a new Project
  def post(self):
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
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
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(project_json))
    else:
      self.response.set_status(401, "Not Authorized")


class ProjectHandler(webapp.RequestHandler):
  """Deals with a single project item"""
  
  # Retrieve a single Project
  def get(self, guid):
    """Retrieves a single project record and returns the JSON"""
    key = db.Key.from_path('Project', int(guid))
    project = db.get(key)
    if not project == None:
      guid = "%s" % project.key().id_or_name()
      
      project_json = { "id": "%s" % guid, "name": project.timeLeft,
        "description": project.description, "developmentStatus": project.developmentStatus,
        "activatedAt": project.activatedAt,
        "createdAt": project.createdAt,
        "updatedAt": project.updatedAt }
      
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(project_json))
    
    else:
      self.response.set_status(404, "Project not found")
  
  def put(self, guid):
    """Update the project with the given id"""
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
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
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
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


class WatchesHandler(webapp.RequestHandler):
  
  # Retrieve a list of all the Watches.
  def get(self):
    # collect saved watches
    watches_json = helpers.build_watch_list_json(Watch.all())
    
    # Set the response content type and dump the json
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(watches_json))
  
  # Create a new Watch
  def post(self):
    # collect the data from the record
    watch_json = simplejson.loads(self.request.body)
    #logging.info(self.request.body)
    # create a watch
    watch = helpers.apply_json_to_model_instance(Watch(), watch_json)
    # save the new watch
    watch.put()
    
    guid = watch.key().id_or_name()
    new_url = "/tasks-server/watch/%s" % guid
    watch_json["id"] = guid
    
    self.response.set_status(201, "Watch created")
    self.response.headers['Location'] = new_url
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(watch_json))


class WatchHandler(webapp.RequestHandler):
  # retrieve the watch with a given id
  def get(self, guid):
    # find the matching watch
    key = db.Key.from_path('Watch', int(guid))
    watch = db.get(key)
    if not watch == None:
      guid = "%s" % watch.key().id_or_name()
      
      watch_json = { "id": "%s" % guid,
      "taskId": watch.taskId,
      "userId": watch.userId,
      "createdAt": watch.createdAt,
      "updatedAt": watch.updatedAt }
      
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(watch_json))
    
    else:
      self.response.set_status(404, "Watch not found [%s]" % guid)
  
  # Update an existing record
  def put(self, guid):
    # find the matching watch
    key = db.Key.from_path('Watch', int(guid))
    watch = db.get(key)
    if not watch == None:
      
      # collect the data from the record
      watch_json = simplejson.loads(self.request.body)
      # update the record
      watch = helpers.apply_json_to_model_instance(watch, watch_json)
      # save the record
      watch.put()
      # return the same record...
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(watch_json))
    else:
      self.response.set_status(404, "Watch not found")
  
  # delete the watch with a given id
  def delete(self, guid):
    # find the matching watch and delete it if found
    key = db.Key.from_path('Watch', int(guid))
    watch = db.get(key)
    if not watch == None:
      watch.delete()
      self.response.set_status(204, "Deleted")
    else:
      self.response.set_status(404, "Not Found")


class CleanupHandler(webapp.RequestHandler):
  """Deletes soft-deleted records more than a month old"""
  def post(self):
    month_ago = int(time.time()*1000) - month_milliseconds
    
    q = User.all()
    q.filter("status =", "deleted")
    q.filter("updatedAt <", month_ago)
    users_to_delete = q.fetch(max_results)
    db.delete(users_to_delete)
    users_json = helpers.build_user_list_json(users_to_delete)
    
    q = Project.all()
    q.filter("status =", "deleted")
    q.filter("updatedAt <", month_ago)
    projects_to_delete = q.fetch(max_results)
    db.delete(projects_to_delete)
    projects_json = helpers.build_project_list_json(projects_to_delete)
    
    q = Task.all()
    q.filter("status =", "deleted")
    q.filter("updatedAt <", month_ago)
    tasks_to_delete = q.fetch(max_results)
    db.delete(tasks_to_delete)
    tasks_json = helpers.build_task_list_json(tasks_to_delete)
    
    q = Watch.all()
    q.filter("status =", "deleted")
    q.filter("updatedAt <", month_ago)
    watches_to_delete = q.fetch(max_results)
    db.delete(watches_to_delete)
    watches_json = helpers.build_watch_list_json(watches_to_delete)
    
    result = {
     "users": users_json,
     "tasks": tasks_json,
     "projects": projects_json,
     "watches": watches_json
    }
  
    records_json = {
      "result": result
    }
  
    # Set the response content type and dump the json
    self.response.set_status(200, "Data Cleaned Out")
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(records_json))
    

class LogoutHandler(webapp.RequestHandler):
  """Logs off a user"""
  def post(self):
    userId = self.request.get('id')
    # find the matching user
    key = db.Key.from_path('User', int(userId))
    user = db.get(key)
    if not user == None:
      # clear out authentication token
      user.authToken = None
      # save the record
      user.put()
      self.response.set_status(200, "User logged out")
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps({ "message": 'Logout successful'}))
    else:
      self.response.set_status(404, "User not found")    


class MailWorker(webapp.RequestHandler):
  """The Mail worker works off the mail queue"""
  def post(self):
    action = {"createTask": "created", "updateTask": "updated", "deleteTask": "deleted"}.get(self.request.get('action'))
    name = self.request.get('name')
    ttype = self.request.get('type')
    priority = self.request.get('priority')
    status = self.request.get('status')
    validation = self.request.get('validation')
    submitterId = self.request.get('submitterId')
    assigneeId = self.request.get('assigneeId')
    effort = self.request.get('effort')
    projectId = self.request.get('projectId')
    description = self.request.get('description')
    notification.send_notification(self.request.get('taskId'), self.request.get('currentUUID'), action, name, ttype, priority, status, validation, submitterId, assigneeId, effort, projectId, description)


def main():
  application = webapp.WSGIApplication([
    (r'/tasks-server/records?$', RecordsHandler),
    (r'/tasks-server/user?$', UsersHandler),
    (r'/tasks-server/project?$', ProjectsHandler),
    (r'/tasks-server/task?$', TasksHandler),
    (r'/tasks-server/watch?$', WatchesHandler),
    (r'/tasks-server/user/([^\.]+)?$', UserHandler),
    (r'/tasks-server/project/([^\.]+)?$', ProjectHandler),
    (r'/tasks-server/task/([^\.]+)?$', TaskHandler),
    (r'/tasks-server/watch/([^\.]+)?$', WatchHandler),
    (r'/tasks-server/cleanup', CleanupHandler),
    (r'/tasks-server/logout', LogoutHandler),
    (r'/mailer', MailWorker)],debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
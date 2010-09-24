#!/usr/bin/env python

""" Purpose: To serve tasks & project to SG's Sproutcore Tasks application.
    Author: Joshua Holt
    Author: Suvajit Gupta
"""

# Google App Engine Imports
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
import helpers, notification

# Global constants
max_results = 10000000
month_milliseconds = 30*24*60*60*1000

class RecordsHandler(webapp.RequestHandler):
  
  # Retrieve a list of all records.
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
        q = Project.all()
        q.filter('updatedAt >', int(lastRetrievedAt))
        result = q.fetch(max_results)
        projects_json = helpers.build_project_list_json(result)
        q = Task.all()
        q.filter('updatedAt >', int(lastRetrievedAt))
        result = q.fetch(max_results)
        tasks_json = helpers.build_task_list_json(result)
        q = Watch.all()
        q.filter('updatedAt >', int(lastRetrievedAt))
        result = q.fetch(max_results)
        watches_json = helpers.build_watch_list_json(result)
    
      result = {
       "users": users_json,
       "projects": projects_json,
       "tasks": tasks_json,
       "watches": watches_json
      }
    
      records_json = {
        "result": result
      }
    
      # Set the response content type and dump the json
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(records_json))
    else:
      helpers.report_unauthorized_access(self.response)


class UserHandler(webapp.RequestHandler):
  
  def get(self):
    users_json = []
    param_count = len(self.request.params)
    self.response.headers['Content-Type'] = 'application/json'
    if param_count > 0:
      loginName = self.request.params['loginName'].strip().replace("\'","")
      q = User.all()
      q.filter('loginName =', loginName)
      result = q.fetch(1)
      result_count = len(result)
    # Check if a specified loginName is available
    if param_count == 1:
      self.response.out.write(simplejson.dumps({ "loginNameAvailable": "yes" if result_count == 0 else "no"}))
    # Login a user given loginName and password
    elif param_count == 2:
      password = self.request.params['password'].strip().replace("\'","")
      if result_count != 0:
        if result[0].password == None or result[0].password == password:
          result[0].authToken = helpers.generate_auth_token()
          result[0].put()
          users_json = [ helpers.build_user_json(result[0], True) ]
      self.response.out.write(simplejson.dumps(users_json))
    else:
      self.response.set_status(401, "Invalid parameters")
      self.response.out.write(simplejson.dumps({ "message": 'Need 1 or 2 parameters for this call'}))
  
  def post(self):
    # Create a new user
    if len(self.request.params) > 0:
      if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
        helpers.create_user(self.request, self.response, False)
      else:
        helpers.report_unauthorized_access(self.response)
    # Signup a new user
    else:
      helpers.create_user(self.request, self.response, True)

  # Update an existing user with a given id
  def put(self, guid):
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
      key = db.Key.from_path('User', int(guid))
      user = db.get(key)
      if not user == None:
        user_json = simplejson.loads(self.request.body)
        # Prevent non-Managers from changing their role
        currentUserId = self.request.params['UUID']
        cukey = db.Key.from_path('User', int(currentUserId))
        cuser = db.get(cukey)
        if str(user.role) != user_json['role'] and str(cuser.role) != "_Manager":
          user_json['role'] = str(user.role)
          helpers.report_unauthorized_access(self.response)
        user = helpers.apply_json_to_model_instance(user, user_json)
        user.put()
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps(user_json))
      else:
        helpers.report_missing_record(self.response)
    else:
      helpers.report_unauthorized_access(self.response)
  
  # Delete a user with a given id
  def delete(self, guid):
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
      # find the matching user and delete it if found
      key = db.Key.from_path('User', int(guid))
      user = db.get(key)
      if not user == None:
        user.delete()
        self.response.set_status(204, "Deleted")
      else:
        helpers.report_missing_record(self.response)
    else:
      helpers.report_unauthorized_access(self.response)


class ProjectHandler(webapp.RequestHandler):
  # Create a new project
  def post(self):
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
      project_json = simplejson.loads(self.request.body)
      project = helpers.apply_json_to_model_instance(Project(), project_json)
      project.save()
      guid = project.key().id_or_name()
      new_url = "/tasks-server/project/%s" % guid
      project_json["id"] = guid
      self.response.set_status(201, "Project created")
      self.response.headers['Location'] = new_url
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(project_json))
    else:
      helpers.report_unauthorized_access(self.response)

  # Update an existing project with a given id
  def put(self, guid):
    """Update the project with the given id"""
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
      key = db.Key.from_path('Project', int(guid))
      project = db.get(key)
      if not project == None:
        project_json = simplejson.loads(self.request.body)
        project = helpers.apply_json_to_model_instance(project, project_json)
        project.put()
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps(project_json))
      else:
        helpers.report_missing_record(self.response)
    else:
      helpers.report_unauthorized_access(self.response)
  
  # Delete a project with a given id
  def delete(self, guid):
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
      key = db.Key.from_path('Project', int(guid))
      project = db.get(key)
      if not project == None:
        project.delete()
        self.response.set_status(204, "Deleted")
      else:
        helpers.report_missing_record(self.response)
    else:
      helpers.report_unauthorized_access(self.response)


class TaskHandler(webapp.RequestHandler):
  # Create a new task
  def post(self):
    wantsNotifications = {"true": True, "false": False}.get(self.request.params['notify'].lower())
    task_json = simplejson.loads(self.request.body)
    logging.info(self.request.body)
    # if the user is a Guest the project must be unallocated
    currentUserId = self.request.params['UUID']
    cukey = db.Key.from_path('User', int(currentUserId))
    user = db.get(cukey)
    if str(user.role) != '_Guest' or (task_json.has_key('projectId') == False or task_json['projectId'] == None):
      task = helpers.apply_json_to_model_instance(Task(),task_json)
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
      helpers.report_unauthorized_access(self.response)

  # Update an existing task with a given id
  def put(self, guid):
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
      task_json = simplejson.loads(self.request.body)
      # if the user is a Guest the project must be unallocated
      wantsNotifications = {"true": True, "false": False}.get(self.request.params['notify'].lower())
      currentUserId = self.request.params['UUID']
      cukey = db.Key.from_path('User', int(currentUserId))
      user = db.get(cukey)
      if str(user.role) != '_Guest' or (task_json.has_key('projectId') == False or task_json['projectId'] == None):
        task = helpers.apply_json_to_model_instance(task, task_json)
        task.put()
        # Push notification email on the queue if we need to notify
        if notification.should_notify(currentUserId,task,"updateTask",wantsNotifications):
          taskqueue.add(url='/mailer', params={'taskId': int(guid), 'currentUUID': self.request.params['UUID'], 'action': "updateTask", 'name': taskName, 'type': taskType, 'priority': taskPriority, 'status': taskStatus, 'validation': taskValidation, 'submitterId': taskSubmitterId, 'assigneeId': taskAssigneeId, 'effort': taskEffort, 'projectId': taskProjectId, 'description': taskDescription})
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps(task_json))
      else:
        helpers.report_unauthorized_access(self.response)
    else:
      helpers.report_missing_record(self.response)

  # Delete a task with a given id
  def delete(self, guid):
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
        helpers.report_missing_record(self.response)
    else:
      helpers.report_unauthorized_access(self.response)


class WatchHandler(webapp.RequestHandler):
  # Create a new watch
  def post(self):
    watch_json = simplejson.loads(self.request.body)
    watch = helpers.apply_json_to_model_instance(Watch(), watch_json)
    watch.put()
    guid = watch.key().id_or_name()
    new_url = "/tasks-server/watch/%s" % guid
    watch_json["id"] = guid
    self.response.set_status(201, "Watch created")
    self.response.headers['Location'] = new_url
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(watch_json))

  # Update an existing watch with a given id
  def put(self, guid):
    """Update the watch with the given id"""
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
      key = db.Key.from_path('Watch', int(guid))
      watch = db.get(key)
      if not watch == None:
        watch_json = simplejson.loads(self.request.body)
        watch = helpers.apply_json_to_model_instance(watch, watch_json)
        watch.put()
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps(watch_json))
      else:
        helpers.report_missing_record(self.response)
    else:
      helpers.report_unauthorized_access(self.response)

  # Delete a watch with a given id
  def delete(self, guid):
    key = db.Key.from_path('Watch', int(guid))
    watch = db.get(key)
    if not watch == None:
      watch.delete()
      self.response.set_status(204, "Deleted")
    else:
      helpers.report_missing_record(self.response)


# Deletes soft-deleted records more than a month old.
# Example command line invocations:
# curl -X POST http://localhost:8091/tasks-server/cleanup -d ""
# curl -X POST http://localhost:8091/tasks-server/cleanup -d "cutoff=1282279058109"
class CleanupHandler(webapp.RequestHandler):
  def post(self):
    cutoff = ''
    
    if len(self.request.params) > 0:
      cutoff = self.request.params['cutoff']
    if cutoff == '':
      cutoff = int(time.time()*1000) - month_milliseconds
    else:
      cutoff = int(cutoff)
    
    q = User.all()
    q.filter("status =", "deleted")
    q.filter("updatedAt <", cutoff)
    users_to_delete = q.fetch(max_results)
    db.delete(users_to_delete)
    users_json = helpers.build_user_list_json(users_to_delete)
    
    q = Project.all()
    q.filter("status =", "deleted")
    q.filter("updatedAt <", cutoff)
    projects_to_delete = q.fetch(max_results)
    db.delete(projects_to_delete)
    projects_json = helpers.build_project_list_json(projects_to_delete)
    
    q = Task.all()
    q.filter("status =", "deleted")
    q.filter("updatedAt <", cutoff)
    tasks_to_delete = q.fetch(max_results)
    db.delete(tasks_to_delete)
    tasks_json = helpers.build_task_list_json(tasks_to_delete)
    
    q = Watch.all()
    q.filter("status =", "deleted")
    q.filter("updatedAt <", cutoff)
    watches_to_delete = q.fetch(max_results)
    db.delete(watches_to_delete)
    watches_json = helpers.build_watch_list_json(watches_to_delete)
    
    result = {
     "cutoff": cutoff,
     "usersDeleted": users_json,
     "projectsDeleted": projects_json,
     "tasksDeleted": tasks_json,
     "watchesDeleted": watches_json
    }
  
    records_json = {
      "result": result
    }
  
    self.response.set_status(200, "Data Cleaned Out")
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(records_json))
    

# Logs off a user wiht a given id
class LogoutHandler(webapp.RequestHandler):
  def post(self):
    userId = self.request.get('id')
    # find the matching user
    key = db.Key.from_path('User', int(userId))
    user = db.get(key)
    if not user == None:
      # clear out authentication token
      user.authToken = None
      user.put()
      self.response.set_status(200, "User logged out")
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps({ "message": 'Logout successful'}))
    else:
      helpers.report_missing_record(self.response)


# The Mail worker processes the mail queue
class MailWorker(webapp.RequestHandler):
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
    (r'/tasks-server/user?$', UserHandler),
    (r'/tasks-server/user/([^\.]+)?$', UserHandler),
    (r'/tasks-server/project?$', ProjectHandler),
    (r'/tasks-server/project/([^\.]+)?$', ProjectHandler),
    (r'/tasks-server/task?$', TaskHandler),
    (r'/tasks-server/task/([^\.]+)?$', TaskHandler),
    (r'/tasks-server/watch?$', WatchHandler),
    (r'/tasks-server/watch/([^\.]+)?$', WatchHandler),
    (r'/tasks-server/cleanup', CleanupHandler),
    (r'/tasks-server/logout', LogoutHandler),
    (r'/mailer', MailWorker)],debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
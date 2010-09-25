#!/usr/bin/env python

""" Purpose: To provide endpoints for Tasks GUI and command-line tools.
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

class RecordsHandler(webapp.RequestHandler):
  
  # Retrieve a list of all records.
  def get(self):
    
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
      lastRetrievedAt = ''
      if len(self.request.params) > 0:
        lastRetrievedAt = self.request.params['lastRetrievedAt']
    
      currentUserId = int(self.request.params['UUID'])
      if lastRetrievedAt == '':
        users_json = helpers.build_user_list_json(User.all(), currentUserId)
        tasks_json = helpers.build_task_list_json(Task.all())
        projects_json = helpers.build_project_list_json(Project.all())
        watches_json = helpers.build_watch_list_json(Watch.all())
      else:
        q = User.all()
        q.filter('updatedAt >', int(lastRetrievedAt))
        result = q.fetch(helpers.MAX_RESULTS)
        users_json = helpers.build_user_list_json(result, currentUserId)
        q = Project.all()
        q.filter('updatedAt >', int(lastRetrievedAt))
        result = q.fetch(helpers.MAX_RESULTS)
        projects_json = helpers.build_project_list_json(result)
        q = Task.all()
        q.filter('updatedAt >', int(lastRetrievedAt))
        result = q.fetch(helpers.MAX_RESULTS)
        tasks_json = helpers.build_task_list_json(result)
        q = Watch.all()
        q.filter('updatedAt >', int(lastRetrievedAt))
        result = q.fetch(helpers.MAX_RESULTS)
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
  

class TaskHandler(webapp.RequestHandler):
  # Create a new task
  def post(self):
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
      wantsNotifications = {"true": True, "false": False}.get(self.request.params['notify'].lower())
      task_json = simplejson.loads(self.request.body)
      logging.info(self.request.body)
      task = helpers.apply_json_to_model_instance(Task(),task_json)
      # ensure Guest-created tasks are unallocated
      currentUserId = self.request.params['UUID']
      cukey = db.Key.from_path('User', int(currentUserId))
      user = db.get(cukey)
      if str(user.role) == '_Guest' and task_json.has_key('projectId') == True and task_json['projectId'] != None:
        task.projectId = None
      task.put()
      guid = task.key().id_or_name()
      # Push notification email on the queue if the task has some sort of status, etc..
      if notification.should_notify(currentUserId, task, wantsNotifications):
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
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
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
        wantsNotifications = {"true": True, "false": False}.get(self.request.params['notify'].lower())
        task = helpers.apply_json_to_model_instance(task, task_json)
        # ensure Guest-created tasks are unallocated
        currentUserId = self.request.params['UUID']
        cukey = db.Key.from_path('User', int(currentUserId))
        user = db.get(cukey)
        if str(user.role) == '_Guest' and task_json.has_key('projectId') == True and task_json['projectId'] != None:
          taskProjectId = task.projectId = None
        task.put()
        # Push notification email on the queue if we need to notify
        action = "deleteTask" if task.status == "deleted" else "updateTask"
        if notification.should_notify(currentUserId, task, wantsNotifications):
          taskqueue.add(url='/mailer', params={'taskId': int(guid), 'currentUUID': self.request.params['UUID'], 'action': action, 'name': taskName, 'type': taskType, 'priority': taskPriority, 'status': taskStatus, 'validation': taskValidation, 'submitterId': taskSubmitterId, 'assigneeId': taskAssigneeId, 'effort': taskEffort, 'projectId': taskProjectId, 'description': taskDescription})
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps(task_json))
      else:
        helpers.report_missing_record(self.response)
    else:
      helpers.report_unauthorized_access(self.response)
      

class WatchHandler(webapp.RequestHandler):
  # Create a new watch
  def post(self):
    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], self.request.params['action']):
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
    else:
      helpers.report_unauthorized_access(self.response)

  # Update an existing watch with a given id
  def put(self, guid):
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


# Logs off a user with a given id
class LogoutHandler(webapp.RequestHandler):
  def post(self):
    userId = self.request.params['UUID']
    key = db.Key.from_path('User', int(userId))
    user = db.get(key)
    if user != None:
      if user.authToken == self.request.params['ATO']:
        # clear out authentication token to indicate user was logged out
        user.authToken = None
        user.put()
        self.response.set_status(200, "User logged out")
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps({ "message": 'Logout successful'}))
      else:
        helpers.report_unauthorized_access(self.response)
    else:
      helpers.report_missing_record(self.response)


# Deletes soft-deleted records more than a month old.
# Example command line invocations (first one cleans up more than month-old soft-deleted data, second one for soft-deleted data older than specified time):
# curl -X POST http://localhost:8091/tasks-server/cleanup -d ""
# curl -X POST http://localhost:8091/tasks-server/cleanup -d "cutoff=1282279058109"
class CleanupHandler(webapp.RequestHandler):
  def post(self):
    cutoff = ''
    
    if len(self.request.params) > 0:
      cutoff = self.request.params['cutoff']
    if cutoff == '':
      cutoff = int(time.time()*1000) - helpers.MONTH_MILLISECONDS
    else:
      cutoff = int(cutoff)
    
    users_json = helpers.build_user_list_json(helpers.purge_soft_deleted_records(User.all(), cutoff), None)
    projects_json = helpers.build_project_list_json(helpers.purge_soft_deleted_records(Project.all(), cutoff))
    tasks_json = helpers.build_task_list_json(helpers.purge_soft_deleted_records(Task.all(), cutoff))
    watches_json = helpers.build_watch_list_json(helpers.purge_soft_deleted_records(Watch.all(), cutoff))
    
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
    (r'/tasks-server/logout', LogoutHandler),
    (r'/tasks-server/cleanup', CleanupHandler),
    (r'/mailer', MailWorker)],debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
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
  
  # If only loginName is provided as parameter: If specified loginName exists, return user information
  # If valid password is also passed as parameter: Authenticate user and return authToken as well
  def get(self):
    users_json = []
    self.response.headers['Content-Type'] = 'application/json'
    param_count = len(self.request.params)
    if param_count == 1 or param_count == 2:
      q = User.all()
      q.filter('loginName =', self.request.params['loginName'].strip().replace("\'",""))
      result = q.fetch(1)
      if len(result) == 1:
        if param_count == 1:
          users_json = [ helpers.build_user_json(result[0], False) ]
        elif param_count == 2:
          if result[0].password == None or result[0].password == self.request.params['password'].strip().replace("\'",""):
            result[0].authToken = helpers.generate_auth_token()
            result[0].put()
            users_json = [ helpers.build_user_json(result[0], True) ]
      self.response.out.write(simplejson.dumps(users_json))
    else:
      self.response.set_status(400, "Invalid parameters")
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
        status = user_json.get('status')
        being_deleted = (status != None and status == 'deleted')
        if being_deleted or helpers.is_login_name_valid(user_json['loginName'], user):
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
          helpers.report_invalid_login_name(self.response)
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


# Delete soft-deleted items and handle IDs referencing non-existent records
# Example command line invocation that cleans up more than month-old soft-deleted data:
# curl -X POST http://localhost:8091/tasks-server/cleanup\?UUID=1\&ATO=0c69bf928aa2157e4a461567632afc9ecf18c010 -d ""
class CleanupHandler(webapp.RequestHandler):
  def post(self):

    if helpers.authorized(self.request.params['UUID'], self.request.params['ATO'], "cleanup"):
      
      now = int(time.time()*1000)
      
      # Delete soft-deleted records older than timestamp (if specified) or older than a month
      cutoff = self.request.get('cutoff')
      if cutoff == None or cutoff == '':
        # default to a cutoff time a month ago
        cutoff = now - helpers.MONTH_MILLISECONDS
      else:
        cutoff = int(cutoff)
    
      users_json = helpers.build_user_list_json(helpers.purge_soft_deleted_records(User.all(), cutoff), None)
      projects_json = helpers.build_project_list_json(helpers.purge_soft_deleted_records(Project.all(), cutoff))
      tasks_json = helpers.build_task_list_json(helpers.purge_soft_deleted_records(Task.all(), cutoff))
      watches_json = helpers.build_watch_list_json(helpers.purge_soft_deleted_records(Watch.all(), cutoff))
    
      # Handle IDs referencing non-existent records:
      # * non-existent task projectId/submitterId/assigneeId should be set to null
      # * watches with non-existent taskId/watchId should be soft-deleted
      # * set updatedAt for all records being modified
      user_ids = helpers.extract_record_ids(User.all())
      project_ids = helpers.extract_record_ids(Project.all())
      tasks = Task.all()
      task_ids = helpers.extract_record_ids(tasks)
      tasks_updated = []
      for task in tasks:
        updated = False
        project_id = task.projectId
        if project_id != None and project_id != '':
          try:
            idx = project_ids.index(project_id)
          except:
            idx = -1
          if idx == -1:
            task.projectId = None
            updated = True
        submitter_id = task.submitterId
        if submitter_id != None and submitter_id != '':
          try:
            idx = user_ids.index(submitter_id)
          except:
            idx = -1
          if idx == -1:
            task.submitterId = None
            updated = True
        assignee_id = task.assigneeId
        if assignee_id != None and assignee_id != '':
          try:
            idx = user_ids.index(assignee_id)
          except:
            idx = -1
          if idx == -1:
            task.assigneeId = None
            updated = True
        if updated:
          task.updatedAt = now
          task.put()
          tasks_updated.append(task)
      tasks_updated_json = helpers.build_task_list_json(tasks_updated)
          
      watches = Watch.all()
      watches_soft_deleted = []
      for watch in watches:
        if watch.status != 'deleted':
          task_id = watch.taskId
          if task_id != None and task_id != '':
            try:
              task_idx = task_ids.index(task_id)
            except:
              task_idx = -1
          user_id = watch.userId
          if user_id != None and user_id != '':
            try:
              user_idx = user_ids.index(user_id)
            except:
              user_idx = -1
          if task_idx == -1 or user_idx == -1:
            watch.status = 'deleted'
            watch.updatedAt = now
            watch.put()
            watches_soft_deleted.append(watch)
      watches_soft_deleted_json = helpers.build_watch_list_json(watches_soft_deleted)
          
      # Return all affected records broken down by category
      result = {
       "cutoff": cutoff,
       "usersDeleted": users_json,
       "projectsDeleted": projects_json,
       "tasksDeleted": tasks_json,
       "watchesDeleted": watches_json,
       "tasksUpdated": tasks_updated_json,
       "watchesSoftDeleted": watches_soft_deleted_json
      }
      records_json = {
        "result": result
      }
  
      self.response.set_status(200, "Cleanup done")
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(records_json))
    
    else:
      helpers.report_unauthorized_access(self.response)


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
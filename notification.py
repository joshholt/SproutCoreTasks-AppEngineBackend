#!/usr/bin/env python

""" Prupose: To Send Notifications based on certain task conditions.
    Author: Joshua Holt
    Date: 12-09-2009
    Last Modified: 02-14-2010
"""
import time,datetime
#from google.appengine.api import xmpp # importing this lib allows jabber chat messages to be sent.
from google.appengine.api import mail
from google.appengine.ext import db
# Data Model Imports
from models import User, Task, Project

def should_notify(currentUserID, task, action, wantsNotifications = True):
  """Determines if a notification should be sent"""
  currentUserKey = db.Key.from_path('User', int(currentUserID))
  currentUser = db.get(currentUserKey)
  if task.submitterId != None:
    submitterKey = db.Key.from_path('User', int(task.submitterId))
    submitter = db.get(submitterKey)
  if task.assigneeId != None:
    assigneeKey = db.Key.from_path('User', int(task.assigneeId))
    assignee = db.get(assigneeKey)
  if wantsNotifications == False:
    retVal = False
  elif int(currentUserID) == int(task.submitterId) and int(currentUserID) == int(task.assigneeId):
    retVal = False
  else:
    retVal = {
    # If task
    "createTask": lambda task: True if task.name != "_NewTask" else False,
    "updateTask": lambda task: True,
    "deleteTask": lambda task: True 
    }[action](task)
    
  return retVal

def send_notification(taskID, currentUserID, action):
  """sends a test email"""
  # Get information about this task and the assignee and submitter
  task_key = db.Key.from_path('Task', int(taskID))
  task = db.get(task_key)
  currentUser_key = db.Key.from_path('User', int(currentUserID))
  currentUser = db.get(currentUser_key)

  if task != None:
    if task.projectId != None:
      project_key = db.Key.from_path('Project', int(task.projectId))
      project = db.get(project_key)
    submitter = None; assignee = None;
    if task.submitterId != None:
      submitter_key = db.Key.from_path('User', int(task.submitterId))
      submitter = db.get(submitter_key)
    if task.assigneeId != None:
      assignee_key = db.Key.from_path('User', int(task.assigneeId))
      assignee = db.get(assignee_key)
    if submitter != None or assignee != None:
      project_name = project.name if task.projectId != None else "Unallocated"
      message = mail.EmailMessage(sender="Tasks <suvajit.gupta@eloqua.com>", subject="Task #%s %s by %s (%s)" % (task.key().id_or_name(), action, currentUser.name, currentUser.loginName ))
      if assignee != None and assignee.email != None and assignee.key().id_or_name() != currentUserID:
        message.to = "%s" % assignee.email
      else:
        message.to = ''
      if submitter != None and submitter.email != None and submitter.key().id_or_name() != currentUserID:
        message.cc = "%s" % submitter.email
      else:
        message.cc = ''
        
      message.body = """Name:\t\t%s

Type:\t\t%s
Priority:\t\t%s
Status:\t\t%s
Validation:\t%s
      
Submitter:\t%s (%s)
Assignee:\t%s (%s)
      
Effort:\t\t%s
Project:\t\t%s
      
Description:
      
%s
      """ % (task.name,
       task.type.replace('_','') if not task.type == None else "-----", 
       task.priority.replace('_','') if not task.priority == None else "-----", 
       task.developmentStatus.replace('_','') if not task.developmentStatus == None else "-----", 
       task.validation.replace('_','') if not task.validation == None else "-----", 
       submitter.name, submitter.loginName,
       assignee.name, assignee.loginName,
       task.effort.replace('_','') if not task.effort == None else "-----", 
       project_name,
       task.description if not task.description == None else "")
       
  if message.to == '' and message.cc != '':
    message.to = message.cc
    message.cc = ''
    message.send()
  elif message.to == '' and message.cc == '':
    pass
  else:
    message.send()

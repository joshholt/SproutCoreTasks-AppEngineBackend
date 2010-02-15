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
  submitterKey = db.Key.from_path('User', int(task.submitterId))
  submitter = db.get(submitterKey)
  assigneeKey = db.Key.from_path('User', int(task.assigneeId))
  assignee = db.get(assigneeKey)
  
  if currentUserID == task.submitterId or currentUserId == task.assigneeId or wantsNotifications == False:
    retVal = False
  else:
    retVal = {
    # If task
    "createTask": lambda task: True if task.priority != None and task.developmentStatus != None and task.type != None and task.name != "_NewTask" else False,
    "updateTask": lambda task: True 
    }[action](task)
    
  return retVal

def send_notification(arg):
  """sends a test email"""
  # Get information about this task and the assignee and submitter
  task_key = db.Key.from_path('Task', int(arg))
  task = db.get(task_key)
  if task != None:
    submitter_key = db.Key.from_path('User', int(task.submitterId))
    submitter = db.get(submitter_key)
    assignee_key = db.Key.from_path('User', int(task.assigneeId))
    assignee = db.get(assignee_key)
    if task.projectId != None:
      project_key = db.Key.from_path('Project', int(task.projectId))
      project = db.get(project_key)
    if submitter != None and assignee != None:
      project_name = project.name if task.projectId != None else "Unallocated"
      message = mail.EmailMessage(sender="Tasks <suvajit.gupta@eloqua.com>", subject="Notification for Task #%s" % task.key().id_or_name())
      if assignee.email != None:
        message.to = "%s" % assignee.email
      else:
        message.to = None
      if submitter.email != None:
        message.cc = "%s" % submitter.email
      else:
        message.cc = None
        
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
       
  if message.to == None and message.cc != None:
    message.to = message.cc
    message.cc = None
    message.send()
  else if message.to == None and message.cc == None:
    pass
  else:
    message.send()

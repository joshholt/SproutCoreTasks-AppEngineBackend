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

def should_notify(currentUserId, task, action, wantsNotifications = True):
  """Determines if a notification should be sent"""
  currentUserKey = db.Key.from_path('User', int(currentUserId))
  currentUser = db.get(currentUserKey)
  if task.submitterId != None:
    submitterKey = db.Key.from_path('User', int(task.submitterId))
    submitter = db.get(submitterKey)
  if task.assigneeId != None:
    assigneeKey = db.Key.from_path('User', int(task.assigneeId))
    assignee = db.get(assigneeKey)
  if wantsNotifications == False:
    retVal = False
  elif task.submitterId != None and int(currentUserId) == int(task.submitterId) and task.assigneeId != None and int(currentUserId) == int(task.assigneeId):
    retVal = False
  else:
    retVal = {
    # If task
    "createTask": lambda task: True if task.name != "New Task" else False,
    "updateTask": lambda task: True,
    "deleteTask": lambda task: True 
    }[action](task)
    
  return retVal

def send_notification(taskId, currentUserId, action, name, ttype, priority, status, validation, submitterId, assigneeId):
  """sends email notification"""
  # message = mail.EmailMessage(sender="DEBUG <suvajit.gupta@eloqua.com>", subject="DEBUG: Task #%s %s" % (taskId, action), to="suvajit.gupta@eloqua.com", body="Name: %s" % (name))
  # message.send()
  
  # Get information about this task and the assignee and submitter
  task = None;
  if action != "deleted":
    task_key = db.Key.from_path('Task', int(taskId))
    task = db.get(task_key)
  currentUser_key = db.Key.from_path('User', int(currentUserId))
  currentUser = db.get(currentUser_key)

  if action == "deleted" or task != None:
    submitter = None; assignee = None;
    if action == "deleted" or (task != None and task.submitterId != None):
      submitter_key = db.Key.from_path('User', int(task.submitterId if action != "deleted" else submitterId))
      submitter = db.get(submitter_key)
    if action == "deleted" or (task != None and task.assigneeId != None):
      assignee_key = db.Key.from_path('User', int(task.assigneeId if action != "deleted" else assigneeId))
      assignee = db.get(assignee_key)
    if submitter != None or assignee != None:
      
      message = mail.EmailMessage(sender="Tasks Server <suvajit.gupta@eloqua.com>", subject="Task #%s %s by %s" % (taskId, action if name != "New Task" else "created", currentUser.name))
      message.to = ';'; message.cc = ';';
      if assignee != None and assignee.email != None and assignee_key.id_or_name() != currentUserId:
        message.to = "%s" % assignee.email
      if submitter != None and submitter.email != None and submitter_key.id_or_name() != currentUserId:
        message.cc = "%s" % submitter.email
      
      newName = task.name if task != None and task.name != None else "Unspecified"
      oldName = newName if name == "New Task" else name
      message.body = "Name:\t\t%s\n\n" % oldName if action == "deleted" or newName == oldName else "Name:\t\t%s\n=>\t\t%s\n\n" % (oldName, newName)
      
      newType = "'" + task.type.replace('_','') + "'" if task != None and task.type != None else "Unspecified"
      oldType = "'" + ttype.replace('_','') + "'" if ttype != None else "Unspecified"
      if name == "New Task":
        oldType = newType
      message.body += "Type:\t\t%s\n" % oldType if action == "deleted" or newType == oldType else "Type:\t\t%s => %s\n" % (oldType, newType)
        
      newPriority = "'" + task.priority.replace('_','') + "'" if task != None and task.priority != None else "Unspecified"
      oldPriority = "'" + priority.replace('_','') + "'" if priority != None else "Unspecified"
      if name == "New Task":
        oldPriority = newPriority
      message.body += "Priority:\t\t%s\n" % oldPriority if action == "deleted" or newPriority == oldPriority else "Priority:\t\t%s => %s\n" % (oldPriority, newPriority)
        
      newStatus = "'" + task.developmentStatus.replace('_','') + "'" if task != None and task.developmentStatus != None else "Unspecified"
      oldStatus = "'" + status.replace('_','') + "'" if status != None else "Unspecified"
      if name == "New Task":
        oldStatus = newStatus
      message.body += "Status:\t\t%s\n" % oldStatus if action == "deleted" or newStatus == oldStatus else "Status:\t\t%s => %s\n" % (oldStatus, newStatus)
        
      newValidation = "'" + task.validation.replace('_','') + "'" if task != None and task.validation != None else "Unspecified"
      oldValidation = "'" + validation.replace('_','') + "'" if validation != None else "Unspecified"
      if name == "New Task":
        oldValidation = newValidation
      message.body += "Validation:\t%s\n" % oldValidation if action == "deleted" or newValidation == oldValidation else "Validation:\t%s => %s\n" % (oldValidation, newValidation)
      #   
      # if task != None and task.projectId != None:
      #   project_key = db.Key.from_path('Project', int(task.projectId))
      #   project = db.get(project_key)
      #   project_name = project.name if task.projectId != None else "Unallocated"
#       message.body += """
# Submitter:\t'%s'
# Assignee:\t'%s'
#       
# Effort:\t\t'%s'
# Project:\t\t'%s'
#       
# Description:
# '%s'
#       """ % (submitter.name if not submitter == None else "Unassigned",
#        assignee.name if not assignee == None else "Unassigned",
#        task.effort if not task.effort == None else "Unspecified", 
#        project_name,
#        task.description if not task.description == None else "Unspecified")
       
    if message.to == ';' and message.cc != ';':
      message.to = message.cc; message.cc = ';'
    if message.to != ';' or message.cc != ';':
      message.send()

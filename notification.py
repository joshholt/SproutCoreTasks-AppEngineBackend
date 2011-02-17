#!/usr/bin/env python

""" Purpose: To send notifications to task watchers.
    Author: Joshua Holt
    Author: Suvajit Gupta
"""
import time,datetime
#from google.appengine.api import xmpp # importing this lib allows jabber chat messages to be sent.
from google.appengine.api import mail
from google.appengine.ext import db
# Data Model Imports
from models import User, Task, Project

def should_notify(currentUserId, task, wantsNotifications = True):
  """Determines if a notification should be sent"""
  if wantsNotifications == False or task.name == "New Task":
    retVal = False
  elif task.submitterId != None and int(currentUserId) == int(task.submitterId) and task.assigneeId != None and int(currentUserId) == int(task.assigneeId):
    retVal = False
  else:
    retVal = True
  return retVal

def send_notification(url, taskId, currentUserId, action, name, ttype, priority, status, validation, submitterId, assigneeId, effort, projectId, description):
  """sends email notification"""
  # Get information about this task and the assignee and submitter
  task = None;
  if action != "deleted":
    task_key = db.Key.from_path('Task', int(taskId))
    task = db.get(task_key)
  currentUser_key = db.Key.from_path('User', int(currentUserId))
  currentUser = db.get(currentUser_key)
  
  # get all watches for task (like user authentication in main.py)
  watcherIds = []; watcherEmails = []
  q = db.GqlQuery("SELECT * FROM Watch WHERE taskId = %s" % taskId)
  # for each watch, push userId into array
  for watch in q:
    watcherIds.append(watch.userId)
    
  # for each watcher, push email (if they have one) into array
  for watcherId in watcherIds:
    watcher_key = db.Key.from_path('User', int(watcherId))
    watcher = db.get(watcher_key)
    if(watcher != None and watcher.email != None and watcher.email != '' and watcher.email != 'None'):
      watcherEmails.append(watcher.email)
      
  # create list of emails for watchers
  watcherSendList = ''
  if(len(watcherEmails) != 0):
    watcherSendList = '; '.join(watcherEmails)
    
  if action == "deleted" or task != None:
    submitter = None; assignee = None;
    if action == "deleted" or (task != None and task.submitterId != None):
      sid = task.submitterId if action != "deleted" else submitterId
      if sid != 'None':
        submitter_key = db.Key.from_path('User', int(sid))
        submitter = db.get(submitter_key)
    if action == "deleted" or (task != None and task.assigneeId != None):
      aid = task.assigneeId if action != "deleted" else assigneeId
      if aid != 'None':
        assignee_key = db.Key.from_path('User', int(aid))
        assignee = db.get(assignee_key)
    if submitter != None or assignee != None:
      
      message = mail.EmailMessage(sender="Tasks Server <suvajit.gupta@eloqua.com>", subject="Task #%s %s by '%s' at %s" % (taskId, action if name != "New Task" else "created", currentUser.name, url))
      message.to = ';'; message.cc = ';';
      if assignee != None and assignee.email != '' and assignee.email != 'None' and assignee.email != None and assigneeId != currentUserId:
        message.to = "%s" % assignee.email
      if submitter != None and submitter.email != '' and submitter.email != 'None' and submitter.email != None and submitterId != currentUserId:
        message.cc = "%s" % submitter.email
      
      newName = task.name if task != None and task.name != None else "Unspecified"
      oldName = newName if name == "New Task" else name
      message.body = "Name:\t\t%s\n\n" % oldName if action == "deleted" or newName == oldName else "Name:\t\t%s\n=>\t\t%s\n\n" % (oldName, newName)
      
      newType = "'" + task.type.replace('_','') + "'" if task != None and task.type != None else "Unspecified"
      oldType = "'" + ttype.replace('_','') + "'" if ttype != 'None' else "Unspecified"
      if name == "New Task":
        oldType = newType
      message.body += "Type:\t\t%s\n" % oldType if action == "deleted" or newType == oldType else "Type:\t\t%s => %s\n" % (oldType, newType)
        
      newPriority = "'" + task.priority.replace('_','') + "'" if task != None and task.priority != None else "Unspecified"
      oldPriority = "'" + priority.replace('_','') + "'" if priority != 'None' else "Unspecified"
      if name == "New Task":
        oldPriority = newPriority
      message.body += "Priority:\t\t%s\n" % oldPriority if action == "deleted" or newPriority == oldPriority else "Priority:\t\t%s => %s\n" % (oldPriority, newPriority)
        
      newStatus = "'" + task.developmentStatus.replace('_','') + "'" if task != None and task.developmentStatus != None else "Unspecified"
      oldStatus = "'" + status.replace('_','') + "'" if status != 'None' else "Unspecified"
      if name == "New Task":
        oldStatus = newStatus
      message.body += "Status:\t\t%s\n" % oldStatus if action == "deleted" or newStatus == oldStatus else "Status:\t\t%s => %s\n" % (oldStatus, newStatus)
        
      newValidation = "'" + task.validation.replace('_','') + "'" if task != None and task.validation != None else "Unspecified"
      oldValidation = "'" + validation.replace('_','') + "'" if validation != 'None' else "Unspecified"
      if name == "New Task":
        oldValidation = newValidation
      message.body += "Validation:\t%s\n" % oldValidation if action == "deleted" or newValidation == oldValidation else "Validation:\t%s => %s\n" % (oldValidation, newValidation)

      newSubmitter = db.get(db.Key.from_path('User', int(task.submitterId))) if task != None and task.submitterId != None else None
      newSubmitterName = "'" + newSubmitter.name + "'" if newSubmitter != None else "Unassigned"
      if submitterId != 'None' and submitterId != '':
        oldSubmitter = db.get(db.Key.from_path('User', int(submitterId)))
      else:
        oldSubmitter = None
      oldSubmitterName = "'" + oldSubmitter.name + "'" if oldSubmitter != None else "Unassigned"
      if name == "New Task":
        oldSubmitterName = newSubmitterName
      message.body += "\nSubmitter:\t%s\n" % oldSubmitterName if action == "deleted" or newSubmitterName == oldSubmitterName else "\nSubmitter:\t%s => %s\n" % (oldSubmitterName, newSubmitterName)

      newAssignee = db.get(db.Key.from_path('User', int(task.assigneeId))) if task != None and task.assigneeId != None else None
      newAssigneeName = "'" + newAssignee.name + "'" if newAssignee != None else "Unassigned"
      if assigneeId != 'None' and assigneeId != '':
        oldAssignee = db.get(db.Key.from_path('User', int(assigneeId)))
      else:
        oldAssignee = None
      oldAssigneeName = "'" + oldAssignee.name + "'" if oldAssignee != None else "Unassigned"
      if name == "New Task":
        oldAssigneeName = newAssigneeName
      message.body += "Assignee:\t%s\n" % oldAssigneeName if action == "deleted" or newAssigneeName == oldAssigneeName else "Assignee:\t%s => %s\n" % (oldAssigneeName, newAssigneeName)

      newEffort = "'" + task.effort + "'" if task != None and task.effort != None else "Unspecified"
      oldEffort = "'" + effort + "'" if effort != 'None' else "Unspecified"
      if name == "New Task":
        oldEffort = newEffort
      message.body += "\nEffort:\t\t%s\n" % oldEffort if action == "deleted" or newEffort == oldEffort else "\nEffort:\t\t%s => %s\n" % (oldEffort, newEffort)

      newProject = db.get(db.Key.from_path('Project', int(task.projectId))) if task != None and task.projectId != None else None
      newProjectName = "'" + newProject.name + "'" if newProject != None else "Unallocated"
      if projectId != 'None' and projectId != '':
        oldProject = db.get(db.Key.from_path('Project', int(projectId)))
      else:
        oldProject = None
      oldProjectName = "'" + oldProject.name + "'" if oldProject != None else "Unallocated"
      if name == "New Task":
        oldProjectName = newProjectName
      message.body += "Project:\t\t%s\n" % oldProjectName if action == "deleted" or newProjectName == oldProjectName else "Project:\t\t%s => %s\n" % (oldProjectName, newProjectName)

      newDescription = task.description if task != None and task.description != None and task.description != '' else "Unspecified"
      oldDescription = description if description != 'None'  and description != '' else "Unspecified"
      if name == "New Task":
        oldDescription = newDescription
      message.body += "\nDescription:\n%s\n" % oldDescription if action == "deleted" or newDescription == oldDescription else "\nDescription:\n%s\n\n=>\n\n%s\n" % (oldDescription, newDescription)

    if watcherSendList != '':
      message.cc += watcherSendList if message.cc == ';' else "; %s" % watcherSendList
    if message.to == ';' and message.cc != ';':
      message.to = message.cc; message.cc = ';'
    if message.to != ';' or message.cc != ';':
      message.send()

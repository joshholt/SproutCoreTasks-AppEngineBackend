#!/usr/bin/env python

""" Prupose: To Send Notifications based on certain task conditions.
    Author: Joshua Holt
    Date: 12-09-2009
    Last Modified: 01-24-2010
"""
import time,datetime
from google.appengine.api import xmpp
from google.appengine.api import mail
from google.appengine.ext import db
# Data Model Imports
import models
from models import User
from models import Task
from models import Project

def send_test_chat():
  """sends a test Instant Message"""
  user_address = "jholt@localhost"
  message_sent = False
  
  if xmpp.get_presence(user_address):
    message = """
    Dear Joshua:
    
    This is an example email that will be sent from the Tasks app when
    a notification needs to be sent. These notifications may be 
    bugs/bug-fixes/etc...
    
    Please let us know if you have any questions.
  
    The Tasks Team
    """
    status_code = xmpp.send_message(user_address,message)
    message_sent = (status_code != xmpp.NO_ERROR)
    
  if not message_sent:
    return "Unable to send message"
  else:
    return "Sent Message"

def should_notify(task,action):
  """Determines if a notification should be sent"""
  retVal = {
  "createTask": lambda task: True if task.priority != None and task.developmentStatus != None and task.type != None else False,
  "updateTask": lambda task: True if task.validation != None and task.validation == "_Risky" else False
  }[action](task)
  return retVal

def send_notification(arg):
  """sends a test email"""
  # Get information about this task and the assignee and submitter
  task_key = db.Key.from_path('Task', int(arg))
  task = db.get(task_key)
  if not task == None:
    submitter_key = db.Key.from_path('User', int(task.submitterId))
    submitter = db.get(submitter_key)
    assignee_key = db.Key.from_path('User', int(task.assigneeId))
    assignee = db.get(assignee_key)
    if not task.projectId == None:
      project_key = db.Key.from_path('Project', int(task.projectId))
      project = db.get(project_key)
    if not submitter == None and not assignee == None:
      project_name = project.name if not task.projectId == None else "Unallocated"
      message = mail.EmailMessage(sender="Tasks <suvajit.gupta@eloqua.com>", subject="Notification for Task #%s" % task.key().id_or_name())
      # if not assignee.email == None:
      #   message.to = "%s" % assignee.email
      # else:
      #   message.to = "holt.josh@gmail.com"
      # if not submitter.email == None:
      #   message.cc = "%s" % submitter.email
      # else:
      #   message.cc = "holt.josh@gmail.com"
      message.to = "josh.holt@eloqua.com"
      message.body = """Name:\t\t%s

Type:\t\t%s
Priority:\t\t%s
Status:\t\t%s
Validation:\t%s

Submitter:\t%s (%s)
Assignee:\t%s (%s)

Effort:\t\t%s
Project:\t\t%s

Created:\t\t%s
Updated:\t%s

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
       datetime.datetime.fromtimestamp(task.createdAt//1000),
       datetime.datetime.fromtimestamp(task.updatedAt//1000),
       task.description if not task.description == None else "")
  message.send()

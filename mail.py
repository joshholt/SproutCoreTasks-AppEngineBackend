#!/usr/bin/env python

""" Prupose: To Send Email Notifications based on certain task conditions.
    Author: Joshua Holt
    Date: 12-09-2009
    Last Modified: 12-09-2009
"""

# App Engine Imports
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db
from django.utils import simplejson
from google.appengine.api import mail

# Data Model Imports
import models
from models import User
from models import Task
from models import Project

# Helper Imports
import helpers

def send_test_email():
  """sends a test email"""
  message = mail.EmailMessage(sender="Tasks Notifications <holt.josh@gmail.com>",
                              subject="Tasks Notifications: Example Email")
  message.to = "Joshua Holt <holt.josh@gmail.com>"
  message.body = """
  Dear Joshua:
  
  This is an example email that will be sent from the Tasks app when
  a notification needs to be sent. These notifications may be 
  bugs/bug-fixes/etc...
  
  Please let us know if you have any questions.
  
  The Tasks Team
  """
  
  message.send()

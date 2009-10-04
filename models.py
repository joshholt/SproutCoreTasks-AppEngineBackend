""" This File holds the model definitions used in this app.
  Author: Joshua Holt 
  Date: 09-30-2009
  Last Modified: 10-02-2009
"""

from google.appengine.ext import db

class User(db.Model):
  """ This is the User Model"""
  name = db.StringProperty(required=True, default="(No Name)")
  loginName = db.StringProperty(required=True, default="(NA)")
  role = db.StringProperty(required=True, default="_Other")
  #preferences = db.StringProperty() -- NOT Used yet.
  emailAddress = db.EmailProperty()
  password = db.StringProperty()
  authToken = db.StringProperty()


class Project(db.Model):
  """ This is the Project Model"""
  name = db.StringProperty(required=True, default="(No Name Project)")
  timeLeft = db.StringProperty()
  tasks = db.ListProperty(int)


class Task(db.Model):
  """ This is the Task Model"""
  name = db.StringProperty(required=True, default="(No Name Task)")
  priority = db.StringProperty()
  effort = db.StringProperty()
  submitter = db.IntegerProperty()
  assignee = db.IntegerProperty()
  type = db.StringProperty()
  status = db.StringProperty()
  validation = db.StringProperty()
  description = db.TextProperty()

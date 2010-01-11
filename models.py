""" This File holds the model definitions used in this app.
  Author: Joshua Holt 
  Date: 09-30-2009
  Last Modified: 12-08-2009
"""

from google.appengine.ext import db

class User(db.Model):
  """ This is the User Model"""
  name = db.StringProperty(required=True, default="(No Name)")
  loginName = db.StringProperty(required=True, default="(NA)")
  role = db.StringProperty(required=True, default="_Guest")
  #preferences = db.StringProperty() -- NOT Used yet.
  email = db.EmailProperty()
  password = db.StringProperty()
  authToken = db.StringProperty()
  createdAt = db.IntegerProperty()
  updatedAt = db.IntegerProperty()


class Project(db.Model):
  """ This is the Project Model"""
  name = db.StringProperty(required=True, default="(No Name Project)")
  description = db.TextProperty()
  timeLeft = db.StringProperty()
  createdAt = db.IntegerProperty()
  updatedAt = db.IntegerProperty()


class Task(db.Model):
  """ This is the Task Model"""
  name = db.StringProperty(required=True, default="(No Name Task)")
  description = db.TextProperty()
  projectId = db.IntegerProperty()
  priority = db.StringProperty(default="_Medium")
  effort = db.StringProperty()
  submitterId = db.StringProperty() # These keep changing
  assigneeId = db.StringProperty()  # These keep changing
  type = db.StringProperty(default="_Other")
  developmentStatus = db.StringProperty(default="_Planned")
  validation = db.StringProperty(default="_Untested")
  createdAt = db.IntegerProperty()
  updatedAt = db.IntegerProperty()

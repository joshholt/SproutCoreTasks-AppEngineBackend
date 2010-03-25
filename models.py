""" This File holds the model definitions used in this app.
  Author: Joshua Holt 
  Date: 09-30-2009
  Last Modified: 12-08-2009
"""

from google.appengine.ext import db

class User(db.Model):
  """ This is the User Model"""
  name = db.StringProperty(required=True, default="_FirstLast")
  loginName = db.StringProperty(required=True, default="_Initials")
  role = db.StringProperty(required=True, default="_Developer")
  #preferences = db.StringProperty() -- NOT Used yet.
  email = db.StringProperty(required=False)
  password = db.StringProperty(required=False)
  authToken = db.StringProperty(required=False)
  createdAt = db.IntegerProperty(required=False)
  updatedAt = db.IntegerProperty(required=False)


class Project(db.Model):
  """ This is the Project Model"""
  name = db.StringProperty(required=True, default="_NewProject")
  description = db.TextProperty(required=False)
  timeLeft = db.StringProperty(required=False)
  createdAt = db.IntegerProperty(required=False)
  updatedAt = db.IntegerProperty(required=False)


class Task(db.Model):
  """ This is the Task Model"""
  name = db.StringProperty(required=True, default="_NewTask")
  description = db.TextProperty(required=False)
  projectId = db.IntegerProperty(required=False)
  priority = db.StringProperty(default="_Medium")
  effort = db.StringProperty(required=False)
  submitterId = db.IntegerProperty() # These keep changing
  assigneeId = db.IntegerProperty()  # These keep changing
  type = db.StringProperty(default="_Other")
  developmentStatus = db.StringProperty(default="_Planned")
  validation = db.StringProperty(default="_Untested")
  createdAt = db.IntegerProperty(required=False)
  updatedAt = db.IntegerProperty(required=False)

class Watch(db.Model):
  """ This is the Watch Model"""
  taskId = db.IntegerProperty(required=False)
  userId = db.IntegerProperty(required=False)
  createdAt = db.IntegerProperty(required=False)
  updatedAt = db.IntegerProperty(required=False)

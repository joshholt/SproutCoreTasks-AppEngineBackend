#!/usr/bin/env python

""" Prupose: To Send Notifications based on certain task conditions.
    Author: Joshua Holt
    Date: 12-09-2009
    Last Modified: 12-10-2009
"""

from google.appengine.api import xmpp
from google.appengine.api import mail

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


def send_test_email():
  """sends a test email"""
  message = mail.EmailMessage(sender="tasks@eloqua.com",
                              subject="Tasks Notifications: Example Email")
  message.to = "josh.holt@eloqua.com"
  message.body = """
  This is an example email that will be sent from the Tasks app when
  a notification needs to be sent. These notifications may be 
  bugs/bug-fixes/etc...
  
  Please let us know if you have any questions.
  
  The Tasks Team
  """
  message.send()

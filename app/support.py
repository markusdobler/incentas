from flask import flash
import hashlib
from random import choice
from datetime import datetime
from threading import Thread
from flask.ext.mail import Mail, Message
import os

from flask.ext.login import LoginManager
login_manager = LoginManager()

@login_manager.user_loader
def load_user(id):
    import models
    return models.User.query.filter_by(username=id).scalar()

def hash(text):
    text = text.encode('utf8')
    return hashlib.sha1(text).hexdigest()[:8]

def flash_errors(form):
    for field, messages in form.errors.items():
        fieldname = form[field].label.text
        try:
            flash("%s: %s" % (fieldname, " & ".join(messages)), "error")
        except:
            flash("err: %s %s" % (fieldname, messages), "error")


def pretty_datetime(datetime_object):
    return datetime_object.strftime("%Y-%m-%d, %H:%M:%S")

def secure_datetime(datetime_object=None):
    if datetime_object is None:
        datetime_object = datetime.now()
    return datetime_object.strftime("%Y-%m-%d_%H.%M.%S")

def totalseconds(timedelta_object):
    return 24*60*60*timedelta_object.days + timedelta_object.seconds

def pretty_timedelta(timedelta_object):
    total_seconds = totalseconds(timedelta_object)
    if total_seconds <= 1:
        return "1 second"
    if total_seconds < 60:
        return "%i seconds" % total_seconds
    minutes = total_seconds // 60
    if minutes == 1:
        return "about a minute"
    if minutes < 60:
        return "about %i minutes" % minutes
    hours = minutes // 60
    if hours == 1:
        return "about an hour"
    if hours < 50:
        return "about %i hours" % hours
    days = hours / 24
    return "about %i days" % days

def none2now(now=None):
    return datetime.now() if now is None else now

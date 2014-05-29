from app import login_manager, models, flash, app
import hashlib
from random import choice
from datetime import datetime
from threading import Thread
from flask.ext.mail import Mail, Message
from twitter import Twitter, OAuth, oauth_dance, read_token_file
import os

@login_manager.user_loader
def load_user(userid):
    try:
        userid = int(userid)
        return models.User.query.get(userid)
    except:
        return None

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


mail = Mail(app)
def send_mail(subject, body, recipients=None, sender="admin@d0b13b8d6e3bc7f6.de"):
    if recipients is None:
        recipients = app.config['ADMIN_MAIL_RECIPIENTS']
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = body
    def send_async_email(msg):
        try:
            mail.send(msg)
        except:
            app.logger.error("failed to send message")
            app.logger.error(msg)
    thr = Thread(target = send_async_email, args = [msg])
    thr.start()


def tweet(status):
    try:
        CONSUMER_KEY, CONSUMER_SECRET, PASSWD, MY_TWITTER_CREDS = app.config['TWITTER_AUTH']
        oauth_token, oauth_secret = read_token_file(MY_TWITTER_CREDS)
        twitter = Twitter(auth=OAuth(
            oauth_token, oauth_secret, CONSUMER_KEY, CONSUMER_SECRET))
        twitter.statuses.update(status=status)
    except:
        app.logger.error("Failed to tweet.  Maybe you just have to call support.setup_twitter_credentials.  Maybe it's more.")

def tweet_async(status):
    thr = Thread(target = tweet, args = [status])
    thr.start()

def setup_twitter_credentials():
    CONSUMER_KEY, CONSUMER_SECRET, PASSWD, MY_TWITTER_CREDS = app.config['TWITTER_AUTH']
    oauth_dance("Deb 948f09771e203", CONSUMER_KEY, CONSUMER_SECRET, MY_TWITTER_CREDS)

def pretty_datetime(datetime_object):
    return datetime_object.strftime("%Y-%m-%d, %H:%M:%S")

def secure_datetime(datetime_object=None):
    if datetime_object is None:
        datetime_object = datetime.now()
    return datetime_object.strftime("%Y-%m-%d_%H.%M.%S")

def pretty_timedelta(timedelta_object):
    total_seconds = 24*60*60*timedelta_object.days + timedelta_object.seconds
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

    return d

@app.context_processor
def utility_processor():
    images = ('fract', 'compass', 'horse', 'hourglass', 'map', 'treasurechest')
    orientations = ('left', 'right')
    def random_image():
        return choice(orientations), choice(images)
    return dict(random_image=random_image)

@app.context_processor
def utility_processor():
    congrats = (
        'Congratulations!',
        'Well done!',
        'One step closer ...',
        'Yippie kay yay!',
        'And onwards ...',
        'Well done, keep on!',
        'Correct',
        'Yippie yippie yeah, yippie yeah!',
    )
    def random_congrats():
        return choice(congrats)
    return dict(random_congrats=random_congrats)

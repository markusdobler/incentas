#------------------------------------------------------------------------------#
# Imports
#------------------------------------------------------------------------------#

from flask import * # do not use '*'; actually input the dependencies
from flask.ext.sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask.ext.login import LoginManager

#------------------------------------------------------------------------------#
# App Config
#------------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = "login"
from app import support
login_manager.init_app(app)
from app import models, routes, support

# Automatically tear down SQLAlchemy
'''
@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()
'''


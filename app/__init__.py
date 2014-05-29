#------------------------------------------------------------------------------#
# Imports
#------------------------------------------------------------------------------#
from flask import Flask
import logging
from logging import Formatter, FileHandler


def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    from support import login_manager
    login_manager.login_view = ".login"
    login_manager.init_app(app)

    from models import db, create_tables, User
    db.init_app(app)
    create_tables(app)

    from routes import blueprints
    for bp in blueprints:
        app.register_blueprint(bp)

    from random import random
    with app.app_context():
        User('name%f'%random(), 'pwd')
        print [u.name for u in User.query.all()]

    return app

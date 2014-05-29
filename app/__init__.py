#------------------------------------------------------------------------------#
# Imports
#------------------------------------------------------------------------------#
from flask import Flask
import logging
from logging import Formatter, FileHandler


def create_app(config_object_name='config'):
    app = Flask(__name__)
    app.config.from_object(config_object_name)

    from support import login_manager
    login_manager.login_view = ".login"
    login_manager.init_app(app)

    from models import db, create_tables, User
    db.init_app(app)
    create_tables(app)

    from routes import blueprints
    for bp in blueprints:
        app.register_blueprint(bp)

    return app

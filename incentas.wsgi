import sys
import os

sys.path.insert(0, '/home/sfoo/.virtualenvs/incentas/lib/python2.6/site-packages/')
sys.path.insert(0, '/home/sfoo/src/incentas')
sys.path.insert(0, '/home/sfoo/src/incentas/app')

from app import app as application

if not application.debug:
    import logging
    basedir = os.path.abspath(os.path.dirname(__file__))
    file_handler = logging.FileHandler(os.path.join(basedir,'error.log'))
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'))
    application.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    application.logger.addHandler(file_handler)
    application.logger.info('startup')

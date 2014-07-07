from flask.ext.script import Manager, prompt, prompt_choices, prompt_bool
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.sqlalchemy import SQLAlchemy

from app import create_app
from app import models

app = create_app()
manager = Manager(app)

@manager.command
def hello():
    print "hello"

migrate = Migrate(app, models.db)
manager.add_command('db', MigrateCommand)

@MigrateCommand.command
def create_tables():
    models.db.create_all()

@manager.command
def list_users():
    for u in models.User.query.all():
        print "% 15s -- %s" % (u.username, u.fullname)

@manager.option('-u', '--user', dest="username")
def list_challenges(username=None):
    query = models.User.query
    if username:
        query = query.filter_by(username=username)
    for user in query.all():
        print "%s (%s)" % (user.username, user.fullname)
        for ch in user.challenges:
            print " * %s: %.1f/%.1f (%4.1fP)" % (ch.title, ch.current_value(),
                                     ch.target_value, ch.calc_points())

@manager.option('-D', '--description', help='Description', default=None)
@manager.option('-T', '--title', help='Title', default=None)
@manager.option('-x', '--unit', help='Unit of target value', required=True)
@manager.option('-v', '--target-value', help='Target value', type=float, required=True)
@manager.option('-f', '--points-fail', help='Points if failed', type=int, default=-5)
@manager.option('-s', '--points-success', help='Points if successful', type=int, default=10)
@manager.option('-d', '--duration', help='Duration in days', type=int, required=True)
@manager.option('-u', '--user', help='User', required=True)
def new_challenge(user, duration, points_success, points_fail,
                  target_value, unit, title, description):
    user = models.User.query.filter_by(username=user).one()

    if title is None:
        title = prompt("Title")
    if description is None:
        description = prompt("Description")
        while True:
            more = prompt("(cont'd - stop with '.')")
            if more == ".": break
            print repr(more)
            description += "<br>\\r" + more

    print "Challenge%s"%((user, duration, title, description, points_success, points_fail, target_value, unit),)
    if prompt_bool("Create this challenge?"):
        models.Challenge(user, duration, title, description, points_success, points_fail, target_value, unit)


if __name__ == "__main__":
    manager.run()


from flask.ext.script import prompt, prompt_choices, prompt_bool
from flask.ext.script import Manager, Command, Option
from flask.ext.migrate import Migrate, MigrateCommand

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

challenge_manager = Manager(lambda app, **kw: None)
manager.add_command('challenge', challenge_manager)

@challenge_manager.option('-u', '--user', dest="username")
def list(username=None):
    query = models.User.query
    if username:
        query = query.filter_by(username=username)
    for user in query.all():
        print "%s (%s)" % (user.username, user.fullname)
        for ch in user.challenges:
            try:
                print " * %s: %.1f/%.1f (%4.1fP)" % (ch.title, ch.current_value(),
                                         ch.target_value, ch.calc_points())
            except:
                print " * %s: (%4.1fP)" % (ch.title, ch.calc_points())


class NewChallengeCommand(Command):
    default_options = (
        Option('-D', '--description', help='Description', default=None),
        Option('-T', '--title', help='Title', default=None),
        Option('-f', '--points-fail', help='Points if failed', type=int, default=-5),
        Option('-s', '--points-success', help='Points if successful', type=int, default=10),
        Option('-d', '--duration', help='Duration in days', type=int, required=True),
        Option('-u', '--user', help='User', required=True),
    )

    def __init__(self, challenge_factory, additional_options):
        self.challenge_factory = challenge_factory
        self.additional_options = additional_options

    def get_options(self):
        return self.default_options + self.additional_options

    def run(self, user, title, description, **kw):
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

        print "%s(user=<%s>, title=%r, description=%r, %s)" % (self.challenge_factory.__name__,
                                                               user.username, title, description,
                                                               ", ".join("%s=%r"% kv for kv
                                                                         in kw.items()))
        if prompt_bool("Create this challenge?"):
            self.challenge_factory(user=user, title=title, description=description, **kw)

challenge_manager.add_command("new_target_value", NewChallengeCommand(
    models.TargetValueChallenge,
    (
        Option('-x', '--unit', help='Unit of target value', required=True),
        Option('-v', '--target-value', help='Target value', type=float, required=True),
    )
))

challenge_manager.add_command("new_daily_evaluation", NewChallengeCommand(
    models.DailyEvaluationChallenge,
    (
        Option('-g', '--label-good', help='Label for good evaluation', required=True),
        Option('-m', '--label-marginal', help='Label for marginal evaluation', required=True),
        Option('-b', '--label-bad', help='Label for bad evaluation', required=True),
    )
))


if __name__ == "__main__":
    manager.run()


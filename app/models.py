from flask import current_app, flash
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import itertools
import math
from support import none2now, totalseconds, daterange

from forms import FormValidationError

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True)
    fullname = db.Column(db.String(100))
    height = db.Column(db.Numeric)
    pw_hash = db.Column(db.String(160))
    _measurement_types_as_string = db.Column(db.Text)
    _assessment_types_as_string = db.Column(db.Text)

    # for Flask-Login
    is_authenticated = is_active = lambda self: True
    is_anonymous = lambda self: False
    get_id = lambda self: self.username

    def __init__(self, username, password, fullname=None):
        self.username = username
        self.fullname = fullname if fullname else username
        self.set_password(password)
        self.measurement_types = current_app.config['DEFAULT_MEASUREMENT_TYPES']
        self.assessment_types = current_app.config['DEFAULT_ASSESSMENT_TYPES']
        db.session.add(self)
        db.session.commit()

    def set_password(self, password):
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

    def calc_challenge_points(self, now=None):
        return sum(ch.calc_points(now) for ch in self.challenges)

    @property
    def measurement_types(self):
        try:
            self._measurement_types_cache
        except AttributeError:
            self._measurement_types_cache = self._measurement_types_as_string.split(':')
        return self._measurement_types_cache

    @measurement_types.setter
    def measurement_types(self, new_value):
        self._measurement_types_cache = new_value
        self._measurement_types_as_string = ":".join(new_value)
        db.session.commit()


    def measurements_grouped_by_type(self):
        measurements = self.measurements.order_by(Measurement.type, Measurement.timestamp).all()
        m_dict = dict((k, list(g)) for k,g in itertools.groupby(measurements, lambda x: x.type))
        return [(k, m_dict.get(k, [])) for k in self.measurement_types]

    @property
    def assessment_types(self):
        try:
            self._assessment_types_cache
        except AttributeError:
            self._assessment_types_cache = self._assessment_types_as_string.split(':')
        return self._assessment_types_cache

    @assessment_types.setter
    def assessment_types(self, new_value):
        self._assessment_types_cache = new_value
        self._assessment_types_as_string = ":".join(new_value)
        db.session.commit()


class Measurement(db.Model):
    __tablename__ = 'Measurements'
    id = db.Column(db.Integer, primary_key = True)
    type = db.Column(db.String(20))
    value = db.Column(db.Numeric)
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    user = db.relationship("User",
                           backref=db.backref("measurements", lazy="dynamic"))

    def __init__(self, user, type, value, timestamp=None):
        self.user = user
        self.type = type
        self.value = value
        self.timestamp = none2now(timestamp)
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<%s: %5.3f>" % (self.type, self.value)

class Assessment(db.Model):
    __tablename__ = 'Assessments'
    id = db.Column(db.Integer, primary_key = True)
    type = db.Column(db.String(20))
    value_int = db.Column(db.Integer)
    startdate = db.Column(db.Date)
    _justoneday = db.Column(db.Boolean)

    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    user = db.relationship("User",
                           backref=db.backref("assessments", lazy="dynamic"))

    __mapper_args__ = {
        'polymorphic_on': '_justoneday'
    }

    """_int2value = current_app.config['ASSESSMENT_LEVELS']
    _value2int = dict((v,k) for (k,v) in
                      enumerate(current_app.config['ASSESSMENT_LEVELS']))
    """

    @property
    def value(self):
        return self._int2value[self.value_int]
    @value.setter
    def value(self, new_value):
        self.value_int = self._value2int[new_value]

    def __init__(self, user, type, value, timestamp=None,
                 just_one_day=False):
        self.user = user
        self.type = type
        self.value = value
        self.set_period(date.today() if timestamp is None else timestamp)
        db.session.add(self)
        db.session.commit()

    def set_period(self, timestamp):
        raise NotImplementedError()


    def __repr__(self):
        return "<%s: %s>" % (self.type, self.value)

class WeeklyAssessment(Assessment):
    __mapper_args__ = {
        'polymorphic_identity': False,
    }
    def set_period(self, timestamp):
            self._startdate = timestamp - timedelta(days=timestamp.weekday())
            # self._enddate = self._startdate + timedelta(days=7)


class DailyAssessment(Assessment):
    __mapper_args__ = {
        'polymorphic_identity': True,
    }
    def set_period(self, timestamp):
            self._startdate = timestamp
            # self._enddate = timestamp + timedelta(days=1)

class Challenge(db.Model):
    __tablename__ = 'Challenges'
    id = db.Column(db.Integer, primary_key = True)
    type = db.Column(db.String(10))
    __mapper_args__ = {
            'polymorphic_identity':'base',
            'polymorphic_on':type
        }
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    user = db.relationship("User",
                           backref=db.backref("challenges", lazy="dynamic"))
    title = db.Column(db.String(50))
    description = db.Column(db.Text)
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    points_success = db.Column(db.Numeric)
    points_fail = db.Column(db.Numeric)

    def __init__(self, user, duration, title, description,
                 points_success=10, points_fail=-5,
                 now=None, **kwargs):
        self.user = user
        now = none2now(now)
        self.start = now
        try:
            self.end = now + duration
        except:
            self.end = now + timedelta(days=duration)
        self.title = title
        self.description = description
        self.points_success = points_success
        self.points_fail = points_fail
        for k, v in kwargs.items():
            self.__setattr__(k, v)
        db.session.add(self)
        db.session.commit()

    def time_ratio(self, now=None):
        seconds_all = totalseconds(self.end-self.start)
        seconds_done = totalseconds(none2now(now)-self.start)
        return 1. * seconds_done / seconds_all

    def is_overdue(self, now=None):
        return none2now(now) > self.end

    def duration(self):
        delta = (self.end - self.start)
        return delta.days

    def days_left(self, now=None):
        now = min(self.end, none2now(now))
        delta = (self.end - none2now(now))
        return delta.days



class DailyEvaluationChallenge(Challenge):
    __tablename__ = 'DailyEvaluationChallenges'
    id = db.Column(db.Integer, db.ForeignKey('Challenges.id'), primary_key = True)
    __mapper_args__ = {'polymorphic_identity':'daily_evaluation'}
    label_good = db.Column(db.String(30))
    label_marginal = db.Column(db.String(30))
    label_bad = db.Column(db.String(30))

    def __init__(self, user, duration, title, description,
                 points_success=10, points_fail=-5,
                 now=None, **kwargs):
        super(DailyEvaluationChallenge, self).__init__(user, duration, title, description,
                 points_success, points_fail, now, **kwargs)
        for timestamp in daterange(self.start, self.end):
            DailyEvaluationChallengeEvaluation(self, timestamp)

    def is_success(self):
        return False

    def is_fail(self, now=None):
        return False

    def bootstrap_context(self, now=None):
        return "info"

    def calc_points(self, now=None):
        return 0

    def update_from_form_data(self, data):
        for data_ev in data['evaluations']:
            db_ev = self.evaluations.filter_by(timestamp=data_ev['timestamp']).one()
            db_ev.evaluation = data_ev['evaluation']
        db.session.commit()

class TargetValueChallenge(Challenge):
    __tablename__ = 'TargetValueChallenges'
    id = db.Column(db.Integer, db.ForeignKey('Challenges.id'), primary_key = True)
    __mapper_args__ = {'polymorphic_identity':'target_value'}
    target_value = db.Column(db.Numeric)
    unit = db.Column(db.String(20))


    def value_ratio(self):
        return self.current_value() / self.target_value

    def is_success(self):
        return self.current_value() >= self.target_value

    def is_fail(self, now=None):
        if self.is_success():
            return False
        return self.is_overdue()

    def bootstrap_context(self, now=None):
        if self.is_success(): return "success"
        if self.is_fail(now): return "danger"
        value_left = 1 - self.value_ratio()
        time_left = 1 - self.time_ratio()
        if value_left > 1.5*time_left: return "warning"
        return "info"

    def calc_points(self, now=None):
        ratio = self.current_value() / self.target_value
        if ratio >= 1:
            return self._overachievement_ratio_to_points(ratio)
        if none2now(now) < self.end:
            return 0
        return self.points_fail

    def _overachievement_ratio_to_points(self, ratio):
        return self.points_success * math.sqrt(ratio)

    def current_value(self):
        return sum(cp.value for cp in self.progress.all())

    def add_progress(self, value, timestamp=None, note=''):
        TargetValueChallengeProgress(self, value, timestamp=timestamp, note=note)

    def update_from_form_data(self, data):
        updated_progress_dict = dict((int(e['id']), e) for e in data['existing_progress'])
        print updated_progress_dict
        for p in self.progress:
            update = updated_progress_dict[p.id]
            p.value = update['value']
            p.timestamp = update['timestamp']
            p.note = update['note']
        new_progress = data['add_progress']
        db.session.commit()

        if new_progress['value']:
            self.add_progress(new_progress['value'], new_progress['timestamp'],
                              new_progress['note'])
        elif new_progress['note']:
            raise FormValidationError(
                'If you want to store a new progress update, you have to submit a value')

class TargetValueChallengeProgress(db.Model):
    __tablename__ = 'TargetValueChallengeProgresses'
    id = db.Column(db.Integer, primary_key = True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('TargetValueChallenges.id'))
    challenge = db.relationship("TargetValueChallenge",
                                backref=db.backref("progress", lazy="dynamic"))
    value = db.Column(db.Numeric)
    timestamp = db.Column(db.Date)
    note = db.Column(db.Text(500))

    def __init__(self, challenge, value, timestamp=None, note=''):
        self.challenge = challenge
        self.value = value
        self.timestamp = none2now(timestamp)
        self.note = note
        db.session.add(self)
        db.session.commit()

class DailyEvaluationChallengeEvaluation(db.Model):
    __tablename__ = 'DailyEvaluationChallengeEvaluations'
    id = db.Column(db.Integer, primary_key = True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('DailyEvaluationChallenges.id'))
    challenge = db.relationship("DailyEvaluationChallenge",
                                backref=db.backref("evaluations", lazy="dynamic"))
    evaluation = db.Column(db.String)
    timestamp = db.Column(db.Date)
    def __init__(self, challenge, timestamp, evaluation=""):
        self.challenge = challenge
        self.evaluation = evaluation
        self.timestamp = timestamp
        db.session.add(self)
        db.session.commit()


def create_tables(app=None):
    if app is None:
        app = current_app
    with app.app_context():
        db.create_all()

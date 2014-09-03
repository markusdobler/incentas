from flask import flash
import models
from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, IntegerField, RadioField, DateTimeField, DateField
from wtforms import FileField, HiddenField, TextAreaField, FieldList, FormField, DecimalField
from wtforms.validators import Required, Length, NumberRange, Optional, EqualTo

from support import none2today, daterange, csv2array, array2csv

class FormValidationError(Exception): pass

PASSWORD_LENGTH = Length(min=6, max=40)

class RegisterForm(Form):
    username        = TextField('Username', validators = [Required(), Length(min=3, max=25)])
    fullname        = TextField('Full name (optional)', validators = [Length(max=100)])
    password    = PasswordField('Password', validators = [Required(), PASSWORD_LENGTH])

class LoginForm(Form):
    name        = TextField('Username', [Required()])
    passwd      = PasswordField('Password', [Required()])

class ChallengeProgressForm(Form):
    def single_challenge_progress_subform(value_required=True):
        validators_for_value = [NumberRange(min=0)]
        if not value_required:
            validators_for_value = [Optional()] + validators_for_value

        class SingleChallengeProgressSubform(Form):
            id = HiddenField('ID')
            challenge_id = HiddenField('ChallengeID')
            timestamp = DateField('Timestamp')
            value = DecimalField('Value', validators_for_value)
            note = TextField('Note', [Length(max=500)])

        return SingleChallengeProgressSubform

    existing_progress = FieldList(FormField(single_challenge_progress_subform()))
    add_progress = FormField(single_challenge_progress_subform(value_required=False))

    def read_existing_progress(self, challenge):
        for p in challenge.progress:
            self.existing_progress.append_entry(p)

    def load_from_challenge(self, ch, today=None):
        self.read_existing_progress(ch)
        self.add_progress.timestamp.data = none2today(today)

    def init_from_challenge(self, challenge):
        pass


class DailyEvaluationChallengeForm(Form):
    class Evaluation(Form):
        timestamp = HiddenField('Timestamp')
        evaluation = RadioField('Evaluation', [Optional()])

    evaluations = FieldList(FormField(Evaluation))

    def init_from_challenge(self, ch):
        for ev in self.evaluations:
            self._set_choices(ev, ch)

    def _set_choices(self, ev, ch):
        ev.evaluation.choices = (
            ('good', ch.label_good),
            ('marginal', ch.label_marginal),
            ('bad', ch.label_bad)
        )

    def load_from_challenge(self, ch, today=None):
        for ev in ch.evaluations:
            self.evaluations.append_entry(dict(timestamp=ev.timestamp, evaluation=ev.evaluation))
        for ev in self.evaluations:
            self._set_choices(ev, ch)

challenge_forms = {
    'target_value': ChallengeProgressForm,
    'daily_evaluation': DailyEvaluationChallengeForm,
}


class SettingsForm(Form):
    fullname = TextField('Name')
    height = DecimalField('Height (m)')
    password = PasswordField('Password', [Optional(), Length(min=6, max=40),
                                          EqualTo('confirm', 'Passwords must match')])
    confirm = PasswordField('Confirm Password')
    measurement_types = TextField('Measurement Types')
    assessment_types = TextField('Assessment Types')

    def init_from_user(self, user):
        self.fullname.data = user.fullname
        self.height.data = user.height
        self.measurement_types.data = user._measurement_types_as_string
        self.assessment_types.data = user._assessment_types_as_string

    def update_user_settings(self, user):
        if self.password.data:
            user.set_password(self.password.data)
            flash('Password updated', 'success')
        user._measurement_types_as_string = self.measurement_types.data
        user._assessment_types_as_string = self.assessment_types.data
        user.fullname = self.fullname.data
        user.height = self.height.data
        models.db.session.commit()

class MeasurementForm(Form):
    type = HiddenField('Type')
    value = DecimalField('Value', [Optional(), NumberRange()])

class AddMeasurementsForm(Form):
    new_measurements = FieldList(FormField(MeasurementForm))

    def init_from_user(self, user):
        for t in user.measurement_types:
            self.new_measurements.append_entry(dict(type=t))

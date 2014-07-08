from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, IntegerField, RadioField, DateTimeField, DateField
from wtforms import FileField, HiddenField, TextAreaField, FieldList, FormField, DecimalField
from wtforms.validators import Required, Length, NumberRange, Optional

from support import none2today, daterange

class FormValidationError(Exception): pass


class RegisterForm(Form):
    username        = TextField('Username', validators = [Required(), Length(min=3, max=25)])
    fullname        = TextField('Full name (optional)', validators = [Length(max=100)])
    password    = PasswordField('Password', validators = [Required(), Length(min=6, max=40)])

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
    test = TextField('test', [Required()])

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
        for timestamp in daterange(ch.start, ch.end):
            data = dict(timestamp=timestamp)
            if timestamp.day%2:
                data['evaluation'] = 'marginal'
            self.evaluations.append_entry(data)
            self._set_choices(self.evaluations[-1], ch)

challenge_forms = {
    'target_value': ChallengeProgressForm,
    'daily_evaluation': DailyEvaluationChallengeForm,
}

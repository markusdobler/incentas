from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, IntegerField, RadioField, FileField, HiddenField, TextAreaField, FieldList, FormField
from wtforms.validators import Required, Length
from app import models

# set your classes here



class RegisterForm(Form):
    username        = TextField('Username', validators = [Required(), Length(min=3, max=25)])
    fullname        = TextField('Full name (optional)', validators = [Length(max=100)])
    password    = PasswordField('Password', validators = [Required(), Length(min=6, max=40)])

class LoginForm(Form):
    name        = TextField('Username', [Required()])
    passwd      = PasswordField('Password', [Required()])

class HashForm(Form):
    plain = TextField('Plaintext', [Required()])

class LevelForm(Form):
    answer = TextField('Answer', [Required()])

class UploadLevelForm(Form):
    file_to_upload = FileField('File', [Required()])

class CheckinForm(Form):
    text =TextField('Comment')
    file_to_upload = FileField('File')

class EditLevelForm(Form):
    title = TextField('Title', [Required()])
    description = TextField('Short description')
    answer = TextField('Expected answer')
    unlock_delay = IntegerField('Delay before answering is allowed', default=0)
    retry_delay = IntegerField('Delay after wrong answer', default=10)
    type = RadioField('Type', choices=[('base','base'),
                                ('upload','upload')])
    upload_label = TextField('Upload Label')

class CheckinNoteField(Form):
    cn_id = HiddenField()
    notes = TextAreaField('Additional Notes')
    guessed_code = TextField('Code')

class CheckinNotesForm(Form):
    notes = FieldList(FormField(CheckinNoteField))

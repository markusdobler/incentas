from flask import Blueprint, render_template, flash, redirect, url_for, request
import forms
from flask.ext.login import login_user, logout_user, login_required, current_user
from support import flash_errors
import models
from datetime import datetime, date, timedelta

#------------------------------------------------------------------------------#
# Controllers
#------------------------------------------------------------------------------#

bp = Blueprint('incentas', __name__, template_folder='templates',
              static_folder='static')
user_management = Blueprint('user_management', __name__,
                            template_folder='templates', static_folder='static')
challenges = Blueprint('challenges', __name__,
                            template_folder='templates', static_folder='static')

blueprints = [bp, user_management, challenges]

@bp.route("/")
def index():
    if current_user.is_authenticated():
        return render_template("overview.html")
    return render_template("index.html")

@user_management.route("/login", methods=['GET','POST'])
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        class LoginException(Exception): pass
        try:
            user = models.User.query.filter(models.User.username ==
                                        form.name.data).scalar()
            if user is None:
                raise LoginException("Username unknown.")
            if not user.check_password(form.passwd.data):
                raise LoginException("Wrong password.")
            login_user(user)
            flash("Hello, %s." % current_user.fullname, "info")
            return redirect(request.args.get("next") or url_for("incentas.index"))
        except LoginException as err:
            flash(" ".join(err.args), "danger")
    flash_errors(form)
    return render_template("login.html", form=form)

@user_management.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("incentas.index"))


@user_management.route("/settings")
@login_required
def settings():
    return "settings, authenticated=%s" % current_user.is_authenticated()


@user_management.route("/register", methods=['GET','POST'])
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        user = models.User(form.username.data, form.password.data,
                           form.fullname.data)
        flash("Account created.  Now, please log in", "success")
        return redirect(url_for('.login'))
    flash_errors(form)
    return render_template("register.html", form=form)

@challenges.route("/challenge")
@login_required
def list_challenges():
    return render_template("list_challenges.html",
                           challenges=current_user.challenges)

@challenges.route("/challenge/active")
@challenges.route("/challenge/active/<slack>")
@login_required
def list_active_challenges(slack=2):
    slack = float(slack)
    latest_endtime = datetime.now() - timedelta(slack)
    flash(latest_endtime)
    active_challenges = [ch for ch in current_user.challenges if ch.end >= latest_endtime]
    return render_template("list_challenges.html", challenges=active_challenges)

@challenges.route("/challenge/<int:id>", methods=['GET','POST'])
@login_required
def challenge(id):
    ch = models.Challenge.query.filter_by(id=id).scalar()
    if ch is None:
        flash("Unknown challenge", "warning")
        return redirect(url_for('.list_challenges'))
    if current_user != ch.user:
        flash("Access denied", "error")
        return redirect(url_for('.list_challenges'))

    form = forms.challenge_forms[ch.type]()
    form.init_from_challenge(ch)
    if form.validate_on_submit():
        flash(repr(form.data))
        try:
            ch.update_from_form_data(form.data)
            return redirect(url_for('.challenge', id=id))
        except forms.FormValidationError as err:
            models.db.session.rollback()
            flash(err.message, 'error')
    if request.method == 'GET':
        form.load_from_challenge(ch, today=date.today())
    flash_errors(form)
    flash(form.data)
    return render_template("%s_challenge.html"%ch.type, challenge=ch, form=form)


# Error Handlers

@bp.app_errorhandler(500)
def internal_error(error):
    models.db_session.rollback()
    return render_template('500.html'), 500

@bp.route('/<path:invalid_path>')
def internal_error(invalid_path):
    return render_template('404.html'), 404

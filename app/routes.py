from flask import *
import forms
from flask.ext.login import login_user, logout_user, login_required, current_user
from support import flash_errors
import models

#------------------------------------------------------------------------------#
# Controllers
#------------------------------------------------------------------------------#

bp = Blueprint('tracking', __name__, template_folder='templates',
              static_folder='static')
user_management = Blueprint('user_management', __name__,
                            template_folder='templates', static_folder='static')

blueprints = [bp, user_management]

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
            user = models.User.query.filter(models.User.name ==
                                        form.name.data).scalar()
            if user is None:
                raise LoginException("Username unknown.")
            if not user.check_password(form.passwd.data):
                raise LoginException("Wrong password.")
            login_user(user)
            flash("Logged in as '%s'." % current_user, "info")
            return redirect(request.args.get("next") or url_for("tracking.index"))
        except LoginException as err:
            flash(" ".join(err.args), "danger")
    flash_errors(form)
    return render_template("login.html", form=form)

@user_management.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("tracking.index"))


@user_management.route("/settings")
@login_required
def settings():
    return "settings, authenticated=%s" % current_user.is_authenticated()


@user_management.route("/register", methods=['GET','POST'])
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        user = models.User(form.name.data, form.password.data)
        flash("Account created.  Now, please log in", "success")
        return redirect(url_for('.login'))
    flash_errors(form)
    return render_template("register.html", form=form)


# Error Handlers

@bp.app_errorhandler(500)
def internal_error(error):
    models.db_session.rollback()
    return render_template('500.html'), 500

@bp.route('/<path:invalid_path>')
def internal_error(invalid_path):
    return render_template('404.html'), 404

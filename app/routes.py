from app import *
import hashlib
import forms
from flask.ext.login import login_user, logout_user, login_required, current_user
from support import flash_errors, pretty_timedelta, pretty_datetime, secure_datetime
from admin_interface import app
import jinja2
from werkzeug import secure_filename
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

#------------------------------------------------------------------------------#
# Controllers
#------------------------------------------------------------------------------#

@app.route("/")
def index():
    if current_user.is_authenticated():
        return render_template("overview.html")
    return render_template("index.html")

@app.route("/login", methods=['GET','POST'])
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
            return redirect(request.args.get("next") or url_for("index"))
        except LoginException as err:
            flash(" ".join(err.args), "danger")
    flash_errors(form)
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/level")
@login_required
def level_overview():
    levels = current_user.unlocked_levels[:]
    return render_template("levels_overview.html", levels=levels)


@app.route("/level/<level_code>", methods=('GET','POST'))
@app.route("/level/<level_code>/<sol>", methods=('GET','POST'))
@login_required
def level(level_code,sol=None):
    level = models.Level.query.filter_by(code=level_code).scalar()
    if level is None:
        flash('Unknown level code.', 'danger')
        return redirect(url_for('level_overview'))
    status = current_user.level_status(level)
    if status=='locked':
        flash('not unlocked yet', 'warning')
        return redirect(url_for('level_overview'))
    elif status=='timeout':
        reason, delta, end = current_user.timeout_info(level)
        return render_template('level_timeout.html', level=level,
                               timeout_reason=reason,
                               timeout_delta=pretty_timedelta(delta),
                               timeout_end=pretty_datetime(end))
    else:
        assert status in ('solved', 'open', 'to_review')
    if level.type == 'upload':
        return upload_level(level_code, level, status)
    if level.rank == 42:
        return redirect(url_for('finale'))
    form = forms.LevelForm()
    if sol is not None:
        form.answer.data = sol
    if form.validate_on_submit():
        correct = level.is_answer_correct(form.answer.data)
        if correct:
            current_user.mark_solved(level)
            return render_template("level_solved.html", form=form,
                                   level=level, open_levels=current_user.open_levels())
        else:
            current_user.mark_failed_attempt(level)
            delay = level.retry_delay
            flash("Wrong answer. Try again after %i seconds."%delay, "danger")
    flash_errors(form)
    try:
        return render_template("level_id_%s.html" % level_code, form=form, level=level)
    except jinja2.exceptions.TemplateNotFound:
        return render_template("level_template.html", form=form, level=level)

def upload_level(level_code, level, status):
    form = forms.UploadLevelForm()
    form.file_to_upload.label.text = level.upload_label
    if form.validate_on_submit():
        file = request.files['file_to_upload']
        if file:
            filename = "%s__%s__%s" % (level.code, secure_datetime(), secure_filename(file.filename))
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            subj = "new upload for level '%s'" % level.title
            preview_url = url_for('admin_show_upload', filename=filename,
                           _external=True)
            accept_url = url_for('admin_accept_upload',
                                 username=current_user.name,
                                 level_code=level.code,
                                 _external=True)
            body = "%s\naccept: %s" % (preview_url, accept_url)
            support.send_mail(subj, body)
            flash('"%s" saved.'%file.filename, 'success')
            current_user.mark_failed_attempt(level)
    elif status == 'to_review':
        flash("You've already uploaded something, but that file is still waiting for its review by an admin before being accepted (or rejected).", 'info')
    flash_errors(form)
    try:
        return render_template("level_id_%s.html" % level_code, form=form, level=level)
    except jinja2.exceptions.TemplateNotFound:
        return render_template("level_upload.html", form=form, level=level)

@app.route("/public/progress/<username>")
def public_progress(username):
    user = models.User.query.filter_by(name=username).scalar()
    if user is None:
        flash('user not known', 'error')
        return redirect(url_for("index"))
    return render_template("public_progress.html", user=user, levels=user.unlocked_levels)

@app.route('/public/level/<level_code>', methods=('GET','POST'))
def public_level(level_code):
    level = models.Level.query.filter_by(code=level_code).scalar()
    if level is None:
        flash('Unknown level code.', 'danger')
        return redirect(url_for('public_progress'))
    if not any(user.status()=='solved' for user in level.users):
        flash('Still locked!', 'warning')
        return render_template('index.html')
    if level.type == 'upload':
        form = forms.UploadLevelForm()
        form.file_to_upload.label.text = level.upload_label
        if form.validate_on_submit():
            flash("your upload won't be saved")
        try:
            return render_template("level_id_%s.html" % level_code, form=form, level=level)
        except jinja2.exceptions.TemplateNotFound:
            return render_template("level_upload.html", form=form, level=level)
    form = forms.LevelForm()
    if form.validate_on_submit():
        correct = level.is_answer_correct(form.answer.data)
        if correct:
            flash("right", "success")
        else:
            flash("nope", "error")
    try:
        return render_template("level_id_%s.html" % level_code, form=form, level=level)
    except jinja2.exceptions.TemplateNotFound:
        return render_template("level_template.html", form=form, level=level)


@app.route("/settings")
@login_required
def settings():
    return "settings"


@app.route("/register", methods=['GET','POST'])
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        user = models.User(form.name.data, form.password.data)
        flash("Account created.  Now, please log in", "success")
        return redirect(url_for('login'))
    flash_errors(form)
    return render_template("register.html", form=form)

@app.route("/checkin/<code>", methods=['GET','POST'])
def checkin(code):
    form = forms.CheckinForm()
    flashs = models.KnownCheckins.check_unknowns_for_code(code)
    for f in flashs:
        flash(str(f), 'info')
    if not flashs:
        try:
            flash(models.CheckinFlashs.latest())
        except:
            pass
    if form.validate_on_submit():
        if form.text.data:
            models.TextCheckin(code, text=form.text.data)
            flash('Hinweistext gespeichert', 'success')
        file = request.files['file_to_upload']
        if file:
            filepath = "ci_%s__%s__%s" % (code, secure_datetime(), secure_filename(file.filename))
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filepath))
            models.FileCheckin(code, filepath=filepath, filename=file.filename)
            flash('Datei gespeichert', 'success')
    former_checkins = models.Checkin.query.filter_by(code=code).order_by(
        models.Checkin.timestamp.desc()).all()
    return render_template("checkin.html", code=code, form=form,
                           former_checkins=former_checkins)

@app.route('/checkin_upload/<filepath>')
def checkin_upload(filepath):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filepath)

@app.route('/checkins', methods=['GET','POST'])
@login_required
def show_checkins():
    form = forms.CheckinNotesForm()
    if form.validate_on_submit():
        for subform in form.notes:
            models.CheckinNote.update_notes(subform.cn_id.data, current_user.id,
                                            subform.notes.data,
                                            subform.guessed_code.data)
    flash_errors(form)
    checkins_and_notes = models.CheckinNote.get_checkins_and_notes(current_user.id)
    sum_corr = 0
    for cn_id, cis, notes, guessed_code, corr in checkins_and_notes:
        form.notes.append_entry(dict(notes=notes, guessed_code=guessed_code,
                                     cn_id=cn_id))
        sum_corr += corr
    answer = None if sum_corr<5 else "b12598"
    return render_template("show_checkins.html",
                           checkins_and_notes=checkins_and_notes, form=form,
                           answer=answer)

@app.route('/public/checkins')
def public_show_checkins():
    checkin_groups= models.Checkin.grouped_visible_checkins()
    return render_template("show_public_checkins.html", checkin_groups=checkin_groups)

@app.route('/ajax/ips')
def ajax_ips():
    my_ip = request.remote_addr
    if not current_user.is_authenticated():
        return jsonify(my_ip=my_ip, known_ips=[(my_ip,
                                    "now, but this won't be stored as you're not logged in")])
    models.IPs.add_if_unknown(my_ip, current_user.id)
    known_ips = models.IPs.list_of_known_ips(current_user.id)
    answer = None if len(known_ips)<10 else '178.77.77.193'
    return jsonify(my_ip=my_ip, known_ips=known_ips, answer=answer)

@app.route('/ajax/slots')
def ajax_slots():
    my_slot = models.TimeSlots.current_slot()
    if current_user.is_authenticated():
        models.TimeSlots.add_if_unknown(my_slot, current_user.id)
        all_slots, cnt_solved = models.TimeSlots.list_all_slots(current_user.id)
        answer = None if cnt_solved < 20 else "adansonia"
    else:
        all_slots = models.TimeSlots.list_all_slots()
        answer = None
    return jsonify(my_slot=my_slot, all_slots=all_slots, answer=answer)


@app.route('/masked.png/<timeslice>')
@app.route('/masked.png')
def masked_png(timeslice=None):
    if timeslice is None:
        timeslice = datetime.now().strftime('%Y-%m-%d, %H:00-%H:59')
    filename = "masked_%s.png" % "".join(c for c in timeslice if c.isdigit())
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except:
        create_masked_image(timeslice, filename)
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def create_masked_image(timeslice, filename):
    app.logger.info('Creating file "%s"' % filename)
    unmasked = Image.open(os.path.join(app.config['RESOURCES_FOLDER'],
                                       'unmasked.png'))
    size = unmasked.size
    masked = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(masked)
    font = ImageFont.truetype(os.path.join(app.config['RESOURCES_FOLDER'],
                                           "inconsolata-dz.otf"), 23)
    draw.text((1, 1), timeslice, fill="#7b1404", font=font)
    boxsize = (200, 200)
    l, u = [int(support.hash(timeslice+c), 20) for c in "xy"]
    l %= (size[0]-boxsize[0])
    u %= (size[1]-boxsize[1])
    box = (l, u, l+boxsize[0], u+boxsize[1])
    region = unmasked.crop(box)
    masked.paste(region, box)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'],filename)
    masked.save(filepath)

@app.route("/merci")
def merci():
    return render_template('merci.html')


@app.route('/finale', methods=["GET", "POST"])
def finale():
    if request.method == 'POST':
        if "submit-yes" in request.form:
            return redirect(url_for("merci"))
        flash("Could you please reconsider?", "warning")
    class Stub(object): pass
    level_stub = Stub()
    level_stub.rank = 42
    level_stub.title = "Keep on swearing"
    return render_template('finale.html', level=level_stub)

# Error Handlers

@app.errorhandler(500)
def internal_error(error):
    #db_session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404

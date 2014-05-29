import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from flask.ext.testing import TestCase
from app import create_app, models
from flask.ext.login import current_user, login_user, logout_user
from flask import current_app, session, message_flashed, appcontext_pushed
from bs4 import BeautifulSoup
from contextlib import contextmanager
import pytest
from app.support import login_manager

not_implemented_yet = pytest.mark.skipif(True, reason="Not implemented yet")


class FlaskTestCase(TestCase):
    def create_app(self):
        app = create_app('tests.config_testing')
        return app

    def set_up(self):
        models.db.create_all()

    def tear_down(self):
        models.db.session.remove()
        models.db.drop_all()

    def get_session(self):
        """Helper function to get the current session."""
        with self.client.session_transaction() as session:
            return session

    @contextmanager
    def force_enable_login_manager(self):
        """ With config['TESTING']==True, the @login_required decorator is
        disabled to facilitate testing.  This context manager re-enables login
        checking, so that login, logout and access restrictions can be tested."""
        login_previously_disabled = login_manager._login_disabled
        login_manager._login_disabled = False
        try:
            with self.client as client:
                yield client
        finally:
            login_manager._login_disabled = login_previously_disabled

    @contextmanager
    def logged_in_as(self, user):
        print "in logged_in_as"
        a = 0
        def handler(sender, **kwargs):
            g.user = user
            a += 1
        with appcontext_pushed.connected_to(handler, self.app):
            yield
            print "end of logged_in_as", a

    @contextmanager
    def capture_flashes(self):
        if hasattr(self, '_captured_flashes'):
            # nested call to this context manager -- just pass through
            yield self._captured_flashes
            return
        self._captured_flashes = []
        def record(sender, message, category, **extra):
            self._captured_flashes.append((message, category))
        message_flashed.connect(record, self.app)
        try:
            yield self._captured_flashes
        finally:
            message_flashed.disconnect(record, self.app)
            del self._captured_flashes

    @contextmanager
    def assert_flash(self, message=None, category=None, message_full=False):
        with self.capture_flashes() as flashes:
            try:
                yield flashes
            except:
                raise
            else:
                for msg,cat in flashes:
                    if category and (category != cat): continue
                    if message and message_full and (message != msg): continue
                    if message and (message not in msg): continue
                    return
                raise AssertionError (
                    "Flash"
                    + (" of category %r"%category if category else "")
                     + (" with %r %s msg"%(message,['in','=='][message_full])
                        if message else "")
                    + (" expected.  Actually received: %r" % (flashes,))
                )

    def get_form_elements(self, html, form_number=0):
        def generator():
            soup = BeautifulSoup(html)
            form = soup('form')[form_number]
            for input in form(attrs={'name':True}):
                yield (input['name'], input.attrs)
        return dict(generator())


class UserManagement(FlaskTestCase):
    def create_user(self, name, password):
        return models.User(name, password)

    def login_as(self, user, password):
        response = self.client.get('/login')
        form = self.get_form_elements(response.data)
        data = dict(name=user.name, passwd=password,
                    csrf_token=form['csrf_token']['value'])
        response = self.client.post('/login', data=data)
        return response

    def logout(self):
        return self.client.get('/logout')

    # test models
    def test_create_user(self):
        """ Creation of a user is reflected in the database."""
        assert len(models.User.query.all())==0
        u0 = self.create_user('name', 'password')
        assert len(models.User.query.all())==1
        u1 = self.create_user('name2', 'password2')
        users = models.User.query.all()
        assert u0 == users[0]
        assert u0.name == 'name'
        assert u1 == users[1]
        assert users[1].name == 'name2'

    def test_password_handling(self):
        """ Only correct password is accepted.
        Updating the password invalidates the old one"""
        u0 = self.create_user('name', 'password')
        u1 = self.create_user('name2', 'password2')
        users = models.User.query.all()
        assert [u.check_password('password') for u in users] == [True, False]
        assert [u.check_password('password2') for u in users] == [False, True]
        u0.set_password('new_password')
        assert [u.check_password('password') for u in users] == [False, False]
        assert [u.check_password('password2') for u in users] == [False, True]
        assert [u.check_password('new_password') for u in users] == [True, False]


    @not_implemented_yet
    def test_users_store_measurement_types(self):
        pass

    @not_implemented_yet
    def test_users_store_assessment_types(self):
        pass

    # test web interaction
    def test_registration(self):
        """Test the account registration via web interface.

        Registration page should show name and password fields.
        Short names and passwords are rejected.
        CSRF token must be supplied.
        After registration, user is asked to log in.
        Newly-created account is stored in database.
        """
        with self.force_enable_login_manager():
            response = self.client.get('/register')
            assert response.status_code == 200
            form = self.get_form_elements(response.data)
            assert 'name' in form
            assert 'password' in form

            data = {'name': 'username', 'password': 'secr3t',
                    'csrf_token': form['csrf_token']['value']}

            with self.assert_flash('Username', 'error'):
                response = self.client.post('/register', data=dict(data, name='st'))
            with self.assert_flash('Password', 'error'):
                response = self.client.post('/register', data=dict(data, password='12345'))
            with self.assert_flash('CSRF token missing', 'error'):
                response = self.client.post('/register', data=dict(data, csrf_token=None))

            with self.assert_flash('Account created', 'success'):
                with self.assert_flash('please log in', 'success'):
                    response = self.client.post('/register', data=data)
            self.assert_redirects(response, '/login')
            user = models.User.query.scalar()
            assert user.name == data['name']
            assert user.check_password(data['password'])

    def test_force_login(self):
        """ When trying to access restricted pages, the user is redirected to
        the login page"""
        u = self.create_user('name', 'password')
        with self.force_enable_login_manager():
            with self.assert_flash("Please log in", 'message'):
                response = self.client.get('/settings')
            assert response.status_code == 302
            self.assert_redirects(response, '/login?next=%2Fsettings')
            response = self.client.get(response.location)
            assert response.status_code == 200

            self.login_as(u, 'password')
            response = self.client.get('/settings')
            assert response.status_code == 200

            self.logout()
            with self.assert_flash("Please log in", 'message'):
                response = self.client.get('/settings')
            assert response.status_code == 302


    def test_login(self):
        """Login page asks for name and password.
        Login notifies if username is unknown.
        Login only works with correct password (even if another user has that
        password).
        current_user is authenticated iff the login process was successful.
        Logged in user is allowed to access restricted pages.
        """
        u0 = self.create_user('name', 'password')
        u1 = self.create_user('name2', 'pwd_for_name2')
        with self.force_enable_login_manager():
            response = self.client.get('/login')
            form = self.get_form_elements(response.data)
            assert 'name' in form
            assert 'passwd' in form
            data = {'name': 'name', 'passwd': 'password',
                    'csrf_token': form['csrf_token']['value']}

            with self.assert_flash("Username unknown"):
                response = self.client.post('/login', data=dict(data, name="unknown"))
            with self.assert_flash("Wrong password"):
                response = self.client.post('/login', data=dict(data, passwd="wrong"))
            with self.assert_flash("Wrong password"):
                response = self.client.post('/login', data=dict(data, passwd="pwd_for_name2"))

            assert not current_user.is_authenticated()
            with self.assert_flash("Logged in"):
                response = self.client.post('/login', data=data)
            assert current_user.is_authenticated()

            response = self.client.get('/settings')
            assert response.status_code == 200

            response = self.client.get('/logout')
            assert not current_user.is_authenticated()

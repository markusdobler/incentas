from .common_test_base import *

from flask import current_app, session, appcontext_pushed

class UserManagementTestCase(TrackerTestCase):
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

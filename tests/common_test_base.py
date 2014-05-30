import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from flask.ext.testing import TestCase
from app import create_app, models
from flask.ext.login import current_user, login_user, logout_user
from flask import message_flashed
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

class TrackerTestCase(FlaskTestCase):
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


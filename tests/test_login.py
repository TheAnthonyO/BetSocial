
import unittest
from flask import Flask, session
from flask.testing import FlaskClient
from login import login_bp
from friends import friends_bp
from models import db, User

class LoginTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'testkey'
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.register_blueprint(login_bp)
        self.app.register_blueprint(friends_bp)
        db.init_app(self.app)

        with self.app.app_context():
            db.create_all()
            user = User(username='testuser', password='testpass')
            db.session.add(user)
            db.session.commit()

        self.client = self.app.test_client()

    def test_home_page_logged_out(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to BetSocial', response.data)

    def test_login_failure(self):
        response = self.client.post('/login', data={
            'username': 'fakeuser',
            'password': 'wrongpass'
        })
        self.assertIn(b'Invalid username or password', response.data)

    def test_logout(self):
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertNotIn('username', sess)

    def test_register_existing_user(self):
        response = self.client.post('/register', data={
            'username': 'testuser',
            'password': 'something'
        })
        self.assertIn(b'Username already exists', response.data)

    def test_deposit_withdraw_logged_out(self):
        response = self.client.post('/deposit_withdraw', data={'amount': '10', 'action': 'deposit'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()

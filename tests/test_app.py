import unittest
from flask import Flask
from app import app, db  # Import app and db from app.py
from models import User, Message, Bet, FriendRequest

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # Set up a test Flask app with an in-memory database. 
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app = app
        self.client = app.test_client()  # Create a test client for HTTP requests
        with self.app.app_context():
            db.create_all()  # Create tables in the in-memory database

    def tearDown(self):
        # Clean up after each test by dropping all tables.
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username, password):
        # Helper method to log in a user. 
        return self.client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

    def logout(self):
        # Helper method to log out a user. 
        return self.client.get('/logout', follow_redirects=True)

class TestApp(BaseTestCase):
    def test_app_initialization(self):
        #Test that the app initializes and responds to the root route.
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to BetSocial', response.data)  # Updated to match current title

if __name__ == '__main__':
    unittest.main()
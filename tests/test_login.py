import unittest
from tests.test_app import BaseTestCase
from models import db, User

class TestLogin(BaseTestCase):
    def test_register_new_user(self):
        #Test registering a new user.
        response = self.client.post('/register', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to BetSocial', response.data)  # Updated to match current title
        with self.app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.password, 'testpass')

    def test_register_duplicate_user(self):
         #Test registering a user with an existing username. 
        self.client.post('/register', data={'username': 'testuser', 'password': 'testpass'})
        response = self.client.post('/register', data={'username': 'testuser', 'password': 'newpass'})
        self.assertIn(b'Username already exists', response.data)

    def test_login_valid_credentials(self):
         #Test logging in with valid credentials. 
        self.client.post('/register', data={'username': 'testuser', 'password': 'testpass'})
        response = self.login('testuser', 'testpass')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome, testuser!', response.data)

    def test_login_invalid_credentials(self):
         #Test logging in with invalid credentials. 
        self.client.post('/register', data={'username': 'testuser', 'password': 'testpass'})
        response = self.login('testuser', 'wrongpass')
        self.assertIn(b'Invalid credentials', response.data)

    def test_logout(self):
         #Test logging out. 
        self.client.post('/register', data={'username': 'testuser', 'password': 'testpass'})
        self.login('testuser', 'testpass')
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'Welcome, testuser!', response.data)
        self.assertIn(b'Login', response.data)  # Back to login form

    def test_deposit(self):
         #Test depositing funds into bankroll. 
        self.client.post('/register', data={'username': 'testuser', 'password': 'testpass'})
        self.login('testuser', 'testpass')
        response = self.client.post('/deposit_withdraw', data={'amount': '100', 'action': 'deposit'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertEqual(user.bankroll, 1100.0)  # 1000 + 100

    def test_withdraw_sufficient_funds(self):
         #Test withdrawing funds when sufficient. 
        self.client.post('/register', data={'username': 'testuser', 'password': 'testpass'})
        self.login('testuser', 'testpass')
        response = self.client.post('/deposit_withdraw', data={'amount': '200', 'action': 'withdraw'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertEqual(user.bankroll, 800.0)  # 1000 - 200

    def test_withdraw_insufficient_funds(self):
         #Test withdrawing more than available funds. 
        self.client.post('/register', data={'username': 'testuser', 'password': 'testpass'})
        self.login('testuser', 'testpass')
        response = self.client.post('/deposit_withdraw', data={'amount': '2000', 'action': 'withdraw'})
        self.assertIn(b'Insufficient funds', response.data)

if __name__ == '__main__':
    unittest.main()
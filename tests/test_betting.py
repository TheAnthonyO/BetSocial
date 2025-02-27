import unittest
from tests.test_app import BaseTestCase
from models import db, User, Bet

class TestBetting(BaseTestCase):
    def setUp(self):
         #Set up test users before each test. 
        super().setUp()
        with self.app.app_context():
            user1 = User(username='user1', password='pass1')
            user2 = User(username='user2', password='pass2')
            db.session.add_all([user1, user2])
            db.session.commit()
            # Store IDs instead of objects to avoid detachment
            self.user1_id = user1.id
            self.user2_id = user2.id

    def test_place_solo_bet(self):
         #Test placing a solo bet. 
        self.login('user1', 'pass1')
        response = self.client.post('/betting', data={'team': 'Boston Celtics', 'amount': '50'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            user1 = db.session.get(User, self.user1_id)
            bet = Bet.query.filter_by(user_id=user1.id).first()
            self.assertIsNotNone(bet)
            self.assertEqual(bet.team, 'Boston Celtics')
            self.assertEqual(bet.amount, 50.0)
            self.assertEqual(user1.bankroll, 950.0)  # 1000 - 50

    def test_place_vs_friend_bet(self):
         #Test placing a bet vs a friend. 
        self.login('user1', 'pass1')
        with self.app.app_context():
            user1 = db.session.get(User, self.user1_id)
            user2 = db.session.get(User, self.user2_id)
            user1.friends.append(user2)
            db.session.commit()
        response = self.client.post('/betting', data={'team': 'Boston Celtics', 'amount': '25', 'bet_type': 'vs_friend', 'friend_id': self.user2_id}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            user1 = db.session.get(User, self.user1_id)
            bet = Bet.query.filter_by(user_id=user1.id).first()
            self.assertEqual(bet.opponent_id, self.user2_id)
            self.assertEqual(bet.amount, 25.0)
            self.assertEqual(user1.bankroll, 975.0)  # 1000 - 25

    def test_insufficient_funds(self):
         #Test placing a bet with insufficient funds. 
        self.login('user1', 'pass1')
        response = self.client.post('/betting', data={'team': 'Boston Celtics', 'amount': '2000'}, follow_redirects=True)
        self.assertIn(b'Insufficient funds', response.data)
        with self.app.app_context():
            user1 = db.session.get(User, self.user1_id)
            self.assertEqual(user1.bankroll, 1000.0)  # No change

    def test_settle_bets_win(self):
         #Test settling bets with a winning outcome. 
        self.login('user1', 'pass1')
        self.client.post('/betting', data={'team': 'Boston Celtics', 'amount': '50'})
        response = self.client.post('/settle_bets', data={'winning_team': 'Boston Celtics'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            user1 = db.session.get(User, self.user1_id)
            bet = Bet.query.filter_by(user_id=user1.id).first()
            self.assertEqual(bet.result, 'win')
            self.assertEqual(user1.bankroll, 1050.0)  # 1000 - 50 + 100 (2x odds)

    def test_settle_bets_loss(self):
         #Test settling bets with a losing outcome. 
        self.login('user1', 'pass1')
        self.client.post('/betting', data={'team': 'Boston Celtics', 'amount': '50'})
        response = self.client.post('/settle_bets', data={'winning_team': 'Los Angeles Lakers'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            user1 = db.session.get(User, self.user1_id)
            bet = Bet.query.filter_by(user_id=user1.id).first()
            self.assertEqual(bet.result, 'lose')
            self.assertEqual(user1.bankroll, 950.0)  # 1000 - 50

if __name__ == '__main__':
    unittest.main()
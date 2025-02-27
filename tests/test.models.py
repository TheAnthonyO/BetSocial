import unittest
from tests.test_app import BaseTestCase
from models import db, User, Message, Bet, FriendRequest

class TestModels(BaseTestCase):
    def test_user_creation(self):
         #Test creating a new user. 
        with self.app.app_context():
            user = User(username='testuser', password='testpass')
            db.session.add(user)
            db.session.commit()
            self.assertEqual(user.username, 'testuser')
            self.assertEqual(user.bankroll, 1000.0)

    def test_update_bankroll_positive(self):
         #Test updating bankroll with a positive amount. 
        with self.app.app_context():
            user = User(username='testuser', password='testpass')
            db.session.add(user)
            db.session.commit()
            user.update_bankroll(500)
            self.assertEqual(user.bankroll, 1500.0)

    def test_update_bankroll_negative_reset(self):
         #Test updating bankroll below zero resets to 500. 
        with self.app.app_context():
            user = User(username='testuser', password='testpass')
            db.session.add(user)
            db.session.commit()
            user.update_bankroll(-1500)
            self.assertEqual(user.bankroll, 500.0)

    def test_message_creation(self):
         #Test creating a message between users. 
        with self.app.app_context():
            user1 = User(username='user1', password='pass1')
            user2 = User(username='user2', password='pass2')
            db.session.add_all([user1, user2])
            db.session.commit()
            message = Message(sender_id=user1.id, receiver_id=user2.id, content='Hi!')
            db.session.add(message)
            db.session.commit()
            self.assertEqual(message.content, 'Hi!')

    def test_bet_creation(self):
         #Test creating a bet. 
        with self.app.app_context():
            user = User(username='testuser', password='testpass')
            db.session.add(user)
            db.session.commit()
            bet = Bet(user_id=user.id, team='Team A', amount=100.0)
            db.session.add(bet)
            db.session.commit()
            self.assertEqual(bet.team, 'Team A')
            self.assertEqual(bet.odds, 2.0)

    def test_friend_request_creation(self):
         #Test creating a friend request. 
        with self.app.app_context():
            user1 = User(username='user1', password='pass1')
            user2 = User(username='user2', password='pass2')
            db.session.add_all([user1, user2])
            db.session.commit()
            request = FriendRequest(sender_id=user1.id, receiver_id=user2.id)
            db.session.add(request)
            db.session.commit()
            self.assertEqual(request.status, 'pending')

if __name__ == '__main__':
    unittest.main()
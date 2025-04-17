import unittest
from models import db, User, Message, Bet, FriendRequest
from flask import Flask

class TestModels(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_creation(self):
        user = User(username='testuser', password='testpass')
        db.session.add(user)
        db.session.commit()
        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, 'testuser')

    def test_bankroll_update_deposit(self):
        user = User(username='deposituser', password='test', bankroll=100.0)
        db.session.add(user)
        db.session.commit()
        user.update_bankroll(-50)
        self.assertEqual(user.bankroll, 150.0)

    def test_message_creation(self):
        sender = User(username='sender', password='123')
        receiver = User(username='receiver', password='123')
        db.session.add_all([sender, receiver])
        db.session.commit()
        message = Message(sender_id=sender.id, receiver_id=receiver.id, content='hello')
        db.session.add(message)
        db.session.commit()
        self.assertIsNotNone(message.id)
        self.assertEqual(message.content, 'hello')

    def test_bet_creation(self):
        user = User(username='bettor', password='123')
        db.session.add(user)
        db.session.commit()
        bet = Bet(user_id=user.id, team='Lakers', amount=100.0, odds=2.5)
        db.session.add(bet)
        db.session.commit()
        self.assertIsNotNone(bet.id)
        self.assertEqual(bet.team, 'Lakers')
        self.assertEqual(bet.result_description, 'Pending')

    def test_friend_request(self):
        sender = User(username='alice', password='abc')
        receiver = User(username='bob', password='xyz')
        db.session.add_all([sender, receiver])
        db.session.commit()
        request = FriendRequest(sender_id=sender.id, receiver_id=receiver.id)
        db.session.add(request)
        db.session.commit()
        self.assertIsNotNone(request.id)
        self.assertEqual(request.status, 'pending')

if __name__ == '__main__':
    unittest.main()


import unittest
from flask import Flask, session
from models import db, User, FriendRequest, Message
from friends import friends_bp
from login import login_bp

class FriendsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'testkey'
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.register_blueprint(friends_bp)
        self.app.register_blueprint(login_bp)  # Register login_bp to support redirects
        db.init_app(self.app)

        with self.app.app_context():
            db.create_all()
            user1 = User(username='user1', password='pass')
            user2 = User(username='user2', password='pass')
            db.session.add_all([user1, user2])
            db.session.commit()
            self.user1_id = user1.id
            self.user2_id = user2.id

        self.client = self.app.test_client()

    def login(self, username):
        with self.client.session_transaction() as sess:
            sess['username'] = username

    def test_send_friend_request(self):
        self.login('user1')
        response = self.client.post('/friends', data={
            'send_request': True,
            'friend_username': 'user2'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            req = FriendRequest.query.filter_by(sender_id=self.user1_id, receiver_id=self.user2_id).first()
            self.assertIsNotNone(req)
            self.assertEqual(req.status, 'pending')

    def test_send_message(self):
        self.login('user1')
        with self.app.app_context():
            receiver = User.query.get(self.user2_id)
            receiver_id = receiver.id
        response = self.client.post('/friends', data={
            'receiver_id': str(receiver_id),
            'message': 'Hey!'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            msg = Message.query.filter_by(sender_id=self.user1_id, receiver_id=self.user2_id).first()
            self.assertIsNotNone(msg)
            self.assertEqual(msg.content, 'Hey!')

if __name__ == '__main__':
    unittest.main()

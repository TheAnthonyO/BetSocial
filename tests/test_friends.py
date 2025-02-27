import unittest
from tests.test_app import BaseTestCase
from models import db, User, FriendRequest, Message

class TestFriends(BaseTestCase):
    def setUp(self):
         #Set up test users before each test. 
        super().setUp()
        with self.app.app_context():
            user1 = User(username='user1', password='pass1')
            user2 = User(username='user2', password='pass2')
            db.session.add_all([user1, user2])
            db.session.commit()
            self.user1_id = user1.id
            self.user2_id = user2.id

    def test_send_friend_request(self):
         #Test sending a friend request. 
        self.login('user1', 'pass1')
        response = self.client.post('/friends', data={'friend_username': 'user2', 'send_request': 'Send Request'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            request = FriendRequest.query.filter_by(sender_id=self.user1_id, receiver_id=self.user2_id).first()
            self.assertIsNotNone(request)
            self.assertEqual(request.status, 'pending')

    def test_accept_friend_request(self):
         #Test accepting a friend request. 
        self.login('user1', 'pass1')
        self.client.post('/friends', data={'friend_username': 'user2', 'send_request': 'Send Request'})
        self.logout()
        self.login('user2', 'pass2')
        with self.app.app_context():
            request = FriendRequest.query.filter_by(sender_id=self.user1_id, receiver_id=self.user2_id).first()
            response = self.client.post('/friends', data={'request_id': request.id, 'accept_request': 'Accept'}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(request.status, 'accepted')
            user2 = db.session.get(User, self.user2_id)
            self.assertIn(self.user1_id, [friend.id for friend in user2.friends])

    def test_duplicate_friendship(self):
         #Test that sending and accepting a second request doesn’t duplicate friendship. 
        # First request: user1 -> user2
        self.login('user1', 'pass1')
        self.client.post('/friends', data={'friend_username': 'user2', 'send_request': 'Send Request'})
        self.logout()
        self.login('user2', 'pass2')
        with self.app.app_context():
            request1 = FriendRequest.query.filter_by(sender_id=self.user1_id, receiver_id=self.user2_id).first()
            self.client.post('/friends', data={'request_id': request1.id, 'accept_request': 'Accept'})
            # Verify initial friendship count
            friendships = db.session.query(db.metadata.tables['friendship']).count()
            self.assertEqual(friendships, 1)  # One friendship established
        
        # Attempt second request: user2 -> user1 (won’t create due to existing friendship)
        self.logout()
        self.login('user2', 'pass2')
        self.client.post('/friends', data={'friend_username': 'user1', 'send_request': 'Send Request'})
        with self.app.app_context():
            request2 = FriendRequest.query.filter_by(sender_id=self.user2_id, receiver_id=self.user1_id).first()
            self.assertIsNone(request2)  # No second request created, as expected
            # Verify friendship count remains 1
            friendships = db.session.query(db.metadata.tables['friendship']).count()
            self.assertEqual(friendships, 1)  # Still only one friendship row

    def test_send_message(self):
         #Test sending a message to a friend. 
        self.login('user1', 'pass1')
        self.client.post('/friends', data={'friend_username': 'user2', 'send_request': 'Send Request'})
        self.logout()
        self.login('user2', 'pass2')
        with self.app.app_context():
            request = FriendRequest.query.filter_by(sender_id=self.user1_id, receiver_id=self.user2_id).first()
            self.client.post('/friends', data={'request_id': request.id, 'accept_request': 'Accept'})
        response = self.client.post('/friends', data={'receiver_id': self.user1_id, 'message': 'Hey!'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            message = Message.query.filter_by(sender_id=self.user2_id, receiver_id=self.user1_id).first()
            self.assertEqual(message.content, 'Hey!')

if __name__ == '__main__':
    unittest.main()
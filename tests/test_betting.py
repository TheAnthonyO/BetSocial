import unittest
from unittest.mock import patch, MagicMock
from app import app, db
from models import User, Bet
import betting

class TestBetting(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            self.user = User(username='testuser', password='password', bankroll=1000)
            db.session.add(self.user)
            db.session.commit()
            self.user_id = self.user.id  # Store the user ID to avoid session issues

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_place_bet_insufficient_funds(self):
        with app.app_context():
            user = db.session.get(User, self.user_id)
            user.bankroll = 50
            db.session.commit()
            with self.app as client:
                with client.session_transaction() as sess:
                    sess['username'] = 'testuser'
                game_data = {
                    'id': 'game1',
                    'team1': 'Team A',
                    'team2': 'Team B',
                    'status': 'scheduled',
                    'date': '2025-04-17 12:00:00',
                    'odds': {'team1': 2.5, 'team2': 1.5}
                }
                with patch('betting.get_all_games', return_value=[game_data]):
                    response = client.post('/betting', data={
                        'team': 'Team A',
                        'amount': '100',
                        'game_id': 'game1'
                    }, follow_redirects=True)
                    self.assertIn(b'Insufficient funds', response.data)
                    self.assertEqual(Bet.query.count(), 0)

    def test_place_bet_invalid_game_status(self):
        with app.app_context():
            with self.app as client:
                with client.session_transaction() as sess:
                    sess['username'] = 'testuser'
                game_data = {
                    'id': 'game1',
                    'team1': 'Team A',
                    'team2': 'Team B',
                    'status': 'completed',
                    'date': '2025-04-17 12:00:00',
                    'odds': {'team1': 2.5, 'team2': 1.5}
                }
                with patch('betting.get_all_games', return_value=[game_data]):
                    response = client.post('/betting', data={
                        'team': 'Team A',
                        'amount': '100',
                        'game_id': 'game1'
                    }, follow_redirects=True)
                    self.assertIn(b'Cannot bet on games that are not scheduled or live', response.data)
                    self.assertEqual(Bet.query.count(), 0)

    def test_settle_bets_loss(self):
        with app.app_context():
            user = db.session.get(User, self.user_id)
            bet = Bet(user_id=user.id, team='Team A', amount=100, odds=2.0, game_id='game1')
            db.session.add(bet)
            db.session.commit()
            betting.betting_system.settle_bets('Team B', 'game1')
            updated_bet = Bet.query.first()
            self.assertEqual(updated_bet.result, 'lose')
            self.assertEqual(updated_bet.result_description, 'Loss - Team B')
            self.assertEqual(db.session.get(User, self.user_id).bankroll, 1000)

    def test_check_and_settle_completed_games(self):
        with app.app_context():
            user = db.session.get(User, self.user_id)
            bet = Bet(user_id=user.id, team='Team A', amount=100, odds=2.0, game_id='game1')
            db.session.add(bet)
            db.session.commit()
            game_data = [{'id': 'game1', 'status': 'completed', 'winner': 'Team A'}]
            with patch('odds_api.odds_api.get_live_games', return_value=game_data):
                with patch('betting.betting_system.settle_bets') as mock_settle:
                    betting.betting_system.check_and_settle_completed_games()
                    mock_settle.assert_called_with('Team A', 'game1')

    def test_get_games_authenticated(self):
        with self.app as client:
            with client.session_transaction() as sess:
                sess['username'] = 'testuser'
            game_data = [{'id': 'game1', 'team1': 'Team A', 'team2': 'Team B'}]
            with patch('betting.get_all_games', return_value=game_data):
                response = client.get('/api/games')
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'Team A', response.data)

    def test_get_games_unauthenticated(self):
        with self.app as client:
            response = client.get('/api/games')
            self.assertEqual(response.status_code, 401)
            self.assertIn(b'Not authenticated', response.data)

    def test_betting_api_error(self):
        with self.app as client:
            with client.session_transaction() as sess:
                sess['username'] = 'testuser'
            with patch('betting.get_all_games', side_effect=Exception("API error")):
                response = client.get('/betting')
                self.assertIn(b'No games available at the moment.', response.data)

if __name__ == '__main__':
    unittest.main()
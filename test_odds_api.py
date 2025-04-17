
import unittest
from unittest.mock import patch, MagicMock
from odds_api import OddsAPI

class TestOddsAPI(unittest.TestCase):
    def setUp(self):
        self.api = OddsAPI()

    @patch('odds_api.requests.get')
    def test_get_live_games_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'id': 'game1',
            'home_team': 'Team A',
            'away_team': 'Team B',
            'commence_time': '2099-01-01T00:00:00Z',
            'bookmakers': [{
                'markets': [{
                    'key': 'h2h',
                    'outcomes': [
                        {'name': 'Team A', 'price': 1.8},
                        {'name': 'Team B', 'price': 2.2}
                    ]
                }]
            }]
        }]
        mock_get.return_value = mock_response

        games = self.api.get_live_games()
        self.assertEqual(len(games), 0)  # Date is future => not live

    @patch('odds_api.requests.get')
    def test_get_upcoming_games_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'id': 'game2',
            'home_team': 'Team X',
            'away_team': 'Team Y',
            'commence_time': '2099-01-02T00:00:00Z',
            'bookmakers': [{
                'markets': [{
                    'key': 'h2h',
                    'outcomes': [
                        {'name': 'Team X', 'price': 1.9},
                        {'name': 'Team Y', 'price': 2.1}
                    ]
                }]
            }]
        }]
        mock_get.return_value = mock_response

        games = self.api.get_upcoming_games()
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]['team1'], 'Team X')
        self.assertEqual(games[0]['team2'], 'Team Y')

    @patch('odds_api.requests.get')
    def test_get_live_games_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        games = self.api.get_live_games()
        self.assertEqual(games, [])

    def test_get_best_odds_with_missing_data(self):
        game = {'home_team': 'Team Z'}
        bookmakers = [{'markets': []}]
        best_odds = self.api._get_best_odds(bookmakers, game)
        self.assertEqual(best_odds['team1'], 2.0)
        self.assertEqual(best_odds['team2'], 2.0)

if __name__ == '__main__':
    unittest.main()

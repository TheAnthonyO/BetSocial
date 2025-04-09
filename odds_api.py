import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import pytz

load_dotenv()

class OddsAPI:
    def __init__(self):
        self.api_key = os.getenv('ODDS_API_KEY')
        if not self.api_key:
            print("ERROR: ODDS_API_KEY not found in environment variables!")
        else:
            print(f"Successfully loaded API key: {self.api_key[:5]}...")
        self.base_url = "https://api.the-odds-api.com/v4/sports"
        # The Odds API uses apiKey as a query parameter, not as a header
        print(f"API key configured: {self.api_key[:5]}...")

    def get_live_games(self):
        """Fetch live games from The Odds API"""
        try:
            # Get NBA games that are in progress
            url = f"{self.base_url}/basketball_nba/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "us",
                "markets": "h2h",
                "oddsFormat": "decimal"
            }
            print(f"Fetching live games from: {url}")
            response = requests.get(url, params=params)
            print(f"Live games response status: {response.status_code}")
            
            if response.status_code == 200:
                games = self._process_games_by_status(response.json(), 'in_progress')
                print(f"Found {len(games)} live games")
                return games
            else:
                print(f"Error response: {response.text}")
            return []
        except Exception as e:
            print(f"Error fetching live games: {str(e)}")
            return []

    def get_upcoming_games(self):
        """Fetch upcoming games for the next 7 days"""
        try:
            # Get today's date in UTC
            today = datetime.now(pytz.UTC)
            # Get date 7 days from now
            next_week = today + timedelta(days=7)
            
            # Format dates for API in ISO format with UTC timezone
            today_str = today.strftime("%Y-%m-%dT%H:%M:%SZ")
            next_week_str = next_week.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            url = f"{self.base_url}/basketball_nba/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "us",
                "markets": "h2h",
                "oddsFormat": "decimal",
                "dateFormat": "iso",
                "commenceTimeFrom": today_str,
                "commenceTimeTo": next_week_str
            }
            print(f"Fetching upcoming games from: {url}")
            response = requests.get(url, params=params)
            print(f"Upcoming games response status: {response.status_code}")
            
            if response.status_code == 200:
                games = self._process_games_by_status(response.json(), 'upcoming')
                print(f"Found {len(games)} upcoming games")
                return games
            else:
                print(f"Error response: {response.text}")
            return []
        except Exception as e:
            print(f"Error fetching upcoming games: {str(e)}")
            return []

    def _process_games_by_status(self, data, status_filter):
        """Process games data into our format based on status filter"""
        processed_games = []
        current_time = datetime.now(pytz.UTC)
        eastern_tz = pytz.timezone('America/New_York')
        
        for game in data:
            try:
                # Convert commence_time to datetime with UTC timezone
                game_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                
                # Determine game status
                if game_time > current_time:
                    status = 'upcoming'
                else:
                    status = 'in_progress'
                
                # Only process games with matching status
                if status == status_filter:
                    # Get the best odds from available bookmakers
                    best_odds = self._get_best_odds(game.get('bookmakers', []), game)
                    
                    # Convert game time to Eastern Time and format in 12-hour format
                    eastern_time = game_time.astimezone(eastern_tz)
                    formatted_time = eastern_time.strftime("%Y-%m-%d %I:%M %p")
                    
                    game_data = {
                        'id': game['id'],
                        'team1': game['home_team'],
                        'team2': game['away_team'],
                        'date': formatted_time,
                        'odds': best_odds
                    }
                    
                    # Add status-specific data
                    if status_filter == 'in_progress':
                        game_data['status'] = 'live'
                        game_data['score'] = {
                            'team1': game.get('scores', {}).get('home', 0),
                            'team2': game.get('scores', {}).get('away', 0)
                        }
                    else:  # upcoming
                        game_data['status'] = 'scheduled'
                    
                    processed_games.append(game_data)
            except Exception as e:
                print(f"Error processing game: {str(e)}")
                print(f"Game data: {game}")
                continue
                
        return processed_games

    def _get_best_odds(self, bookmakers, game):
        """Get the best available odds from all bookmakers"""
        best_odds = {'team1': 2.0, 'team2': 2.0}  # Default odds
        
        try:
            for bookmaker in bookmakers:
                for market in bookmaker.get('markets', []):
                    if market.get('key') == 'h2h':
                        for outcome in market.get('outcomes', []):
                            if outcome.get('name') == game.get('home_team'):
                                best_odds['team1'] = max(best_odds['team1'], float(outcome.get('price', 2.0)))
                            else:
                                best_odds['team2'] = max(best_odds['team2'], float(outcome.get('price', 2.0)))
        except Exception as e:
            print(f"Error processing odds: {str(e)}")
            
        return best_odds

# Create a singleton instance
odds_api = OddsAPI() 
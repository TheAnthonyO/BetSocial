# Import Flask components for routing, templating, and request handling
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
# Import database and models for user and bet management
from models import db, User, Bet
from datetime import datetime
import schedule
import time
from odds_api import odds_api

# Create a Blueprint named 'betting' for betting-related routes
betting_bp = Blueprint('betting', __name__)

# Define a BettingSystem class to encapsulate betting logic
class BettingSystem:
    # Method to place a bet, deducting from bankroll if funds are sufficient
    def place_bet(self, user, team, amount, odds=2.0, bet_type='solo', opponent_id=None, game_id=None):
        if user.bankroll < amount:
            return None  # Return None if insufficient funds
        # Create a new bet record
        bet = Bet(user_id=user.id, team=team, amount=amount, odds=odds, bet_type=bet_type, opponent_id=opponent_id, game_id=game_id)
        db.session.add(bet)
        # Deduct the bet amount from the user's bankroll
        user.update_bankroll(-amount)
        db.session.commit()
        return bet  # Return the created bet object

    # Method to settle all pending bets based on a winning team
    def settle_bets(self, winning_team, game_id):
        # Loop through all unsettled bets
        for bet in Bet.query.filter_by(result=None, game_id=game_id).all():
            if bet.team == winning_team:
                # If the bet's team matches the winner, mark as win and pay out
                bet.result = 'win'
                winnings = bet.amount * bet.odds
                User.query.get(bet.user_id).update_bankroll(winnings)
                bet.result_description = f"Win - {winning_team}"
            else:
                # Otherwise, mark as loss
                bet.result = 'lose'
                bet.result_description = f"Loss - {winning_team}"
        db.session.commit()
        return winning_team  # Return the winning team for reference

    # Method to check and settle completed games
    def check_and_settle_completed_games(self):
        live_games = odds_api.get_live_games()
        for game in live_games:
            if game['status'] == 'completed':
                # Get the winning team from the game result
                winning_team = game.get('winner')
                if winning_team:
                    self.settle_bets(winning_team, game['id'])

# Instantiate the BettingSystem
betting_system = BettingSystem()

# Helper function to get all games from the API
def get_all_games():
    """Get all games (live and upcoming) from the API"""
    live_games = odds_api.get_live_games()
    upcoming_games = odds_api.get_upcoming_games()
    return live_games + upcoming_games

# Route for the betting page, handling both GET (display) and POST (bet placement)
@betting_bp.route('/betting', methods=['GET', 'POST'])
def betting():
    if 'username' not in session:
        return redirect(url_for('login.home'))
    
    user = User.query.filter_by(username=session['username']).first()
    friends_list = list(user.friends.all())
    error = None
    success = None
    api_error = None

    betting_system.check_and_settle_completed_games()

    try:
        all_games = get_all_games()
    except Exception as e:
        if "Usage quota has been reached" in str(e):
            api_error = "The odds service is currently unavailable. Please try again later."
        else:
            api_error = "An error occurred while fetching games. Please try again later."
        all_games = []

    if request.method == 'POST':
        try:
            print(f"Form data: {request.form}")  # Debug log
            
            # Validate and get team
            team = request.form.get('team')
            if not team:
                raise ValueError("Team selection is required")
            
            # Validate and get amount
            amount_str = request.form.get('amount')
            if not amount_str:
                raise ValueError("Amount is required")
            try:
                amount = float(amount_str)
                if amount <= 0:
                    raise ValueError("Amount must be greater than 0")
            except ValueError as e:
                raise ValueError(f"Invalid amount format: {amount_str}")
            
            # Validate and get game_id
            game_id = request.form.get('game_id')
            if not game_id:
                raise ValueError("Game ID is required")
            
            print(f"Processing bet - Team: {team}, Amount: {amount}, Game ID: {game_id}")  # Debug log
            
            # Get current games from API
            all_games = get_all_games()
            print(f"Total games found: {len(all_games)}")  # Debug log
            
            # Find the game and its odds
            game = next((g for g in all_games if g['id'] == game_id), None)
            if not game:
                error = "Game not found."
                print(f"Game not found for ID: {game_id}")  # Debug log
            elif game['status'] not in ['scheduled', 'live']:
                error = "Cannot bet on games that are not scheduled or live."
                print(f"Invalid game status: {game['status']}")  # Debug log
            else:
                # Determine odds based on team selection
                try:
                    odds = game['odds']['team1'] if team == game['team1'] else game['odds']['team2']
                    print(f"Selected odds: {odds}")  # Debug log
                    
                    bet = betting_system.place_bet(user, team, amount, odds, 'solo', None, game_id)
                    if not bet:
                        error = "Insufficient funds."
                        print(f"Insufficient funds for user: {user.username}")  # Debug log
                    else:
                        success = f"Bet placed successfully on {team} with {odds}x odds!"
                        print(f"Bet placed successfully: {bet.id}")  # Debug log
                except KeyError as e:
                    error = f"Error processing odds: {str(e)}"
                    print(f"Error processing odds: {str(e)}")  # Debug log
        except ValueError as e:
            error = f"Invalid input: {str(e)}"
            print(f"ValueError occurred: {str(e)}")  # Debug log
        except Exception as e:
            error = f"An error occurred: {str(e)}"
            print(f"Unexpected error: {str(e)}")  # Debug log

    # Fetch all bets for display
    bets = Bet.query.all()
    bet_data = []
    for bet in bets:
        opponent_username = '-'  # Default if no opponent
        if bet.opponent_id:
            opponent = User.query.get(bet.opponent_id)
            opponent_username = opponent.username if opponent else 'Unknown'
        
        # Get current games from API
        all_games = get_all_games()
        
        # Find the game for this bet
        game = next((g for g in all_games if g['id'] == bet.game_id), None)
        game_info = f"{game['team1']} vs {game['team2']}" if game else "Unknown Game"
        
        bet_data.append({
            'team': bet.team,
            'amount': bet.amount,
            'odds': bet.odds,
            'result_description': bet.result_description,
            'opponent_username': opponent_username,
            'user_id': bet.user_id,
            'game_info': game_info
        })

    return render_template('betting.html', 
                         user=user, 
                         bets=bet_data, 
                         friends=friends_list, 
                         error=error,
                         success=success,
                         games=all_games,
                         api_error=api_error)

# Route to get updated games data (for AJAX updates)
@betting_bp.route('/api/games', methods=['GET'])
def get_games():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    print("API games route accessed")  # Debug log
    all_games = get_all_games()
    print(f"API returning {len(all_games)} games")  # Debug log
    
    return jsonify(all_games)
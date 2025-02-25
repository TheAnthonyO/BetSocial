# Import Flask components for routing, templating, and request handling
from flask import Blueprint, render_template, request, redirect, url_for, session
# Import database and models for user and bet management
from models import db, User, Bet

# Create a Blueprint named 'betting' for betting-related routes
betting_bp = Blueprint('betting', __name__)

# Define a BettingSystem class to encapsulate betting logic
class BettingSystem:
    # Method to place a bet, deducting from bankroll if funds are sufficient
    def place_bet(self, user, team, amount, odds=2.0, bet_type='solo', opponent_id=None):
        if user.bankroll < amount:
            return None  # Return None if insufficient funds
        # Create a new bet record
        bet = Bet(user_id=user.id, team=team, amount=amount, odds=odds, bet_type=bet_type, opponent_id=opponent_id)
        db.session.add(bet)
        # Deduct the bet amount from the user’s bankroll
        user.update_bankroll(-amount)
        db.session.commit()
        return bet  # Return the created bet object

    # Method to settle all pending bets based on a winning team
    def settle_bets(self, winning_team):
        # Loop through all unsettled bets
        for bet in Bet.query.filter_by(result=None).all():
            if bet.team == winning_team:
                # If the bet’s team matches the winner, mark as win and pay out
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

# Instantiate the BettingSystem
betting_system = BettingSystem()

# Static list of NBA games (fictional matchups as of Feb 24, 2025)
NBA_GAMES = [
    {"team1": "Boston Celtics", "team2": "Los Angeles Lakers"},
    {"team1": "Oklahoma City Thunder", "team2": "Denver Nuggets"},
    {"team1": "Cleveland Cavaliers", "team2": "New York Knicks"},
    {"team1": "Philadelphia 76ers", "team2": "Miami Heat"},
    {"team1": "Golden State Warriors", "team2": "Dallas Mavericks"}
]

# Route for the betting page, handling both GET (display) and POST (bet placement)
@betting_bp.route('/betting', methods=['GET', 'POST'])
def betting():
    # Redirect to home if user isn’t logged in
    if 'username' not in session:
        return redirect(url_for('login.home'))
    # Fetch the current user
    user = User.query.filter_by(username=session['username']).first()
    # Convert dynamic friends query to a list to ensure it’s fully loaded
    friends_list = list(user.friends.all())
    error = None
    # Handle POST request (placing a bet)
    if request.method == 'POST':
        team = request.form['team']
        amount = float(request.form['amount'])
        bet_type = request.form.get('bet_type', 'solo')
        odds = 2.0  # Fixed 2x odds for all bets
        # Only set opponent_id for vs_friend bets if friend_id is provided
        opponent_id = int(request.form['friend_id']) if bet_type == 'vs_friend' and 'friend_id' in request.form else None
        bet = betting_system.place_bet(user, team, amount, odds, bet_type, opponent_id)
        if not bet:
            error = "Insufficient funds."
    # Fetch all bets for display
    bets = Bet.query.all()
    # Preprocess bets to include opponent usernames
    bet_data = []
    for bet in bets:
        opponent_username = '-'  # Default if no opponent
        if bet.opponent_id:
            opponent = User.query.get(bet.opponent_id)
            opponent_username = opponent.username if opponent else 'Unknown'
        bet_data.append({
            'team': bet.team,
            'amount': bet.amount,
            'odds': bet.odds,
            'result_description': bet.result_description,
            'opponent_username': opponent_username,
            'user_id': bet.user_id
        })
    # Render betting.html with user, preprocessed bets, friends, error, and NBA games
    return render_template('betting.html', user=user, bets=bet_data, friends=friends_list, error=error, games=NBA_GAMES)

# Route to settle bets, handling both GET (form display) and POST (settlement)
@betting_bp.route('/settle_bets', methods=['GET', 'POST'])
def settle_bets():
    # Redirect to home if user isn’t logged in
    if 'username' not in session:
        return redirect(url_for('login.home'))
    # Handle POST request (settling bets)
    if request.method == 'POST':
        winning_team = request.form['winning_team']
        betting_system.settle_bets(winning_team)
        return redirect(url_for('betting.betting'))
    # If GET, return a simple form to input the winning team
    return '''
    <form method="POST">
        <label>Winning Team:</label>
        <input type="text" name="winning_team" required>
        <button type="submit">Settle Bets</button>
    </form>
    <p><a href="{{ url_for('betting.betting') }}">Back to Betting</a></p>
    '''
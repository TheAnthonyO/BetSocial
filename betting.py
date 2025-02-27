# Import Flask components for routing, templating, and request handling
from flask import Blueprint, render_template, request, redirect, url_for, session
# Import database and models for user and bet management
from models import db, User, Bet

# Create a Blueprint named 'betting' to organize betting-related routes
betting_bp = Blueprint('betting', __name__)

# Define a class to encapsulate betting-related logic
class BettingSystem:
    # Method to place a bet for a user
    def place_bet(self, user, team, amount, odds=2.0, bet_type='solo', opponent_id=None):
        """Place a bet, deducting the amount from the user's bankroll if sufficient funds exist."""
        # Check if the user has enough funds for the bet
        if user.bankroll < amount:
            return None  # Return None to indicate insufficient funds
        # Create a new bet instance with provided details
        bet = Bet(user_id=user.id, team=team, amount=amount, odds=odds, bet_type=bet_type, opponent_id=opponent_id)
        # Add the bet to the database session
        db.session.add(bet)
        # Deduct the bet amount from the user's bankroll
        user.update_bankroll(-amount)
        # Commit the transaction to save the bet and update bankroll
        db.session.commit()
        return bet  # Return the created bet object

    # Method to settle all pending bets based on a winning team
    def settle_bets(self, winning_team):
        """Settle all unresolved bets, updating results and bankrolls based on the winning team."""
        # Iterate over all bets that haven’t been settled yet
        for bet in Bet.query.filter_by(result=None).all():
            if bet.team == winning_team:
                # Mark the bet as a win if the team matches the winning team
                bet.result = 'win'
                # Calculate winnings based on odds (e.g., 2.0 odds doubles the amount)
                winnings = bet.amount * bet.odds
                # Update the user's bankroll with the winnings using modern Session.get
                db.session.get(User, bet.user_id).update_bankroll(winnings)
                # Set a descriptive result string
                bet.result_description = f"Win - {winning_team}"
            else:
                # Mark the bet as a loss if the team doesn’t match
                bet.result = 'lose'
                bet.result_description = f"Loss - {winning_team}"
        # Commit all changes to the database
        db.session.commit()
        # Return the winning team for reference
        return winning_team

# Instantiate the BettingSystem class for use in routes
betting_system = BettingSystem()

# Define a static list of NBA games for betting (fictional matchups as of Feb 24, 2025)
NBA_GAMES = [
    {"team1": "Boston Celtics", "team2": "Los Angeles Lakers"},
    {"team1": "Oklahoma City Thunder", "team2": "Denver Nuggets"},
    {"team1": "Cleveland Cavaliers", "team2": "New York Knicks"},
    {"team1": "Philadelphia 76ers", "team2": "Miami Heat"},
    {"team1": "Golden State Warriors", "team2": "Dallas Mavericks"}
]

# Route to handle the betting page, supporting both GET (display) and POST (bet placement)
@betting_bp.route('/betting', methods=['GET', 'POST'])
def betting():
    """Handle the betting page: display games and history, process new bets."""
    # Redirect to home if the user isn’t logged in
    if 'username' not in session:
        return redirect(url_for('login.home'))
    # Fetch the current user based on session username
    user = User.query.filter_by(username=session['username']).first()
    # Convert the dynamic friends query to a list for template use
    friends_list = list(user.friends.all())
    error = None  # Initialize error message as None
    # Handle form submission for placing a bet
    if request.method == 'POST':
        # Extract bet details from the form
        team = request.form['team']
        amount = float(request.form['amount'])
        bet_type = request.form.get('bet_type', 'solo')  # Default to 'solo' if not specified
        odds = 2.0  # Fixed 2x odds for all bets
        # Set opponent_id only for vs_friend bets if friend_id is provided
        opponent_id = int(request.form['friend_id']) if bet_type == 'vs_friend' and 'friend_id' in request.form else None
        # Attempt to place the bet
        bet = betting_system.place_bet(user, team, amount, odds, bet_type, opponent_id)
        if not bet:
            error = "Insufficient funds."  # Set error if bet placement fails
    # Fetch all bets from the database
    bets = Bet.query.all()
    # Preprocess bets to include opponent usernames for display
    bet_data = []
    for bet in bets:
        opponent_username = '-'  # Default to '-' if no opponent
        if bet.opponent_id:
            # Fetch opponent user using modern Session.get
            opponent = db.session.get(User, bet.opponent_id)
            opponent_username = opponent.username if opponent else 'Unknown'
        # Build a dictionary with bet details for the template
        bet_data.append({
            'team': bet.team,
            'amount': bet.amount,
            'odds': bet.odds,
            'result_description': bet.result_description,
            'opponent_username': opponent_username,
            'user_id': bet.user_id
        })
    # Render the betting page with user data, bets, friends, errors, and games
    return render_template('betting.html', user=user, bets=bet_data, friends=friends_list, error=error, games=NBA_GAMES)

# Route to handle settling bets, supporting both GET (form display) and POST (settlement)
@betting_bp.route('/settle_bets', methods=['GET', 'POST'])
def settle_bets():
    """Handle settling all pending bets based on a user-specified winning team."""
    # Redirect to home if the user isn’t logged in
    if 'username' not in session:
        return redirect(url_for('login.home'))
    # Handle form submission to settle bets
    if request.method == 'POST':
        winning_team = request.form['winning_team']  # Get the winning team from the form
        betting_system.settle_bets(winning_team)  # Settle all bets
        return redirect(url_for('betting.betting'))  # Redirect back to betting page
    # If GET, display a simple form to input the winning team
    return '''
    <form method="POST">
        <label>Winning Team:</label>
        <input type="text" name="winning_team" required>
        <button type="submit">Settle Bets</button>
    </form>
    <p><a href="{{ url_for('betting.betting') }}">Back to Betting</a></p>
    '''
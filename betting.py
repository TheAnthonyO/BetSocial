from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, User, Bet

betting_bp = Blueprint('betting', __name__)

class BettingSystem:
    def place_bet(self, user, team, amount, odds=2.0, bet_type='solo', opponent_id=None):
        if user.bankroll < amount:
            return None
        bet = Bet(user_id=user.id, team=team, amount=amount, odds=odds, bet_type=bet_type, opponent_id=opponent_id)
        db.session.add(bet)
        user.update_bankroll(-amount)
        db.session.commit()
        return bet

    def settle_bets(self, winning_team):
        for bet in Bet.query.filter_by(result=None).all():
            if bet.team == winning_team:
                bet.result = 'win'
                winnings = bet.amount * bet.odds
                User.query.get(bet.user_id).update_bankroll(winnings)
                bet.result_description = f"Win - {winning_team}"
            else:
                bet.result = 'lose'
                bet.result_description = f"Loss - {winning_team}"
        db.session.commit()
        return winning_team

betting_system = BettingSystem()

# List of NBA games (as of Feb 24, 2025, fictional matchups for demo)
NBA_GAMES = [
    {"team1": "Boston Celtics", "team2": "Los Angeles Lakers"},
    {"team1": "Oklahoma City Thunder", "team2": "Denver Nuggets"},
    {"team1": "Cleveland Cavaliers", "team2": "New York Knicks"},
    {"team1": "Philadelphia 76ers", "team2": "Miami Heat"},
    {"team1": "Golden State Warriors", "team2": "Dallas Mavericks"}
]

@betting_bp.route('/betting', methods=['GET', 'POST'])
def betting():
    if 'username' not in session:
        return redirect(url_for('login.home'))
    user = User.query.filter_by(username=session['username']).first()
    error = None
    if request.method == 'POST':
        team = request.form['team']
        amount = float(request.form['amount'])
        bet_type = request.form.get('bet_type', 'solo')
        odds = 2.0  # All odds are 2x
        opponent_id = int(request.form['friend_id']) if bet_type == 'vs_friend' and 'friend_id' in request.form else None
        bet = betting_system.place_bet(user, team, amount, odds, bet_type, opponent_id)
        if not bet:
            error = "Insufficient funds."
    bets = Bet.query.all()
    return render_template('betting.html', user=user, bets=bets, friends=user.friends, error=error, games=NBA_GAMES)

@betting_bp.route('/settle_bets', methods=['GET', 'POST'])
def settle_bets():
    if 'username' not in session:
        return redirect(url_for('login.home'))
    if request.method == 'POST':
        winning_team = request.form['winning_team']
        betting_system.settle_bets(winning_team)
        return redirect(url_for('betting.betting'))
    return '''
    <form method="POST">
        <label>Winning Team:</label>
        <input type="text" name="winning_team" required>
        <button type="submit">Settle Bets</button>
    </form>
    <p><a href="{{ url_for('betting.betting') }}">Back to Betting</a></p>
    '''
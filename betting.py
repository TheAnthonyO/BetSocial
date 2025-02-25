from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, User, Bet
import random

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

    def settle_bets(self):
        winning_team = random.choice(["Team A", "Team B"])
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
        odds = 2.5 if bet_type == 'vs_friend' else 2.0
        opponent_id = int(request.form['friend_id']) if bet_type == 'vs_friend' else None
        bet = betting_system.place_bet(user, team, amount, odds, bet_type, opponent_id)
        if not bet:
            error = "Insufficient funds."
    bets = Bet.query.all()
    return render_template('betting.html', user=user, bets=bets, friends=user.friends, error=error)

@betting_bp.route('/settle_bets')
def settle_bets():
    if 'username' not in session:
        return redirect(url_for('login.home'))
    betting_system.settle_bets()
    return redirect(url_for('betting.betting'))
from flask import Flask, render_template, request, redirect, url_for, session
from models import db, User
from betting import BettingSystem

app = Flask(__name__)
app.secret_key = 'supersecretkey'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fantasy_football.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

betting_system = BettingSystem()

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    user = None
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
    return render_template('index.html', session=session, user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            return "Username already exists."

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('register_success'))

    return '''
    <form method="POST">
        Username: <input type="text" name="username" required><br>
        Password: <input type="password" name="password" required><br>
        <button type="submit">Register</button>
    </form>
    '''

@app.route('/register_success')
def register_success():
    return "<h1>Registration successful!</h1><p>You can now <a href='/'>login</a>.</p>"

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()

    if not user or user.password != password:  # Simple check, adjust later with hashing if needed
        return "Invalid credentials."

    session['username'] = user.username
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/place_bet', methods=['POST'])
def place_bet():
    if 'username' not in session:
        return redirect(url_for('home'))

    user = User.query.filter_by(username=session['username']).first()
    team = request.form['team']
    amount = float(request.form['amount'])

    result = betting_system.place_bet(user, team, amount)
    return result

@app.route('/betting', methods=['GET', 'POST'])
def betting():
    if 'username' not in session:
        return redirect(url_for('home'))

    user = User.query.filter_by(username=session['username']).first()
    error = None

    if request.method == 'POST':
        try:
            team = request.form['team']
            amount = float(request.form['amount'])

            bet = betting_system.place_bet(user, team, amount)
            if bet is None:
                error = "Insufficient bankroll to place this bet."

        except ValueError:
            error = "Invalid input. Please enter a valid number."

    return render_template('betting.html', user=user, bets=betting_system.bets, error=error)

@app.route('/settle_bets')
def settle_bets():
    if 'username' not in session:
        return redirect(url_for('home'))

    winning_team = betting_system.settle_bets()
    return redirect(url_for('betting'))

if __name__ == '__main__':
    app.run(debug=True)

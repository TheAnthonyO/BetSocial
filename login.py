from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, User

login_bp = Blueprint('login', __name__)

@login_bp.route('/')
def home():
    user = None
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
    return render_template('index.html', session=session, user=user)

@login_bp.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if not user or user.password != password:
        return "Invalid credentials."
    session['username'] = user.username
    return redirect(url_for('login.home'))

@login_bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login.home'))

@login_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return "Username already exists."
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login.home'))
    return '''
    <form method="POST">
        Username: <input type="text" name="username" required><br>
        Password: <input type="password" name="password" required><br>
        <button type="submit">Register</button>
    </form>
    '''

@login_bp.route('/deposit_withdraw', methods=['POST'])
def deposit_withdraw():
    if 'username' not in session:
        return redirect(url_for('login.home'))
    user = User.query.filter_by(username=session['username']).first()
    amount = float(request.form['amount'])
    action = request.form['action']
    
    if action == 'deposit':
        user.update_bankroll(amount)
    elif action == 'withdraw':
        if user.bankroll >= amount:
            user.update_bankroll(-amount)
        else:
            return "Insufficient funds for withdrawal."
    
    return redirect(url_for('login.home'))
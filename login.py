# Import necessary Flask components for routing, templating, and request handling
from flask import Blueprint, render_template, request, redirect, url_for, session
# Import database and User model for user management
from models import db, User

# Create a Blueprint named 'login' to organize login-related routes
login_bp = Blueprint('login', __name__)

# Route for the homepage (root URL '/')
@login_bp.route('/')
def home():
    # Initialize user as None (no user logged in by default)
    user = None
    # If a user is logged in (username in session), fetch their details
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
    # Render the index.html template, passing session and user data
    return render_template('index.html', session=session, user=user)

# Route to handle login form submissions (POST only)
@login_bp.route('/login', methods=['POST'])
def login():
    # Get username and password from the form
    username = request.form['username']
    password = request.form['password']
    # Look up the user in the database by username
    user = User.query.filter_by(username=username).first()
    # If user doesn’t exist or password is wrong, return an error message
    if not user or user.password != password:
        return "Invalid credentials."
    # Store username in session to keep user logged in
    session['username'] = user.username
    # Redirect to the homepage after successful login
    return redirect(url_for('login.home'))

# Route to log out the user
@login_bp.route('/logout')
def logout():
    # Remove username from session, effectively logging out the user
    session.pop('username', None)
    # Redirect to the homepage
    return redirect(url_for('login.home'))

# Route for user registration, handling both GET (form display) and POST (form submission)
@login_bp.route('/register', methods=['GET', 'POST'])
def register():
    # If form is submitted (POST request)
    if request.method == 'POST':
        # Get username and password from the form
        username = request.form['username']
        password = request.form['password']
        # Check if username is already taken
        if User.query.filter_by(username=username).first():
            return "Username already exists."
        # Create a new user with the provided credentials
        new_user = User(username=username, password=password)
        # Add the new user to the database session
        db.session.add(new_user)
        # Commit the changes to save the user
        db.session.commit()
        # Redirect to the homepage after registration
        return redirect(url_for('login.home'))
    # If GET request, return a simple HTML form for registration
    return '''
    <form method="POST">
        Username: <input type="text" name="username" required><br>
        Password: <input type="password" name="password" required><br>
        <button type="submit">Register</button>
    </form>
    '''

# Route to handle deposit and withdrawal actions (POST only)
@login_bp.route('/deposit_withdraw', methods=['POST'])
def deposit_withdraw():
    # Ensure user is logged in
    if 'username' not in session:
        return redirect(url_for('login.home'))
    # Fetch the current user
    user = User.query.filter_by(username=session['username']).first()
    # Get the amount and action (deposit or withdraw) from the form
    amount = float(request.form['amount'])
    action = request.form['action']
    
    # If depositing, increase the bankroll
    if action == 'deposit':
        user.update_bankroll(amount)
    # If withdrawing, check funds and decrease bankroll if sufficient
    elif action == 'withdraw':
        if user.bankroll >= amount:
            user.update_bankroll(-amount)
        else:
            return "Insufficient funds for withdrawal."
    
    # Redirect back to the homepage after processing
    return redirect(url_for('login.home'))
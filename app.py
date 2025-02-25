from flask import Flask
from models import db
from login import login_bp
from friends import friends_bp
from betting import betting_bp
import os

# Create a Flask application instance; __name__ tells Flask where to look for templates and static files
app = Flask(__name__)
# Set a secret key for session security (e.g., for login sessions); should be a random, secure value in production
app.secret_key = 'supersecretkey'
# Configure the database URI to use SQLite, storing the file in the 'instance' directory relative to app.py
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'fantasy_football.db')
# Disable SQLAlchemy's modification tracking to save resources (we don’t need it here)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the SQLAlchemy database with the Flask app, linking them together
db.init_app(app)

# Register the login Blueprint, making its routes (e.g., /login, /register) available in the app
app.register_blueprint(login_bp)
# Register the friends Blueprint for friend-related routes (e.g., /friends)
app.register_blueprint(friends_bp)
# Register the betting Blueprint for betting-related routes (e.g., /betting)
app.register_blueprint(betting_bp)

# Create an application context to allow database operations (like creating tables) outside a request
with app.app_context():
    # Create all database tables defined in models.py if they don’t already exist
    db.create_all()

# Check if this script is run directly (not imported), and if so, start the Flask development server
if __name__ == '__main__':
    # Run the app in debug mode (auto-reloads on code changes, shows detailed errors)
    app.run(debug=True)
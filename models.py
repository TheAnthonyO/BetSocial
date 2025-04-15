# Import SQLAlchemy for database management
from flask_sqlalchemy import SQLAlchemy

# Create a SQLAlchemy instance to use throughout the app
db = SQLAlchemy()

# Define the friendship table for many-to-many user relationships
friendship = db.Table('friendship',
    # Column linking user_id to User.id
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    # Column linking friend_id to User.id
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# User model representing a registered user
class User(db.Model):
    # Unique identifier for each user, auto-incremented
    id = db.Column(db.Integer, primary_key=True)
    # Username, must be unique and not null
    username = db.Column(db.String(50), unique=True, nullable=False)
    # Password, stored as plaintext (should be hashed in production)
    password = db.Column(db.String(100), nullable=False)
    # User's betting funds, defaults to 1000
    bankroll = db.Column(db.Float, default=1000.0)
    # Many-to-many relationship with other Users via friendship table
    friends = db.relationship('User', secondary=friendship,
                              primaryjoin=(friendship.c.user_id == id),
                              secondaryjoin=(friendship.c.friend_id == id),
                              backref=db.backref('friend_of', lazy='dynamic'), lazy='dynamic')

    # Method to update the user's bankroll (positive for deposit/win, negative for withdrawal/bet)
    def update_bankroll(self, amount):
        # For withdrawals (positive amount), subtract from bankroll
        if amount > 0:
            self.bankroll -= amount
        # For deposits or winnings (negative amount), add to bankroll
        else:
            self.bankroll += abs(amount)
        
        # Only reset to 500 if bankroll drops to 0 or below due to a bet
        if self.bankroll <= 0 and amount < 0:
            self.bankroll = 500
        db.session.commit()

# Message model for private messages between users
class Message(db.Model):
    # Unique identifier for each message
    id = db.Column(db.Integer, primary_key=True)
    # Foreign key linking to the sender's User.id
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Foreign key linking to the receiver's User.id
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Message content, max 500 characters
    content = db.Column(db.String(500), nullable=False)
    # Timestamp of when the message was sent, defaults to current time
    timestamp = db.Column(db.DateTime, default=db.func.now())

# Bet model representing a user's wager
class Bet(db.Model):
    # Unique identifier for each bet
    id = db.Column(db.Integer, primary_key=True)
    # Foreign key linking to the user who placed the bet
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Team or condition the bet is on (e.g., "Boston Celtics")
    team = db.Column(db.String(50), nullable=False)
    # Amount wagered
    amount = db.Column(db.Float, nullable=False)
    # Odds for the bet, defaults to 2.0 (2x)
    odds = db.Column(db.Float, default=2.0)
    # Result of the bet: 'win', 'lose', or None (pending)
    result = db.Column(db.String(10))  # 'win', 'lose', or None
    # Description of the result (e.g., "Win - Boston Celtics")
    result_description = db.Column(db.String(50), default="Pending")
    # Type of bet: 'solo' or 'vs_friend'
    bet_type = db.Column(db.String(20))  # 'solo', 'vs_friend'
    # Optional foreign key linking to opponent's User.id for vs_friend bets
    opponent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    # ID of the game this bet is associated with
    game_id = db.Column(db.Integer, nullable=True)

# FriendRequest model for managing friend request states
class FriendRequest(db.Model):
    # Unique identifier for each friend request
    id = db.Column(db.Integer, primary_key=True)
    # Foreign key linking to the sender's User.id
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Foreign key linking to the receiver's User.id
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Status of the request: 'pending', 'accepted', 'rejected'
    status = db.Column(db.String(20), default='pending')
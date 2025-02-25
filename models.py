from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

friendship = db.Table('friendship',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    bankroll = db.Column(db.Float, default=1000.0)
    friends = db.relationship('User', secondary=friendship,
                              primaryjoin=(friendship.c.user_id == id),
                              secondaryjoin=(friendship.c.friend_id == id))                      

    def update_bankroll(self, amount):
        self.bankroll += amount
        if self.bankroll <= 0:
            self.bankroll = 500
        db.session.commit()
    
    def reset_bankroll(self):
        self.bankroll = 500
        db.session.commit()

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    odds = db.Column(db.Float, default=2.0)
    result = db.Column(db.String(10))  # 'win', 'lose', or None
    result_description = db.Column(db.String(50), default="Pending")
    bet_type = db.Column(db.String(20))  # 'solo', 'vs_friend'
    opponent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'rejected'


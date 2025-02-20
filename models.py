from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    bankroll = db.Column(db.Float, default=1000.0)

    def update_bankroll(self, amount):
        """ Updates user's bankroll (positive or negative). """
        self.bankroll += amount
        if self.bankroll <= 0:
            self.reset_bankroll()
        db.session.commit()

    def reset_bankroll(self):
        """ Resets bankroll when it reaches 0. """
        self.bankroll = 500
        db.session.commit()

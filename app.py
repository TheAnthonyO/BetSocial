from flask import Flask
from models import db
from login import login_bp
from friends import friends_bp
from betting import betting_bp
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'fantasy_football.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

app.register_blueprint(login_bp)
app.register_blueprint(friends_bp)
app.register_blueprint(betting_bp)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, User, Message

friends_bp = Blueprint('friends', __name__)

@friends_bp.route('/friends', methods=['GET', 'POST'])
def friends():
    if 'username' not in session:
        return redirect(url_for('login.home'))
    user = User.query.filter_by(username=session['username']).first()
    if request.method == 'POST':
        if 'add_friend' in request.form:
            friend_username = request.form['friend_username']
            friend = User.query.filter_by(username=friend_username).first()
            if friend and friend != user and friend not in user.friends:
                user.friends.append(friend)
                db.session.commit()
        elif 'message' in request.form:
            receiver_id = int(request.form['receiver_id'])
            content = request.form['message']
            message = Message(sender_id=user.id, receiver_id=receiver_id, content=content)
            db.session.add(message)
            db.session.commit()
    messages = Message.query.filter((Message.sender_id == user.id) | (Message.receiver_id == user.id)).all()
    return render_template('friends.html', user=user, friends=user.friends, messages=messages)
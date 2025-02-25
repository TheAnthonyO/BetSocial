from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, User, Message, FriendRequest

friends_bp = Blueprint('friends', __name__)

@friends_bp.route('/friends', methods=['GET', 'POST'])
def friends():
    if 'username' not in session:
        return redirect(url_for('login.home'))
    user = User.query.filter_by(username=session['username']).first()
    
    if request.method == 'POST':
        if 'send_request' in request.form:
            friend_username = request.form['friend_username']
            friend = User.query.filter_by(username=friend_username).first()
            if friend and friend != user and friend not in user.friends:
                existing_request = FriendRequest.query.filter_by(sender_id=user.id, receiver_id=friend.id, status='pending').first()
                if not existing_request:
                    friend_request = FriendRequest(sender_id=user.id, receiver_id=friend.id)
                    db.session.add(friend_request)
                    db.session.commit()
        elif 'accept_request' in request.form:
            request_id = int(request.form['request_id'])
            friend_request = FriendRequest.query.get(request_id)
            if friend_request and friend_request.receiver_id == user.id and friend_request.status == 'pending':
                friend_request.status = 'accepted'
                user.friends.append(User.query.get(friend_request.sender_id))
                db.session.commit()
        elif 'message' in request.form:
            receiver_id = int(request.form['receiver_id'])
            content = request.form['message']
            message = Message(sender_id=user.id, receiver_id=receiver_id, content=content)
            db.session.add(message)
            db.session.commit()
    
    pending_requests = FriendRequest.query.filter_by(receiver_id=user.id, status='pending').all()
    # Preprocess pending requests
    pending_request_data = []
    for req in pending_requests:
        sender = User.query.get(req.sender_id)
        pending_request_data.append({
            'id': req.id,
            'sender_username': sender.username if sender else 'Unknown'
        })
    
    messages = Message.query.filter((Message.sender_id == user.id) | (Message.receiver_id == user.id)).all()
    # Preprocess messages
    message_data = []
    for msg in messages:
        sender = User.query.get(msg.sender_id)
        receiver = User.query.get(msg.receiver_id)
        message_data.append({
            'sender_username': sender.username if sender else 'Unknown',
            'receiver_username': receiver.username if receiver else 'Unknown',
            'content': msg.content,
            'timestamp': msg.timestamp,
            'is_from_user': msg.sender_id == user.id,
            'is_to_user': msg.receiver_id == user.id
        })
    
    return render_template('friends.html', user=user, friends=user.friends, messages=message_data, pending_requests=pending_request_data)
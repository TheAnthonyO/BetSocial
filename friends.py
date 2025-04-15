# Import Flask components for routing, templating, and request handling
from flask import Blueprint, render_template, request, redirect, url_for, session
# Import database and models for user, message, and friend request management
from models import db, User, Message, FriendRequest

# Create a Blueprint named 'friends' for friend-related routes
friends_bp = Blueprint('friends', __name__)

# Route for the friends page, handling both GET (display) and POST (actions)
@friends_bp.route('/friends', methods=['GET', 'POST'])
def friends():
    # Redirect to home if user isn't logged in
    if 'username' not in session:
        return redirect(url_for('login.home'))
    # Fetch the current user
    user = User.query.filter_by(username=session['username']).first()
    
    # Handle POST requests (form submissions)
    if request.method == 'POST':
        # If sending a friend request
        if 'send_request' in request.form:
            friend_username = request.form['friend_username']
            friend = User.query.filter_by(username=friend_username).first()
            # Ensure friend exists, isn't the user, and isn't already a friend
            if friend and friend != user and friend not in user.friends:
                # Check for existing pending request
                existing_request = FriendRequest.query.filter_by(sender_id=user.id, receiver_id=friend.id, status='pending').first()
                if not existing_request:
                    # Create and save a new friend request
                    friend_request = FriendRequest(sender_id=user.id, receiver_id=friend.id)
                    db.session.add(friend_request)
                    db.session.commit()
        # If accepting a friend request
        elif 'accept_request' in request.form:
            request_id = int(request.form['request_id'])
            friend_request = FriendRequest.query.get(request_id)
            # Verify the request is for this user and still pending
            if friend_request and friend_request.receiver_id == user.id and friend_request.status == 'pending':
                friend = User.query.get(friend_request.sender_id)
                # Only add to friends if not already friends
                if friend and friend not in user.friends:
                    friend_request.status = 'accepted'
                    # Add friend to user's friends list
                    user.friends.append(friend)
                    # Add user to friend's friends list
                    friend.friends.append(user)
                    db.session.commit()
                else:
                    # If already friends, just mark the request as accepted
                    friend_request.status = 'accepted'
                    db.session.commit()
        # If sending a message
        elif 'message' in request.form:
            receiver_id = int(request.form['receiver_id'])
            content = request.form['message']
            # Create and save a new message
            message = Message(sender_id=user.id, receiver_id=receiver_id, content=content)
            db.session.add(message)
            db.session.commit()
    
    # Fetch all pending friend requests for the current user
    pending_requests = FriendRequest.query.filter_by(receiver_id=user.id, status='pending').all()
    # Preprocess pending requests into a list of dictionaries with sender usernames
    pending_request_data = []
    for req in pending_requests:
        sender = User.query.get(req.sender_id)
        pending_request_data.append({
            'id': req.id,
            'sender_username': sender.username if sender else 'Unknown'
        })
    
    # Fetch all messages involving the current user (sent or received)
    messages = Message.query.filter((Message.sender_id == user.id) | (Message.receiver_id == user.id)).all()
    # Preprocess messages into a list of dictionaries with usernames and flags
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
    
    # Render the friends.html template with user, friends, messages, and pending requests
    return render_template('friends.html', user=user, friends=user.friends, messages=message_data, pending_requests=pending_request_data)
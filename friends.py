# Import Flask components for routing, templating, and request handling
from flask import Blueprint, render_template, request, redirect, url_for, session
# Import database and models for user, message, and friend request management
from models import db, User, Message, FriendRequest

# Create a Blueprint named 'friends' for friend-related routes
friends_bp = Blueprint('friends', __name__)

# Route for the friends page, handling both GET (display) and POST (actions)
@friends_bp.route('/friends', methods=['GET', 'POST'])
def friends():
    #Handle the friends page: display friends, requests, messages, and process actions.
    # Redirect to home if the user isn’t logged in
    if 'username' not in session:
        return redirect(url_for('login.home'))
    # Fetch the current user based on session username
    user = User.query.filter_by(username=session['username']).first()
    
    # Handle POST requests for sending requests, accepting requests, or sending messages
    if request.method == 'POST':
        # Handle sending a friend request
        if 'send_request' in request.form:
            friend_username = request.form['friend_username']  # Get the target username
            friend = User.query.filter_by(username=friend_username).first()  # Find the user
            # Ensure the friend exists, isn’t the current user, and isn’t already a friend
            if friend and friend != user and friend not in user.friends:
                # Check for an existing pending request to avoid duplicates
                existing_request = FriendRequest.query.filter_by(sender_id=user.id, receiver_id=friend.id, status='pending').first()
                if not existing_request:
                    # Create and save a new friend request
                    friend_request = FriendRequest(sender_id=user.id, receiver_id=friend.id)
                    db.session.add(friend_request)
                    db.session.commit()
        # Handle accepting a friend request
        elif 'accept_request' in request.form:
            request_id = int(request.form['request_id'])  # Get the request ID from the form
            # Fetch the friend request using modern Session.get
            friend_request = db.session.get(FriendRequest, request_id)
            # Verify the request exists, is for this user, and is still pending
            if friend_request and friend_request.receiver_id == user.id and friend_request.status == 'pending':
                # Fetch the sender using modern Session.get
                friend = db.session.get(User, friend_request.sender_id)
                # Add the friend only if they’re not already in the friends list
                if friend and friend not in user.friends:
                    friend_request.status = 'accepted'  # Mark the request as accepted
                    user.friends.append(friend)  # Add the sender to the user’s friends
                    db.session.commit()
                else:
                    # If already friends, just mark as accepted without adding again
                    friend_request.status = 'accepted'
                    db.session.commit()
        # Handle sending a message
        elif 'message' in request.form:
            receiver_id = int(request.form['receiver_id'])  # Get the recipient’s ID
            content = request.form['message']  # Get the message content
            # Create and save a new message
            message = Message(sender_id=user.id, receiver_id=receiver_id, content=content)
            db.session.add(message)
            db.session.commit()
    
    # Fetch all pending friend requests for the current user
    pending_requests = FriendRequest.query.filter_by(receiver_id=user.id, status='pending').all()
    # Preprocess pending requests into a list of dictionaries with sender usernames
    pending_request_data = []
    for req in pending_requests:
        # Fetch the sender using modern Session.get
        sender = db.session.get(User, req.sender_id)
        pending_request_data.append({
            'id': req.id,  # Request ID for acceptance form
            'sender_username': sender.username if sender else 'Unknown'  # Sender’s username
        })
    
    # Fetch all messages sent or received by the current user
    messages = Message.query.filter((Message.sender_id == user.id) | (Message.receiver_id == user.id)).all()
    # Preprocess messages into a list of dictionaries with usernames and flags
    message_data = []
    for msg in messages:
        # Fetch sender and receiver using modern Session.get
        sender = db.session.get(User, msg.sender_id)
        receiver = db.session.get(User, msg.receiver_id)
        message_data.append({
            'sender_username': sender.username if sender else 'Unknown',  # Sender’s username
            'receiver_username': receiver.username if receiver else 'Unknown',  # Receiver’s username
            'content': msg.content,  # Message text
            'timestamp': msg.timestamp,  # When the message was sent
            'is_from_user': msg.sender_id == user.id,  # Flag if sent by current user
            'is_to_user': msg.receiver_id == user.id  # Flag if received by current user
        })
    
    # Render the friends page with user data, friends list, messages, and pending requests
    return render_template('friends.html', user=user, friends=user.friends, messages=message_data, pending_requests=pending_request_data)
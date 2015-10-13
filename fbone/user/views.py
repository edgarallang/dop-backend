# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
import jwt
import json
import requests
from flask import Blueprint, request, jsonify
from flask import current_app as app
from flask.ext.login import login_required, current_user
from jwt import DecodeError, ExpiredSignature
from .models import *
from ..extensions import db
from juggernaut import Juggernaut
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, close_room, disconnect

user = Blueprint('user', __name__, url_prefix='/api/user')
socketio = SocketIO(app)



def parse_token(req, token_index):
    if token_index:
        token = req.headers.get('Authorization').split()[0]
    else:
        token = req.headers.get('Authorization').split()[1]
    return jwt.decode(token, app.config['TOKEN_SECRET'])

def create_token(user):
    payload = {
        'id': user.user_id,
        'iat': datetime.now(),
        'exp': datetime.now() + timedelta(days=14)
    }

    token = jwt.encode(payload, app.config['TOKEN_SECRET'])

    return token.decode('unicode_escape')

@login_required
def index():
    if not current_user.is_authenticated():
        abort(403)
    return render_template('user/index.html', user=current_user)


def get_friends_by_id(userId):
    friends_query = 'SELECT COUNT(*) as total FROM friends \
                 INNER JOIN users ON (friends.user_one_id = user_id  AND friends.user_one_id != %d) \
                 OR (friends.user_two_id = user_id  AND friends.user_two_id != %d) \
                 INNER JOIN users_image ON (friends.user_one_id = users_image.user_id AND friends.user_one_id != %d)\
                 OR (friends.user_two_id = users_image.user_id AND friends.user_two_id != %d) \
                 WHERE (user_one_id = %d OR user_two_id = %d)\
                 AND operation_id = 1' % (userId, userId, userId, userId, userId, userId)
    result = db.engine.execute(friends_query)
    total_friends = friends_count_schema.dump(result).data

    return total_friends

@user.route('/<int:userId>/profile', methods=['GET'])
def profile(userId):
    query = "SELECT users.user_id, users.names, users.surnames, users.birth_date, users.facebook_key, users.google_key,\
                    users.twitter_key, users_image.main_image, users_image.user_image_id\
                    FROM users INNER JOIN users_image ON users.user_id = users_image.user_id\
                    WHERE users.user_id = %d" % (userId)

    total_friends = get_friends_by_id(userId)
    
    

    result = db.engine.execute(query)
    user_with_image = user_joined_schema.dump(result).data

    return jsonify({'data': user_with_image,'friends':total_friends})

@user.route('/<int:user_id>/avatar/<path:filename>')
@login_required
def avatar(user_id, filename):
    dir_path = os.path.join(APP.config['UPLOAD_FOLDER'], 'user_%s' % user_id)
    return send_from_directory(dir_path, filename, as_attachment=True)

@user.route('/login/facebook', methods=['POST'])
def facebook_login():
    facebookUser = User.query.filter_by(facebook_key = request.json['facebook_key']).first()
    if not facebookUser:
        facebookUser = User(names = request.json['names'],
                            surnames = request.json['surnames'],
                            birth_date = request.json['birth_date'],
                            facebook_key = request.json['facebook_key'])
        db.session.add(facebookUser)
        db.session.commit()

        userSession = UserSession(user_id=facebookUser.user_id,
                                  email=request.json['email'])
        db.session.add(userSession)
        db.session.commit()

        userImage = UserImage(user_id=facebookUser.user_id,
                              main_image=request.json['main_image'])
        db.session.add(userImage)
        db.session.commit()

    token = create_token(facebookUser)

    return jsonify(token=token)

@user.route('/login/twitter', methods=['POST'])
def twitter_login():
    twitterUser = User.query.filter_by(twitter_key = request.json['twitter_key']).first()
    if not twitterUser:
        twitterUser = User(names = request.json['names'],
                            surnames = request.json['surnames'],
                            birth_date = request.json['birth_date'],
                            twitter_key = request.json['twitter_key'])
        db.session.add(twitterUser)
        db.session.commit()

        userSession = UserSession(user_id=twitterUser.user_id)
        db.session.add(userSession)

        userImage = UserImage(user_id=twitterUser.user_id,
                              main_image=request.json['main_image'])
        db.session.add(userImage)
        db.session.commit()
    token = create_token(twitterUser)

    return jsonify(token=token)

@user.route('/login/google', methods=['POST'])
def google_login():
    googleUser = User.query.filter_by(google_key = request.json['google_key']).first()
    if not googleUser:
        googleUser = User(names = request.json['names'],
                            surnames = request.json['surnames'],
                            birth_date = request.json['birth_date'],
                            google_key = request.json['google_key'])
        db.session.add(googleUser)
        db.session.commit()

        userSession = UserSession(user_id=googleUser.user_id)
        db.session.add(userSession)
        db.session.commit()

        userSession = UserSession(user_id=googleUser.user_id,
                                  email=request.json['email'])
        db.session.add(userSession)

        userImage = UserImage(user_id=googleUser.user_id,
                              main_image=request.json['main_image'])
        db.session.add(userImage)
        db.session.commit()

    token = create_token(googleUser)

    return jsonify(token=token)

@user.route('/friends/get', methods = ['GET'])
def get_friends():
    if request.headers.get('Authorization'):
        payload = parse_token(request, True)

        user_id = User.query.get(payload['id']).user_id
        
        query = 'SELECT * FROM friends \
                 INNER JOIN users ON (friends.user_one_id = user_id  AND friends.user_one_id != %d) \
                 OR (friends.user_two_id=user_id  AND friends.user_two_id!=%d) \
                 INNER JOIN users_image ON (friends.user_one_id = users_image.user_id AND friends.user_one_id != %d)\
                 OR (friends.user_two_id = users_image.user_id AND friends.user_two_id != %d) \
                 WHERE (user_one_id = %d OR user_two_id = %d)\
                 AND operation_id = 1' % (user_id, user_id, user_id, user_id, user_id, user_id)

        friends = db.engine.execute(query)
        friends_list = user_join_friends.dump(friends)
        return jsonify({'data': friends_list.data})
    return jsonify({'message': 'Oops! algo salió mal :('})

@user.route('/friends/add', methods=['POST'])
def add_friend():
    if request.headers.get('Authorization'):
        payload = parse_token(request, True)

        user_id = User.query.get(payload['id']).user_id

        friendsRelationship  = Friends(user_one_id = user_id,
                                       user_two_id = request.json['user_two_id'],
                                       operation_id = 0,
                                       launcher_user_id = user_id)

        db.session.add(friendsRelationship)
        db.session.commit()

        return jsonify({'data': 'Agregado correctamente'})

    return jsonify({'message': 'Oops! algo salió mal :('})

@user.route('/friends/accept', methods=['PUT'])
def accept_friend():
    if request.headers.get('Authorization'):
        payload = parse_token(request, True)

        user_id = User.query.get(payload['id']).user_id

        friendsRelationship = Friends.query.filter_by(friends_id=request.json['friends_id']).first()

        friendsRelationship.operation_id = 1
        friendsRelationship.launcher_user_id = user_id

        db.session.commit()
        
        return jsonify({'data': 'Agregado correctamente'})

    return jsonify({'message': 'Oops! algo salió mal :('})

@user.route('/friends/decline', methods=['PUT'])
def decline_friend():
    if request.headers.get('Authorization'):
        payload = parse_token(request, True)

        user_id = User.query.get(payload['id']).user_id

        friendsRelationship = Friends.query.filter_by(friends_id=request.json['friends_id']).first()

        friendsRelationship.operation_id = 2
        friendsRelationship.launcher_user_id = user_id

        db.session.commit()

        return jsonify({'data': 'Usuario rechazado'})

    return jsonify({'message': 'Oops! algo salió mal :('})

@user.route('/friends/block', methods=['PUT'])
def block_friend():
    if request.headers.get('Authorization'):
        payload = parse_token(request, True)

        user_id = User.query.get(payload['id']).user_id

        friendsRelationship = Friends.query.filter_by(friends_id=request.json['friends_id']).first()

        friendsRelationship.operation_id = 3
        friendsRelationship.launcher_user_id = user_id

        db.session.commit()

        return jsonify({'data': 'Usuario bloqueado'})

    return jsonify({'message': 'Oops! algo salió mal :('})

@user.route('/friends/delete', methods=['PUT'])
def delete_friend():
    if request.headers.get('Authorization'):
        payload = parse_token(request, True)

        friendsRelationship = Friends.query.filter_by(friends_id=request.json['friends_id']).first()

        db.session.delete(friendsRelationship)
        
        db.session.commit()

        return jsonify({'data': 'Usuario eliminado'})

    return jsonify({'message': 'Oops! algo salió mal :('})

@user.route('/<int:user_id>/profile/get', methods=['GET'])
def get_profile(user_id):    
    query = 'SELECT users.names,users.surnames,users.twitter_key, users.facebook_key, users.google_key, users.user_id,\
                    users.birth_date, users_image.main_image FROM users\
             INNER JOIN users_image ON users.user_id = users_image.user_id WHERE users.user_id = %d' % user_id

    friends = db.engine.execute(query)
    friends_list = user_joined_schema.dump(friends)
    return jsonify({'data': friends_list.data})



@socketio.on('my event', namespace='/test')
def test_message(message):
    emit('my response', {'data': message['data']})

@socketio.on('my broadcast event', namespace='/test')
def test_message(message):
    emit('my response', {'data': message['data']}, broadcast=True)

@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')
 

# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
import jwt
import json
import requests
from flask import Blueprint, request, jsonify, session
from flask import current_app as app
from flask.ext.login import login_required, current_user
from flask.ext.socketio import SocketIO, send, emit, join_room, leave_room
from jwt import DecodeError, ExpiredSignature
from .models import *
from ..extensions import db, socketio
from juggernaut import Juggernaut
from gevent import socket, monkey

monkey.patch_all()

notification = Blueprint('notification', __name__, url_prefix='/api/notification')




def parse_token(req, token_index):
    if token_index:
        token = req.headers.get('Authorization').split()[0]
    else:
        token = req.headers.get('Authorization').split()[1]
    return jwt.decode(token, app.config['TOKEN_SECRET'])

def parse_token_socket(token):
    return jwt.decode(token, app.config['TOKEN_SECRET'])

def create_token(user):
    payload = {
        'id': user.user_id,
        'iat': datetime.now(),
        'exp': datetime.now() + timedelta(days=14)
    }

    token = jwt.encode(payload, app.config['TOKEN_SECRET'])

    return token.decode('unicode_escape')

@notification.route('/<int:user_id>/profile/get', methods=['GET'])
def get_profile(user_id):    
    query = 'SELECT users.names,users.surnames,users.twitter_key, users.facebook_key, users.google_key, users.user_id,\
                    users.birth_date, users_image.main_image FROM users\
             INNER JOIN users_image ON users.user_id = users_image.user_id WHERE users.user_id = %d' % user_id

    friends = db.engine.execute(query)
    friends_list = user_joined_schema.dump(friends)
    return jsonify({'data': friends_list.data})

@notification.route('/sslinfo')
def sslinfo():
    return """I know the following things about the certificate you provided:
    Host: {}
    X-SSL-Verified: {}
    X-SSL-DN: {}
    X-SSL-Client-Cert: {}
    """.format(
        request.headers.get('Host'),
        request.headers.get('X-SSL-Verified'),
        request.headers.get('X-SSL-DN'),
        request.headers.get('X-SSL-Client-Cert'))

@socketio.on('join_room', namespace='/app')
def join_room(message):
    payload = parse_token_socket(message)
    session["id"] = payload["id"]
    room = session["id"]
    print room
    join_room("hola")

    notifications = db.engine.execute('SELECT * FROM notifications WHERE user_id = %d AND readed = 0' % (payload['id']))


    notifications_list = notifications_schema.dump(notifications)

    emit('my response', {'data': notifications_list.data}, room = room)
    
    print room

@socketio.on('my broadcast event', namespace='/app')
def test_message(message):
    print "test"
    #emit('my response', {'data': message['data']}, broadcast=True)

@socketio.on('connect', namespace='/app')
def test_connect():
    #room = session["token"]
    #join_room(session["id"])
    #send(' has entered the room.', room=session["id"])
    print "conectado "
    #emit('my response', {'data': 'Connected'})

@socketio.on('disconnect', namespace='/app')
def test_disconnect():
    leave_room(session["id"])
    print('Client disconnected')
 

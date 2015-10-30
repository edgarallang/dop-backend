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

def send_notification(event,message,namespace,room):
    socketio.emit(event,{'data': message}, namespace='/app',room=liked_user.user_id)



@notification.route('/<int:user_id>/profile/get', methods=['GET'])
def get_profile(user_id):    
    query = 'SELECT users.names,users.surnames,users.twitter_key, users.facebook_key, users.google_key, users.user_id,\
                    users.birth_date, users_image.main_image FROM users\
             INNER JOIN users_image ON users.user_id = users_image.user_id WHERE users.user_id = %d' % user_id

    friends = db.engine.execute(query)
    friends_list = user_joined_schema.dump(friends)
    return jsonify({'data': friends_list.data})

@notification.route('/set/read', methods = ['PUT'])
def set_read():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        Notification.query.filter_by(user_id=payload['id']).update({"read": "true"})

        db.session.commit()
        return jsonify({'message': 'Notificaciones leidas'})

    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})



@notification.route('/all/get', methods=['GET'])
def get_notifications():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        notifications_query = "SELECT notifications.notification_id,notifications.type, launcher_user.names AS "+"launcher_name"+",\
                                launcher_user.surnames AS "+"launcher_surnames"+",launcher_user.user_id AS "+"launcher_id"+",friends.operation_id AS "+"friendship_status"+",\
                                branches.name AS "+"newsfeed_activity"+", notifications.read FROM notifications\
                                LEFT JOIN clients_coupon ON notifications.object_id = clients_coupon.clients_coupon_id AND notifications.type= 'newsfeed'\
                                LEFT JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id\
                                LEFT JOIN branches ON coupons.branch_id = branches.branch_id\
                                LEFT JOIN friends ON notifications.object_id = friends.friends_id AND notifications.type= 'friend'\
                                INNER JOIN users AS launcher_user ON notifications.launcher_id = launcher_user.user_id \
                                WHERE notifications.user_id = %d ORDER BY notification_date DESC LIMIT 11" % (payload['id'])
        notifications = db.engine.execute(notifications_query)

        notifications_list = notifications_schema.dump(notifications)

        return jsonify({'data': notifications_list.data})

    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@notification.route('/all/offset/get/', methods=['GET'])
def get_notifications_offset():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        offset = request.args.get('offset')

        #notification_id = request.args.get('notification_id')

        notifications_query = "SELECT notifications.notification_id,notifications.type, launcher_user.names AS "+"launcher_name"+",\
                                launcher_user.surnames AS "+"launcher_surnames"+",launcher_user.user_id AS "+"launcher_id"+",friends.operation_id AS "+"friendship_status"+",\
                                branches.name AS "+"newsfeed_activity"+", notifications.read FROM notifications\
                                LEFT JOIN clients_coupon ON notifications.object_id = clients_coupon.clients_coupon_id AND notifications.type= 'newsfeed'\
                                LEFT JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id\
                                LEFT JOIN branches ON coupons.branch_id = branches.branch_id\
                                LEFT JOIN friends ON notifications.object_id = friends.friends_id AND notifications.type= 'friend'\
                                INNER JOIN users AS launcher_user ON notifications.launcher_id = launcher_user.user_id \
                                WHERE notifications.user_id = %d ORDER BY notification_date DESC LIMIT 11 OFFSET %s " % (payload['id'], offset)
        notifications = db.engine.execute(notifications_query)

        notifications_list = notifications_schema.dump(notifications)

        return jsonify({'data': notifications_list.data})

    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@socketio.on('join room', namespace='/app')
def on_join_room(message):
    payload = parse_token_socket(message)
    session["id"] = payload["id"]
    room = session["id"]
    join_room(room)

    #notifications = db.engine.execute('SELECT * FROM notifications WHERE user_id = %d AND readed = 0' % (payload['id']))


    #notifications_list = notifications_schema.dump(notifications)

    #emit('my response', {'data': notifications_list.data}, broadcast = True)
    
    #print room

@socketio.on('leave')
def on_leave(data):
    room = session['id']
    leave_room(room)

@socketio.on('notification', namespace='/app')
def test_message(message):
    emit('my response', {'data': 'data'}, broadcast = True)
    print "test"
    #emit('my response', {'data': message['data']}, broadcast=True)

@socketio.on('connect', namespace='/app')
def test_connect():
    print "conectado "
    #emit('my response', {'data': 'Connected'})

@socketio.on('disconnect', namespace='/app')
def test_disconnect():
    print('Client disconnected')
 

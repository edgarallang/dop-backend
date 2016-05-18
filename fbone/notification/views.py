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
from ..user import *
from ..extensions import db, socketio, client
from juggernaut import Juggernaut
from gevent import socket, monkey
from flask_pushjack import FlaskAPNS

# config = {
#     'APNS_CERTIFICATE': '../../certs/push.pem>'
# }



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

#def send_notification(event,message,namespace,room):
#    socketio.emit(event,{'data': message}, room=liked_user.user_id)

def send_notification(device_token, notification_data):
    options = { "sound": "default" ,"badge": 0,"extra": notification_data }

    if notification_data['data']['type'] == 'user_like':
        message = 'A '+notification_data['data']['launcher_names'] + ' le ha gustado tu actividad.'
    if notification_data['data']['type'] == 'now_friends':
        message = notification_data['data']['launcher_names'] + ' ahora te sigue.'
    if notification_data['data']['type'] == 'pending_friends':
        message = notification_data['data']['launcher_names'] + ' quiere seguirte.'
    if notification_data['data']['type'] == 'friend_accepted':
        message = 'Ahora sigues a ' + notification_data['data']['launcher_names'] + '.'

    res = client.send(device_token, message, **options)

    return jsonify({'data': "Éxito"})

@notification.route('/push/test/global/<string:message>', methods=['GET'])
def push_test_global(message):
    users_list = User.query.filter(User.device_token!=None)
    token_list = device_tokens_schema.dump(users_list)

    token_list_data = token_list.data

    tokens = []

    for key in token_list_data:
        tokens.append(key['device_token'])

    #token = '1124931f005c00b7ce00c4f76d6c75589b37680706190098939ccf7fbd244909'

    notification_data = { "data": {
                                "object_id": 5,
                                "type": "branch"
                            }
                         }

    options = { "sound": "default" ,"badge": 0,"extra": notification_data }

    # Send to single device.
    res = client.send(tokens, message, **options)
    # List of all tokens sent.
    #res.tokens
    # List of any subclassed APNSServerError objects.
    #print res.errors
    # Dict mapping token => APNSServerError.
    #print res.token_errors
    # Send to multiple devices.
    #client.send([token], alert, **options)
    # Get expired tokens.
    #expired_tokens = client.get_expired_tokens()
    return jsonify({'data': tokens})

@notification.route('/test/<int:user_id>', methods=['GET'])
def test_notification(user_id):
    socketio.emit('notification',{'data': 'friend'}, room = user_id)
    print("send")
    return jsonify({'data': 'exito'})

@notification.route('/test/global', methods=['GET'])
def test_global_notification():
    socketio.emit('notification',{'data': 'friend'}, broadcast = True)
    return jsonify({'data': 'exito'})

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
        notification_id = request.json['notification_id']

        Notification.query.filter_by(notification_id=notification_id).update({"read": "true"})

        db.session.commit()
        return jsonify({'message': 'Notificacion leida'})

    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})



@notification.route('/all/get', methods=['GET'])
def get_notifications():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        notifications_query = "SELECT notifications.notification_id, notifications.object_id, notifications.type, launcher_user.names AS "+"launcher_name"+",\
                                launcher_user.surnames AS "+"launcher_surnames"+",launcher_user.user_id AS "+"launcher_id"+",friends.operation_id AS "+"friendship_status"+",\
                                branches.name AS "+"newsfeed_activity"+", branches.company_id, branches.branch_id, notifications.read, notifications.notification_date,users_image.main_image AS "+"user_image"+", friends.launcher_user_id AS "+"launcher_friend"+" FROM notifications\
                                LEFT JOIN clients_coupon ON notifications.object_id = clients_coupon.clients_coupon_id AND notifications.type= 'newsfeed'\
                                LEFT JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id\
                                LEFT JOIN branches ON coupons.branch_id = branches.branch_id\
                                LEFT JOIN friends ON notifications.object_id = friends.friends_id AND notifications.type= 'friend' AND friends.operation_id<2\
                                LEFT JOIN users_image ON notifications.launcher_id = users_image.user_id\
                                INNER JOIN users AS launcher_user ON notifications.launcher_id = launcher_user.user_id \
                                WHERE notifications.user_id = %d ORDER BY notification_date DESC LIMIT 11" % (payload['id'])

        notifications = db.engine.execute(notifications_query)
        notifications_list = notifications_schema.dump(notifications)

        print notifications_list.data

        return jsonify({'data': notifications_list.data})


    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@notification.route('/all/offset/get/', methods=['GET'])
def get_notifications_offset():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        offset = request.args.get('offset')

        #notification_id = request.args.get('notification_id')

        notifications_query = "SELECT notifications.notification_id,notifications.object_id, notifications.type, launcher_user.names AS "+"launcher_name"+",\
                                launcher_user.surnames AS "+"launcher_surnames"+",launcher_user.user_id AS "+"launcher_id"+",friends.operation_id AS "+"friendship_status"+",\
                                branches.name AS "+"newsfeed_activity"+", branches.company_id, branches.branch_id, notifications.read, notifications.notification_date,users_image.main_image AS "+"user_image"+", friends.launcher_user_id AS "+"launcher_friend"+" FROM notifications\
                                LEFT JOIN clients_coupon ON notifications.object_id = clients_coupon.clients_coupon_id AND notifications.type= 'newsfeed'\
                                LEFT JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id\
                                LEFT JOIN branches ON coupons.branch_id = branches.branch_id\
                                LEFT JOIN friends ON notifications.object_id = friends.friends_id AND notifications.type= 'friend'\
                                LEFT JOIN users_image ON notifications.launcher_id = users_image.user_id \
                                INNER JOIN users AS launcher_user ON notifications.launcher_id = launcher_user.user_id \
                                WHERE notifications.user_id = %d ORDER BY notification_date DESC LIMIT 11 OFFSET %s " % (payload['id'], offset)
        notifications = db.engine.execute(notifications_query)

        notifications_list = notifications_schema.dump(notifications)

        print notifications_list.data
        return jsonify({'data': notifications_list.data})

    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@socketio.on('joinRoom')
def on_join_room(message):
    payload = parse_token_socket(message)
    session["id"] = payload["id"]
    room = session["id"]
    join_room(room)
    emit('joined', {'data': 'Joined to room'}, room = room)
    return jsonify({'message': 'Todo bien'})

@socketio.on('leave')
def on_leave(data):
    room = session['id']
    leave_room(room)

@socketio.on('notification')
def test_message(message):
    emit('my response', {'data': 'data'}, broadcast = True)
    return jsonify({'message': 'Todo bien'})

@socketio.on('connect')
def test_connect():
    return jsonify({'message': 'Todo bien'})

@socketio.on('disconnect')
def test_disconnect():
    return jsonify({'message': 'Todo bien'})

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
from ..extensions import db, socketio, apns_client, gcm_client
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

def send_notification(device_token, notification_data, device_os):
    if notification_data['data']['type'] == 'user_like':
        message = 'A '+notification_data['data']['launcher_names'] + ' le ha gustado tu actividad.'
    if notification_data['data']['type'] == 'now_friends':
        message = notification_data['data']['launcher_names'] + ' ahora te sigue.'
    if notification_data['data']['type'] == 'pending_friends':
        message = notification_data['data']['launcher_names'] + ' quiere seguirte.'
    if notification_data['data']['type'] == 'friend_accepted':
        message = 'Ahora sigues a ' + notification_data['data']['launcher_names'] + '.'

    if device_os == 'ios':
        options = { "sound": "default" ,"badge": 0,"extra": notification_data }
        res = apns_client.send(device_token, message, **options)
        return jsonify({'message': 'success'})
    else:
        options = { "notification": { "body": message, "title":"dop", "icon":"ic_stat_dop" }}
        res = gcm_client.send(device_token, message, **options)
        return jsonify({'message': 'success'})

    return jsonify({'message': 'error'})

@notification.route('/push/to', methods=['POST'])
def push_to():
    message = request.json['message']

    notification_data = { "data": {
                                "object_id": 108,
                                "type": "branch"
                            }
                         }
    options = { "sound": "default", "badge": 0, "extra": notification_data }

    if 'ios_tokens' in request.json:
        ios_res = apns_client.send(request.json['ios_tokens'], message, **options)
    
    if 'android_tokens' in request.json:
        android_res = gcm_client.send(request.json['android_tokens'], message)

    return jsonify({'ios': ios_res.tokens, 'ios_failure': ios_res.errors, 'android': android_res.successes, 'android_failure':android_res.failures})

@notification.route('/push/to/all', methods=['POST'])
def push_to_all():
    message = request.json['message']

    extra_query = ''
    if request.json['adults_only']==True:
        extra_query = 'AND adult=true'

    ios = "SELECT * FROM users \
             WHERE device_token!='' AND device_os='ios' %s" % (extra_query) 
    ios_users = db.engine.execute(ios)
    ios_token_list = device_tokens_schema.dump(ios_users)
    ios_token_list_data = ios_token_list.data
    ios_tokens = []
    for key in ios_token_list_data:
        ios_tokens.append(key['device_token'])


    android = "SELECT * FROM users \
             WHERE device_token!='' AND device_os='android' %s" % (extra_query) 
    android_users = db.engine.execute(android)
    android_token_list = device_tokens_schema.dump(android_users)
    android_token_list_data = android_token_list.data
    android_tokens = []
    for key in android_token_list_data:
        android_tokens.append(key['device_token'])


    notification_data = { "data": {
                                "object_id": 108,
                                "type": "branch"
                            }
                         }
    options = { "sound": "default", "badge": 0, "extra": notification_data }
    

    # Send to single device.
    ios_res = apns_client.send(ios_tokens, message, **options)
    android_res = gcm_client.send(android_tokens, message)


    #users_list = notifications_schema.dump(notifications)

    return jsonify({'ios': ios_res.tokens, 'ios_failure': ios_res.errors, 'android': android_res.successes, 'android_failure':android_res.failures})
@notification.route('/push/like', methods=['POST'])
def like_push_notification():
    if request.headers.get('Authorization'):
        payload = parse_token(request, True)
        user_to_notify = request.json['user_two_id']
        user_two = User.query.get(user_to_notify)
        launcher_user_data = User.query.get(payload['id'])
        message = 'A '+ launcher_user_data.names + ' le ha gustado tu actividad.'

        notification_data = { "data": {
                                    "object_id": user_to_notify,
                                    "type": "user_like",
                                    "launcher_names": launcher_user_data.names
                                }
                             }

        if user_two.device_os == 'ios':
            options = { "sound": "default", "badge": 0,"extra": notification_data }
            res = apns_client.send(user_two.device_token, message, **options)
            return jsonify({'message': 'success'})
        else:
            options = { "notification": { "body": message, "title":"dop", "icon":"ic_stat_dop" }}
            res = gcm_client.send(user_two.device_token, message, **options)
            return jsonify({'message': 'success'})
    return jsonify({'message': 'error'})


@notification.route('/push/follow', methods=['POST'])
def follow_push_notification():
    if request.headers.get('Authorization'):
        payload = parse_token(request, True)

        user_to_add = request.json['user_two_id']
        user_two = User.query.get(user_to_add)
        friendsRelationship = Friends.query.filter(((Friends.user_one_id == payload['id']) & (Friends.user_two_id == user_to_add))).first()
        launcher_user_data = User.query.get(payload['id'])
        notification_type = ''
        if user_two.privacy_status == 0:
            operation_id = 1
            notification_type = 'now_friends'
        elif user_two.privacy_status == 1:
            operation_id = 0
            notification_type = 'pending_friends'
        notification_data = { "data": {
                                    "object_id": friendsRelationship.friends_id,
                                    "type": notification_type,
                                    "launcher_names": launcher_user_data.names
                                }
                             }
        if user_two.device_token != None  and user_two.device_token != "":
            # send_notification(user_two.device_token, notification_data, user_two.device_os)

            if notification_data['data']['type'] == 'user_like':
                message = 'A '+notification_data['data']['launcher_names'] + ' le ha gustado tu actividad.'
            if notification_data['data']['type'] == 'now_friends':
                message = notification_data['data']['launcher_names'] + ' ahora te sigue.'
            if notification_data['data']['type'] == 'pending_friends':
                message = notification_data['data']['launcher_names'] + ' quiere seguirte.'
            if notification_data['data']['type'] == 'friend_accepted':
                message = 'Ahora sigues a ' + notification_data['data']['launcher_names'] + '.'

            if user_two.device_os == 'ios':
                options = { "sound": "default", "badge": 0, "extra": notification_data }
                res = apns_client.send(user_two.device_token, message, **options)
                return jsonify({'message': 'success'})
            else:
                options = { "notification": { "body": message, "title": "dop", "icon": "ic_stat_dop" }}
                res = gcm_client.send(user_two.device_token, message, **options)
                return jsonify({'message': 'success'})

        return jsonify({'message': 'error'})

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

    options = { "sound": "default" , "badge": 0," extra": notification_data }

    # Send to single device.
    res = apns_client.send(tokens, message, **options)
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

    return jsonify({'message': 'Oops! algo salio mal, intentalo de nuevo, echale ganas'})

@notification.route('/all/get', methods=['GET'])
def get_notifications():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        notifications_query = "SELECT notifications.*, launcher_user.names AS launcher_name, catcher_user.names AS catcher_name, \
                                       launcher_user.surnames AS launcher_surnames, catcher_user.surnames AS catcher_surnames, \
                                       friends.operation_id, branches.name AS branches_name, branches.company_id, branches.branch_id, \
                                       launcher_image.main_image AS launcher_image, catcher_image.main_image AS catcher_image, \
                                       (SELECT EXISTS (SELECT * FROM friends \
                                               WHERE friends.user_one_id = %d AND (friends.user_two_id = launcher_user.user_id OR friends.user_two_id = catcher_user.user_id) \
                                               AND friends.operation_id = 1)::bool) AS is_friend \
                                    FROM notifications \
                                         LEFT JOIN clients_coupon ON notifications.object_id = clients_coupon.clients_coupon_id \
                                            AND notifications.type = 'newsfeed' \
                                         LEFT JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id \
                                         LEFT JOIN branches ON coupons.owner_id = branches.branch_id \
                                         LEFT JOIN friends ON notifications.object_id = friends.friends_id \
                                            AND notifications.type = 'friend' \
                                         LEFT JOIN users_image AS launcher_image ON notifications.launcher_id = launcher_image.user_id \
                                         LEFT JOIN users_image AS catcher_image ON notifications.catcher_id = catcher_image.user_id \
                                         INNER JOIN users AS launcher_user ON notifications.launcher_id = launcher_user.user_id \
                                         INNER JOIN users AS catcher_user ON notifications.catcher_id = catcher_user.user_id \
                                    WHERE (notifications.catcher_id = %d AND (operation_id < 2 OR operation_id IS null)) \
                                    OR ( launcher_id = %d AND operation_id < 2) \
                                         ORDER BY notification_date DESC LIMIT 11" % (payload['id'], payload['id'], payload['id'])

        notifications = db.engine.execute(notifications_query)
        notifications_list = notifications_schema.dump(notifications)

        print notifications_list.data
        return jsonify({'data': notifications_list.data})
    return jsonify({'message': 'Oops! algo salio mal, intentalo de nuevo, echale ganas'})

@notification.route('/all/offset/get/', methods=['GET'])
def get_notifications_offset():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        offset = request.args.get('offset')

        #notification_id = request.args.get('notification_id')

        notifications_query = "SELECT notifications.*, launcher_user.names AS launcher_name, catcher_user.names AS catcher_name, \
                                       launcher_user.surnames AS launcher_surnames, catcher_user.surnames AS catcher_surnames, \
                                       friends.operation_id, branches.name AS branches_name, branches.company_id, branches.branch_id, \
                                       launcher_image.main_image AS launcher_image, catcher_image.main_image AS catcher_image, \
                                       (SELECT EXISTS (SELECT * FROM friends \
                                               WHERE friends.user_one_id = %d AND (friends.user_two_id = launcher_user.user_id OR friends.user_two_id = catcher_user.user_id) \
                                               AND friends.operation_id = 1)::bool) AS is_friend \
                                    FROM notifications \
                                         LEFT JOIN clients_coupon ON notifications.object_id = clients_coupon.clients_coupon_id \
                                            AND notifications.type = 'newsfeed' \
                                         LEFT JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id \
                                         LEFT JOIN branches ON coupons.owner_id = branches.branch_id \
                                         LEFT JOIN friends ON notifications.object_id = friends.friends_id \
                                            AND notifications.type = 'friend' \
                                         LEFT JOIN users_image AS launcher_image ON notifications.launcher_id = launcher_image.user_id \
                                         LEFT JOIN users_image AS catcher_image ON notifications.catcher_id = catcher_image.user_id \
                                         INNER JOIN users AS launcher_user ON notifications.launcher_id = launcher_user.user_id \
                                         INNER JOIN users AS catcher_user ON notifications.catcher_id = catcher_user.user_id \
                                    WHERE (notifications.catcher_id = %d AND (operation_id < 2 OR operation_id IS null)) \
                                    OR ( launcher_id = %d AND operation_id < 2) \
                                         ORDER BY notification_date DESC LIMIT 11 OFFSET %s " % (payload['id'], payload['id'], payload['id'], offset)
        notifications = db.engine.execute(notifications_query)

        notifications_list = notifications_schema.dump(notifications)

        print notifications_list.data
        return jsonify({'data': notifications_list.data})

    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@notification.route('/test/socket/redeem/', methods=['GET'])
def test_socket_redeem():
    socketio.emit('event', {'data': 'data'}, broadcast = True)
    return jsonify({'message': 'Todo bien'})

@socketio.on('joinRoom')
def on_join_room(message):
    payload = parse_token_socket(message)
    session["id"] = payload["id"]
    room = session["id"]
    join_room(room)
    emit('joined', {'data': 'Joined to room'}, room = room)
    return jsonify({'message': 'Todo bien'})


@socketio.on('waitingForRedeemAdmin')
def on_waiting_for_redeem(message):
    room = message
    join_room(room)
    print room
    emit('event',{'data':'new_admin'}, room = room)
    return jsonify({'message': 'admin'})

@socketio.on('waitingForRedeemUser')
def on_waiting_for_redeem(user):
    print user['room']
    #room = user.get('room')
    #join_room(room)
    #emit('event',{'data':'new_user'}, room = room)
    return jsonify({'message': 'user'})

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
    print "Conectado"
    return jsonify({'message': 'Todo bien'})

@socketio.on('disconnect')
def test_disconnect():
    print "Desconectado"
    return jsonify({'message': 'Todo bien'})

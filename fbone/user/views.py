# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
import jwt
import json
import requests
from flask import Blueprint, request, jsonify, session
from flask import current_app as app
from flask.ext.login import login_required, current_user
from jwt import DecodeError, ExpiredSignature
from .models import *
from ..extensions import db, socketio
from marshmallow import pprint
from ..notification import Notification
from ..badge import *
from flask.ext.socketio import SocketIO, send, emit, join_room, leave_room
from ..utils import *

user = Blueprint('user', __name__, url_prefix='/api/user')

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

def level_up(user_id):
    user = User.query.get(user_id)
    for key, val in LEVELS.iteritems():
        if user.exp >= val:
            user.level = key
    return user.level



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
    query = "SELECT users.user_id, users.names, users.surnames, users.birth_date, users.facebook_key, users.google_key, \
                    users.twitter_key,users.privacy_status, users_image.main_image, users_image.user_image_id, level \
                    FROM users INNER JOIN users_image ON users.user_id = users_image.user_id\
                    WHERE users.user_id = %d" % (userId)

    #total_friends = get_friends_by_id(userId)
    
    result = db.engine.execute(query)
    user_with_image = user_joined_schema.dump(result).data

    return jsonify({'data': user_with_image})

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
                            facebook_key = request.json['facebook_key'],
                            level = 0,
                            exp = 0,
                            privacy_status = 0)

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

        userFirstEXP = UserFirstEXP(user_id = facebookUser.user_id,
                                    first_following = False,
                                    first_follower = False, 
                                    first_company_fav = False, 
                                    first_using = False)

        db.session.add(userFirstEXP)
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
        
        query = 'SELECT DISTINCT ON (users.user_id) *, \
                    (SELECT EXISTS (SELECT * FROM friends \
                            WHERE friends.user_one_id = %d and friends.user_two_id = users.user_id and friends.operation_id = 1)::bool) AS friend \
                 FROM friends \
                 INNER JOIN users ON (friends.user_one_id = user_id  AND friends.user_one_id != %d) \
                 OR (friends.user_two_id=user_id  AND friends.user_two_id!=%d) \
                 INNER JOIN users_image ON (friends.user_one_id = users_image.user_id AND friends.user_one_id != %d) \
                 OR (friends.user_two_id = users_image.user_id AND friends.user_two_id != %d) \
                 WHERE (user_one_id = %d OR user_two_id = %d) \
                 AND operation_id = 1' % (user_id, user_id, user_id, user_id, user_id, user_id, user_id)

        friends = db.engine.execute(query)
        friends_list = user_join_friends.dump(friends)
        return jsonify({'data': friends_list.data})
    return jsonify({'message': 'Oops! algo salió mal :('})

@user.route('/friends/add', methods=['POST'])
def add_friend():
    if request.headers.get('Authorization'):
        payload = parse_token(request, True)

        user_id = User.query.get(payload['id']).user_id
        user_to_add = request.json['user_two_id']
        user_two = User.query.get(user_to_add)
        friendshipExist = Friends.query.filter(((Friends.user_one_id == user_id) & (Friends.user_two_id == user_to_add))).first()

        if not friendshipExist:
            user_two = User.query.get(user_to_add)
            if user_two.privacy_status == 0:
                operation_id = 1
            elif user_two.privacy_status == 1:
                operation_id = 0

            friendsRelationship  = Friends(user_one_id = user_id,
                                           user_two_id = user_to_add,
                                           operation_id = operation_id,
                                           launcher_user_id = user_id)


            db.session.add(friendsRelationship)
            db.session.commit()

            notification = Notification(user_id = user_to_add,
                                        object_id = friendsRelationship.friends_id,
                                        type = "friend",
                                        notification_date = datetime.now(),
                                        launcher_id = user_id,
                                        read = False
                                        )
            db.session.add(notification)
            db.session.commit()

            socketio.emit('notification',{'data': 'friend'},namespace='/app',room = user_to_add)

            return jsonify({'message': 'Agregado correctamente'})
        else:
            if user_two.privacy_status == 0:
                friendshipExist.operation_id = 1
            elif user_two.privacy_status == 1:
                friendshipExist.operation_id = 0
            
            db.session.commit()
            socketio.emit('notification',{'data': 'someone triggered me'},namespace='/app',room = user_to_add)

        return jsonify({'message': 'registro existente'})
    return jsonify({'message': 'Oops! algo salió mal :('})

@user.route('/friends/accept', methods=['POST'])
def accept_friend():
    if request.headers.get('Authorization'):
        payload = parse_token(request, True)

        today = datetime.now()

        user_id = User.query.get(payload['id']).user_id

        friendsRelationship = Friends.query.get(request.json['friends_id'])

        friendsRelationship.operation_id = 1
        #friendsRelationship.launcher_user_id = user_id

        db.session.commit()

        notification = Notification.query.filter_by(notification_id=request.json['notification_id']).first()
        notification.notification_date = today

        db.session.commit()

        notification = Notification(user_id = friendsRelationship.user_one_id,
                                        object_id = friendsRelationship.friends_id,
                                        type = "friend",
                                        notification_date = today,
                                        launcher_id = user_id,
                                        read = False
                                        )
        db.session.add(notification)
        db.session.commit()

        socketio.emit('notification',{'data': 'someone triggered me'},namespace='/app',room = friendsRelationship.user_one_id)

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
        action_user = User.query.get(payload['id']).user_id
        user_to_delete = User.query.get(request.json['friends_id'])

        friendsRelationship = Friends.query.filter((Friends.user_one_id == action_user) & (Friends.user_two_id == request.json['friends_id'])).first()
        friendsRelationship.operation_id = 4
        
        db.session.commit()

        return jsonify({'data': 'Has dejado de seguir a este usuario'})

    return jsonify({'message': 'Oops! algo salió mal :('})

@user.route('/<int:user_id>/profile/get', methods=['GET'])
def get_profile(user_id):    
    query = 'SELECT users.names,users.surnames,users.twitter_key, users.facebook_key, users.google_key, users.user_id,\
                    users.birth_date, users_image.main_image FROM users\
             INNER JOIN users_image ON users.user_id = users_image.user_id WHERE users.user_id = %d' % user_id

    friends = db.engine.execute(query)
    friends_list = user_joined_schema.dump(friends)
    return jsonify({'data': friends_list.data})

#SEARCH API
@user.route('/people/search/', methods = ['GET','POST'])
def search_people():
    if request.headers.get('Authorization'):
        token_index = True
        text = request.args.get('text')

        payload = parse_token(request, token_index)
        #list_coupon = db.engine.execute(query)
        people = db.engine.execute("SELECT *, \
                                    (SELECT EXISTS (SELECT * FROM friends \
                                        WHERE friends.user_one_id = %d and friends.user_two_id = users.user_id)::bool) AS friend \
                                    FROM users \
                                    INNER JOIN users_image on users.user_id = users_image.user_id \
                                    WHERE users.names ILIKE '%s' " % (payload['id'], '%%' + text + '%%'))
        
        selected_list_people = people_schema.dump(people, many=True)
        # pprint(selected_list_people, indent = 2)
        return jsonify({'data': selected_list_people.data})
    return jsonify({'message': 'Oops! algo salió mal :('})

@user.route('/activity/get/user/', methods=['GET'])
def get_coupons_activity_by_user_likes():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        user_id = User.query.get(payload['id']).user_id
        limit = request.args.get('limit')
        user_profile_id = request.args.get('user_profile_id')
        
        users = db.engine.execute('SELECT coupons.branch_id,coupons.coupon_id,branches_design.logo,coupons.name,clients_coupon.clients_coupon_id,clients_coupon.latitude,clients_coupon.longitude \
                                    , users.names, users.surnames, users.user_id, users_image.main_image, branches.name AS branch_name, branches.company_id, clients_coupon.used_date, \
                                    (SELECT COUNT(*)  FROM clients_coupon_likes WHERE clients_coupon.clients_coupon_id = clients_coupon_likes.clients_coupon_id) AS total_likes, \
                                    (SELECT COUNT(*)  FROM clients_coupon_likes WHERE clients_coupon_likes.user_id = %s AND clients_coupon_likes.clients_coupon_id = clients_coupon.clients_coupon_id) AS user_like \
                                    FROM clients_coupon \
                                    INNER JOIN users ON clients_coupon.user_id=users.user_id  \
                                    INNER JOIN users_image ON users.user_id = users_image.user_id \
                                    INNER JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_design ON coupons.branch_id = branches_design.branch_id \
                                    WHERE users.user_id = %s AND clients_coupon.used = true AND clients_coupon.private = false \
                                    ORDER BY used_date DESC LIMIT %s OFFSET 0' % (user_profile_id, user_profile_id, limit))

        users_list = user_join_activity_newsfeed.dump(users)
        return jsonify({'data': users_list.data})

    return jsonify({'message': 'Oops! algo salió mal'})

@user.route('/activity/get/user/offset', methods=['POST'])
def get_used_coupons_by_user_likes_offset():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        user_id = User.query.get(payload['id']).user_id
        offset = request.json['offset']
        used_date = request.json['used_date']
        user_profile_id = request.json['user_id']

        users = db.engine.execute('SELECT coupons.branch_id, coupons.coupon_id, branches_design.logo, coupons.name, \
                                            clients_coupon.clients_coupon_id, clients_coupon.latitude,clients_coupon.longitude, \
                                            users.names, users.surnames, users.user_id, users_image.main_image, branches.name AS branch_name, branches.company_id,clients_coupon.used_date, \
                                    (SELECT COUNT(*)  FROM clients_coupon_likes WHERE clients_coupon.clients_coupon_id = clients_coupon_likes.clients_coupon_id) AS total_likes, \
                                    (SELECT COUNT(*)  FROM clients_coupon_likes WHERE clients_coupon_likes.user_id = %d AND clients_coupon_likes.clients_coupon_id = clients_coupon.clients_coupon_id) AS user_like \
                                    FROM clients_coupon \
                                    INNER JOIN users ON clients_coupon.user_id = users.user_id  \
                                    INNER JOIN users_image ON users.user_id = users_image.user_id \
                                    INNER JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_design ON coupons.branch_id = branches_design.branch_id \
                                    WHERE users.user_id = %s AND clients_coupon.used = true AND clients_coupon.private = false \
                                    AND clients_coupon.used_date <= %s ORDER BY used_date DESC LIMIT 6 OFFSET %s' % (payload['id'], user_profile_id, "'"+used_date+"'" , offset))

        users_list = user_join_activity_newsfeed.dump(users)

        return jsonify({'data': users_list.data})

    return jsonify({'message': 'Oops! algo salió mal'})

@user.route('/<int:user_id>/<int:exp>/set', methods=['GET','PUT'])
def set_experience(user_id, exp):
    user = User.query.get(user_id)
    old_exp = user.exp
    user.exp = old_exp + exp
    badge_name = []

    for key, val in BADGES.iteritems():
        if (val > old_exp) and (val <= user.exp):
          badge_name.append(key)

    badges_tuple = tuple(badge_name)
    if len(badges_tuple) == 1:
        badge = db.engine.execute("SELECT * FROM badges WHERE LOWER(name) in(" + `badges_tuple[0]`+")")
    elif len(badges_tuple) > 1:
        badge = db.engine.execute("SELECT * FROM badges WHERE LOWER(name) in" + `badges_tuple`)

    db.session.commit()
    if len(badges_tuple) == 0:
        return jsonify({ 'message': 'experiencia asignada %d' % exp })
    else:
        badges = badge_schema.dump(badge)
        return jsonify({'message': 'experiencia asignada %d' % exp,
                    'badges': badges.data })


@user.route('/privacy_status/set', methods=['POST'])
def set_privacy():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        privacy_status = request.json['privacy_status']
        user = User.query.get(payload['id'])
        user.privacy_status = privacy_status

        db.session.commit()

        return jsonify({'message': 'user privacy is set :D'})
    return jsonify({'message': 'Oops! algo salió mal'})

@user.route('/following/get', methods=['GET'])
def get_following():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        people = db.engine.execute('SELECT *, \
                                    (SELECT EXISTS (SELECT * FROM friends \
                                        WHERE friends.user_one_id = %d and friends.user_two_id = users.user_id)::bool) AS friend \
                                    FROM friends INNER JOIN users \
                                        ON users.user_id = friends.user_two_id \
                                        INNER JOIN users_image ON users_image.user_id = users.user_id \
                                        WHERE friends.user_one_id = %d AND friends.operation_id = 1' % (payload['id'], payload['id']))
        people_list = people_schema.dump(people)

        return jsonify({'data': people_list.data})
    return jsonify({'message': 'Oops! algo salió mal'})



        

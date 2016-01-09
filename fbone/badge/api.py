# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
import jwt
import json
import requests
from flask import Blueprint, current_app, request, jsonify
from flask import current_app as app
from flask.ext.login import login_required, current_user
from jwt import DecodeError, ExpiredSignature
from .models import *
from ..extensions import db
from .schemas import *

badge = Blueprint('badge', __name__, url_prefix='/api/badge')

def create_token(user):
    payload = {
        'id': user.branches_user_id,
        'iat': datetime.now(),
        'exp': datetime.now() + timedelta(days=14)
    }

    token = jwt.encode(payload, app.config['TOKEN_SECRET'])
    return token.decode('unicode_escape')

def parse_token(req, token_index):
    if token_index:
        token = req.headers.get('Authorization').split()[0]
    else:
        token = req.headers.get('Authorization').split()[1]
    return jwt.decode(token, app.config['TOKEN_SECRET'])


@badge.route('/all/get', methods=['GET'])
def badge_grid():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        badges = db.engine.execute('SELECT badges.badge_id, name, info, badges.type, user_id, reward_date, \
                                        (SELECT exists(SELECT * FROM users_badges WHERE user_id = %d \
                                         AND badges.badge_id = badge_id)::bool) AS earned \
                                    FROM badges LEFT JOIN users_badges ON badges.badge_id = users_badges.badge_id \
                                    WHERE user_id = %d OR user_id is null' % (payload['id'], payload['id']))

        badges_list = badges_schema.dump(badges)
        return jsonify({'data': badges_list.data})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@badge.route('/all/trophy/get', methods=['GET'])
def badge_trophy_grid():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        badges = db.engine.execute("SELECT badges.badge_id, name, info, badges.type, user_id, reward_date, \
                                        (SELECT exists(SELECT * FROM users_badges WHERE user_id = %d \
                                         AND badges.badge_id = badge_id)::bool) AS earned \
                                    FROM badges LEFT JOIN users_badges ON badges.badge_id = users_badges.badge_id \
                                    WHERE badges.type = 'trophy' AND (user_id = %d OR user_id is null)" % (payload['id'], payload['id']))

        badges_list = badges_schema.dump(badges)
        return jsonify({'data': badges_list.data})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@badge.route('/all/medal/get', methods=['GET'])
def badge_medal_grid():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        badges = db.engine.execute("SELECT badges.badge_id, name, info, badges.type, user_id, reward_date, \
                                        (SELECT exists(SELECT * FROM users_badges WHERE user_id = %d \
                                         AND badges.badge_id = badge_id)::bool) AS earned \
                                    FROM badges LEFT JOIN users_badges ON badges.badge_id = users_badges.badge_id \
                                    WHERE badges.type = 'medal' AND (user_id = %d OR user_id is null)" % (payload['id'], payload['id']))

        badges_list = badges_schema.dump(badges)
        return jsonify({'data': badges_list.data})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})




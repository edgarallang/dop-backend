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
from ..user import *
from ..extensions import db, socketio
from juggernaut import Juggernaut


# config = {
#     'APNS_CERTIFICATE': '../../certs/push.pem>'
# }



loyalty = Blueprint('loyalty', __name__, url_prefix='/api/loyalty')



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


@loyalty.route('/', methods=['POST'])
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


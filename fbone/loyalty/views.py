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


@loyalty.route('/<int:branch_id>/get', methods=['GET'])
def loyalty_get(branch_id):
    loyalty = Loyalty.query.filter_by(branch_id = branch_id).first()
    loyalty_list = loyalties_schema.dump(loyalty)
    return jsonify({'data': loyalty_list.data})


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


user = Blueprint('user', __name__, url_prefix='/user')

def create_token(user):
    payload = {
        'id': user.user_id,
        'iat': datetime.now(),
        'exp': datetime.now() + timedelta(days=14)
    }

    token = jwt.encode(payload, app.config['TOKEN_SECRET'])

    return token.decode('unicode_escape')

@user.route('/')
@login_required
def index():
    if not current_user.is_authenticated():
        abort(403)
    return render_template('user/index.html', user=current_user)


@user.route('/<int:user_id>/profile')
def profile(user_id):
    user = User.get_by_id(user_id)
    return render_template('user/profile.html', user=user)


@user.route('/<int:user_id>/avatar/<path:filename>')
@login_required
def avatar(user_id, filename):
    dir_path = os.path.join(APP.config['UPLOAD_FOLDER'], 'user_%s' % user_id)
    return send_from_directory(dir_path, filename, as_attachment=True)

@user.route('/login/facebook',methods=['POST'])
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

        userImage = UserImage(user_id=facebookUser.user_id,
                              main_image=request.json['main_image'])
        db.session.add(userImage)
        db.session.commit()

    token = create_token(facebookUser)

    return jsonify(token=token)

@user.route('/login/twitter',methods=['POST'])
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

        userImage = UserImage(user_id=twitter.user_id,
                              main_image=request.json['main_image'])
        db.session.add(userImage)
        db.session.commit()
    token = create_token(twitterUser)

    return jsonify(token=token)

@user.route('/login/google',methods=['POST'])
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

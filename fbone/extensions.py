# -*- coding: utf-8 -*-

from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from flask.ext.mail import Mail
mail = Mail()

from flask.ext.cache import Cache
cache = Cache()

from flask.ext.login import LoginManager
login_manager = LoginManager()

from flask.ext.openid import OpenID
oid = OpenID()

from flask.ext.socketio import SocketIO, emit, join_room, leave_room, close_room, disconnect
socketio = SocketIO()

from flask_pushjack import FlaskAPNS, FlaskGCM
apns_client = FlaskAPNS()
gcm_client = FlaskGCM()

# from flask.ext.jwt import JWT
# jwt = JWT()

from flask.ext.cors import CORS

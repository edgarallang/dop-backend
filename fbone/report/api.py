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
from ..extensions import db
from .schemas import *

report = Blueprint('report', __name__, url_prefix='/api/report')

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


@report.route('/uses/<int:coupon_id>', methods=['GET'])
def uses_by_coupon(coupon_id):
    #if request.headers.get('Authorization'):
    token_index = False

    report_query = db.engine.execute("SELECT date_trunc('day', clients_coupon.used_date) as day, count(*) \
                                FROM clients_coupon \
                                INNER JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id AND clients_coupon.used = TRUE \
                                WHERE clients_coupon.coupon_id = %d \
                                GROUP BY day" % (coupon_id) )

    report = report_schema.dump(report_query)
    return jsonify({'data': report.data})
    #return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

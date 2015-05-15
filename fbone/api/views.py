# -*- coding: utf-8 -*-
import conekta
conekta.api_key = 'key_ReaoWd2MyxP5QdUWKSuXBQ'
conekta.locale = 'es'
import json
import jwt
from flask import Blueprint, current_app, request, jsonify
from flask.ext.login import login_user, current_user, logout_user
from ..extensions import db

from ..user import User


api = Blueprint('api', __name__, url_prefix='/api')

def parse_token(req):
    token = req.headers.get('Authorization').split()[1]
    return jwt.decode(token, app.config['TOKEN_SECRET'])

@api.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated():
        return jsonify(flag='success')

    username = request.form.get('username')
    password = request.form.get('password')
    if username and password:
        user, authenticated = User.authenticate(username, password)
        if user and authenticated:
            if login_user(user, remember='y'):
                return jsonify(flag='success')

    current_app.logger.debug('login(api) failed, username: %s.' % username)
    return jsonify(flag='fail', msg='Sorry, try again.')


@api.route('/logout')
def logout():
    if current_user.is_authenticated():
        logout_user()
    return jsonify(flag='success', msg='Logouted.')

@api.route('/payment/card', methods=['POST'])
def process_payment():
    payment_data = request.json['paymentData']
    if request.headers.get('Authorization'):
      payload = parse_token(request)
      user = BranchUser.query.get(payload['id'])
      try:
          charge = conekta.Charge.create({
            "amount": payment_data['total'],
            "currency": "MXN",
            "description": "Compra de campaña",
            "reference_id": user.branch_id,
            "card": request.json['token_id'], 
            "details": {
              "email": user.email
            }
          })
      except conekta.ConektaError as e:
          return jsonify({ 'message': e.message_to_purchaser })
    #el pago no pudo ser procesado
    return jsonify({ 'message': charge.status })

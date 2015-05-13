# -*- coding: utf-8 -*-
import conekta
conekta.api_key = 'key_ReaoWd2MyxP5QdUWKSuXBQ'
conekta.locale = 'es'
from flask import Blueprint, current_app, request, jsonify
from flask.ext.login import login_user, current_user, logout_user
from ..extensions import db

from ..user import User


api = Blueprint('api', __name__, url_prefix='/api')


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
    try:
        charge = conekta.Charge.create({
          "amount": payment_data.total,
          "currency": "MXN",
          "description": "Pizza Delivery",
          "reference_id": "1",
          "card": request.json['token_id'], 
          "details": {
            "email": "edgarallan182@gmail.com"
          }
        })
    except conekta.ConektaError as e:
        return jsonify({ 'message': e.message_to_purchaser })
    #el pago no pudo ser procesado
    return jsonify({ 'message': charge.status })

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


coupon = Blueprint('coupon', __name__, url_prefix='/api/coupon')

def create_coupon():
    

@coupon.route('/bond/create', methods=['POST'])
def create_bond():
    bondCoupon = BondCoupon(coupon_category_id=request.json['coupon_category_id'], bond_size=request.json['bond_size'])
    db.session.add(bondCoupon)
    db.session.commit()

    return jsonify({'data': bondCoupon})

@coupon.route('/discount/create', methods=['POST'])
def create_discount():
    discountCoupon = DiscountCoupon(coupon_category_id=request.json['coupon_category_id'], bond_size=request.json['bond_size'])
    db.session.add(discountCoupon)
    db.session.commit()

    return jsonify({'data': discountCoupon})

@coupon.route('/nxn/create', methods=['POST'])
def create_nxn():
    nxnCoupon = NxNCoupon(coupon_category_id=request.json['coupon_category_id'], bond_size=request.json['bond_size'])
    db.session.add(nxnCoupon)
    db.session.commit()

    return jsonify({'data': nxnCoupon})
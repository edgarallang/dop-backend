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

def create_coupon(request):
    coupon = Coupon(branch_id = request.json['branch_id'], 
                    name = request.json['name'], 
                    start_date = request.json['start_date'],
                    end_date = request.json['end_date'],
                    limit = request.json['limit'],
                    description = request.json['description'],
                    coupon_folio = 'EAG',
                    min_spent = request.json['min_spent'],
                    coupon_category_id = request.json['coupon_category_id'])
    db.session(coupon)
    db.session.commit()
    print coupon.coupon_id
    return coupon.coupon_id

@coupon.route('/bond/create', methods=['POST'])
def create_bond():
    new_coupon_id = self.create_coupon(request)
    bondCoupon = BondCoupon(coupon_id = new_coupon_id, 
                            coupon_category_id = request.json['coupon_category_id'], 
                            bond_size = request.json['bond_size'])
    db.session.add(bondCoupon)
    db.session.commit()

    return jsonify({'data': bondCoupon})

@coupon.route('/discount/create', methods = ['POST'])
def create_discount():
    new_coupon_id = self.create_coupon(request)
    discountCoupon = DiscountCoupon(coupon_id = new_coupon_id,
                                    coupon_category_id = request.json['coupon_category_id'],
                                    discount = request.json['discount'])
    db.session.add(discountCoupon)
    db.session.commit()

    return jsonify({'data': discountCoupon})

@coupon.route('/nxn/create', methods = ['POST'])
def create_nxn():
    new_coupon_id = self.create_coupon(request)
    nxnCoupon = NxNCoupon(coupon_id = new_coupon_id,
                          coupon_category_id = request.json['coupon_category_id'],
                          n1 = request.json['n1'],
                          n2 = request.json['n2'])
    db.session.add(nxnCoupon)
    db.session.commit()

    return jsonify({'data': nxnCoupon})
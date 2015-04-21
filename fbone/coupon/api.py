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
    new_coupon = Coupon(branch_id = request.json['branch_id'], 
                    name = request.json['name'], 
                    start_date = request.json['start_date'],
                    end_date = request.json['end_date'],
                    limit = request.json['limit'],
                    description = request.json['description'],
                    coupon_folio = 'EAG',
                    min_spent = request.json['min_spent'],
                    coupon_category_id = request.json['coupon_category_id'])
    db.session.add(new_coupon)
    db.session.commit()

    return new_coupon.coupon_id

@coupon.route('/bond/create', methods = ['POST'])
def create_bond():
    new_coupon_id = create_coupon(request)
    bondCoupon = BondCoupon(coupon_id = new_coupon_id, 
                            coupon_category_id = request.json['coupon_category_id'], 
                            bond_size = request.json['bond_size'])
    db.session.add(bondCoupon)
    db.session.commit()

    return jsonify({'message': 'se creo un cupon ten tu 200'})

@coupon.route('/discount/create', methods = ['POST'])
def create_discount():
    new_coupon_id = create_coupon(request)
    discountCoupon = DiscountCoupon(coupon_id = new_coupon_id,
                                    coupon_category_id = request.json['coupon_category_id'],
                                    percent = request.json['discount'])
    db.session.add(discountCoupon)
    db.session.commit()

    return jsonify({'message': 'se creo un cupon ten tu 200'})

@coupon.route('/nxn/create', methods = ['POST'])
def create_nxn():
    new_coupon_id = create_coupon(request)
    nxnCoupon = NxNCoupon(coupon_id = new_coupon_id,
                          coupon_category_id = request.json['coupon_category_id'],
                          n1 = request.json['n1'],
                          n2 = request.json['n2'])
    db.session.add(nxnCoupon)
    db.session.commit()

    return jsonify({'data': nxnCoupon})

@coupon.route('/get/<int:coupon_id>', methods = ['GET'])
def get_coupon(coupon_id):
    generic_coupon = Coupon.query.filter_by(coupon_id=coupon_id).first()

    selected_coupon = coupon_schema.dump(generic_coupon)
    return jsonify(selected_coupon.data)

@coupon.route('/get/all', methods = ['GET'])
def get_all_coupon():
    list_coupon = Coupon.query.join(BondCoupon.coupon).\
                               join(DiscountCoupon.coupon).\
                               join(NxNCoupon.coupon).\
                               filter(Coupon.coupon_id)

    selected_coupon = coupon_schema.dump(list_coupon)
    return jsonify(selected_coupon.data)

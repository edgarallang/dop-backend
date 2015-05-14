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
# class methods
def parse_token(req):
    token = req.headers.get('Authorization').split()[1]
    return jwt.decode(token, app.config['TOKEN_SECRET'])

def create_coupon(request):
    new_coupon = Coupon(branch_id = request.json['branch_id'], 
                        name = request.json['name'], 
                        start_date = request.json['start_date'],
                        end_date = request.json['end_date'],
                        limit = request.json['limit'],
                        description = request.json['description'],
                        coupon_folio = "EAG",
                        min_spent = request.json['min_spent'],
                        coupon_category_id = request.json['coupon_category_id'],
                        available = 0,
                        deleted = False)
    db.session.add(new_coupon)
    db.session.commit()

    return new_coupon

# POST methods
@coupon.route('/bond/create', methods = ['POST'])
def create_bond():
    import pdb; pdb.set_trace()
    if request.headers.get('Authorization'):
        payload = parse_token(request)

        new_coupon = create_coupon(request)
        bondCoupon = BondCoupon(coupon_id = new_coupon.coupon_id, 
                                coupon_category_id = request.json['coupon_category_id'], 
                                bond_size = request.json['bond_size'])
        db.session.add(bondCoupon)
        db.session.commit()

    return jsonify({'message': 'El cupon se creo con exito, ten, toma una galleta'})

@coupon.route('/discount/create', methods = ['POST'])
def create_discount():
    new_coupon = create_coupon(request)
    discountCoupon = DiscountCoupon(coupon_id = new_coupon.coupon_id,
                                    coupon_category_id = request.json['coupon_category_id'],
                                    percent = request.json['discount'])
    db.session.add(discountCoupon)
    db.session.commit()

    return jsonify({'message': 'El cupon se creo con exito, ten, toma una galleta'})

@coupon.route('/nxn/create', methods = ['POST'])
def create_nxn():
    new_coupon = create_coupon(request)
    nxnCoupon = NxNCoupon(coupon_id = new_coupon.coupon_id,
                          coupon_category_id = request.json['coupon_category_id'],
                          n1 = request.json['n1'],
                          n2 = request.json['n2'])
    db.session.add(nxnCoupon)
    db.session.commit()

    return jsonify({'message': 'El cupon se creo con exito, ten, toma una galleta'})

@coupon.route('/user/take',methods=['POST'])
def take_coupon():
    
    mangled = (request.json['coupon_id']*1679979167)%(36**6)
    folio = baseN(mangled,36)

    user_take = ClientsCoupon(user_id = request.json['user_id'],
                              coupon_id = request.json['coupon_id'],
                              folio = folio,
                              taken_date = request.json['taken_date'])

    db.session.add(user_take)
    db.session.commit()

    return jsonify({'message': 'El cupon se tomó con éxito','folio':folio})

# GET methods
@coupon.route('/<int:coupon_id>/get', methods = ['GET'])
def get_coupon(coupon_id):
    generic_coupon = Coupon.query.get(coupon_id)
    coupon_type = generic_coupon.coupon_category_id

    if (coupon_type == 1):
      coupon_benefit = BondCoupon.query.filter_by(coupon_id = coupon_id).first()
      coupon_benefit_json = bond_coupon_schema.dump(coupon_benefit)
    elif (coupon_type == 2):
      coupon_benefit = DiscountCoupon.query.filter_by(coupon_id = coupon_id).first()
      coupon_benefit_json = discount_coupon_schema.dump(coupon_benefit)
    elif (coupon_type == 3):
      coupon_benefit = NxNCoupon.query.filter_by(coupon_id = coupon_id).first()
      coupon_benefit_json = nxn_coupon_schema.dump(coupon_benefit)

    selected_coupon = coupon_schema.dump(generic_coupon)
    return jsonify({'coupon_info': selected_coupon.data, 'benefit': coupon_benefit_json.data})

@coupon.route('/all/<int:branch_id>/get', methods = ['GET'])
def get_all_coupon_by_branch(branch_id):
    list_coupon = Coupon.query.filter_by(deleted = False).filter_by(branch_id = branch_id).limit(6).all()

    selected_list_coupon = coupons_schema.dump(list_coupon)
    return json.dumps(selected_list_coupon.data)

@coupon.route('/all/get', methods = ['GET'])
def get_all_coupon():
    list_coupon = Coupon.query.filter_by(deleted = False).limit(6).all()

    selected_list_coupon = coupons_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})

# PUT methods
@coupon.route('/<int:coupon_id>/delete', methods = ['PUT'])
def pseudo_delete(coupon_id):
    coupon_to_delete = Coupon.query.get(coupon_id)
    coupon_to_delete.deleted = True
    db.session.commit()

    return jsonify({'message': 'El cupón ha sido eliminado'})






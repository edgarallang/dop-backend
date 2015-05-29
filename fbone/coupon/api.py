# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import conekta
conekta.api_key = 'key_ReaoWd2MyxP5QdUWKSuXBQ'
conekta.locale = 'es'
import os
import jwt
import json
import requests
from flask import Blueprint, current_app, request, jsonify
from flask import current_app as app
from flask.ext.login import login_required, current_user
from jwt import DecodeError, ExpiredSignature
from .models import *
from ..user import *
from ..extensions import db


coupon = Blueprint('coupon', __name__, url_prefix='/api/coupon')
# class methods
def parse_token(req, token_index):
    if token_index:
        token = req.headers.get('Authorization').split()[0]
    else:
        token = req.headers.get('Authorization').split()[1]
    return jwt.decode(token, app.config['TOKEN_SECRET'])

def create_coupon(request):
    if request.headers.get('Authorization'):
        payment_data = request.json['paymentData']
        payload = parse_token(request, False)
        branch_id = BranchUser.query.get(payload['id']).branch_id
        new_coupon = Coupon(branch_id = branch_id, 
                            # name = request.json['name'], 
                            # start_date = request.json['start_date'],
                            # end_date = request.json['end_date'],
                            limit = payment_data['amountOfCoupon'],
                            # description = request.json['description'],
                            coupon_folio = "EAG",
                            # min_spent = request.json['min_spent'],
                            coupon_category_id = 0,
                            available = 0,
                            deleted = False,
                            active = False)
        db.session.add(new_coupon)
        db.session.commit()

        return "OK si se creo el cupon despues del pago"

# POST methods
@coupon.route('/bond/create', methods = ['POST'])
def create_bond():
    
    if request.headers.get('Authorization'):
        payload = parse_token(request, False)

        branch_id = BranchUser.query.get(payload['id']).branch_id

        bondCoupon = BondCoupon.query.filter_by(coupon_id = request.json['coupon_id']).first()
        if not bondCoupon:
            newBondCoupon = BondCoupon(coupon_id = request.json['coupon_id'], 
                                    coupon_category_id = request.json['coupon_category_id'], 
                                    bond_size = request.json['bond_size'])
            coupon = Coupon.query.get(request.json['coupon_id'])
            coupon.name = request.json['name']
            coupon.start_date = request.json['start_date']
            coupon.end_date = request.json['end_date']
            coupon.description = request.json['description']
            coupon.min_spent = request.json['min_spent']
            db.session.add(newBondCoupon)
            db.session.commit()

            return jsonify({'message': 'El cupon se creo con exito, ten, toma una galleta'})
        else: 
            bondCoupon.bond_size = request.json['bond_size']
            coupon = Coupon.query.get(request.json['coupon_id'])
            coupon.name = request.json['name']
            coupon.start_date = request.json['start_date']
            coupon.end_date = request.json['end_date']
            coupon.description = request.json['description']
            coupon.min_spent = request.json['min_spent']
            db.session.commit()

            return jsonify({'message': 'El cupon se modificó con exito, ten, toma una galleta'})
    return jsonify({'message': 'Oops! algo salió mal :('})

@coupon.route('/discount/create', methods = ['POST'])
def create_discount():
    
    if request.headers.get('Authorization'):
        payload = parse_token(request, False)

        branch_id = BranchUser.query.get(payload['id']).branch_id
        new_coupon = create_coupon(request, branch_id)
        discountCoupon = DiscountCoupon(coupon_id = new_coupon.coupon_id,
                                        coupon_category_id = request.json['coupon_category_id'],
                                        percent = request.json['discount'])
        db.session.add(discountCoupon)
        db.session.commit()

        return jsonify({'message': 'El cupon se creo con exito, ten, toma una galleta'})
    return jsonify({'message': 'Oops! algo salió mal :('})

@coupon.route('/nxn/create', methods = ['POST'])
def create_nxn():

    if request.headers.get('Authorization'):
        payload = parse_token(request)

        branch_id = BranchUser.query.get(payload['id']).branch_id
        new_coupon = create_coupon(request)
        nxnCoupon = NxNCoupon(coupon_id = new_coupon.coupon_id,
                              coupon_category_id = request.json['coupon_category_id'],
                              n1 = request.json['n1'],
                              n2 = request.json['n2'])
        db.session.add(nxnCoupon)
        db.session.commit()

        return jsonify({'message': 'El cupon se creo con exito, ten, toma una galleta'})
    return jsonify({'message': 'Oops! algo salió mal :('})

@coupon.route('/user/take',methods=['POST'])
def take_coupon():

    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        mangled = (request.json['coupon_id']*1679979167)%(36**6)
        folio = baseN(mangled, 36)

        user_take = ClientsCoupon(user_id = payload['id'],
                                  coupon_id = request.json['coupon_id'],
                                  folio = folio,
                                  taken_date = request.json['taken_date'],
                                  latitude= request.json['latitude'],
                                  longitude = request.json['longitude'])

        db.session.add(user_take)
        db.session.commit()

        return jsonify({'message': 'El cupon se tomó con éxito','folio': folio})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

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
    list_coupon = Coupon.query.filter_by(deleted = False) \
                              .filter_by(branch_id = branch_id) \
                              .limit(6).all()

    bond_coupons = db.engine.execute('select * from coupons inner join bond_coupon on coupons.coupon_id = bond_coupon.coupon_id')
    discount_coupons = db.engine.execute('select * from coupons inner join discount_coupon on coupons.coupon_id = discount_coupon.coupon_id')
    nxn_coupons = db.engine.execute('select * from coupons inner join nxn_coupon on coupons.coupon_id = nxn_coupon.coupon_id')

    selected_list_coupon = coupons_schema.dump(list_coupon)
    bondlist = bond_join_coupon_schema.dump(bond_coupons)
    discountlist = discount_join_coupon_schema.dump(discount_coupons)
    nxnlist = nxn_join_coupon_schema.dump(nxn_coupons)

    return jsonify({'bond': bondlist.data,
                    'discount': discountlist.data,
                    'nxn': nxnlist.data })

    

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


@coupon.route('/payment/card', methods=['POST'])
def process_payment():
    payment_data = request.json['paymentData']
    if request.headers.get('Authorization'):
      payload = parse_token(request, False)
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
    if (charge.status == 'paid'):
        message = create_coupon(request)

        return jsonify({ 'message': message })
    return jsonify({'message': 'Oops! algo salió mal, seguramente fue tu tarjeta sobregirada'})

@coupon.route('/used/<int:user_id>/get', methods=['GET'])
def get_used_coupons_by_user(user_id):
    users = db.engine.execute("SELECT coupons.branch_id,coupons.coupon_id,branches_design.logo,coupons.name,clients_coupon.latitude,clients_coupon.longitude \
                                , users.names, users.surnames, users.user_id, users_image.main_image FROM clients_coupon \
                                INNER JOIN users ON clients_coupon.user_id=users.user_id  \
                                INNER JOIN users_image ON users.user_id = users_image.user_id \
                                INNER JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id \
                                INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                INNER JOIN branches_design ON coupons.branch_id = branches_design.branch_id \
                                ORDER BY taken_date DESC")

    users_list = user_join_exchanges_coupon_schema.dump(users)

    return jsonify({'data': users_list.data})



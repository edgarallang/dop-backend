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
from ..extensions import db, socketio
from flask.ext.socketio import SocketIO, send, emit, join_room, leave_room
from sqlalchemy import and_


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
                            coupon_category_id = 1,
                            available = 0,
                            deleted = False,
                            active = False)
        db.session.add(new_coupon)
        db.session.commit()

        return "OK si se creo el cupon despues del pago"

# POST methods

@coupon.route('/user/take',methods=['POST'])
def take_coupon():

    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        user_take = ClientsCoupon(user_id = payload['id'],
                                  coupon_id = request.json['coupon_id'],
                                  folio = '',
                                  taken_date = request.json['taken_date'],
                                  latitude= request.json['latitude'],
                                  longitude = request.json['longitude'],
                                  used = False)


        db.session.add(user_take)
        db.session.commit()
        folio = '%d%s%d' % (request.json['branch_id'], request.json['folio_date'], user_take.clients_coupon_id)
        user_take.folio = folio
        db.session.commit()

        return jsonify({'message': 'El cupon se tomó con éxito','folio': folio})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@coupon.route('/user/use',methods=['GET'])
def use_coupon():

    #if request.headers.get('Authorization'):
    token_index = True
    payload = 5 #parse_token(request, token_index)
    qr_code = 4 #int(request.json['qr_code'])
    coupon_id = 5 #request.json['coupon_id']

    client_coupon = ClientsCoupon.query.join(Coupon, ClientsCoupon.coupon_id==Coupon.coupon_id).add_columns(ClientsCoupon.clients_coupon_id,ClientsCoupon.used, Coupon.branch_id).filter(and_(ClientsCoupon.coupon_id==coupon_id),(ClientsCoupon.user_id==payload)).first()

    client_coupon_json = clients_coupon_inner_coupon_schema.dump(client_coupon)
    
    if client_coupon_json.data['branch_id'] == qr_code:
        client_coupon = ClientsCoupon.query.filter_by(clients_coupon_id = client_coupon.clients_coupon_id).first()
        client_coupon.used = True
        client_coupon.used_date = datetime.now()
        db.session.commit()
        return jsonify({'message': 'Cupón cajeado'})
    else:
        return jsonify({'message': 'Codigo qr incorrecto'})
   
    
    #return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})


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
                              .filter_by(coupon_category_id = 1).all()

    bond_query = 'SELECT * FROM coupons INNER JOIN bond_coupon \
                  ON coupons.coupon_id = bond_coupon.coupon_id WHERE coupons.branch_id = %d' % branch_id
    bond_coupons = db.engine.execute(bond_query)

    discount_query = 'SELECT * FROM coupons INNER JOIN discount_coupon \
                      ON coupons.coupon_id = discount_coupon.coupon_id WHERE coupons.branch_id = %d' % branch_id
    discount_coupons = db.engine.execute(discount_query)

    nxn_query = 'SELECT * FROM coupons INNER JOIN nxn_coupon \
                 ON coupons.coupon_id = nxn_coupon.coupon_id WHERE coupons.branch_id = %d' % branch_id
    nxn_coupons = db.engine.execute(nxn_query)


    selected_list_coupon = coupons_schema.dump(list_coupon)
    bondlist = bond_join_coupon_schema.dump(bond_coupons)
    discountlist = discount_join_coupon_schema.dump(discount_coupons)
    nxnlist = nxn_join_coupon_schema.dump(nxn_coupons)

    return jsonify({'new_promo': selected_list_coupon.data,
                    'bond': bondlist.data,
                    'discount': discountlist.data,
                    'nxn': nxnlist.data })
    
@coupon.route('/all/for/user/get/', methods = ['GET'])
def get_all_coupon_for_user():
    #user_id = request.args.get('user_id')
    token_index = True
    limit = request.args.get('limit')
    payload = parse_token(request, token_index)

    list_coupon = db.engine.execute('SELECT coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, latitude, longitude, banner, category_id, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id) AS user_like \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id \
                                    WHERE deleted = false ORDER BY coupons.coupon_id DESC LIMIT %s OFFSET 0' % (payload['id'],limit))



    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})

@coupon.route('/all/for/user/offset/get/', methods = ['GET'])
def get_all_coupon_for_user_offset():
    token_index = True
    offset = request.args.get('offset')
    coupon_id = request.args.get('coupon_id')
    payload = parse_token(request, token_index)

    list_coupon = db.engine.execute('SELECT coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, latitude, longitude, banner, category_id, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id) AS user_like \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id \
                                    WHERE deleted = false AND coupons.coupon_id < %s ORDER BY start_date DESC LIMIT 6 OFFSET %s' % (payload['id'],coupon_id,offset))



    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})

@coupon.route('/all/taken/for/user/get/', methods = ['GET'])
def get_all_taken_coupon_for_user():
    token_index = True
    limit = request.args.get('limit')
    payload = parse_token(request, token_index)

    list_coupon = db.engine.execute('SELECT coupons.coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, branches_location.latitude, branches_location.longitude, \
                                            banner, category_id, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id) AS user_like \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    INNER JOIN clients_coupon on coupons.coupon_id = clients_coupon.coupon_id \
                                    INNER JOIN users on clients_coupon.user_id = users.user_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id WHERE used = false \
                                    AND users.user_id = %d \
                                    AND deleted = false ORDER BY coupons.coupon_id DESC LIMIT %s OFFSET 0' % (payload['id'], payload['id'], limit))



    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})

@coupon.route('/all/taken/for/user/offset/get/', methods = ['GET'])
def get_all_taken_coupon_for_user_offset():
    token_index = True
    offset = request.args.get('offset')
    coupon_id = request.args.get('coupon_id')
    payload = parse_token(request, token_index)

    list_coupon = db.engine.execute('SELECT coupons.coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, branches_location.latitude, branches_location.longitude, \
                                            banner, category_id, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id) AS user_like \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    INNER JOIN clients_coupon on coupons.coupon_id = clients_coupon.coupon_id \
                                    INNER JOIN users on clients_coupon.user_id = users.user_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id WHERE used = false \
                                    AND users.user_id = %d \
                                    AND deleted = false AND coupons.coupon_id < %s ORDER BY start_date DESC LIMIT 6 OFFSET %s' % (payload['id'], payload['id'], coupon_id,offset))



    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})

@coupon.route('/all/used/for/user/get/', methods = ['GET'])
def get_all_used_coupon_for_user():
    token_index = True
    limit = request.args.get('limit')
    payload = parse_token(request, token_index)

    list_coupon = db.engine.execute('SELECT coupons.coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, branches_location.latitude, branches_location.longitude, \
                                            banner, category_id, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id) AS user_like \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    INNER JOIN clients_coupon on coupons.coupon_id = clients_coupon.coupon_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id WHERE used = true \
                                    AND deleted = false ORDER BY coupons.coupon_id DESC LIMIT %s OFFSET 0' % (payload['id'], limit))



    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})

@coupon.route('/all/used/for/user/offset/get/', methods = ['GET'])
def get_all_used_coupon_for_user_offset():
    token_index = True
    offset = request.args.get('offset')
    coupon_id = request.args.get('coupon_id')
    payload = parse_token(request, token_index)

    list_coupon = db.engine.execute('SELECT coupons.coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, branches_location.latitude, branches_location.longitude, \
                                            banner, category_id, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id) AS user_like \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    INNER JOIN clients_coupon on coupons.coupon_id = clients_coupon.coupon_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id WHERE used = true \
                                    AND deleted = false AND coupons.coupon_id < %s ORDER BY start_date DESC LIMIT 6 OFFSET %s' % (payload['id'],coupon_id,offset))



    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})

@coupon.route('/all/used/for/myself/get/', methods = ['GET'])
def get_all_used_coupon_for_myself():
    token_index = True
    limit = request.args.get('limit')
    payload = parse_token(request, token_index)

    list_coupon = db.engine.execute('SELECT coupons.coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, branches_location.latitude, branches_location.longitude, \
                                            banner, category_id, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id) AS user_like \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    INNER JOIN clients_coupon on coupons.coupon_id = clients_coupon.coupon_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id WHERE used = true \
                                    AND clients_coupon.user_id = %d \
                                    AND deleted = false ORDER BY coupons.coupon_id DESC LIMIT %s OFFSET 0' % (payload['id'], payload['id'], limit))

    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})

@coupon.route('/all/used/for/myself/offset/get/', methods = ['GET'])
def get_all_used_coupon_for_myself_offset():
    token_index = True
    offset = request.args.get('offset')
    coupon_id = request.args.get('coupon_id')
    payload = parse_token(request, token_index)

    list_coupon = db.engine.execute('SELECT coupons.coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, branches_location.latitude, branches_location.longitude, \
                                            banner, category_id, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id) AS user_like \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    INNER JOIN clients_coupon on coupons.coupon_id = clients_coupon.coupon_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id WHERE used = true \
                                    AND clients_coupon.user_id = %d \
                                    AND deleted = false AND coupons.coupon_id < %s ORDER BY start_date DESC LIMIT 6 OFFSET %s' % (payload['id'], payload['id'], coupon_id, offset))

    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})

@coupon.route('/all/for/user/by/branch/get/', methods = ['GET'])
def get_all_coupon_for_user_by_branch():
    token_index = True
    branch_id = request.args.get('branch_id')
    payload = parse_token(request, token_index)

    list_coupon = db.engine.execute('SELECT coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, latitude, longitude, banner, category_id, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id) AS user_like \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id \
                                    WHERE coupons.branch_id = %s AND deleted = false ORDER BY start_date DESC LIMIT 6 OFFSET 0' % (payload['id'],branch_id))


    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})


@coupon.route('/all/for/user/by/branch/offset/get/', methods = ['GET'])
def get_all_coupon_for_user_by_branch_offset():
    token_index = True
    offset = request.args.get('offset')
    coupon_id = request.args.get('coupon_id')
    branch_id = request.args.get('branch_id')
    payload = parse_token(request, token_index)

    list_coupon = db.engine.execute('SELECT coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, latitude, longitude, banner, category_id, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id) AS user_like \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id \
                                    WHERE coupons.branch_id = %s AND deleted = false AND coupons.coupon_id < %s ORDER BY start_date DESC LIMIT 6 OFFSET %s' % (payload['id'],branch_id,coupon_id,offset))



    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})


@coupon.route('/trending/get/', methods = ['GET'])
def get_trending_coupons():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        list_coupon = db.engine.execute('SELECT *,\
                                        (SELECT COUNT(*) FROM coupons_likes  WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                        ((SELECT COUNT(*) FROM coupons_likes  WHERE coupons.coupon_id = coupons_likes.coupon_id)*.30 + (SELECT COUNT(*) FROM clients_coupon WHERE coupons.coupon_id = clients_coupon.coupon_id)*.70)as total_value,\
                                        (SELECT COUNT(*)  FROM coupons_likes  WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id) AS user_like \
                                        FROM coupons INNER JOIN branches_design ON \
                                        coupons.branch_id = branches_design.branch_id \
                                        INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                        INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                        WHERE deleted = false ORDER BY total_value DESC LIMIT 8' % payload['id'])


        selected_list_coupon = trending_coupon_schema.dump(list_coupon)
        return jsonify({'data': selected_list_coupon.data})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@coupon.route('/almost/expired/get/', methods = ['GET'])
def get_almost_expired_coupons():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        list_coupon = db.engine.execute('SELECT *,\
                                        (SELECT COUNT(*) FROM coupons_likes  WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                        (SELECT COUNT(*)  FROM coupons_likes  WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id) AS user_like \
                                        FROM coupons INNER JOIN branches_design ON \
                                        coupons.branch_id = branches_design.branch_id \
                                        INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                        INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                        WHERE deleted = false AND coupons.end_date>now() ORDER BY coupons.end_date ASC LIMIT 8' % payload['id'])

        selected_list_coupon = toexpire_coupon_schema.dump(list_coupon)
        return jsonify({'data': selected_list_coupon.data})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@coupon.route('/nearest/get/', methods=['GET', 'POST'])
def nearest_coupons():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    radio = request.args.get('radio')
    


    query = 'SELECT branch_location_id, branch_id, state, city, latitude, longitude, distance, address, name, category_id, coupon_name, coupon_id, description,start_date,end_date,min_spent \
                FROM (SELECT coupons.name as coupon_name, coupons.coupon_id,coupons.start_date,coupons.end_date,coupons.limit,coupons.min_spent, coupons.description, z.branch_location_id, z.branch_id, z.state, z.city, z.address, \
                    z.latitude, z.longitude, branches.name, subcategory.category_id, \
                    p.radius,\
                    p.distance_unit \
                             * DEGREES(ACOS(COS(RADIANS(p.latpoint)) \
                             * COS(RADIANS(z.latitude)) \
                             * COS(RADIANS(p.longpoint - z.longitude)) \
                             + SIN(RADIANS(p.latpoint)) \
                             * SIN(RADIANS(z.latitude)))) AS distance \
                FROM branches_location AS z \
                JOIN branches on z.branch_id = branches.branch_id \
                JOIN branches_subcategory on z.branch_id = branches_subcategory.branch_id \
                JOIN subcategory on subcategory.subcategory_id = branches_subcategory.subcategory_id \
                JOIN coupons on branches.branch_id = coupons.branch_id AND deleted = false AND coupons.end_date>now() \
                JOIN (   /* these are the query parameters */ \
                    SELECT '+ latitude +'  AS latpoint, '+ longitude +' AS longpoint, \
                           '+ radio +' AS radius,      111.045 AS distance_unit \
                ) AS p ON 1=1 \
                WHERE z.latitude \
                 BETWEEN p.latpoint  - (p.radius / p.distance_unit) \
                     AND p.latpoint  + (p.radius / p.distance_unit) \
                AND z.longitude \
                 BETWEEN p.longpoint - (p.radius / (p.distance_unit * COS(RADIANS(p.latpoint)))) \
                     AND p.longpoint + (p.radius / (p.distance_unit * COS(RADIANS(p.latpoint)))) \
                ) AS d \
                WHERE distance <= radius \
                ORDER BY distance LIMIT 8'

    nearestCoupons = db.engine.execute(query)
    nearest = nearest_coupon_schema.dump(nearestCoupons)
    
    return jsonify({'data': nearest.data})

@coupon.route('/all/get', methods = ['GET'])
def get_all_coupon():

    list_coupon = db.engine.execute('SELECT *, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    WHERE deleted = false')


    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
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

@coupon.route('/used/get', methods=['GET'])
def get_coupons_activity_by_user():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        user_id = User.query.get(payload['id']).user_id

        users = db.engine.execute("SELECT coupons.branch_id,coupons.coupon_id,branches_design.logo,coupons.name,clients_coupon.latitude,clients_coupon.longitude \
                                    , users.names, users.surnames, users.user_id, users_image.main_image, branches.name AS branch_name FROM clients_coupon \
                                    INNER JOIN users ON clients_coupon.user_id=users.user_id  \
                                    INNER JOIN users_image ON users.user_id = users_image.user_id \
                                    INNER JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_design ON coupons.branch_id = branches_design.branch_id \
                                    ORDER BY taken_date DESC")

        users_list = user_join_exchanges_coupon_schema.dump(users)

        return jsonify({'data': users_list.data})

    return jsonify({'message': 'Oops! algo salió mal'})

@coupon.route('/used/get/user', methods=['GET'])
def get_coupons_activity_by_user_likes():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        user_id = User.query.get(payload['id']).user_id
        limit = request.args.get('limit')

        users = db.engine.execute('SELECT coupons.branch_id,coupons.coupon_id,branches_design.logo,coupons.name,clients_coupon.clients_coupon_id,clients_coupon.latitude,clients_coupon.longitude \
                                    , users.names, users.surnames, users.user_id, users_image.main_image, branches.name AS branch_name, branches.company_id, \
                                    (SELECT COUNT(*)  FROM clients_coupon_likes WHERE clients_coupon.clients_coupon_id = clients_coupon_likes.clients_coupon_id) AS total_likes, \
                                    (SELECT COUNT(*)  FROM clients_coupon_likes WHERE clients_coupon_likes.user_id = %d AND clients_coupon_likes.clients_coupon_id = clients_coupon.clients_coupon_id) AS user_like \
                                    FROM clients_coupon \
                                    INNER JOIN users ON clients_coupon.user_id=users.user_id  \
                                    INNER JOIN users_image ON users.user_id = users_image.user_id \
                                    INNER JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_design ON coupons.branch_id = branches_design.branch_id \
                                    ORDER BY start_date DESC LIMIT %s OFFSET 0 ORDER BY clients_coupon.clients_coupon_id DESC' % payload['id'],limit)

        users_list = user_join_activity_newsfeed.dump(users)

        return jsonify({'data': users_list.data})

    return jsonify({'message': 'Oops! algo salió mal'})

@coupon.route('/used/get/user/offset/', methods=['GET'])
def get_used_coupons_by_user_likes_offset():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        user_id = User.query.get(payload['id']).user_id
        offset = request.args.get('offset')
        client_coupon_id = request.args.get('client_coupon_id')

        users = db.engine.execute('SELECT coupons.branch_id,coupons.coupon_id,branches_design.logo,coupons.name,clients_coupon.clients_coupon_id,clients_coupon.latitude,clients_coupon.longitude \
                                    , users.names, users.surnames, users.user_id, users_image.main_image, branches.name AS branch_name, branches.company_id, \
                                    (SELECT COUNT(*)  FROM clients_coupon_likes WHERE clients_coupon.clients_coupon_id = clients_coupon_likes.clients_coupon_id) AS total_likes, \
                                    (SELECT COUNT(*)  FROM clients_coupon_likes WHERE clients_coupon_likes.user_id = %d AND clients_coupon_likes.clients_coupon_id = clients_coupon.clients_coupon_id) AS user_like \
                                    FROM clients_coupon \
                                    INNER JOIN users ON clients_coupon.user_id=users.user_id  \
                                    INNER JOIN users_image ON users.user_id = users_image.user_id \
                                    INNER JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_design ON coupons.branch_id = branches_design.branch_id \
                                    WHERE clients_coupon.clients_coupon_id < %s ORDER BY clients_coupon.clients_coupon_id DESC LIMIT 6 OFFSET %s' % (payload['id'], client_coupon_id , offset))

        users_list = user_join_activity_newsfeed.dump(users)

        return jsonify({'data': users_list.data})

    return jsonify({'message': 'Oops! algo salió mal'})

@coupon.route('/used/get/bycoupon', methods=['POST'])
def get_used_coupons_by_coupon():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        coupon_id = request.json['coupon_id']
        query = 'SELECT coupons.branch_id,coupons.coupon_id,branches_design.logo,coupons.name,clients_coupon.clients_coupon_id,clients_coupon.latitude,clients_coupon.longitude \
                                    , users.names, users.surnames, users.user_id, users_image.main_image, branches.name AS branch_name, \
                                    (SELECT COUNT(*)  FROM clients_coupon_likes WHERE clients_coupon.clients_coupon_id = clients_coupon_likes.clients_coupon_id) AS total_likes, \
                                    (SELECT COUNT(*)  FROM clients_coupon_likes WHERE clients_coupon_likes.user_id = %d AND clients_coupon_likes.clients_coupon_id = clients_coupon.clients_coupon_id) AS user_like \
                                    FROM clients_coupon \
                                    INNER JOIN users ON clients_coupon.user_id=users.user_id  \
                                    INNER JOIN users_image ON users.user_id = users_image.user_id \
                                    INNER JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id AND coupons.coupon_id = %s \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id  \
                                    INNER JOIN branches_design ON coupons.branch_id = branches_design.branch_id \
                                    ORDER BY taken_date DESC' % (payload['id'], coupon_id)
        users = db.engine.execute(query)
        users_list = user_join_exchanges_coupon_schema.dump(users, partial=True)

        return jsonify({'data': users_list.data})

    return jsonify({'message': 'Oops! algo salió mal'})

@coupon.route('/used/like',methods=['POST'])
def like_used_coupon():

    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)


        userLike = CouponsUsedLikes.query.filter_by(clients_coupon_id = request.json['clients_coupon_id'],user_id = payload['id']).first()
        if not userLike:
            user_like = CouponsUsedLikes(clients_coupon_id = request.json['clients_coupon_id'],
                                      user_id = payload['id'],
                                      date = request.json['date'])

            liked_user = ClientsCoupon.query.filter_by(clients_coupon_id = request.json['clients_coupon_id']).first()

            notification = Notification(user_id = liked_user.user_id,
                                        object_id = request.json['clients_coupon_id'],
                                        type = "newsfeed",
                                        notification_date = datetime.now(),
                                        launcher_id = payload['id'],
                                        read = False
                                        )

            socketio.emit('notification',{'data': 'someone triggered me'},namespace='/app',room=liked_user.user_id)


            db.session.add(user_like)
            db.session.add(notification)
            db.session.commit()
            return jsonify({'message': 'El like se asigno con éxito'})
        else:
            db.session.delete(userLike)
            db.session.commit()
            return jsonify({'message': 'El like se elimino con éxito'})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@coupon.route('/like',methods=['POST'])
def like_coupon():

    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        userLike = CouponsLikes.query.filter_by(coupon_id = request.json['coupon_id'],user_id = payload['id']).first()
        if not userLike:
            user_like = CouponsLikes(coupon_id = request.json['coupon_id'],
                                      user_id = payload['id'],
                                      date = request.json['date'])

            db.session.add(user_like)


            db.session.commit()
            return jsonify({'message': 'El like se asigno con éxito'})
        else:
            db.session.delete(userLike)
            db.session.commit()
            return jsonify({'message': 'El like se elimino con éxito'})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@coupon.route('/customize', methods=['POST'])
def custom_coupon():
    if request.headers.get('Authorization'):
        payload = parse_token(request, False)

        branch_id = BranchUser.query.get(payload['id']).branch_id
        coupon_category = request.json['coupon_category_id'] 
        if (coupon_category == 2):
            success = create_bond(request)
        elif (coupon_category == 3):
            success = create_discount(request)
        elif (coupon_category == 4):
            success = create_nxn(request)

        if success:
            return jsonify({'message': 'La promoción se modifico con éxito'})
        return jsonify({'message': 'Oops! algo salió mal :('})

    return jsonify({'message': 'Oops! algo salió mal :('})



def create_bond(request):
    customizationSuccess = False
    bondCoupon = BondCoupon.query.filter_by(coupon_id = request.json['coupon_id']).first()
    if not bondCoupon:
        newBondCoupon = BondCoupon(coupon_id = request.json['coupon_id'], 
                                   coupon_category_id = request.json['coupon_category_id'], 
                                   bond_size = request.json['bond_size'])
        coupon = Coupon.query.get(request.json['coupon_id'])
        coupon.coupon_category_id = request.json['coupon_category_id']
        coupon.name = request.json['name']
        coupon.description = request.json['description']
        coupon.min_spent = request.json['min_spent']
        db.session.add(newBondCoupon)
        db.session.commit()
        customizationSuccess = True
        return customizationSuccess
    else: 
        bondCoupon.bond_size = request.json['bond_size']
        coupon = Coupon.query.get(request.json['coupon_id'])
        coupon.name = request.json['name']
        coupon.description = request.json['description']
        coupon.min_spent = request.json['min_spent']
        db.session.commit()

        return customizationSuccess
    return customizationSuccess

def create_discount(request):
    customizationSuccess = False
    discountCoupon = DiscountCoupon.query.filter_by(coupon_id = request.json['coupon_id']).first()
    if not discountCoupon:
        newDiscountCoupon = DiscountCoupon(coupon_id = request.json['coupon_id'], 
                                           coupon_category_id = request.json['coupon_category_id'], 
                                           percent = request.json['percent'])
        coupon = Coupon.query.get(request.json['coupon_id'])
        coupon.coupon_category_id = request.json['coupon_category_id']
        coupon.name = request.json['name']
        coupon.description = request.json['description']
        coupon.min_spent = request.json['min_spent']
        db.session.add(newDiscountCoupon)
        db.session.commit()
        customizationSuccess = True
        return customizationSuccess
    else: 
        discountCoupon.percent = request.json['percent']
        coupon = Coupon.query.get(request.json['coupon_id'])
        coupon.name = request.json['name']
        coupon.description = request.json['description']
        coupon.min_spent = request.json['min_spent']
        db.session.commit()

        return customizationSuccess
    return customizationSuccess

def create_nxn(request):
    customizationSuccess = False
    nxnCoupon = NxNCoupon.query.filter_by(coupon_id = request.json['coupon_id']).first()
    if not nxnCoupon:
        newNxNCoupon = NxNCoupon(coupon_id = request.json['coupon_id'], 
                                 coupon_category_id = request.json['coupon_category_id'], 
                                 n1 = request.json['n1'],
                                 n2 = request.json['n2'])
        coupon = Coupon.query.get(request.json['coupon_id'])
        coupon.coupon_category_id = request.json['coupon_category_id']
        coupon.name = request.json['name']
        coupon.description = request.json['description']
        coupon.min_spent = request.json['min_spent']
        db.session.add(newNxNCoupon)
        db.session.commit()
        customizationSuccess = True
        return customizationSuccess
    else: 
        nxnCoupon.n1 = request.json['n1']
        nxnCoupon.n2 = request.json['n2']
        coupon = Coupon.query.get(request.json['coupon_id'])
        coupon.name = request.json['name']
        coupon.description = request.json['description']
        coupon.min_spent = request.json['min_spent']
        db.session.commit()

        return customizationSuccess
    return customizationSuccess

#SEARCH API
@coupon.route('/search', methods = ['POST'])
def search_all_coupon_user_offset():
    #user_id = request.args.get('user_id')
    token_index = True
    offset = request.json['offset']
    coupon_id = request.json['coupon_id']
    text = request.json['text']
    
    payload = parse_token(request, token_index)

    list_coupon = "SELECT *, \
            (SELECT COUNT(*)  FROM coupons_likes \
            WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
            (SELECT COUNT(*)  FROM coupons_likes \
            WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id) AS user_like \
            FROM coupons INNER JOIN branches_design ON \
            coupons.branch_id = branches_design.branch_id \
            INNER JOIN branches ON coupons.branch_id = branches.branch_id \
            INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
            WHERE deleted = false AND coupons.name ILIKE %s" % (payload['id'],"%" + "sta" + "%",)

    #list_coupon = db.engine.execute(query)
    list_coupon = db.engine.execute("SELECT * FROM coupons WHERE name ILIKE %s ", ("%" + text + "%",))

    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})

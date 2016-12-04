# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import conekta
import io
conekta.api_key = 'key_ReaoWd2MyxP5QdUWKSuXBQ'
conekta.locale = 'es'
import os
import jwt
import json
import requests
from flask import Blueprint, current_app, request, jsonify, render_template
from flask import current_app as app
from flask.ext.login import login_required, current_user
from jwt import DecodeError, ExpiredSignature
from .models import *
from ..badge import *
from ..user import *
from ..notification import *
from ..extensions import db, socketio
from flask.ext.socketio import SocketIO, send, emit, join_room, leave_room
from sqlalchemy.orm import joinedload
from marshmallow import pprint
from sqlalchemy import and_, desc
from ..company import *
from ..utils import *
import pdfkit
from xhtml2pdf import pisa

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
                            available = payment_data['amountOfCoupon'],
                            deleted = False,
                            active = False,
                            views = 0,
                            duration = payment_data['expireTime'])

        db.session.add(new_coupon)
        db.session.commit()

        return "success"

#leveling up
def level_up(user_id):
    user = User.query.get(user_id)
    exp = user.exp
    for key, val in sorted(LEVELS.iteritems(), key=lambda x: x[1]):
        print key, val
        print exp >= val
        if (exp >= val):
            user.level = key
        else:
            break
    db.session.commit()
    return user.level

def set_experience(user_id, exp):
    user = User.query.get(user_id)
    old_exp = user.exp
    user.exp = old_exp + exp
    badge_name = []

    for key, val in sorted(BADGES.iteritems(), key=lambda x: x[1]):
        if (val > old_exp) and (val <= user.exp):
          badge_name.append(key)

    badges_tuple = tuple(badge_name)
    if len(badges_tuple) == 1:
        badge = db.engine.execute("SELECT * FROM badges WHERE LOWER(name) in(" + `badges_tuple[0]`+")")
    elif len(badges_tuple) > 1:
        badge = db.engine.execute("SELECT * FROM badges WHERE LOWER(name) in" + `badges_tuple`)

    db.session.commit()
    if len(badges_tuple) == 0:
        return { 'message': 'experiencia asignada %d' % exp }
    else:
        badges = badge_schema.dump(badge)
        return {'message': 'experiencia asignada %d' % exp,
                        'badges': badges.data }

@coupon.route('/generate/pdf', methods=['GET'])
def generate_pdf():
    x = pdfkit.from_string('Hello!', 'out.pdf')

    print x
    return jsonify({'message': 'Generado'})
# POST methods

@coupon.route('/user/take',methods=['POST'])
def take_coupon():

    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        actual_date = datetime.now()
        coupon_id = request.json['coupon_id']

        client_coupon = ClientsCoupon.query.filter(and_(ClientsCoupon.coupon_id==coupon_id),(ClientsCoupon.user_id==payload['id']),(ClientsCoupon.used==False)).first()
        if not client_coupon:
            coupon = Coupon.query.get(coupon_id)
            if coupon.available > 0:
                user_take = ClientsCoupon(user_id = payload['id'],
                                          coupon_id = coupon_id,
                                          folio = '',
                                          taken_date = actual_date,
                                          latitude= request.json['latitude'],
                                          longitude = request.json['longitude'],
                                          used = False,
                                          private = False)


                db.session.add(user_take)
                db.session.commit()
                folio = '%d%s%d' % (request.json['branch_id'], "{:%d%m%Y}".format(actual_date), user_take.clients_coupon_id)
                user_take.folio = folio
                db.session.commit()
                coupon.available = coupon.available - 1
                db.session.commit()
                return jsonify({'message': 'El cupon se tomó con éxito','total': coupon.available})
            else:
                return jsonify({'message': 'agotado','total': coupon.available})
        else:
            coupon = Coupon.query.get(coupon_id)
            coupon.available = coupon.available + 1
            db.session.delete(client_coupon)
            db.session.commit()
            return jsonify({'message': 'El coupon se elimino con éxito','total': coupon.available})
        return jsonify({'message': 'Ya tomaste este cupón'})

    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@coupon.route('/user/redeem', methods=['POST'])
def use_coupon():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index) #5
        coupon_id = request.json['coupon_id'] #5
        qr_code = request.json['qr_code']
        branch_id = request.json['branch_id']


        actual_date = datetime.now()
        #WHEN USER HAS TAKEN A COUPON
        client_coupon = ClientsCoupon.query.filter(and_(ClientsCoupon.coupon_id==coupon_id),
                                                       (ClientsCoupon.user_id==payload['id']),
                                                       (ClientsCoupon.used==False)).first()

        recently_used = ClientsCoupon.query.filter(and_(ClientsCoupon.coupon_id==coupon_id),
                                                       (ClientsCoupon.user_id==payload['id']),
                                                       (ClientsCoupon.used==True)) \
                                                        .order_by(desc(ClientsCoupon.used_date)) \
                                                        .first()

        coupon = Coupon.query.get(request.json['coupon_id'])
        if recently_used:
            minutes = (actual_date-recently_used.used_date).total_seconds() / 60

        if not recently_used or minutes > 20:
            if not client_coupon:
                if coupon.available > 0:
                    client_coupon = ClientsCoupon(user_id = payload['id'],
                                      coupon_id = request.json['coupon_id'],
                                      folio = '',
                                      taken_date = actual_date,
                                      latitude= request.json['latitude'],
                                      longitude = request.json['longitude'],
                                      used = True,
                                      used_date = actual_date,
                                      private = True)
                    db.session.add(client_coupon)
                    db.session.commit()
                    folio = '%d%s%d' % (request.json['branch_id'], "{:%d%m%Y}".format(actual_date), client_coupon.clients_coupon_id)
                    client_coupon.folio = folio
                    coupon.available = coupon.available - 1

                    db.session.commit()

                    branch = Branch.query.filter_by(branch_id = branch_id).first()
                    branch_data = branch_schema.dump(branch)

                    reward = set_experience(payload['id'], USING)
                    user_level = level_up(payload['id'])
                    db.session.commit()

                    if not request.json['first_using']:
                        user_first_exp = UserFirstEXP.query.filter_by(user_id = payload['id']).first()
                        user_first_exp.first_using = True

                        db.session.commit()

                    return jsonify({'data': branch_data.data, 'reward': reward, 'level': user_level, 'folio': folio })
                else:
                    return jsonify({'message': 'agotado'})
            else:
                client_coupon.used = True
                client_coupon.used_date = actual_date

                db.session.commit()

                branch = Branch.query.get(branch_id)
                branch_data = branch_schema.dump(branch)

                reward = set_experience(payload['id'], USING)
                user_level = level_up(payload['id'])
                return jsonify({'data': branch_data.data, 'reward': reward, 'level': user_level, 'folio': client_coupon.folio })
        else:
            minutes_left = 20 - minutes
            return jsonify({'message': 'error',"minutes": str(minutes_left)})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@coupon.route('/report',methods=['POST'])
def user_report():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        report = CouponReport( user_id = payload['id'],
                               branch_id = request.json['branch_id'],
                               coupon_id = request.json['coupon_id'],
                               branch_indiference = request.json['branch_indiference'],
                               camera_broken = request.json['camera_broken'],
                               app_broken = request.json['app_broken'],
                               qr_lost = request.json['qr_lost'] )

        db.session.add(report)
        db.session.commit()

        coupons_report = coupons_report_schema.dump(report)
        return jsonify({ 'data': coupons_report.data })
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@coupon.route('/user/privacy',methods=['POST'])
def set_coupon_privacy():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        folio = request.json['folio']
        private = request.json['privacy_status']

        client_coupon = ClientsCoupon.query.filter(ClientsCoupon.folio == request.json['folio']).first()

        if client_coupon:
            client_coupon.private = private
            db.session.commit()
            return jsonify({'message': 'success'})

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
    # list_coupon = Coupon.query.filter_by(deleted = False) \
    #                           .filter_by(branch_id = branch_id) \
    #                           .filter_by(coupon_category_id = 1).all()

    # bond_query = 'SELECT * FROM coupons INNER JOIN bond_coupon \
    #               ON coupons.coupon_id = bond_coupon.coupon_id WHERE coupons.branch_id = %d' % branch_id
    # bond_coupons = db.engine.execute(bond_query)

    # discount_query = 'SELECT * FROM coupons INNER JOIN discount_coupon \
    #                   ON coupons.coupon_id = discount_coupon.coupon_id WHERE coupons.branch_id = %d' % branch_id
    # discount_coupons = db.engine.execute(discount_query)

    # nxn_query = 'SELECT * FROM coupons INNER JOIN nxn_coupon \
    #              ON coupons.coupon_id = nxn_coupon.coupon_id WHERE coupons.branch_id = %d' % branch_id
    # nxn_coupons = db.engine.execute(nxn_query)


    # selected_list_coupon = coupons_schema.dump(list_coupon)
    # bondlist = bond_join_coupon_schema.dump(bond_coupons)
    # discountlist = discount_join_coupon_schema.dump(discount_coupons)
    # nxnlist = nxn_join_coupon_schema.dump(nxn_coupons)

    #list_coupon = Coupon.query.filter_by(branch_id = branch_id).all()
    list_coupon = db.engine.execute('SELECT coupons.*, branches.company_id, \
                                    ((coupons.available = 0) OR (coupons.end_date < now()) )::bool AS completed, \
                                    (SELECT end_date::DATE - now()::DATE FROM coupons AS c WHERE coupons.coupon_id = c.coupon_id) AS remaining \
                                    FROM coupons \
                                        INNER JOIN branches ON branches.branch_id = coupons.branch_id \
                                    WHERE coupons.branch_id = %d' % branch_id)

    branches_coupons = coupons_schema.dump(list_coupon)
    return jsonify({ 'data': branches_coupons.data })

@coupon.route('/available/<int:coupon_id>', methods = ['GET'])
def get_availables(coupon_id):
    coupon = Coupon.query.get(coupon_id)
    return jsonify({ 'available': coupon.available })

@coupon.route('/all/for/user/get/', methods = ['GET'])
def get_all_coupon_for_user():
    #user_id = request.args.get('user_id')
    token_index = True
    limit = request.args.get('limit')
    payload = parse_token(request, token_index)

    user = User.query.get(payload['id'])
    adult_validation = ''
    if not user.adult:
        adult_validation = 'AND branches_subcategory.subcategory_id != 25'

    list_coupon = db.engine.execute('SELECT coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, latitude, longitude, banner, category_id, coupons.available, subcategory.subcategory_id, \
                                    (SELECT EXISTS (SELECT * FROM clients_coupon \
                                        WHERE USER_id = %d AND clients_coupon.coupon_id = coupons.coupon_id AND used = false)::bool) AS taken, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT EXISTS (SELECT * FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id)::bool) AS user_like \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id \
                                    WHERE deleted = false AND coupons.available > 0 %s AND active=true ORDER BY coupons.start_date DESC LIMIT %s OFFSET 0' % (payload['id'], payload['id'], adult_validation, limit))


    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
    pprint(selected_list_coupon)
    return jsonify({'data': selected_list_coupon.data})

@coupon.route('/all/for/user/offset/get', methods = ['POST'])
def get_all_coupon_for_user_offset():
    token_index = True
    offset = request.json['offset']
    start_date = request.json['start_date']
    payload = parse_token(request, token_index)

    user = User.query.get(payload['id'])
    adult_validation = ''
    if not user.adult:
        adult_validation = 'AND branches_subcategory.subcategory_id!=25'

    list_coupon = db.engine.execute('SELECT coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, latitude, longitude, banner, category_id, coupons.available, subcategory.subcategory_id, \
                                    (SELECT EXISTS (SELECT * FROM clients_coupon \
                                        WHERE USER_id = %d AND clients_coupon.coupon_id = coupons.coupon_id AND used = false)::bool) AS taken, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT EXISTS (SELECT * FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id)::bool) AS user_like \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id \
                                    WHERE deleted = false AND active=true AND coupons.start_date <= %s AND coupons.available>0 %s ORDER BY coupons.start_date DESC LIMIT 6 OFFSET %s' % (payload['id'], payload['id'],"'"+start_date+"'", adult_validation,offset))


    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
    pprint(selected_list_coupon)
    return jsonify({'data': selected_list_coupon.data})

@coupon.route('/all/taken/for/user/get/', methods = ['GET'])
def get_all_taken_coupon_for_user():
    token_index = True
    limit = request.args.get('limit')
    payload = parse_token(request, token_index)

    list_coupon = db.engine.execute('SELECT coupons.coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, branches_location.latitude, branches_location.longitude, \
                                            banner, category_id, available, clients_coupon.taken_date, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT EXISTS (SELECT * FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id)::bool) AS user_like \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    INNER JOIN clients_coupon on coupons.coupon_id = clients_coupon.coupon_id \
                                    INNER JOIN users on clients_coupon.user_id = users.user_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id WHERE used = false \
                                    AND users.user_id = %d \
                                    AND deleted = false  AND active=true ORDER BY clients_coupon.taken_date DESC LIMIT %s OFFSET 0' % (payload['id'], payload['id'], limit))



    selected_list_coupon = coupons_taken_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})

@coupon.route('/all/taken/for/user/offset/get', methods = ['POST'])
def get_all_taken_coupon_for_user_offset():
    if request.headers.get('Authorization'):

        token_index = True
        offset = request.json['offset']
        taken_date = request.json['taken_date']
        payload = parse_token(request, token_index)
        user_id = payload['id']

        list_coupon_query = 'SELECT coupons.coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                                end_date, coupons.limit, min_spent, coupon_category_id, logo, branches_location.latitude, branches_location.longitude, \
                                                banner, category_id, available, clients_coupon.taken_date, \
                                        (SELECT COUNT(*)  FROM coupons_likes \
                                            WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                        (SELECT EXISTS (SELECT * FROM coupons_likes \
                                            WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id)::bool) AS user_like \
                                        FROM coupons INNER JOIN branches_design ON \
                                        coupons.branch_id = branches_design.branch_id \
                                        INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                        INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                        INNER JOIN clients_coupon on coupons.coupon_id = clients_coupon.coupon_id \
                                        INNER JOIN users on clients_coupon.user_id = users.user_id \
                                        JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                        JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id WHERE used = false \
                                        AND users.user_id = %d \
                                        AND deleted = false  AND active=true AND clients_coupon.taken_date <= %s ORDER BY clients_coupon.taken_date DESC LIMIT 6 OFFSET %s' % (user_id, user_id, "'"+taken_date+"'",offset)


        list_coupon = db.engine.execute(list_coupon_query)
        selected_list_coupon = coupons_taken_schema.dump(list_coupon)
        return jsonify({'data': selected_list_coupon.data})

        return jsonify({'data':'hola'})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@coupon.route('/all/used/for/user/get/', methods = ['GET'])
def get_all_used_coupon_for_user():
    token_index = True
    limit = request.args.get('limit')
    payload = parse_token(request, token_index)

    list_coupon = db.engine.execute('SELECT coupons.coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, branches_location.latitude, branches_location.longitude, \
                                            banner, category_id, available, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT EXISTS (SELECT * FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id)::bool) AS user_like \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    INNER JOIN clients_coupon on coupons.coupon_id = clients_coupon.coupon_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id WHERE used = true \
                                    AND deleted = false  AND active=true ORDER BY clients_coupon.used_date DESC LIMIT %s OFFSET 0' % (payload['id'], limit))



    selected_list_coupon = coupons_taken_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})

@coupon.route('/all/used/for/user/offset/get/', methods = ['GET'])
def get_all_used_coupon_for_user_offset():
    token_index = True
    offset = request.args.get('offset')
    used_date = request.args.get('used_date')
    payload = parse_token(request, token_index)

    list_coupon = db.engine.execute('SELECT coupons.coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, branches_location.latitude, branches_location.longitude, \
                                            banner, category_id, available, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT EXISTS (SELECT * FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id)::bool) AS user_like \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    INNER JOIN clients_coupon on coupons.coupon_id = clients_coupon.coupon_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id WHERE used = true \
                                    AND deleted = false  AND active=true AND clients_coupon.used_date <= %s ORDER BY used_date DESC LIMIT 6 OFFSET %s' % (payload['id'],used_date,offset))



    selected_list_coupon = coupons_taken_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})


@coupon.route('/all/for/user/by/branch/<int:branch_id>/get', methods = ['GET'])
def get_all_coupon_for_user_by_branch(branch_id):
    token_index = True
    payload = parse_token(request, token_index)

    list_coupon = db.engine.execute('SELECT coupon_id, branches.branch_id, company_id, branches.name, coupon_folio, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, latitude, longitude, banner, category_id, available, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT EXISTS (SELECT * FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id)::bool) AS user_like, \
                                    (SELECT EXISTS (SELECT * FROM clients_coupon \
                                        WHERE user_id = %d AND clients_coupon.coupon_id = coupons.coupon_id AND used = false)::bool) AS taken \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id \
                                    WHERE coupons.branch_id = %s AND deleted = false  AND active=true ORDER BY start_date DESC LIMIT 6 OFFSET 0' % (payload['id'], payload['id'], branch_id))


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
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, latitude, longitude, banner, category_id, available, \
                                    (SELECT COUNT(*)  FROM coupons_likes \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                    (SELECT EXISTS (SELECT * FROM coupons_likes \
                                        WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id)::bool) AS user_like, \
                                    (SELECT EXISTS (SELECT * FROM clients_coupon \
                                        WHERE user_id = %d AND clients_coupon.coupon_id = coupons.coupon_id AND used = false)::bool) AS taken \
                                    FROM coupons INNER JOIN branches_design ON \
                                    coupons.branch_id = branches_design.branch_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id \
                                    WHERE coupons.branch_id = %s AND deleted = false  AND active=true AND coupons.coupon_id < %s ORDER BY start_date DESC LIMIT 6 OFFSET %s' % (payload['id'], payload['id'], branch_id, coupon_id,offset))



    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})


@coupon.route('/trending/get/', methods = ['GET'])
def get_trending_coupons():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        user_id = payload['id']

        user = User.query.get(user_id)

        adult_validation = ''
        if not user.adult:
            adult_validation = 'AND branches_subcategory.subcategory_id!=25'



        list_coupon = db.engine.execute('SELECT *,\
                                        (SELECT COUNT(*) FROM coupons_likes  WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                        ((SELECT COUNT(*) FROM coupons_likes  WHERE coupons.coupon_id = coupons_likes.coupon_id)*.30 + (SELECT COUNT(*) FROM clients_coupon WHERE coupons.coupon_id = clients_coupon.coupon_id AND clients_coupon.used = true)*1)as total_value,\
                                        (SELECT EXISTS (SELECT * FROM coupons_likes  WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id)::bool) AS user_like, \
                                        (SELECT EXISTS (SELECT * FROM clients_coupon \
                                        WHERE user_id = %d AND clients_coupon.coupon_id = coupons.coupon_id AND used = false)::bool) AS taken \
                                        FROM coupons INNER JOIN branches_design ON \
                                        coupons.branch_id = branches_design.branch_id \
                                        INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                        INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                        JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id   \
                                        WHERE deleted = false %s  AND active=true AND coupons.end_date>now() ORDER BY total_value DESC LIMIT 8' % (user_id, user_id, adult_validation))


        selected_list_coupon = trending_coupon_schema.dump(list_coupon)
        return jsonify({'data': selected_list_coupon.data})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@coupon.route('/almost/expired/get/', methods = ['GET'])
def get_almost_expired_coupons():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        user_id = payload['id']

        user = User.query.get(user_id)

        adult_validation = ''
        if not user.adult:
            adult_validation = 'AND branches_subcategory.subcategory_id!=25'

        list_coupon = db.engine.execute('SELECT *,\
                                        (SELECT COUNT(*) FROM coupons_likes  WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                                        (SELECT EXISTS (SELECT * FROM coupons_likes  WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id)::bool) AS user_like, \
                                        (SELECT EXISTS (SELECT * FROM clients_coupon \
                                            WHERE user_id = %d AND clients_coupon.coupon_id = coupons.coupon_id AND used = false)::bool) AS taken \
                                        FROM coupons INNER JOIN branches_design ON \
                                        coupons.branch_id = branches_design.branch_id \
                                        INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                        INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
                                        JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id   \
                                        WHERE deleted = false %s AND active=true AND coupons.end_date>now() AND coupons.available>0 ORDER BY coupons.end_date ASC LIMIT 8' % (user_id, user_id, adult_validation))

        selected_list_coupon = toexpire_coupon_schema.dump(list_coupon)
        return jsonify({'data': selected_list_coupon.data})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@coupon.route('/latest/stats/<int:branch_id>', methods=['GET'])
def coupon_stats(branch_id):
    list_coupon = db.engine.execute('SELECT coupon_id, coupon_folio,coupons.name, description, start_date, \
                                            end_date, coupons.limit, min_spent, coupon_category_id, logo, banner, category_id, available,views,  \
                                    (SELECT COUNT(*)  FROM coupons_likes   \
                                        WHERE coupons.coupon_id = coupons_likes.coupon_id) AS total_likes,   \
                                    (SELECT COUNT(*)  FROM clients_coupon   \
                                        WHERE coupons.coupon_id = clients_coupon.coupon_id AND clients_coupon.used = true) AS total_uses \
                                    FROM coupons INNER JOIN branches_design ON   \
                                    coupons.branch_id = branches_design.branch_id   \
                                    JOIN branches_subcategory ON branches_subcategory.branch_id = coupons.branch_id   \
                                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id   \
                                    WHERE coupons.branch_id = %d AND deleted = false AND coupons.end_date>now() ORDER BY start_date DESC LIMIT 4' % branch_id)
    stats_list_coupon = coupons_views_schema.dump(list_coupon)
    return jsonify({'data': stats_list_coupon.data})

@coupon.route('/used/ages/<int:branch_id>', methods = ['GET'])
def used_by_ages(branch_id):
    used_coupons_query =  db.engine.execute("SELECT date_part('year',age(users.birth_date)) AS age, COUNT(*) FROM clients_coupon \
                                            INNER JOIN users ON clients_coupon.user_id = users.user_id \
                                            INNER JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id \
                                            WHERE used = TRUE AND coupons.branch_id = %d \
                                            GROUP BY age" % branch_id)

    used_coupons_stats = used_coupons_by_age_schema.dump(used_coupons_query)

    return jsonify({'data': used_coupons_stats.data})

@coupon.route('/used/gender/<int:branch_id>', methods = ['GET'])
def used_by_gender(branch_id):
    used_coupons_query =  db.engine.execute("SELECT users.gender, COUNT(*) FROM clients_coupon \
                                            INNER JOIN users ON clients_coupon.user_id = users.user_id \
                                            INNER JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id \
                                            WHERE used = TRUE AND coupons.branch_id = %d \
                                            GROUP BY users.gender" % branch_id)

    used_coupons_stats = used_coupons_by_gender_schema.dump(used_coupons_query)

    return jsonify({'data': used_coupons_stats.data})

@coupon.route('/nearest/get/', methods=['GET'])
def nearest_coupons():
    token_index = True
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    radio = request.args.get('radio')
    payload = parse_token(request, token_index)
    user_id = str(payload['id'])

    user = User.query.get(user_id)

    adult_validation = ''
    if not user.adult:
        adult_validation = 'AND branches_subcategory.subcategory_id != 25'

    query = "SELECT branch_location_id, branch_id, company_id, state, city, latitude, longitude, distance, address, \
                    name, category_id, subcategory_id, available, \
                    coupon_name, coupon_id, description, start_date, end_date, min_spent, logo, \
                (SELECT COUNT(*)  FROM coupons_likes \
                        WHERE d.coupon_id = coupons_likes.coupon_id) AS total_likes, \
                (SELECT EXISTS (SELECT * FROM coupons_likes  WHERE coupons_likes.user_id = "+ user_id +" AND d.coupon_id = coupons_likes.coupon_id)::bool) AS user_like, \
                (SELECT EXISTS (SELECT * FROM clients_coupon \
                    WHERE user_id = "+ user_id +" AND clients_coupon.coupon_id = d.coupon_id AND used = false)::bool) AS taken \
                FROM (SELECT coupons.name as coupon_name, coupons.coupon_id,coupons.start_date,coupons.end_date, coupons.limit ,coupons.min_spent, \
                             coupons.description, z.branch_location_id, z.branch_id, z.state, z.city, z.address, coupons.available, \
                    z.latitude, z.longitude, branches.name, branches.company_id, branches_design.logo, subcategory.category_id, subcategory.subcategory_id, \
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
                JOIN branches_design ON branches.branch_id = branches_design.branch_id \
                JOIN subcategory on subcategory.subcategory_id = branches_subcategory.subcategory_id \
                JOIN coupons on branches.branch_id = coupons.branch_id AND deleted = false AND active = true AND coupons.end_date>now() AND available>0 \
                JOIN (   /* these are the query parameters */ \
                    SELECT "+ latitude +"  AS latpoint, "+ longitude +" AS longpoint, \
                           "+ radio +" AS radius,      111.045 AS distance_unit \
                ) AS p ON 1=1 \
                WHERE z.latitude \
                 BETWEEN p.latpoint  - (p.radius / p.distance_unit) \
                     AND p.latpoint  + (p.radius / p.distance_unit) \
                AND z.longitude \
                 BETWEEN p.longpoint - (p.radius / (p.distance_unit * COS(RADIANS(p.latpoint)))) \
                     AND p.longpoint + (p.radius / (p.distance_unit * COS(RADIANS(p.latpoint)))) \
                "+ adult_validation +" \
                ) AS d \
                WHERE distance <= radius \
                ORDER BY distance LIMIT 8"

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


@coupon.route('/payment/campaign/card', methods=['POST'])
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
          return jsonify({ 'message': e['message_to_purchaser'] })
    #el pago no pudo ser procesado
    if (charge.status == 'paid'):
        message = create_coupon(request)

        return jsonify({ 'message': message })
    return jsonify({'message': 'Oops! algo salió mal, seguramente fue tu tarjeta sobregirada'})

@coupon.route('/<int:branch_id>/credits/payment', methods = ['GET', 'POST'])
def credits_payment(branch_id):
    if request.headers.get('Authorization'):
        token_index = False
        payload = parse_token(request, token_index)
        payment_data = request.json['paymentData']

        company = Company.query.get(Branch.query.get(branch_id).company_id)
        if company.credits < (payment_data['total'] / 100):
            return jsonify({'message': 'Oops! no tienes suficientes créditos'})
        else:
            company.credits = company.credits - (payment_data['total'] / 100)
            db.session.commit()

            message = create_coupon(request)

            return jsonify({'data': {
                                'balance': company.credits,
                                'status': message }
                          })
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

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
        user_id = payload['id']

        users = db.engine.execute('SELECT coupons.branch_id,coupons.coupon_id,branches_design.logo,coupons.name,clients_coupon.clients_coupon_id,clients_coupon.latitude,clients_coupon.longitude, \
                                          users.names, users.surnames, users.user_id, users.exp, users.level, users_image.main_image, branches.name AS branch_name, \
                                          branches.company_id, clients_coupon.used_date, friends.operation_id, users.privacy_status, \
                                    (SELECT COUNT(*)  FROM clients_coupon_likes WHERE clients_coupon.clients_coupon_id = clients_coupon_likes.clients_coupon_id) AS total_likes, \
                                    (SELECT EXISTS (SELECT * FROM clients_coupon_likes WHERE clients_coupon_likes.user_id = %d AND clients_coupon_likes.clients_coupon_id = clients_coupon.clients_coupon_id)::bool) AS user_like, \
                                    (SELECT EXISTS (SELECT * FROM friends \
                                        WHERE friends.user_one_id = %d AND friends.user_two_id = users.user_id AND friends.operation_id = 1)::bool) AS is_friend \
                                    FROM clients_coupon \
                                    INNER JOIN users ON clients_coupon.user_id=users.user_id  \
                                    INNER JOIN users_image ON users.user_id = users_image.user_id \
                                    INNER JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_design ON coupons.branch_id = branches_design.branch_id \
                                    LEFT JOIN friends ON friends.user_one_id = %d AND friends.user_two_id = users.user_id \
                                    WHERE clients_coupon.used = true AND clients_coupon.private = false AND friends.operation_id = 1 ORDER BY used_date DESC LIMIT 6 OFFSET 0' % (payload['id'], payload['id'], payload['id']))

        users_list = user_join_activity_newsfeed.dump(users)
        print users_list.data
        return jsonify({'data': users_list.data})

    return jsonify({'message': 'Oops! algo salió mal'})

@coupon.route('/used/get/user/offset', methods=['POST'])
def get_used_coupons_by_user_likes_offset():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)
        user_id = payload['id']
        offset = request.json['offset']
        used_date = request.json['used_date']

        query = 'SELECT coupons.branch_id,coupons.coupon_id,branches_design.logo,coupons.name,clients_coupon.clients_coupon_id,clients_coupon.latitude,clients_coupon.longitude, \
                                          users.names, users.surnames, users.user_id, users.exp, users.level, users_image.main_image, branches.name AS branch_name, \
                                          branches.company_id, clients_coupon.used_date, friends.operation_id, users.privacy_status, \
                                    (SELECT COUNT(*)  FROM clients_coupon_likes WHERE clients_coupon.clients_coupon_id = clients_coupon_likes.clients_coupon_id) AS total_likes, \
                                    (SELECT EXISTS (SELECT * FROM clients_coupon_likes WHERE clients_coupon_likes.user_id = %d AND clients_coupon_likes.clients_coupon_id = clients_coupon.clients_coupon_id)::bool) AS user_like, \
                                    (SELECT EXISTS (SELECT * FROM friends \
                                        WHERE friends.user_one_id = %d AND friends.user_two_id = users.user_id AND friends.operation_id = 1)::bool) AS is_friend \
                                    FROM clients_coupon \
                                    INNER JOIN users ON clients_coupon.user_id=users.user_id  \
                                    INNER JOIN users_image ON users.user_id = users_image.user_id \
                                    INNER JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id \
                                    INNER JOIN branches_design ON coupons.branch_id = branches_design.branch_id \
                                    LEFT JOIN friends ON friends.user_one_id = %d AND friends.user_two_id = users.user_id \
                                    WHERE clients_coupon.used = true AND clients_coupon.used_date <= %s AND clients_coupon.private = false AND friends.operation_id = 1 ORDER BY used_date DESC LIMIT 6 OFFSET %s' % (user_id, user_id, user_id, "'" + used_date + "'" , offset)


        users = db.engine.execute(query)

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
                                    (SELECT EXISTS (SELECT * FROM clients_coupon_likes WHERE clients_coupon_likes.user_id = %d AND clients_coupon_likes.clients_coupon_id = clients_coupon.clients_coupon_id)::bool) AS user_like \
                                    FROM clients_coupon \
                                    INNER JOIN users ON clients_coupon.user_id=users.user_id  \
                                    INNER JOIN users_image ON users.user_id = users_image.user_id \
                                    INNER JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id AND coupons.coupon_id = %s \
                                    INNER JOIN branches ON coupons.branch_id = branches.branch_id  \
                                    INNER JOIN branches_design ON coupons.branch_id = branches_design.branch_id \
                                    ORDER BY taken_date DESC' % (payload['id'], coupon_id)
        users = db.engine.execute(query)
        users_list = user_join_exchanges_coupon_schema.dump(users)

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

            if liked_user.user_id != payload['id']:
                notification = Notification(catcher_id = liked_user.user_id,
                                            object_id = request.json['clients_coupon_id'],
                                            type = "newsfeed",
                                            notification_date = datetime.now(),
                                            launcher_id = payload['id'],
                                            read = False
                                            )
                db.session.add(notification)

                liked_user_data = User.query.filter_by(user_id = liked_user.user_id).first()
                launcher_user_data = User.query.filter_by(user_id = payload['id']).first()

                notification_data = { "data": {
                                            "object_id": liked_user.user_id,
                                            "type": "user_like",
                                            "launcher_names": launcher_user_data.names
                                        }
                                     }
                if liked_user_data.device_token != None and liked_user_data.device_token != "":
                    callback = send_notification(liked_user_data.device_token, notification_data, liked_user_data.device_os)

            db.session.add(user_like)
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
                                      date = datetime.now())

            db.session.add(user_like)
            db.session.commit()
            return jsonify({'message': 'El like se asigno con éxito'})
        else:
            db.session.delete(userLike)
            db.session.commit()
            return jsonify({'message': 'El like se elimino con éxito'})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@coupon.route('/view', methods=['POST'])
def add_view():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        coupon_id = request.json['coupon_id']
        coupon = Coupon.query.get(coupon_id)
        coupon.views = coupon.views + 1

        db.session.commit()

        return jsonify({'message': 'vistas actualizada'})
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

@coupon.route('/taken/location/<int:branch_id>', methods = ['GET'])
def taken_by_location(branch_id):
    coupons_query = "SELECT coupons.coupon_id,coupons.name, coupons.description, clients_coupon.latitude, \
                   clients_coupon.longitude, coupons.available, clients_coupon.taken_date FROM coupons \
                   INNER JOIN clients_coupon ON coupons.coupon_id = clients_coupon.coupon_id AND \
                   coupons.branch_id = %d WHERE clients_coupon.used = false" % branch_id
    coupons_list = db.engine.execute(coupons_query)

    taken_coupons = taken_coupons_location_schema.dump(coupons_list)
    return jsonify({'data' : taken_coupons.data})


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
            (SELECT EXISTS (SELECT * FROM coupons_likes \
            WHERE coupons_likes.user_id = %d AND coupons.coupon_id = coupons_likes.coupon_id)::bool) AS user_like \
            FROM coupons INNER JOIN branches_design ON \
            coupons.branch_id = branches_design.branch_id \
            INNER JOIN branches ON coupons.branch_id = branches.branch_id \
            INNER JOIN branches_location on coupons.branch_id = branches_location.branch_id \
            WHERE deleted = false AND coupons.name ILIKE %s" % (payload['id'],"%" + "sta" + "%",)

    #list_coupon = db.engine.execute(query)
    list_coupon = db.engine.execute("SELECT * FROM coupons WHERE name ILIKE %s ", ("%" + text + "%",))

    selected_list_coupon = coupons_logo_schema.dump(list_coupon)
    return jsonify({'data': selected_list_coupon.data})

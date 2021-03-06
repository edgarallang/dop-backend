# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from ..user import *
from ..conekta_utils import *
import os
import jwt
import json
import requests
import conekta
import base64
from PIL import Image
import StringIO
conekta.api_key = 'key_ReaoWd2MyxP5QdUWKSuXBQ'
conekta.api_version = "2.0.0"
conekta.locale = 'es'

from binascii import a2b_base64
from flask import Blueprint, current_app, request, jsonify, redirect, url_for
from flask import current_app as app
from flask.ext.login import login_required, current_user
from jwt import DecodeError, ExpiredSignature
from .models import *
from ..extensions import db, socketio
from ..company import Branch, BranchUser

company = Blueprint('company', __name__, url_prefix='/api/company')

def create_token(user):
    options = {
        'verify_exp': False
    }
    payload = {
        'id': user.branches_user_id,
        'iat': datetime.now()#,
        #'exp': datetime.now() + timedelta(days=99)
    }

    token = jwt.encode(payload, app.config['TOKEN_SECRET'])
    return token.decode('unicode_escape')

def parse_token(req, token_index):
    if token_index:
        token = req.headers.get('Authorization').split()[0]
    else:
        token = req.headers.get('Authorization').split()[1]
    return jwt.decode(token, app.config['TOKEN_SECRET'])

@company.route('/auth/login', methods=['POST'])
def login():
    branchUser = BranchUser.query.filter_by(email = request.json['email'], password = request.json['password']).first()
    #flagPass = branchUser.check_password(request.json['password'])
    if not branchUser:
        response = jsonify(message='Wrong Email or Password')
        response.status_code = 401
        print response
        return response
    token = create_token(branchUser)

    return jsonify(token=token)

@company.route('/select/companies', methods=['GET'])
def companies():
    selectedCompanies = Company.query.all()
    companies = companies_schema.dump(selectedCompanies)

    return jsonify({'data': companies.data})

@company.route('/<int:companyId>/get', methods=['GET'])
def select_company(companyId):
    selectedCompany = Company.query.get(companyId)
    company = company_schema.dump(selectedCompany)

    return jsonify({'data': company.data})

@company.route('/branch/<int:branchId>/get', methods=['GET'])
def select_branch(branchId):
    selectedBranch = Branch.query.get(branchId)
    branch = branch_schema.dump(selectedBranch)

    return jsonify({'data': branch.data})

@company.route('/branch/social/view', methods=['POST'])
def set_social_views():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        social_view = SocialNetworkViews(user_id = payload['id'],
                                         owner_id = request.json['owner_id'],
                                         type = request.json['type'],
                                         view_date = datetime.now())

        if 'latitude' in request.json and 'longitude' in request.json:
            if request.json['latitude'] != 0 and request.json['longitude'] != 0:
                social_view.latitude = request.json['latitude']
                social_view.longitude = request.json['longitude']

        db.session.add(social_view)
        db.session.commit()

        return jsonify({ 'message': 'vistas actualizada' })
    return jsonify({ 'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas' })

@company.route('/branch/<int:branch_id>/full/stats/get', methods=['GET', 'POST'])
def full_stats_get(branch_id):
    if request.headers.get('Authorization'):
        token_index = False
        payload = parse_token(request, token_index)
        query = 'SELECT ((C.available = 0) OR (C.end_date < now()))::bool AS completed, \
                  B.name AS branches_name, C.name, C.description, C.start_date, C.end_date, C.views, \
                       (SELECT COUNT(*) \
                          FROM coupons_likes as CL \
                          WHERE C.coupon_id = CL.coupon_id) AS total_likes, \
                       (SELECT COUNT(*) \
                          FROM clients_coupon AS CC \
                          WHERE C.coupon_id = CC.coupon_id AND CC.used = true) AS total_uses, \
                       (SELECT COUNT(*) \
					      FROM company_stats as CS \
					      WHERE owner_id = %d) as profile_views, \
                       (SELECT COUNT(*) \
					      FROM branches_follower as BF \
					      WHERE branch_id = %d) as followers \
                 FROM coupons as C \
                   INNER JOIN branches_design AS BD ON C.owner_id = BD.branch_id \
                   INNER JOIN branches AS B on C.owner_id = B.branch_id \
                   LEFT JOIN nxn_coupon AS NC ON C.coupon_id = NC.coupon_id \
                   LEFT JOIN discount_coupon AS DC ON C.coupon_id = DC.coupon_id \
                   LEFT JOIN bond_coupon AS BC ON C.coupon_id = BC.coupon_id \
                 WHERE deleted = FALSE and B.branch_id = %d ORDER BY active DESC' % (branch_id, branch_id, branch_id)
        result = db.engine.execute(query)
        full_stats = company_stats_schema.dump(result)
        
        return jsonify({ 'data': full_stats.data })
    return jsonify({ 'error': 'Se te olvidó el token mi chavo' })

@company.route('/branch/<int:branch_id>/profile/get', methods=['GET', 'POST'])
def select_branch_profile(branch_id):
    if request.headers.get('Authorization'):
        token_index = True
        # if not request.json['token_index']:
        #     token_index = request.json['token_index']

        payload = parse_token(request, token_index)
        query = 'SELECT BL.branch_location_id, B.folio, B.branch_id, state, category_id, longitude, latitude, logo,  \
                        city, address, B.name, B.company_id, banner, logo, phone, about, BS.subcategory_id,  \
                        BD.facebook_url, BD.instagram_url, \
                        (SELECT EXISTS (SELECT * FROM branches_follower \
                                WHERE branch_id = %d AND user_id = %d)::bool) AS following, \
                        (SELECT EXISTS (SELECT * FROM branches_subcategory \
                                WHERE branch_id = %d AND subcategory_id = 25)::bool) AS adults_only \
                    FROM branches as B JOIN branches_location as BL \
                        ON B.branch_id = BL.branch_id \
                    JOIN branches_design as BD ON BD.branch_id = B.branch_id \
                    JOIN branches_subcategory as BS ON BS.branch_id = B.branch_id \
                    JOIN subcategory as S ON S.subcategory_id = BS.subcategory_id \
                 WHERE B.branch_id = %d' % (branch_id, payload['id'], branch_id, branch_id)

        selectedBranch = db.engine.execute(query)
        branch = branch_profile_schema.dump(selectedBranch)

        company_stat = CompanyStats(user_id = payload['id'],
                                    owner_id = branch_id,
                                    view_date = datetime.now())

        # if 'latitude' in request.json and 'longitude' in request.json:
        #     if request.json['latitude'] != 0 and request.json['longitude'] != 0:
        #         company_stat.latitude = request.json['latitude']
        #         company_stat.longitude = request.json['longitude']

        db.session.add(company_stat)
        db.session.commit()

        return jsonify({'data': branch.data})
    return jsonify({'message': 'Oops! algo salió mal'})

@company.route('/branch/<int:branch_id>/profile/tool/get', methods=['GET'])
def select_branch_tool_profile(branch_id):
    if request.headers.get('Authorization'):
        token_index = False
        payload = parse_token(request, token_index)
        query = 'SELECT branches_location.branch_location_id, branches.branch_id, branches.folio, state, category_id, longitude, latitude, logo,  \
                        city, address, branches.name, branches.company_id, banner, logo, phone, about,  \
                        (SELECT EXISTS (SELECT * FROM branches_subcategory \
                                WHERE branch_id = %d AND subcategory_id = 25)::bool) AS adults_only \
                    FROM branches JOIN branches_location \
                        ON branches.branch_id = branches_location.branch_id \
                    JOIN branches_design ON branches_design.branch_id = branches.branch_id \
                    JOIN branches_subcategory ON branches_subcategory.branch_id = branches.branch_id \
                    JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id \
                 WHERE branches.branch_id = %d' % (branch_id, branch_id)

        selectedBranch = db.engine.execute(query)
        branch = branch_profile_tool_schema.dump(selectedBranch)

        return jsonify({'data': branch.data})
    return jsonify({'message': 'Oops! algo salió mal'})

@company.route('/me', methods = ['POST'])
def select_branch_user():
    query = 'SELECT branches.*, branches_user.branches_user_id, \
                    branches_user.name as user_name, branches_user.email, logo, banner, credits, \
                    branches_location.latitude, branches_location.longitude \
                FROM branches_user \
                    LEFT JOIN branches ON branches_user.branch_id = branches.branch_id \
                    LEFT JOIN branches_location ON branches_user.branch_id = branches_location.branch_id \
                    LEFT JOIN companies ON branches.company_id = companies.company_id \
                    LEFT JOIN branches_design ON branches_design.branch_id = branches.branch_id \
                    WHERE branches_user.branches_user_id = %d' % request.json['branches_user_id']

    branch_data = db.engine.execute(query)
    branch = branch_user_schema.dump(branch_data)
    # selectedBranchUser = BranchUser.query.get(request.json['branches_user_id'])
    # branchUser = branch_user_schema.dump(selectedBranchUser)
    company = Company.query.get(Branch.query.get(
                                  BranchUser.query.get(request.json['branches_user_id']).branch_id)
                                    .company_id)
    if company.conekta_id:
      customer = conekta.Customer.find(company.conekta_id)
      return jsonify({ 'data': branch.data,
                       'payment_sources': {
                           "last4": customer.payment_sources[0].last4,
                           "exp_month": customer.payment_sources[0].exp_month,
                           "exp_year": customer.payment_sources[0].exp_year,
                           "brand": customer.payment_sources[0].brand,
                           "name": customer.payment_sources[0].name
                        }
                     })

    return jsonify({ 'data': branch.data })

@company.route('/branch/<int:branchId>/update ', methods=['GET'])
def update_branch_user(branchId):
    Branch.query.filter_by(branch_id=branchId).update({"name": "Bob Marley"})

    return jsonify({'data': ':P'})

ALLOWED_EXTENSIONS = set(['png'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@company.route('/branch/<int:companyId>/upload/logo', methods=['GET','POST'])
def upload_logo(companyId):
    directory = "../branches/images/%d" % companyId

    if not os.path.isdir(directory):
        os.makedirs(directory)

    image = request.form['file']
    logo = directory + "/logo.png"
    data = image.split(",")
    imgdata = base64.b64decode(data[1])

    with open(logo, 'wb') as f:
        f.write(imgdata)

    return jsonify({'data':'image'})

@company.route('/branch/<int:companyId>/upload/banner', methods=['GET','POST'])
def upload_banner(companyId):

    directory = "../branches/images/%d" % companyId


    if not os.path.isdir(directory):
        os.makedirs(directory)

    image = request.form['file']
    banner = directory + "/banner.png"
    data = image.split(",")
    imgdata = base64.b64decode(data[1])

    with open(banner, 'wb') as f:
        f.write(imgdata)

    #original = Image.open(StringIO.StringIO(imgdata))
    #size = original.size
    #left = 0
    #top = 0
    #right = size[0]
    #bottom = (size[1]/2)-31
    #cropped = original.crop((left, top, right, bottom))
    #cropped.save(directory+'/banner.png','PNG')

    return jsonify({'data':'image'})

@company.route('/branch/nearest/', methods=['GET', 'POST'])
def nearest_branches():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    radio = request.args.get('radio')

    filterQuery = ''
    prefixFilterQuery = 'AND branches_subcategory.subcategory_id = ANY(ARRAY'
    filterArray = request.json['filterArray']

    if filterArray:
        filterQuery = prefixFilterQuery + `filterArray` + ')'

    query = 'SELECT DISTINCT ON (branch_id) branch_location_id, branch_id, silent, folio,  state, city, latitude, longitude, distance, address, name, category_id, logo, company_id \
                FROM (SELECT z.branch_location_id, z.branch_id, z.state, z.city, z.address, branches_design.logo, branches.company_id, \
                    z.latitude, z.longitude, branches.name, branches.folio, branches.silent, subcategory.category_id, \
                    p.radius, \
                    p.distance_unit \
                             * DEGREES(ACOS(COS(RADIANS(p.latpoint)) \
                             * COS(RADIANS(z.latitude)) \
                             * COS(RADIANS(p.longpoint - z.longitude)) \
                             + SIN(RADIANS(p.latpoint)) \
                             * SIN(RADIANS(z.latitude)))) AS distance \
                FROM branches_location AS z \
                INNER JOIN branches on z.branch_id = branches.branch_id \
                INNER JOIN branches_design on branches.branch_id = branches_design.branch_id \
                INNER JOIN branches_subcategory on z.branch_id = branches_subcategory.branch_id \
                INNER JOIN subcategory on subcategory.subcategory_id = branches_subcategory.subcategory_id\
                INNER JOIN (   /* these are the query parameters */ \
                    SELECT  '+ latitude +'  AS latpoint,  '+ longitude +' AS longpoint, \
                            '+ radio +' AS radius,      111.045 AS distance_unit \
                ) AS p ON 1=1 \
                WHERE z.latitude \
                 BETWEEN p.latpoint  - (p.radius / p.distance_unit) \
                     AND p.latpoint  + (p.radius / p.distance_unit) \
                AND z.longitude \
                 BETWEEN p.longpoint - (p.radius / (p.distance_unit * COS(RADIANS(p.latpoint)))) \
                     AND p.longpoint + (p.radius / (p.distance_unit * COS(RADIANS(p.latpoint)))) \
                ' + filterQuery + ' \
                ) AS d \
                WHERE distance <= radius AND silent = false \
                ORDER BY branch_id, distance'

    nearestBranches = db.engine.execute(query)
    nearest = branches_location_schema.dump(nearestBranches)

    return jsonify({'data': nearest.data})

@company.route('/branch/follow',methods=['POST'])
def like_branch():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        branchFollower = BranchesFollower.query.filter_by(branch_id = request.json['branch_id'],user_id = payload['id']).first()
        if not branchFollower:
            branch_follower = BranchesFollower(branch_id = request.json['branch_id'],
                                      user_id = payload['id'],
                                      date = datetime.now())

            db.session.add(branch_follower)
            db.session.commit()
            return jsonify({'data': 'following'})
        else:
            db.session.delete(branchFollower)
            db.session.commit()
            return jsonify({'data': 'unfollowing'})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@company.route('/branch/<int:user_id>/following/get',methods=['GET'])
def following_branch(user_id):
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        query = 'SELECT * FROM branches_follower \
                    INNER JOIN branches ON branches_follower.branch_id = branches.branch_id \
                    INNER JOIN  branches_design ON branches_follower.branch_id = branches_design.branch_id \
                    WHERE user_id = %d \
                    ORDER BY branch_follower_id DESC LIMIT 6' % (user_id)

        branches_list = db.engine.execute(query)
        branches_followed = branches_followed_schema.dump(branches_list).data

        return jsonify({'data': branches_followed})

    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@company.route('/branch/<int:user_id>/following/<int:last_branch>/<int:offset>/get',methods=['GET'])
def following_branch_offset(user_id, last_branch, offset):
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        query = 'SELECT * FROM branches_follower \
                    INNER JOIN branches ON branches_follower.branch_id = branches.branch_id \
                    INNER JOIN  branches_design ON branches_follower.branch_id = branches_design.branch_id \
                    WHERE user_id = %d AND branch_follower_id < %d \
                    ORDER BY branch_follower_id DESC LIMIT 6 OFFSET %d' % (user_id, last_branch, offset)

        branches_list = db.engine.execute(query)
        branches_followed = branches_followed_schema.dump(branches_list).data

        return jsonify({'data': branches_followed})

    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

#SEARCH API
@company.route('/branch/search/', methods = ['GET'])
def search_branch():
    if request.headers.get('Authorization'):
        token_index = True
        text = request.args.get('text')
        latitude = request.args.get('latitude')
        longitude = request.args.get('longitude')

        #payload = parse_token(request, token_index)
        #list_coupon = db.engine.execute(query)
        if not latitude or not longitude or latitude == '0':
            branches = db.engine.execute("SELECT * FROM branches WHERE name ILIKE '%s' " % ('%%' + text + '%%' ))
            selected_list_branch = branch_profile_search_schema.dump(branches)
            return jsonify({'data': selected_list_branch.data})
        else:
            query = "SELECT branch_location_id, branch_id, folio,  state, city, latitude, longitude, distance, address, \
                            name, company_id, logo, category_id, banner \
                        FROM (SELECT z.branch_location_id, z.branch_id, z.state, z.city, z.address, \
                            z.latitude, z.longitude, branches.name, branches.folio, branches.company_id, branches_design.logo,branches_design.banner, subcategory.category_id, \
                            p.distance_unit \
                                     * DEGREES(ACOS(COS(RADIANS(p.latpoint)) \
                                     * COS(RADIANS(z.latitude)) \
                                     * COS(RADIANS(p.longpoint - z.longitude)) \
                                     + SIN(RADIANS(p.latpoint)) \
                                     * SIN(RADIANS(z.latitude)))) AS distance \
                        FROM branches_location AS z \
                        JOIN branches on z.branch_id = branches.branch_id \
                        JOIN branches_design on z.branch_id = branches_design.branch_id \
                        JOIN branches_subcategory on z.branch_id = branches_subcategory.branch_id \
                        JOIN subcategory ON subcategory.subcategory_id = branches_subcategory.subcategory_id \
                        JOIN (   /* these are the query parameters */ \
                            SELECT  "+latitude+"  AS latpoint,  "+longitude+" AS longpoint, \
                                         111.045 AS distance_unit \
                        ) AS p ON 1=1 \
                        WHERE branches.name ILIKE '%s' AND branches.silent = false\
                        ) AS d \
                        ORDER BY distance" % ('%%'+ text +'%%' )
            #branches = db.engine.execute("SELECT * FROM branches WHERE name ILIKE '%s' " % ('%%' + text + '%%' ))
            branches = db.engine.execute(query)

            selected_list_branch = branch_profile_search_schema.dump(branches)
            return jsonify({'data': selected_list_branch.data})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})


# - Triggers - ###########
@company.route('/first/trigger', methods = ['GET', 'PUT'])
def fisrt_job():
    adArray = BranchAd.query.filter(BranchAd.duration > 0).all()

    for ad in adArray:
        if not (ad.duration == 0):
            ad.duration = ad.duration - 1
    db.session.commit()
    return jsonify({'message': 'the trigger went well'})

@company.route('/branch/dashboard', methods = ['GET'])
def dashboard_branches():
    token_index = True
    payload = parse_token(request, token_index)
    user = User.query.get(payload['id'])

    if user.adult:
        adBranches = 'SELECT * FROM branches \
                INNER JOIN branches_design ON branches.branch_id = branches_design.branch_id \
                INNER JOIN branch_ad ON branches.branch_id = branch_ad.branch_id \
                INNER JOIN branches_subcategory ON branches.branch_id = branches_subcategory.branch_id \
                WHERE branch_ad.duration>0 AND branches.silent = false ORDER BY branch_ad.start_date LIMIT 8'
    else:
        adBranches = 'SELECT * FROM branches \
                 INNER JOIN branches_design ON branches.branch_id = branches_design.branch_id \
                 INNER JOIN branch_ad ON branches.branch_id = branch_ad.branch_id \
                 INNER JOIN branches_subcategory ON branches.branch_id = branches_subcategory.branch_id \
                 WHERE branch_ad.duration>0 AND branches_subcategory.subcategory_id != 25 AND branches.silent = false ORDER BY branch_ad.start_date LIMIT 8'

    branches = db.engine.execute(adBranches)

    selected_list_branch = branch_ad_schema.dump(branches)


    result = number_of_rows(selected_list_branch.data)

    remaining = 8-result

    if remaining > 0:
        filterArray = []

        for branch in selected_list_branch.data:
            filterArray.append(branch["branch_id"])

        filterQuery = ''
        prefixFilterQuery = 'AND branches.branch_id != ALL(ARRAY'

        if filterArray:
            filterQuery = prefixFilterQuery + `filterArray` + ')'

        remainingBranches = 'SELECT * FROM branches \
                              JOIN branches_design ON branches.branch_id = branches_design.branch_id \
                              INNER JOIN branches_subcategory ON branches.branch_id = branches_subcategory.branch_id \
                              WHERE branches.silent = false' + filterQuery + ' ORDER BY RANDOM() LIMIT %d' % (remaining)

        extra_branches = db.engine.execute(remainingBranches)
        selected_list_extra = branch_ad_schema.dump(extra_branches)

    return jsonify({'data': selected_list_branch.data+selected_list_extra.data})

def calculate_age(born):
    today = datetime.now()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

@company.route('/branch/<int:branch_id>/ranking/get', methods = ['GET'])
def branch_ranking(branch_id):
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        query = 'SELECT DISTINCT users.*, client.clients_coupon_id, users_image.main_image, friends.operation_id, \
                    (SELECT COUNT(*) FROM clients_coupon \
                       INNER JOIN coupons ON clients_coupon.coupon_id = coupons.coupon_id \
                       WHERE users.user_id = clients_coupon.user_id AND used = TRUE AND coupons.owner_id = %d) AS total_used, \
                       (SELECT EXISTS (SELECT * FROM friends \
                                        WHERE friends.user_one_id = %d and friends.user_two_id = users.user_id AND friends.operation_id = 1)::bool) AS is_friend \
                    FROM users JOIN (SELECT DISTINCT ON (user_id) * FROM clients_coupon ORDER BY user_id) AS client ON users.user_id = client.user_id \
                               JOIN users_image ON users.user_id = users_image.user_id \
                               LEFT JOIN friends ON friends.user_one_id = %d AND friends.user_two_id = users.user_id \
                ORDER BY total_used DESC LIMIT 20' % (branch_id, payload['id'], payload['id'])

        ranking_users = db.engine.execute(query)
        ranking_users_list = ranking_users_schema.dump(ranking_users).data

        return jsonify({'data': ranking_users_list})

    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@company.route('/<int:branch_id>/credits/add', methods = ['GET', 'POST'])
def credit_add(branch_id):
    if request.headers.get('Authorization'):
        token_index = False
        payload = parse_token(request, token_index)
        payment_data = request.json['paymentData']
        try:
            charge = conekta.Charge.create({
              "amount": payment_data['total'],
              "currency": "MXN",
              "description": "Compra de campaña",
              "reference_id": branch_id,
              "card": request.json['token_id'],
              "details": {
                "email": 'calis@gmail.com'
              }
            })
        except conekta.ConektaError as e:
            return jsonify({ 'message': e['message_to_purchaser'] })
        #el pago no pudo ser procesado
        if (charge.status == 'paid'):
            company = Company.query.get(Branch.query.get(branch_id).company_id)
            if (payment_data['total'] >= 100000) and (payment_data['total'] < 200000):
                bonus = (payment_data['total'] / 100) * 0.1
            if (payment_data['total'] >= 200000) and (payment_data['total'] < 500000):
                bonus = (payment_data['total'] / 100) * 0.25
            if (payment_data['total'] >= 500000):
                bonus = (payment_data['total'] / 100) * 0.4
            company.credits = company.credits + (payment_data['total'] / 100) + bonus

            db.session.commit()

            return jsonify({'data': 'success'})
        return jsonify({'message': 'Oops! algo salió mal, seguramente fue tu tarjeta sobregirada'})

    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})
  
@company.route('/<int:branch_id>/payment/method/add', methods = ['POST'])
def add_payment_method(branch_id):
    if request.headers.get('Authorization'):
        token_index = False
        payload = parse_token(request, token_index)

        branch = Branch.query.get(branch_id)
        company = Company.query.get(branch.company_id)
        
        if not company.conekta_id:
            try:
                customer = conekta.Customer.create({
                    'name': branch.name,
                    'email': company.email,
                    'phone': branch.phone,
                    'payment_sources': [{
                      'type': 'card',
                      'token_id': request.json['token_id']
                    }]
                })
                company.conekta_id = customer.id
                db.session.commit()
            
                return jsonify({ 'message': 'Se agregó metodo de pago',
                                 'data': 'success',
                                 'payment_sources': {
                                    "last4": customer.payment_sources[0].last4,
                                    "exp_month": customer.payment_sources[0].exp_month,
                                    "exp_year": customer.payment_sources[0].exp_year,
                                    "brand": customer.payment_sources[0].brand,
                                    "name": customer.payment_sources[0].name
                                 }
                               })
            
            except conekta.ConektaError as e:
                print e.message
                return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, échale ganas',
                                'error': e.message,
                                'phone': branch.phone })
        else:
            customer = conekta.Customer.find(company.conekta_id)
            source = create_payment_method(customer, request.json['token_id'])
            if source:
                return jsonify({ 'data': 'Se agregó metodo de pago',
                                 'payment_sources': {
                                    "last4": customer.payment_sources[0].last4,
                                    "exp_month": customer.payment_sources[0].exp_month,
                                    "exp_year": customer.payment_sources[0].exp_year,
                                    "brand": customer.payment_sources[0].brand,
                                    "name": customer.payment_sources[0].name
                                 }
                               })
            else:
                return jsonify({ 'data': 'algo falló, intenta de nuevo' })
        return jsonify({ 'message': 'Oops! algo salió mal, intentalo de nuevo, échale ganas' })

@company.route('/<int:branch_id>/pro/subscription', methods = ['GET', 'POST'])
def monthly_subscription(branch_id):
    if request.headers.get('Authorization'):
        token_index = False
        payload = parse_token(request, token_index)
        payment_data = request.json['paymentData']
        branch = Branch.query.get(branch_id)
        company = Company.query.get(branch.company_id)
        
        if not company.conekta_id:
            try:
                customer = conekta.Customer.create({
                    'name': branch.name,
                    'email': company.email,
                    'phone': branch.phone,
                    'payment_sources': [{
                      'type': 'card',
                      'token_id': request.json['token_id']
                    }]
                })
                company.conekta_id = customer.id
                db.session.commit()
                
                subscription = create_subscription(customer, request.json['token_id'])
                
                if subscription:
                    branch.pro = True
                    db.session.commit()
                    return jsonify({'data': 'PRO'})
                else:
                    return jsonify({'data': 'algo falló, tal vez sea tu tarjeta'})
            except conekta.ConektaError as e:
                print e.message
        
        elif not branch.pro:
            customer = conekta.Customer.find(company.conekta_id)
            #Si el usuario no tiene tarjeta de credito agregada se crea
            subscription = create_subscription(customer, request.json['token_id'])
            #si se agrega con exito se suscribe al plan mensual
            if subscription:
                branch.pro = True
                db.session.commit()
                return jsonify({'data': 'PRO'})
            #si source o subscription es false la tarjeta no se pudo agregar y no se suscribe
            else:
                return jsonify({'data': 'algo falló, tal vez sea tu tarjeta'}) 
        return jsonify({'data': 'algo falló, o ya eras PRO'})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

@company.route('/<int:branch_id>/config/set', methods = ['GET', 'POST'])
def set_config(branch_id):
    if request.headers.get('Authorization'):
        token_index = False
        payload = parse_token(request, token_index)

        messages = { 'locator': '',
                     'about': '' }
        longitude = request.json['data']['locator']['longitude']
        latitude = request.json['data']['locator']['latitude']
        state = request.json['data']['locator']['state']
        city = request.json['data']['locator']['city']
        address = request.json['data']['locator']['description']

        branchLocation = BranchLocation.query.filter_by(branch_id = branch_id).first()

        if not branchLocation:
            branchLocation = BranchLocation(branch_id = branch_id,
                                            state = state,
                                            longitude = longitude,
                                            latitude = latitude,
                                            city = city,
                                            address = address)
            db.session.add(branchLocation)
            db.session.commit()
            messages['locator'] = 'Localización creada.'
        else:
            if address:
                branchLocation.state = state
                branchLocation.longitude = longitude
                branchLocation.latitude = latitude
                branchLocation.city = city
                branchLocation.address = address
            else:
                branchLocation.longitude = longitude
                branchLocation.latitude = latitude

            db.session.commit()
            messages['locator'] = 'Localización asignada.'

        branch = Branch.query.get(branch_id)

        if request.json['data']['about']:
            name = request.json['data']['about']['name']
            phone = request.json['data']['about']['phone']
            description = request.json['data']['about']['description']

            if name:
                branch.name = name
            if phone:
                branch.phone = phone
            if description:
                branch.about = description

            db.session.commit()
            messages['about'] = 'Información asignada.'

        return jsonify({'messages': messages})
    return jsonify({'message': 'Oops! algo salió mal, al parecer no tienes autorización'})

# @company.route('/<int:branch_id>/config/get', methods = ['GET', 'POST'])
# def get_config(branch_id):

@company.route('/auth/signup', methods = ['POST'])
def signup_branch():
    company = Company(name = request.json['name'],
                      email = request.json['email'],
                      credits = 400)

    db.session.add(company)
    db.session.commit()

    branch = Branch(company_id = company.company_id,
                    name = '',
                    about = '',
                    phone = '',
                    folio = '',
                    silent = False,
                    pro = False)

    db.session.add(branch)
    db.session.commit()

    branch_user = BranchUser( branch_id = branch.branch_id,
                              name = 'Admin',
                              email = company.email,
                              password = request.json['password'] )

    db.session.add(branch_user)
    db.session.commit()

    branches_subcategory = BranchSubcategory( subcategory_id = 0,
                                              branch_id = branch.branch_id )

    db.session.add(branches_subcategory)
    db.session.commit()

    branches_design = BranchDesign( branch_id = branch.branch_id,
                                    logo = 'logo.png',
                                    color_a = None,
                                    color_b = None,
                                    color_c = None,
                                    banner = 'banner.png',
                                    facebook_url = '',
                                    instagram_url = '' )

    db.session.add(branches_design)
    db.session.commit()

    token = create_token(branch_user)
    return jsonify(token=token)

def number_of_rows(query):
    result = 0
    for row in query:
        result += 1
    return result


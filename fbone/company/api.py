# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
import jwt
import json
import requests
from flask import Blueprint, current_app, request, jsonify, create_app
APSapp = create_app()
APSapp.test_request_context().push()
from flask import current_app as app
from flask.ext.login import login_required, current_user
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from jwt import DecodeError, ExpiredSignature
from .models import *
from ..extensions import db



company = Blueprint('company', __name__, url_prefix='/api/company')

def create_token(user):
    payload = {
        'id': user.branches_user_id,
        'iat': datetime.now(),
        'exp': datetime.now() + timedelta(days=14)
    }

    token = jwt.encode(payload, app.config['TOKEN_SECRET'])
    return token.decode('unicode_escape')

def parse_token(req, token_index):
    if token_index:
        token = req.headers.get('Authorization').split()[0]
    else:
        token = req.headers.get('Authorization').split()[1]
    return jwt.decode(token, app.config['TOKEN_SECRET'])

def parse_token(req, token_index):
    if token_index:
        token = req.headers.get('Authorization').split()[0]
    else:
        token = req.headers.get('Authorization').split()[1]
    return jwt.decode(token, app.config['TOKEN_SECRET'])

@company.route('/auth/signup', methods=['POST'])
def signup():
    branchUser = BranchUser(email = request.json['email'],
                            password = request.json['password'],
                            branch_id = request.json['branch_id'],
                            name = request.json['name'])
    db.session.add(branchUser)
    db.session.commit()
    token = create_token(branchUser)

    return jsonify(token=token)

@company.route('/auth/login', methods=['POST'])
def login():
    branchUser = BranchUser.query.filter_by(email = request.json['email']).first()
    flagPass = branchUser.check_password(request.json['password'])
    if not branchUser or not flagPass:
        response = jsonify(message='Wrong Email or Password')
        response.status_code = 401
        return response
    print 
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

@company.route('/branch/<int:branchId>/profile/get', methods=['GET'])    
def select_branch_profile(branchId):
    query = 'SELECT * FROM branches INNER JOIN branches_location \
             ON branches.branch_id = branches_location.branch_id \
             WHERE branches.branch_id = %d' % branchId

    selectedBranch = db.engine.execute(query)
    branch = branch_profile_schema.dump(selectedBranch)
    
    return jsonify({'data': branch.data})

@company.route('/me', methods = ['POST'])    
def select_branch_user():
    selectedBranchUser = BranchUser.query.get(request.json['branches_user_id'])
    branchUser = branch_user_schema.dump(selectedBranchUser)

    return jsonify({'data': branchUser.data})

@company.route('/branch/<int:branchId>/update ', methods=['GET'])    
def update_branch_user(branchId):
    Branch.query.filter_by(branch_id=branchId).update({"name": "Bob Marley"})

    return jsonify({'data': ':P'})

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

    query = 'SELECT branch_location_id, branch_id, state, city, latitude, longitude, distance, address, name \
                FROM (SELECT z.branch_location_id, z.branch_id, z.state, z.city, z.address, \
                    z.latitude, z.longitude, branches.name, \
                    p.radius, \
                    p.distance_unit \
                             * DEGREES(ACOS(COS(RADIANS(p.latpoint)) \
                             * COS(RADIANS(z.latitude)) \
                             * COS(RADIANS(p.longpoint - z.longitude)) \
                             + SIN(RADIANS(p.latpoint)) \
                             * SIN(RADIANS(z.latitude)))) AS distance \
                FROM branches_location AS z \
                JOIN branches on z.branch_id = branches.branch_id \
                JOIN branches_subcategory on z.branch_id = branches_subcategory.branch_id \
                JOIN (   /* these are the query parameters */ \
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
                WHERE distance <= radius \
                ORDER BY distance'

    nearestBranches = db.engine.execute(query)
    nearest = branches_location_schema.dump(nearestBranches)
    
    return jsonify({'data': nearest.data})

@company.route('/branch/follow',methods=['POST'])
def like_branch():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        branchLike = BranchesLikes.query.filter_by(branch_id = request.json['branch_id'],user_id = payload['id']).first()
        if not branchLike:
            branch_like = BranchesLikes(branch_id = request.json['branch_id'],
                                      user_id = payload['id'],
                                      date = request.json['date'])

            db.session.add(branch_like)
            db.session.commit()
            return jsonify({'message': 'El like se asigno con éxito'})
        else:
            db.session.delete(branchLike)
            db.session.commit()
            return jsonify({'message': 'El like se elimino con éxito'})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

#SEARCH API
@company.route('/branch/search/', methods = ['GET','POST'])
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
            selected_list_branch = branch_profile_schema.dump(branches)
            return jsonify({'data': selected_list_branch.data})
        else:
            query = "SELECT branch_location_id, branch_id, state, city, latitude, longitude, distance, address, name \
                        FROM (SELECT z.branch_location_id, z.branch_id, z.state, z.city, z.address, \
                            z.latitude, z.longitude, branches.name, \
                            p.distance_unit \
                                     * DEGREES(ACOS(COS(RADIANS(p.latpoint)) \
                                     * COS(RADIANS(z.latitude)) \
                                     * COS(RADIANS(p.longpoint - z.longitude)) \
                                     + SIN(RADIANS(p.latpoint)) \
                                     * SIN(RADIANS(z.latitude)))) AS distance \
                        FROM branches_location AS z \
                        JOIN branches on z.branch_id = branches.branch_id \
                        JOIN branches_subcategory on z.branch_id = branches_subcategory.branch_id \
                        JOIN (   /* these are the query parameters */ \
                            SELECT  "+latitude+"  AS latpoint,  "+longitude+" AS longpoint, \
                                         111.045 AS distance_unit \
                        ) AS p ON 1=1 \
                        WHERE branches.name ILIKE '%s' \
                        ) AS d \
                        ORDER BY distance" % ('%%'+ text +'%%' )
            #branches = db.engine.execute("SELECT * FROM branches WHERE name ILIKE '%s' " % ('%%' + text + '%%' ))
            branches = db.engine.execute(query)

            selected_list_branch = branch_profile_schema.dump(branches)
            return jsonify({'data': selected_list_branch.data})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

# -Triggers- ######################################
def job_function():
    with APSapp():
        adArray = BranchAd.query.all()

        for ad in branchesArray:
            branch = Branch.query.get(ad.branch_id)
            print branch.name





###################################################



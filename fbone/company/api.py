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


company = Blueprint('company', __name__, url_prefix='/api/company')

def create_token(user):
    payload = {
        'id': user.branches_user_id,
        'iat': datetime.now(),
        'exp': datetime.now() + timedelta(days=14)
    }

    token = jwt.encode(payload, app.config['TOKEN_SECRET'])

    return token.decode('unicode_escape')

def parse_token(req):
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

@company.route('/me', methods = ['POST'])    
def select_branch_user():
    selectedBranchUser = BranchUser.query.get(request.json['branches_user_id'])
    branchUser = branch_user_schema.dump(selectedBranchUser)

    return jsonify({'data': branchUser.data})

@company.route('/branch/<int:branchId>/update', methods=['GET'])    
def update_branch_user(branchId):
    Branch.query.filter_by(branch_id=branchId).update({"name": "Bob Marley"})

    return jsonify({'data': ':P'})

@company.route('/branch/nearest/', methods=['GET'])
def nearest_branches():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    radio = request.args.get('radio')

    query = 'SELECT branch_location_id, state, city, latitude, longitude, distance \
                FROM (SELECT z.branch_location_id, z.state, z.city, \
                    z.latitude, z.longitude, \
                    p.radius, \
                    p.distance_unit \
                             * DEGREES(ACOS(COS(RADIANS(p.latpoint)) \
                             * COS(RADIANS(z.latitude)) \
                             * COS(RADIANS(p.longpoint - z.longitude)) \
                             + SIN(RADIANS(p.latpoint)) \
                             * SIN(RADIANS(z.latitude)))) AS distance \
                FROM branches_location AS z \
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
                ) AS d \
                WHERE distance <= radius \
                ORDER BY distance \
                LIMIT 15'

    nearestBranches = db.engine.execute(query)

    print nearestBranches
    return 'ok entró'


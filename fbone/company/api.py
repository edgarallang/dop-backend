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
    branchUser = BranchUser(email=request.json['email'], password=request.json['password'], branch_id=request.json['branch_id'], name=request.json['name'])
    db.session.add(branchUser)
    db.session.commit()
    token = create_token(branchUser)

    return jsonify(token=token)

@company.route('/auth/login', methods=['POST'])
def login():
    branchUser = BranchUser.query.filter_by(email=request.json['email']).first()
    flagPass = branchUser.check_password(request.json['password'])
    if not branchUser or not flagPass:
        response = jsonify(message='Wrong Email or Password')
        response.status_code = 401
        return response
    token = create_token(branchUser)

    return jsonify(token=token)

@company.route('/select/companies', methods=['GET'])    
def companies():
    selectedCompanies = Company.query.all()
    companies = companies_schema.dump(selectedCompanies)

    return jsonify(companies)

@company.route('/select/company/<int:companyId>', methods=['GET'])    
def select_company(companyId):
    selectedCompany = Company.query.get(companyId)
    company = company_schema.dump(selectedCompany)

    return jsonify(company)

@company.route('/select/branch/<int:branchId>', methods=['GET'])    
def select_branch(branchId):
    selectedBranch = Branch.query.get(branchId)
    branch = branch_schema.dump(selectedBranch)
    
    return jsonify(branch)

@company.route('/me', methods = ['POST'])    
def select_branch_user():
    selectedBranchUser = BranchUser.query.get(request.json['branches_user_id'])
    branchUser = branch_user_schema.dump(selectedBranchUser)

    return jsonify(branchUser)

@company.route('/update/branch/<int:branchId>', methods=['GET'])    
def update_branch_user(branchId):
    Branch.query.filter_by(branch_id=branchId).update({"name": "Bob Marley"})

    return jsonify({'data': ':P'})

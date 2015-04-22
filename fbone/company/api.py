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
from .models import Company, Branch, BranchDesign, BranchLocation, BranchUser, Category
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

@company.route('/select-companies', methods=['GET'])    
def companies():
    result = db.engine.execute("SELECT * FROM companies")
    user = {
        'user': 'pikochin',
        'pass': 123456
    }
    names = []
    for row in result:
        names.append(row[1])

    return jsonify({'data': names})

@company.route('/select/company', methods=['GET'])    
def select_company():
    selectCompany = Company.query.filter_by(company_id=request.json['company_id']).first()
    companyName = selectCompany.get_name()
    company = {
        'name': company
    }

    return jsonify({'data': company})

@company.route('/select/branch', methods=['GET'])    
def select_branch():
    selectBranch = Branch.query.filter_by(branch_id=request.json['branch_id']).first()
    branchCompanyId = selectBranch.get_company_id()
    branchName = selectBranch.get_name()
    branchCategoryId = selectBranch.get_category_id()
    branch = {
        'company_id': branchCompanyId,
        'category_id': branchCategoryId,
        'name': branchName
    }

    return jsonify({'data': branch})

@company.route('/me', methods=['GET'])    
def select_branch_user():
    selectBranchUser = BranchUser.query.filter_by(branches_user_id=request.json['branches_user_id']).first()
    branchId = selectBranchUser.get_branch_id()
    branchUserName = selectBranchUser.get_name()
    branchEmail = selectBranchUser.get_email()
    selectBranch = Branch.query.filter_by(branch_id=branchId).first()
    branchName = selectBranch.get_name()
    branchUser = {
        'branch_id': branchId,
        'name': branchUserName,
        'email': branchEmail,
        'branch_name': branchName
    }

    return jsonify({'data': branchUser})

@company.route('/update/branch', methods=['GET'])    
def update_branch_user():
    Branch.query.filter_by(branch_id=request.json['branch_id']).update({"name": "Bob Marley"})

    return jsonify({'data': ':P'})

# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
import jwt
import json
import requests
from flask import Blueprint, current_app, request, jsonify
from flask import current_app as APP
from flask.ext.login import login_required, current_user
from jwt import DecodeError, ExpiredSignature
from .models import Company, Branch, BranchDesign, BranchLocation, BranchUser, Category


company = Blueprint('company', __name__, url_prefix='/')

# @company.route('/signup', methods=['GET', 'POST'])
# def signup():
#     if current_user.is_authenticated():
#         return redirect(url_for('user.index'))

#     form = SignupForm(next=request.args.get('next'))

#     if form.validate_on_submit():
#         user = User()
#         # user.user_detail = UserDetail()
#         form.populate_obj(user)

#         db.session.add(user)
#         db.session.commit()

#         if login_user(user):
#             return redirect(form.next.data or url_for('user.index'))

#     return render_template('frontend/signup.html', form=form)

@company.route('/auth/signup', methods=['POST'])
def signup():
    branchUser = BranchUserUser(email=request.json['email'], password=request.json['password'])
    db.session.add(branchUser)
    db.session.commit()
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

    return jsonify({'AquiEstaTuApi': names})


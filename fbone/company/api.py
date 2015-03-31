# -*- coding: utf-8 -*-

import os

from flask import Blueprint, render_template, send_from_directory, abort
from flask import current_app as APP
from flask.ext.login import login_required, current_user
from ..extensions import db
from .models import Company, Branch, BranchDesign, BranchLocation, BranchUser, Category


company = Blueprint('company', __name__, url_prefix='/')

@company.route('/signup', methods=['GET'])	
def companies():
	result = db.engine.execute("SELECT * FROM companies")
	user = {
        'user': 'Edgar Allan',
        'pass': 123456
    }
    print result
    return jsonify({'AquiEstaTuApi': user})

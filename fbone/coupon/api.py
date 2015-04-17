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
from .models import 
from ..extensions import db


company = Blueprint('coupon', __name__, url_prefix='/api/coupon')

@company.route('/bond/create', methods=['POST'])
def create_bond():

@company.route('/discount/create', methods=['POST'])
def create_discount():

@company.route('/nxn/create', methods=['POST'])
def create_nxn():
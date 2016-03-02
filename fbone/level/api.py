# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
import jwt
import json
import requests
from flask import Blueprint, render_template, send_from_directory, abort, jsonify
from flask import current_app as APP
from flask.ext.login import login_required, current_user
from jwt import DecodeError, ExpiredSignature
from .models import Level

level = Blueprint('level', __name__, url_prefix='/level')

@level.route('/select_level', methods=['GET'])
def levels():
    lvl = {
      'name': 'Dragon Master',
      'benefits': 'Ruby',
      'lvl': 30
    }
    return jsonify(level=lvl)

@level.route('/set_levels', methods=['GET'])
def set_levels():
	first_flag = 0
	second_flag = 15

	for x in range(0, 20):

		result = first_flag + second_flag
		print result

		first_flag = second_flag
		second_flag = second_flag + first_flag

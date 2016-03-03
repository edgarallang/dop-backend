# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
import jwt
import json
import math
import requests
from flask import Blueprint, render_template, send_from_directory, abort, jsonify
from flask import current_app as APP
from flask.ext.login import login_required, current_user
from jwt import DecodeError, ExpiredSignature
from .models import Level
from ..extensions import db

level = Blueprint('level', __name__, url_prefix='/level')

@level.route('/select_level', methods=['GET'])
def levels():
    lvl = {
      'name': 'Dragon Master',
      'benefits': 'Ruby',
      'lvl': 30
    }
    return jsonify(level=lvl)

@level.route('/set_level_table', methods=['GET'])
def set_levels():
    for x in range(1, 51):
      result = int(math.ceil(15 * (math.pow(x, 1.3))))
      new_level = Level(min_exp = result, badge_id = 1)

      db.session.add(new_level)

    db.session.commit()

    return jsonify(message = "success")

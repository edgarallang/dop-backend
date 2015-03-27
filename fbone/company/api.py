# -*- coding: utf-8 -*-

import os

from flask import Blueprint, render_template, send_from_directory, abort
from flask import current_app as APP
from flask.ext.login import login_required, current_user

from .models import Company, Branch, BranchDesign, BranchLocation, BranchUser, Category


company = Blueprint('company', __name__, url_prefix='/')
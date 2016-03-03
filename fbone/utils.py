# -*- coding: utf-8 -*-
"""
    Utils has nothing to do with models and views.
"""

import string
import random
import os
import requests
from flask import jsonify

from datetime import datetime


# Instance folder path, make it independent.
INSTANCE_FOLDER_PATH = os.path.join('/tmp', 'instance')

ALLOWED_AVATAR_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

# Form validation

USERNAME_LEN_MIN = 4
USERNAME_LEN_MAX = 25

REALNAME_LEN_MIN = 4
REALNAME_LEN_MAX = 25

PASSWORD_LEN_MIN = 6
PASSWORD_LEN_MAX = 16

AGE_MIN = 1
AGE_MAX = 300

DEPOSIT_MIN = 0.00
DEPOSIT_MAX = 9999999999.99

# Sex type.
MALE = 1
FEMALE = 2
OTHER = 9
SEX_TYPE = {
    MALE: u'Male',
    FEMALE: u'Female',
    OTHER: u'Other',
}

# Model
STRING_LEN = 264

############# EXP CONSTANTS ################

SHARE = 5
PAGE_LIKE = 10
INVITE = 20
USING = 5
FIRST_FOLLOWING = 3
FIRST_FOLLOWER = 3
FIRST_COMPANY_FAV = 3
FIRST_USING = 5
FACEBOOK_LOGIN = 5

############################################

############## LEVELS CONSTANTS ############

LEVELS = {
    '1': '15',
    '2': '37',
    '3': '63',
    '4': '91',
    '5': '122',
    '6': '155',
    '7': '189',
    '8': '224',
    '9': '261',
    '10': '300',
    '11': '339',
    '12': '380',
    '13': '421',
    '14': '464',
    '15': '508',
    '16': '552',
    '17': '597',
    '18': '643',
    '19': '690',
    '20': '737',
    '21': '786',
    '22': '835',
    '23': '884',
    '24': '935',
    '25': '985',
    '26': '1037',
    '27': '1089',
    '28': '1142',
    '29': '1195',
    '30': '1249',
    '31': '1303',
    '32': '1358',
    '33': '1414',
    '34': '1469',
    '35': '1526',
    '36': '1583',
    '37': '1640',
    '38': '1698',
    '39': '1756',
    '40': '1815',
    '41': '1874',
    '42': '1934',
    '43': '1994',
    '44': '2054',
    '45': '2115',
    '46': '2177',
    '47': '2238',
    '48': '2300',
    '49': '2363',
    '50': '2426'
}


############################################

############## BADGES CONSTANTS ############

BADGES = {
    'bronce': 50,
    'plata': 200,
    'oro': 500,
    'ruby': 1000
}


#############################################

def assign_exp(user_id, exp):
    response = requests.put("https://inmoon.com.mx/api/user/"+`user_id`+"/"+`exp`+"/set")
    return response.json()
    # except: return jsonify({'message': 'Oops! algo salió mal'})

def get_current_time():
    return datetime.utcnow()


def pretty_date(dt, default=None):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    Ref: https://bitbucket.org/danjac/newsmeme/src/a281babb9ca3/newsmeme/
    """

    if default is None:
        default = 'just now'

    now = datetime.utcnow()
    diff = now - dt

    periods = (
        (diff.days / 365, 'year', 'years'),
        (diff.days / 30, 'month', 'months'),
        (diff.days / 7, 'week', 'weeks'),
        (diff.days, 'day', 'days'),
        (diff.seconds / 3600, 'hour', 'hours'),
        (diff.seconds / 60, 'minute', 'minutes'),
        (diff.seconds, 'second', 'seconds'),
    )

    for period, singular, plural in periods:

        if not period:
            continue

        if period == 1:
            return u'%d %s ago' % (period, singular)
        else:
            return u'%d %s ago' % (period, plural)

    return default


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_AVATAR_EXTENSIONS


def id_generator(size=10, chars=string.ascii_letters + string.digits):
    #return base64.urlsafe_b64encode(os.urandom(size))
    return ''.join(random.choice(chars) for x in range(size))


def make_dir(dir_path):
    try:
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
    except Exception, e:
        raise e

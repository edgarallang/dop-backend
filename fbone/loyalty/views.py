# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
import jwt
import json
import requests
from flask import Blueprint, request, jsonify, session
from flask import current_app as app
from flask.ext.login import login_required, current_user
from jwt import DecodeError, ExpiredSignature
from sqlalchemy import and_, desc
from .models import *
from ..user import *
from ..company import *
from ..badge import *
from ..utils import *
from ..extensions import db, socketio

loyalty = Blueprint('loyalty', __name__, url_prefix='/api/loyalty')

def parse_token(req, token_index):
    if token_index:
        token = req.headers.get('Authorization').split()[0]
    else:
        token = req.headers.get('Authorization').split()[1]
    return jwt.decode(token, app.config['TOKEN_SECRET'])

def parse_token_socket(token):
    return jwt.decode(token, app.config['TOKEN_SECRET'])

def create_token(user):
    payload = {
        'id': user.user_id,
        'iat': datetime.now(),
        'exp': datetime.now() + timedelta(days=14)
    }

    token = jwt.encode(payload, app.config['TOKEN_SECRET'])

    return token.decode('unicode_escape')

#leveling up
def level_up(user_id):
    user = User.query.get(user_id)
    exp = user.exp
    for key, val in sorted(LEVELS.iteritems(), key=lambda x: x[1]):
        print key, val
        print exp >= val
        if (exp >= val):
            user.level = key
        else:
            break
    db.session.commit()
    return user.level

def set_experience(user_id, exp):
    user = User.query.get(user_id)
    old_exp = user.exp
    user.exp = old_exp + exp
    badge_name = []

    for key, val in sorted(BADGES.iteritems(), key=lambda x: x[1]):
        if (val > old_exp) and (val <= user.exp):
          badge_name.append(key)

    badges_tuple = tuple(badge_name)
    if len(badges_tuple) == 1:
        badge = db.engine.execute("SELECT * FROM badges WHERE LOWER(name) in(" + `badges_tuple[0]`+")")
    elif len(badges_tuple) > 1:
        badge = db.engine.execute("SELECT * FROM badges WHERE LOWER(name) in" + `badges_tuple`)

    db.session.commit()
    if len(badges_tuple) == 0:
        return { 'message': 'experiencia asignada %d' % exp }
    else:
        badges = badge_schema.dump(badge)
        return {'message': 'experiencia asignada %d' % exp,
                           'badges': badges.data }

@loyalty.route('/all/get/', methods=['GET'])
def loyalty_all_get():
    token_index = True
    payload = parse_token(request, token_index)
    limit = request.args.get('limit')
    query = "SELECT L.loyalty_id, L.owner_id, L.name, L.description, L.type, \
                        L.goal, L.is_global, L.end_date, LD.logo, LU.visit, B.company_id \
                FROM loyalty as L \
                INNER JOIN branches as B on L.owner_id = B.branch_id \
                LEFT JOIN loyalty_design as LD ON LD.loyalty_id = L.loyalty_id \
                LEFT JOIN loyalty_user as LU ON LU.loyalty_id = L.loyalty_id \
                AND LU.user_id = %d LIMIT %s" % (payload['id'], limit)
    
    loyalty = db.engine.execute(query)
    loyalty_list = loyalties_schema.dump(loyalty)
    return jsonify({'data': loyalty_list.data})

@loyalty.route('/<int:owner_id>/get', methods=['GET'])
def loyalty_get(owner_id):
    token_index = True
    payload = parse_token(request, token_index)
    query = "SELECT L.loyalty_id, L.owner_id, L.name, L.description, L.type, \
                        L.goal, L.is_global, L.end_date, LD.logo, LU.visit, B.company_id \
                FROM loyalty as L \
                INNER JOIN branches as B on L.owner_id = B.branch_id \
                INNER JOIN loyalty_design as LD ON LD.loyalty_id = L.loyalty_id \
                LEFT JOIN loyalty_user as LU ON LU.loyalty_id = L.loyalty_id AND LU.user_id = %d \
                WHERE L.owner_id = %d" % (payload['id'], owner_id)
    loyalty = db.engine.execute(query)
    loyalty_list = loyalties_schema.dump(loyalty)
    return jsonify({'data': loyalty_list.data})

@loyalty.route('/user/redeem/by/branch', methods=['POST'])
def loyalty_redeem():
    branch_id = request.json['branch_id']
    loyaly_id = request.json['loyalty_id']
    branch_folio = request.json['branch_folio']
    user_id = request.json['user_id']
    today = datetime.now()

    loyalty = Loyalty.query.get(loyalty_id)

    if loyalty.is_global:
        branch = Branch.query.filter_by(folio = branch_folio, silent = True).first()
        if not branch:
            return jsonify({'message':'error'})

    recently_used = LoyaltyRedeem.query.filter_by(loyalty_id = loyalty_id,
                                                    user_id = user_id).order_by(desc(LoyaltyRedeem.date)).first()
    if recently_used:
        minutes = (today - recently_used.date).total_seconds() / 60

    if not recently_used or minutes > 480: # 8 hours
        loyalty_redeem = LoyaltyRedeem(user_id = user_id,
                                        loyalty_id = loyalty_id,
                                        date = today,
                                        private = True,
                                        branch_folio = branch_folio)
        db.session.add(loyalty_redeem)
        db.session.commit()

        folio = '%d%s%d' % (request.json['branch_id'], "{:%d%m%Y}".format(today),
                                    loyalty_redeem.loyalty_redeem_id)

        loyalty_user = LoyaltyUser.query.filter_by(loyalty_id = loyalty_id,
                                                         user_id = payload['id']).first()

        if not loyalty_user:
            loyalty_user = LoyaltyUser(user_id = payload['id'],
                                        loyalty_id = loyalty_id,
                                        visit = 1)

            db.session.add(loyalty_user)
            db.session.commit()
        else:
            if loyalty_user.visit == loyalty.goal:
                loyalty_user.visit = 0
            else:
                loyalty_user.visit = loyalty_user.visit + 1
            db.session.commit()

        branch = Branch.query.filter_by(branch_id = branch_id).first()
        branch_data = branch_schema.dump(branch)

        reward = set_experience(user_id, USING)
        user_level = level_up(user_id)
        db.session.commit()

        if 'first_using' in request.json and request.json['first_using'] == False:
            user_first_exp = UserFirstEXP.query.filter_by(user_id =user_id).first()
            user_first_exp.first_using = True
            first_badge = UsersBadges(user_id = payload['id'],
                                      badge_id = 1,
                                      reward_date = datetime.now(),
                                      type = 'trophy')

            db.session.add(first_badge)
            db.session.commit()

        return jsonify({'data': branch_data.data,
                        'reward': reward,
                        'level': user_level,
                        'folio': folio })
    else:
        minutes_left = 480 - minutes
        return jsonify({ 'message': 'error', "minutes": str(minutes_left) })


@loyalty.route('/user/old/redeem', methods=['POST'])
def loyalty_old_redeem():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index) #5

        qr_code = request.json['qr_code']
        branch_id = request.json['branch_id']
        loyalty_id = request.json['loyalty_id']
        today = datetime.now()

        loyalty = Loyalty.query.get(loyalty_id)

        if loyalty.is_global:
            branch = Branch.query.filter_by(folio = qr_code, silent = True).first()
            if not branch:
                return jsonify({'message': 'error_qr'})

        recently_used = LoyaltyRedeem.query.filter_by(loyalty_id = loyalty_id,
                                                        user_id = payload['id']) \
                                                        .order_by(desc(LoyaltyRedeem.date)).first()

        if recently_used:
            minutes = (today - recently_used.date).total_seconds() / 60
            print recently_used.date
            print minutes

        if not recently_used or minutes > 25:
            loyalty_redeem = LoyaltyRedeem(user_id = payload['id'],
                                           loyalty_id = loyalty_id,
                                           date = today,
                                           private = True,
                                           branch_folio = qr_code)
            db.session.add(loyalty_redeem)
            db.session.commit()
            folio = '%d%s%d' % (request.json['branch_id'], "{:%d%m%Y}".format(today),
                                    loyalty_redeem.loyalty_redeem_id)


            loyalty_user = LoyaltyUser.query.filter_by(loyalty_id = loyalty_id,
                                                         user_id = payload['id']).first()

            if not loyalty_user:
                loyalty_user = LoyaltyUser(user_id = payload['id'],
                                            loyalty_id = loyalty_id,
                                            visit = 1)

                db.session.add(loyalty_user)
                db.session.commit()
            else:
                if loyalty_user.visit == loyalty.goal:
                    loyalty_user.visit = 0
                else:
                    loyalty_user.visit = loyalty_user.visit + 1
                db.session.commit()

            branch = Branch.query.filter_by(branch_id = branch_id).first()
            branch_data = branch_schema.dump(branch)

            reward = set_experience(payload['id'], USING)
            user_level = level_up(payload['id'])
            db.session.commit()

            if request.json['first_using'] == False:
                user_first_exp = UserFirstEXP.query.filter_by(user_id = payload['id']).first()
                user_first_exp.first_using = True
                first_badge = UsersBadges(user_id = payload['id'],
                                          badge_id = 1,
                                          reward_date = datetime.now(),
                                          type = 'trophy')

                db.session.add(first_badge)
                db.session.commit()

            return jsonify({'data': branch_data.data,
                            'reward': reward,
                            'level': user_level,
                            'folio': folio })
        else:
            minutes_left = 25 - minutes
            return jsonify({ 'message': 'error', "minutes": str(minutes_left) })
    return jsonify({ 'message': 'Oops! algo salió mal, intentalo de nuevo, échale ganas' })

@loyalty.route('/view', methods=['POST'])
def add_view():
    if request.headers.get('Authorization'):
        token_index = True
        payload = parse_token(request, token_index)

        loyalty_id = request.json['loyalty_id']
        loyalty = Loyalty.query.get(loyalty_id)
        loyalty.views = loyalty.views + 1
        db.session.commit()

        loyalty_view = LoyaltyViews(user_id = payload['id'],
                                    loyalty_id = loyalty_id,
                                    view_date = datetime.now())

        if 'latitude' in request.json and 'longitude' in request.json:
            if request.json['latitude'] != 0 and request.json['longitude'] != 0:
                loyalty_view.latitude = request.json['latitude']
                loyalty_view.longitude = request.json['longitude']

        db.session.add(loyalty_view)
        db.session.commit()

        return jsonify({'message': 'vistas actualizada'})
    return jsonify({'message': 'Oops! algo salió mal, intentalo de nuevo, echale ganas'})

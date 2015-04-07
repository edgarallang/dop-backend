# -*- coding: utf-8 -*-

from sqlalchemy import Column, types
from sqlalchemy.ext.mutable import Mutable
from werkzeug import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin
from ..user import UserLevel
from ..badge import Badge
from ..extensions import db
from ..utils import get_current_time, SEX_TYPE, STRING_LEN

class Level(db.Model):
    __tablename__ = 'levels'
    level_id = Column(db.Integer, primary_key=True)
    name = Column(db.String(STRING_LEN), nullable=False, unique=True)
    min_exp = Column(db.Integer)
    badge_id = Column(db.Integer, db.ForeignKey('badges.badge_id'),nullable=False)

    user_level = db.relationship("UserLevel", uselist=False, backref="levels")
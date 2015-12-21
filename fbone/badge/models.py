from sqlalchemy import Column, types
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..utils import get_current_time, SEX_TYPE, STRING_LEN
from ..level import *
from .schemas import *

class Badge(db.Model):
    __tablename__ = 'badges'
    badge_id = Column(db.Integer, primary_key=True)
    name = Column(db.String(STRING_LEN), nullable=False, unique=True)
    info = Column(db.String(STRING_LEN), nullable=False)
    
    level = db.relationship("Level", uselist=False, backref="badges")

class UsersBadges(db.Model):
    __tablename__ = 'users_badges'
    users_badges_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer)
    badge_id = Column(db.Integer)
    reward_date = Column(db.DateTime)

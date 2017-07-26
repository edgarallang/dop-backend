from marshmallow import *
from sqlalchemy import Column, types
from sqlalchemy.ext.mutable import Mutable
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..utils import get_current_time, SEX_TYPE, STRING_LEN
from ..user import User
from ..company import Branch, BranchUser


# =====================================================================
# Loyalty

class Loyalty(db.Model):
    __tablename__ = 'loyalty'
    loyalty_id = Column(db.Integer, primary_key=True)
    owner_id = Column(db.Integer, nullable=False)
    name = Column(db.String(STRING_LEN))
    description = Column(db.String(STRING_LEN))
    type = Column(db.String(STRING_LEN))
    goal = Column(db.Integer)
    is_global = Column(db.Boolean)
    end_date = Column(db.DateTime)
    is_active = Column(db.Boolean)
    views = Column(db.Integer)

class LoyaltyRedeem(db.Model):
    __tablename__ = 'loyalty_redeem'
    loyalty_redeem_id = Column(db.Integer, primary_key=True)
    loyalty_id = Column(db.Integer, db.ForeignKey('loyalty.loyalty_id'), nullable=False)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    date = Column(db.DateTime)
    private = Column(db.Boolean, nullable = False)
    branch_folio = Column(db.String(STRING_LEN), default='')

    loyalty_user = db.relationship('User', uselist=False, backref='loyalty_redeem')
    loyalty = db.relationship('Loyalty', uselist=False, backref='loyalty_redeem')

class LoyaltyUser(db.Model):
    __tablename__ = 'loyalty_user'
    loyalty_user_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    loyalty_id = Column(db.Integer, db.ForeignKey('loyalty.loyalty_id'), nullable=False)
    visit = Column(db.Integer)

    loyalty_user = db.relationship('User', uselist=False, backref='loyalty_user')
    loyalty = db.relationship('Loyalty', uselist=False, backref='loyalty_user')
    
class LoyaltyViews(db.Model):
    __tablename__ = 'loyalty_views'
    id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, nullable=False)
    loyalty_id = Column(db.Integer, nullable=False)
    latitude = Column(db.Numeric)
    longitude = Column(db.Numeric)
    view_date = Column(db.DateTime)

class Loyalties(Schema):
    class Meta:
        dateformat = ('iso')
        fields = ('loyalty_id',
                  'owner_id',
                  'name',
                  'description',
                  'type',
                  'goal',
                  'is_global',
                  'end_date',
                  'logo',
                  'visit',
                  'company_id')


loyalties_schema = Loyalties(many=True)

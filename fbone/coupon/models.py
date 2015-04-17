from sqlalchemy import Column, types
from sqlalchemy.ext.mutable import Mutable
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db, jwt
from ..utils import get_current_time, SEX_TYPE, STRING_LEN
from ..user import User
from ..company import Branch
# =====================================================================
# Coupon

class Coupon(db.Model):
    __tablename__ = 'coupons'
    coupon_id = Column(db.Integer, primary_key=True)
    branch_id = Column(db.Integer, db.ForeignKey('branches.branch_id'),nullable=False)
    name = Column(db.String(STRING_LEN), nullable=False, unique=True)
    coupon_folio = Column(db.Integer, nullable=False, unique=True)
    description = Column(db.String(STRING_LEN))
    start_date  = Column(db.Date, nullable=False)
    end_date = Column(db.Date, nullable=False)
    min_spent = Column(db.Integer, nullable=False)
    coupon_category_id = Column(db.Integer, db.ForeignKey('coupons_category.coupon_category_id'),nullable=False)

    coupons_category = db.relationship('CouponCategory', uselist=False, backref="coupons")
    branches_coupons = db.relationship('Branch', uselist=False, backref="coupons")

class CouponCategory(db.Model):
    __tablename__ = 'coupons_category'
    coupon_category_id = Column(db.Integer, primary_key=True)
    type_name = Column(db.String(STRING_LEN), nullable=False)

class BondCoupon(db.Model):
    __tablename__ = 'bond_coupon'
    bond_id = Column(db.Integer, primary_key=True)
    coupon_category_id = Column(db.Integer, db.ForeignKey('coupons_category.coupon_category_id'),nullable=False)
    bond_size = Column(db.Integer, nullable=False)

    coupons_category = db.relationship('CouponCategory', uselist=False, backref="bond_coupon")

class DiscountCoupon(db.Model):
    __tablename__ = 'discount_coupon'
    discount_coupon_id = Column(db.Integer, primary_key=True)
    percent = Column(db.Integer, nullable=False)
    coupon_category_id = Column(db.Integer, db.ForeignKey('coupons_category.coupon_category_id'),nullable=False)

    coupons_category = db.relationship('CouponCategory', uselist=False, backref="bond_coupon")

class NxNCoupon(db.Model):
    __tablename__ = 'nxn_coupon'
    nxn_id = Column(db.Integer, primary_key=True)
    n1 = Column(db.Integer, nullable=False)
    n2 = Column(db.Integer, nullable=False)
    coupon_category_id = Column(db.Integer, db.ForeignKey('coupons_category.coupon_category_id'),nullable=False)

    coupons_category = db.relationship('CouponCategory', uselist=False, backref="nxn_coupon")

class ClientsCoupon(db.Model):
    __tablename__ = 'clients_coupon'
    clients_coupon_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    coupon_id = Column(db.Integer, db.ForeignKey('coupons.coupon_id'), nullable=False)
    folio = Column(db.String(STRING_LEN), nullable=False)
    taken_date = Column(db.Date, nullable=False)

    coupons_user = db.relationship('User', uselist=False, backref='clients_coupon')
    clients_coupons = db.relationship('Coupon', uselist=False, backref='clients_coupon')










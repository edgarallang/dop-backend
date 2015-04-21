from marshmallow import Schema, fields, ValidationError
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
    coupon_folio = Column(db.String(STRING_LEN), nullable=False)
    description = Column(db.String(STRING_LEN))
    start_date  = Column(db.Date, nullable=False)
    end_date = Column(db.Date, nullable=False)
    limit = Column(db.Integer)
    min_spent = Column(db.Integer, nullable=False)
    coupon_category_id = Column(db.Integer, db.ForeignKey('coupons_category.coupon_category_id'),nullable=False)

    coupons_category = db.relationship('CouponCategory', backref="coupons")
    branches_coupons = db.relationship('Branch', backref="coupons")

class CouponCategory(db.Model):
    __tablename__ = 'coupons_category'
    coupon_category_id = Column(db.Integer, primary_key=True)
    type_name = Column(db.String(STRING_LEN), nullable=False)

class BondCoupon(db.Model):
    __tablename__ = 'bond_coupon'
    bond_id = Column(db.Integer, primary_key=True)
    coupon_category_id = Column(db.Integer, db.ForeignKey('coupons_category.coupon_category_id'),nullable=False)
    bond_size = Column(db.Integer, nullable=False)
    coupon_id = Column(db.Integer, db.ForeignKey('coupons.coupon_id'), nullable=False)

    coupon = db.relationship('Coupon', backref=db.backref("bond_coupon", lazy='joined'), lazy="dynamic")
    coupons_category = db.relationship('CouponCategory', backref="bond_coupon")

class DiscountCoupon(db.Model):
    __tablename__ = 'discount_coupon'
    discount_coupon_id = Column(db.Integer, primary_key=True)
    percent = Column(db.Integer, nullable=False)
    coupon_category_id = Column(db.Integer, db.ForeignKey('coupons_category.coupon_category_id'),nullable=False)
    coupon_id = Column(db.Integer, db.ForeignKey('coupons.coupon_id'), nullable=False)

    coupon = db.relationship('Coupon', backref=db.backref("discount_coupon", lazy='joined'), lazy="dynamic")
    coupons_category = db.relationship('CouponCategory', backref="discount_coupon")

class NxNCoupon(db.Model):
    __tablename__ = 'nxn_coupon'
    nxn_id = Column(db.Integer, primary_key=True)
    n1 = Column(db.Integer, nullable=False)
    n2 = Column(db.Integer, nullable=False)
    coupon_category_id = Column(db.Integer, db.ForeignKey('coupons_category.coupon_category_id'),nullable=False)
    coupon_id = Column(db.Integer, db.ForeignKey('coupons.coupon_id'), nullable=False)

    coupon = db.relationship('Coupon', backref=db.backref("nxn_coupon", lazy='joined'), lazy="dynamic")
    coupons_category = db.relationship('CouponCategory', backref="nxn_coupon")

class ClientsCoupon(db.Model):
    __tablename__ = 'clients_coupon'
    clients_coupon_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    coupon_id = Column(db.Integer, db.ForeignKey('coupons.coupon_id'), nullable=False)
    folio = Column(db.String(STRING_LEN), nullable=False)
    taken_date = Column(db.Date, nullable=False)

    coupons_user = db.relationship('User', backref='clients_coupon')
    clients_coupons = db.relationship('Coupon', backref='clients_coupon')

# Serializer Schemas

class BondCouponSchema(Schema):
    class Meta:
        fields = ('bond_size')

class DiscountCouponSchema(Schema):
    class Meta:
        fields = ('percent')

class NxNCouponSchema(Schema):
    class Meta:
        fields = ('n1',
                  'n2')

class CouponSchema(Schema):
    bond = fields.Nested('BondCouponSchema')
    discount = fields.Nested('DiscountCouponSchema')
    nxn = fields.Nested('NxNCouponSchema')
    class Meta:
        fields = ('coupon_id',
                  'branch_id',
                  'name',
                  'coupon_folio',
                  'description',
                  'start_date',
                  'end_date',
                  'limit',
                  'min_spent',
                  'coupon_category_id')


coupon_schema = CouponSchema(many=True)








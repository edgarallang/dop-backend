from marshmallow import Schema, fields, ValidationError
from sqlalchemy import Column, types
from sqlalchemy.ext.mutable import Mutable
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..utils import get_current_time, SEX_TYPE, STRING_LEN
from ..user import User
from ..company import Branch, BranchUser
# =====================================================================
# Coupon

class Coupon(db.Model):
    __tablename__ = 'coupons'
    coupon_id = Column(db.Integer, primary_key=True)
    branch_id = Column(db.Integer, db.ForeignKey('branches.branch_id'),nullable=False)
    name = Column(db.String(STRING_LEN))
    coupon_folio = Column(db.String(STRING_LEN), nullable=False)
    description = Column(db.String(STRING_LEN))
    start_date  = Column(db.DateTime)
    end_date = Column(db.DateTime)
    limit = Column(db.Integer, nullable = False)
    min_spent = Column(db.Integer)
    coupon_category_id = Column(db.Integer, db.ForeignKey('coupons_category.coupon_category_id'),nullable=False)
    deleted = Column(db.Boolean)
    available = Column(db.Integer)
    active = Column(db.Boolean)

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
    coupon_id = Column(db.Integer, db.ForeignKey('coupons.coupon_id'), nullable=False)

    coupon = db.relationship('Coupon', uselist=False, backref="bond_coupon")
    coupons_category = db.relationship('CouponCategory', uselist=False, backref="bond_coupon")

class DiscountCoupon(db.Model):
    __tablename__ = 'discount_coupon'
    discount_coupon_id = Column(db.Integer, primary_key=True)
    percent = Column(db.Integer, nullable=False)
    coupon_category_id = Column(db.Integer, db.ForeignKey('coupons_category.coupon_category_id'),nullable=False)
    coupon_id = Column(db.Integer, db.ForeignKey('coupons.coupon_id'), nullable=False)

    coupon = db.relationship('Coupon', uselist=False, backref="discount_coupon")
    coupons_category = db.relationship('CouponCategory', uselist=False, backref="discount_coupon")

class NxNCoupon(db.Model):
    __tablename__ = 'nxn_coupon'
    nxn_id = Column(db.Integer, primary_key=True)
    n1 = Column(db.Integer, nullable=False)
    n2 = Column(db.Integer, nullable=False)
    coupon_category_id = Column(db.Integer, db.ForeignKey('coupons_category.coupon_category_id'),nullable=False)
    coupon_id = Column(db.Integer, db.ForeignKey('coupons.coupon_id'), nullable=False)

    coupon = db.relationship('Coupon', uselist=False, backref="nxn_coupon")
    coupons_category = db.relationship('CouponCategory', uselist=False, backref="nxn_coupon")

class ClientsCoupon(db.Model):
    __tablename__ = 'clients_coupon'
    clients_coupon_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    coupon_id = Column(db.Integer, db.ForeignKey('coupons.coupon_id'), nullable=False)
    folio = Column(db.String(STRING_LEN))
    taken_date = Column(db.DateTime, nullable=False)
    latitude = Column(db.Numeric, nullable=False)
    longitude = Column(db.Numeric, nullable=False)


    coupons_user = db.relationship('User', uselist=False, backref='clients_coupon')
    clients_coupons = db.relationship('Coupon', uselist=False, backref='clients_coupon')

class CouponsLikes(db.Model):
    __tablename__ = 'coupons_likes'
    coupon_like_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    coupon_id = Column(db.Integer, db.ForeignKey('coupons.coupon_id'), nullable=False)
    date = Column(db.DateTime, nullable=False)


    coupons_user = db.relationship('User', uselist=False, backref='coupons_likes')
    clients_coupons = db.relationship('Coupon', uselist=False, backref='coupons_likes')

class CouponsUsedLikes(db.Model):
    __tablename__ = 'clients_coupon_likes'
    clients_coupon_like_id = Column(db.Integer, primary_key=True)
    clients_coupon_id = Column(db.Integer, db.ForeignKey('clients_coupon.clients_coupon_id'), nullable=False)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    date = Column(db.DateTime, nullable=False)

    coupons_user = db.relationship('User', uselist=False, backref='clients_coupon_likes')
    clients_coupons = db.relationship('ClientsCoupon', uselist=False, backref='clients_coupon_likes')

# Serializer Schemas

class CouponSchema(Schema):
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

class CouponLogoSchema(Schema):
    class Meta:
        fields = ('coupon_id',
                  'branch_id',
                  'company_id',
                  'name',
                  'coupon_folio',
                  'description',
                  'start_date',
                  'end_date',
                  'limit',
                  'min_spent',
                  'coupon_category_id',
                  'logo',
                  'total_likes',
                  'user_like',
                  'latitude',
                  'longitude',
                  'banner',
                  'category_id')

class BondJoinCouponSchema(Schema):
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
                  'coupon_category_id',
                  'bond_id',
                  'bond_size')

class DiscountJoinCouponSchema(Schema):
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
                  'coupon_category_id',
                  'discount_coupon_id',
                  'percent')

class NxNJoinCouponSchema(Schema):
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
                  'coupon_category_id',
                  'nxn_id',
                  'n1',
                  'n2')

class BondCouponSchema(Schema):
    class Meta:
        fields = ('bond_id',
                  'bond_size')

class DiscountCouponSchema(Schema):
    class Meta:
        fields = ('discount_coupon_id',
                  'percent')

class NxNCouponSchema(Schema):
    class Meta:
        fields = ('n1',
                  'n2')

class ClientsCouponSchema(Schema):
    class Meta:
        fields = ('clients_coupon_id',
                  'user_id',
                  'folio',
                  'taken_date',
                  'latitude',
                  'longitude')

class UserJoinExchanges(Schema):
    class Meta:
        fields = ('clients_coupon_id',
                  'branch_id',
                  'coupon_id',
                  'logo',
                  'name',
                  'latitude',
                  'longitude',
                  'names',
                  'surnames',
                  'user_id',
                  'main_image',
                  'exchange_date',
                  'friend_id',
                  'branch_name',
                  'total_likes',
                  'user_like')

class CouponLike(Schema):
    class Meta:
        fields = ('coupon_like_id',
                  'coupon_id',
                  'user_id',
                  'date')

class CouponsLocation(Schema):
    class Meta:
        fields = ('coupon_id',
                  'branch_id',
                  'company_id',
                  'name',
                  'distance',
                  'description',
                  'start_date',
                  'end_date',
                  'limit',
                  'min_spent',
                  'coupon_category_id',
                  'total_likes',
                  'user_like',
                  'latitude',
                  'longitude',
                  'category_id')

coupon_schema = CouponSchema()
coupons_schema = CouponSchema(many=True)

coupons_logo_schema = CouponLogoSchema(many=True)


bond_join_coupon_schema = BondJoinCouponSchema(many=True)
discount_join_coupon_schema = DiscountJoinCouponSchema(many=True)
nxn_join_coupon_schema = NxNJoinCouponSchema(many=True)

bond_coupon_schema = BondCouponSchema()
discount_coupon_schema = DiscountCouponSchema()
nxn_coupon_schema = NxNCouponSchema()

clients_coupon_schema = ClientsCouponSchema()

user_join_exchanges_coupon_schema = UserJoinExchanges(many=True)

coupons_likes_schema = CouponLike(many=True)

coupons_location_schema = CouponsLocation(many=True)






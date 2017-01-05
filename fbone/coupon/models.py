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
    views = Column(db.Integer)
    duration = Column(db.Integer)

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
    latitude = Column(db.Numeric)
    longitude = Column(db.Numeric)
    used = Column(db.Boolean, nullable = False)
    used_date = Column(db.DateTime, nullable=False)
    private = Column(db.Boolean, nullable = False)

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

class CouponReport(db.Model):
    __tablename__ = 'problems_report'
    id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    branch_id = Column(db.Integer, db.ForeignKey('branches.branch_id'), nullable=False)
    coupon_id = Column(db.Integer, db.ForeignKey('coupons.coupon_id'), nullable=False)
    branch_indiference = Column(db.Boolean)
    camera_broken = Column(db.Boolean)
    app_broken = Column(db.Boolean)
    qr_lost = Column(db.Boolean)

class CouponsViews(db.Model):
    __tablename__ = 'coupons_views'
    id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    coupon_id = Column(db.Integer, db.ForeignKey('coupons.coupon_id'), nullable=False)
    latitude = Column(db.Numeric)
    longitude = Column(db.Numeric)

# Serializer Schemas

class CouponReportSchema(Schema):
    class Meta:
        fields = ( 'user_id',
                   'branch_id',
                   'coupon_id',
                   'branch_indiference',
                   'camera_broken',
                   'app_broken',
                   'qr_lost' )


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
                'coupon_category_id',
                'active',
                'completed',
                'remaining',
                'available')

class CouponLogoSchema(Schema):
    dateformat = ('iso')
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
                  'category_id',
                  'available',
                  'taken')

class CouponsTakenSchema(Schema):
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
                  'category_id',
                  'available',
                  'taken_date')


class TrendingCouponSchema(Schema):
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
                  'available',
                  'taken',
                  'subcategory_id')

class NearestCouponSchema(Schema):
    class Meta:
        fields = ('coupon_id',
                  'branch_id',
                  'company_id',
                  'name',
                  'description',
                  'start_date',
                  'end_date',
                  'min_spent',
                  'latitude',
                  'longitude',
                  'available',
                  'taken',
                  'total_likes',
                  'user_like',
                  'subcategory_id',
                  'distance',
                  'logo')

class ToExpireCouponSchema(Schema):
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
                  'available',
                  'taken',
                  'subcategory_id')

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

class ClientsCouponsInnerCouponSchema(Schema):
    class Meta:
        fields = ('clients_coupon_id',
                  'branch_id')

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
                  'coupon_name',
                  'name',
                  'address',
                  'distance',
                  'description',
                  'city',
                  'category_id',
                  'latitude',
                  'longitude')

class UserActivityNewsfeed(Schema):
    class Meta:
        fields = ('clients_coupon_id',
                  'branch_id',
                  'company_id',
                  'coupon_id',
                  'logo',
                  'name',
                  'latitude',
                  'longitude',
                  'names',
                  'surnames',
                  'user_id',
                  'main_image',
                  'branch_name',
                  'total_likes',
                  'user_like',
                  'used_date',
                  'is_friend',
                  'operation_id',
                  'exp',
                  'level',
                  'privacy_status')

class CouponsViews(Schema):
    class Meta:
        fields = ('coupon_id',
                  'coupon_folio',
                  'name',
                  'description',
                  'start_date',
                  'end_date',
                  'limit',
                  'min_spent',
                  'available',
                  'views',
                  'total_likes',
                  'total_uses')

class TakenCouponsLocationSchema(Schema):
    class Meta:
        fields = ('coupon_id',
                  'name',
                  'description',
                  'latitude',
                  'longitude',
                  'available',
                  'taken_date')

class UsedCouponsByAge(Schema):
    class Meta:
        fields = ('age',
                  'count')

class UsedCouponsByGender(Schema):
    class Meta:
        fields = ('gender',
                  'count')

coupon_schema = CouponSchema()
coupons_schema = CouponSchema(many=True)

coupons_logo_schema = CouponLogoSchema(many=True)
trending_coupon_schema = TrendingCouponSchema(many=True)
nearest_coupon_schema = NearestCouponSchema(many=True)
toexpire_coupon_schema = ToExpireCouponSchema(many=True)

bond_join_coupon_schema = BondJoinCouponSchema(many=True)
discount_join_coupon_schema = DiscountJoinCouponSchema(many=True)
nxn_join_coupon_schema = NxNJoinCouponSchema(many=True)

bond_coupon_schema = BondCouponSchema()
discount_coupon_schema = DiscountCouponSchema()
nxn_coupon_schema = NxNCouponSchema()

clients_coupon_schema = ClientsCouponSchema()
clients_coupon_inner_coupon_schema = ClientsCouponsInnerCouponSchema()

user_join_exchanges_coupon_schema = UserJoinExchanges(many=True)
user_join_activity_newsfeed = UserActivityNewsfeed(many=True)

coupons_likes_schema = CouponLike(many=True)
coupons_taken_schema = CouponsTakenSchema(many=True)

coupons_location_schema = CouponsLocation(many=True)
coupons_views_schema = CouponsViews(many=True)

taken_coupons_location_schema = TakenCouponsLocationSchema(many=True)

used_coupons_by_age_schema = UsedCouponsByAge(many=True)
used_coupons_by_gender_schema = UsedCouponsByGender(many=True)

coupons_report_schema = CouponReportSchema()

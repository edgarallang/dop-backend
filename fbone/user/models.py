# -*- coding: utf-8 -*-
from marshmallow import Schema, fields, ValidationError
from sqlalchemy import Column, types
from sqlalchemy.ext.mutable import Mutable
from werkzeug import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin
from ..extensions import db
from ..utils import get_current_time, SEX_TYPE, STRING_LEN
from .constants import USER, USER_ROLE, ADMIN, INACTIVE, USER_STATUS


class DenormalizedText(Mutable, types.TypeDecorator):
    """
    Stores denormalized primary keys that can be
    accessed as a set.

    :param coerce: coercion function that ensures correct
                   type is returned

    :param separator: separator character
    """

    impl = types.Text

    def __init__(self, coerce=int, separator=" ", **kwargs):

        self.coerce = coerce
        self.separator = separator

        super(DenormalizedText, self).__init__(**kwargs)

    def process_bind_param(self, value, dialect):
        if value is not None:
            items = [str(item).strip() for item in value]
            value = self.separator.join(item for item in items if item)
        return value

    def process_result_value(self, value, dialect):
        if not value:
            return set()
        return set(self.coerce(item) for item in value.split(self.separator))

    def copy_value(self, value):
        return set(value)



    # role_code = Column(db.SmallInteger, default=USER, nullable=False)

    # @property
    # def role(self):
    #     return USER_ROLE[self.role_code]

    # def is_admin(self):
    #     return self.role_code == ADMIN

    # ================================================================
    # One-to-many relationship between users and user_statuses.
    # status_code = Column(db.SmallInteger, default=INACTIVE)

    # @property
    # def status(self):
    #     return USER_STATUS[self.status_code]

class User(db.Model, UserMixin):

    __tablename__ = 'users'

    user_id = Column(db.Integer, primary_key=True)
    names = Column(db.String(STRING_LEN))
    surnames = Column(db.String(STRING_LEN))
    birth_date = Column(db.DateTime)
    facebook_key = Column(db.String(STRING_LEN))
    google_key = Column(db.String(STRING_LEN))
    twitter_key = Column(db.String(STRING_LEN))
    privacy_status = Column(db.Integer)
    level = Column(db.Integer)
    exp = Column(db.Integer)
    gender = Column(db.String(STRING_LEN))
    device_os = Column(db.String(STRING_LEN))
    device_token = Column(db.String(STRING_LEN))
    adult = Column(db.Boolean)

    #users_image_user_id = db.relationship("UserImage", uselist=False, backref="users")

    # Images

class UserImage(db.Model, UserMixin):
    __tablename__ = 'users_image'
    user_image_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    main_image = Column(db.String(STRING_LEN))

# ================================================================
# User Level

class UserLevel(db.Model, UserMixin):
    __tablename__ = 'users_level'
    user_level_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    level_id = Column(db.Integer, db.ForeignKey('levels.level_id'), nullable=False)
    exp = Column(db.Integer, nullable=False)

# ================================================================
# User Session

class UserSession(db.Model,UserMixin):
    __tablename__ = 'users_session'
    user_session_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    email = Column(db.String(STRING_LEN))
    password = Column(db.String(STRING_LEN))
    verified = Column(db.Boolean, default=False)

# ================================================================
# Friends

class Friends(db.Model,UserMixin):
    __tablename__ = 'friends'
    friends_id = Column(db.Integer, primary_key=True)
    user_one_id = Column(db.Integer, nullable=False)
    user_two_id = Column(db.Integer, nullable=False)
    operation_id = Column(db.Integer, nullable=False)

class UserFirstEXP(db.Model, UserMixin):
    __tablename__ = 'user_first_exp'
    user_first_exp = Column(db.Integer, primary_key = True)
    user_id = Column(db.Integer, nullable = False)
    first_following = Column(db.Boolean, nullable = False)
    first_follower = Column(db.Boolean, nullable = False)
    first_company_fav = Column(db.Boolean, nullable = False)
    first_using = Column(db.Boolean, nullable = False)

# Invited Friends

class InvitedFriends(db.Model,UserMixin):
    __tablename__ = 'invited_friends'
    user_id = Column(db.Integer, primary_key=True)
    facebook_key = Column(db.String(STRING_LEN))
    email = Column(db.String(STRING_LEN))

#Forgot password
class ForgotPassword(db.Model, UserMixin):
  __tablename__ = 'forgot_password'
  forgot_password_id = Column(db.Integer, primary_key=True)
  user_id = Column(db.Integer)
  token = Column(db.String(100))

#Verify email
class VerifyEmail(db.Model, UserMixin):
  __tablename__ = 'verify_email'
  verify_email_id = Column(db.Integer, primary_key=True)
  user_id = Column(db.Integer)
  token = Column(db.String(100))

#Login stats
class LoginStats(db.Model, UserMixin):
  __tablename__ = "login_stats"
  id_login_stat = Column(db.Integer, primary_key=True)
  user_id = Column(db.Integer)
  date = Column(db.DateTime)
  latitude = Column(db.Numeric)
  longitude = Column(db.Numeric)

# Serializer Schemas

class UserSchema(Schema):
    class Meta:
        fields = ('user_id',
                  'names',
                  'surnames',
                  'birth_date',
                  'facebook_key',
                  'google_key',
                  'twitter_key',
                  'privacy_status',
                  'level',
                  'exp')

class UserJoinImage(Schema):
    class Meta:
        fields = ('user_id',
                  'names',
                  'surnames',
                  'birth_date',
                  'facebook_key',
                  'google_key',
                  'twitter_key',
                  'main_image',
                  'user_image_id',
                  'privacy_status',
                  'level',
                  'exp',
                  'is_friend',
                  'email')

class UserJoinImageFriendshipStatus(Schema):
    class Meta:
        fields = ('user_id',
                  'names',
                  'surnames',
                  'birth_date',
                  'facebook_key',
                  'google_key',
                  'twitter_key',
                  'main_image',
                  'user_image_id',
                  'privacy_status',
                  'level',
                  'exp',
                  'is_friend',
                  'email',
                  'operation_id')

class FriendsSchema(Schema):
    class Meta:
        fields = ('user_one_id',
                  'user_two_id',
                  'operation_id')

class UserJoinFriends(Schema):
    class Meta:
        fields = ('friends_id',
                  'user_id',
                  'names',
                  'surnames',
                  'main_image',
                  'is_friend',
                  'facebook_key',
                  'privacy_status',
                  'birth_date',
                  'level',
                  'exp',
                  'operation_id')

class FriendsCountSchema(Schema):
    class Meta:
        fields = ('friends_id',
                  'total')

class PeopleSchema(Schema):
    class Meta:
        fields = ('user_id',
                  'names',
                  'surnames',
                  'birth_date',
                  'facebook_key',
                  'google_key',
                  'twitter_key',
                  'privacy_status',
                  'exp',
                  'user_image_id',
                  'main_image',
                  'is_friend',
                  'level',
                  'exp',
                  'operation_id')

class UserJoinExchanges(Schema):
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
                  'exchange_date',
                  'friend_id',
                  'branch_name',
                  'total_likes',
                  'user_like')

class UserFlags(Schema):
    class Meta:
        fields = ('privacy_status',
                  'first_following',
                  'first_follower',
                  'first_company_fav',
                  'first_using')


class UserActivityNewsfeed(Schema):
    class Meta:
        fields = ('clients_coupon_id',
                  'branch_id',
                  'owner_id',
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
                  'private')

class SimpleUser(Schema):
    class Meta:
        fields = ('user_id',
                  'names',
                  'surnames',
                  'device_os',
                  'device_token',
                  'main_image')

class SimilarPeople(Schema):
    class Meta:
        fields = ('user_id',
                  'names',
                  'main_image')

class UserDeviceTokens(Schema):
        device_token = fields.Str()

user_schema = UserSchema(many=True)
user_joined_schema = UserJoinImage(many=True)
friends_schema = FriendsSchema()
user_join_friends = UserJoinFriends(many=True)
user_join_exchanges_coupon_schema = UserJoinExchanges(many=True)
user_join_activity_newsfeed_u = UserActivityNewsfeed(many=True)
friends_count_schema = FriendsCountSchema(many=True)
people_schema = PeopleSchema(many=True)
user_flags_schema = UserFlags(many=True)
device_tokens_schema = UserDeviceTokens(many=True)
simple_user_schema = SimpleUser(many=True)
similar_people_schema = SimilarPeople(many=True)
user_friendship_status_schema = UserJoinImageFriendshipStatus(many=True)

    # ================================================================
    # Class methods

    # @classmethod
    # def authenticate(cls, login, password):
    #     user = cls.query.filter(db.or_(User.names == login, User.email == login)).first()

    #     if user:
    #         authenticated = user.check_password(password)
    #     else:
    #         authenticated = False

    #     return user, authenticated

    # @classmethod
    # def search(cls, keywords):
    #     criteria = []
    #     for keyword in keywords.split():
    #         keyword = '%' + keyword + '%'
    #         criteria.append(db.or_(
    #             User.name.ilike(keyword),
    #             User.email.ilike(keyword),
    #         ))
    #     q = reduce(db.and_, criteria)
    #     return cls.query.filter(q)

    # @classmethod
    # def get_by_id(cls, user_id):
    #     return cls.query.filter_by(id=user_id).first_or_404()

    # def check_name(self, name):
    #     return User.query.filter(db.and_(User.names == names, User.email != self.id)).count() == 0

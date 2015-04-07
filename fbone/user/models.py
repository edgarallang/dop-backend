# -*- coding: utf-8 -*-

from sqlalchemy import Column, types
from sqlalchemy.ext.mutable import Mutable
from werkzeug import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin
# from ..level import Level
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
    names = Column(db.String(STRING_LEN), nullable=False)
    surnames = Column(db.String(STRING_LEN), nullable=False)
    birth_date = Column(db.Date, nullable=False)
    facebook_key = Column(db.String(STRING_LEN))
    google_key = Column(db.String(STRING_LEN))
    twitter_key = Column(db.String(STRING_LEN))

    users_image_user_id = db.relationship("UserImage", uselist=False, backref="users")
    # created_time = Column(db.DateTime, default=get_current_time)

    # ================================================================
    # Follow / Following
    # followers = Column(DenormalizedText)
    # following = Column(DenormalizedText)

    # @property
    # def num_followers(self):
    #     if self.followers:
    #         return len(self.followers)
    #     return 0

    # @property
    # def num_following(self):
    #     return len(self.following)

    # def follow(self, user):
    #     user.followers.add(self.id)
    #     self.following.add(user.user_id)

    # def unfollow(self, user):
    #     if self.id in user.followers:
    #         user.followers.remove(self.id)

    #     if user.user_id in self.following:
    #         self.following.remove(user.user_id)

    # def get_following_query(self):
    #     return User.query.filter(User.user_id.in_(self.following or set()))

    # def get_followers_query(self):
    #     return User.query.filter(User.user_id.in_(self.followers or set()))

    # Images 

class UserImage(db.Model, UserMixin):
    __tablename__ = 'user_images'
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
    # Class methods

    @classmethod
    def authenticate(cls, login, password):
        user = cls.query.filter(db.or_(User.names == login, User.email == login)).first()

        if user:
            authenticated = user.check_password(password)
        else:
            authenticated = False

        return user, authenticated

    @classmethod
    def search(cls, keywords):
        criteria = []
        for keyword in keywords.split():
            keyword = '%' + keyword + '%'
            criteria.append(db.or_(
                User.name.ilike(keyword),
                User.email.ilike(keyword),
            ))
        q = reduce(db.and_, criteria)
        return cls.query.filter(q)

    @classmethod
    def get_by_id(cls, user_id):
        return cls.query.filter_by(id=user_id).first_or_404()

    def check_name(self, name):
        return User.query.filter(db.and_(User.names == names, User.email != self.id)).count() == 0

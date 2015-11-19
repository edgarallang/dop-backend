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

class Notification(db.Model):
    __tablename__ = 'notifications'
    notification_id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'),nullable=False)
    object_id = Column(db.Integer)
    type = Column(db.String(STRING_LEN))
    notification_date = Column(db.DateTime, nullable=False)
    launcher_id = Column(db.Integer)
    read = Column(db.Boolean)

    notification_user = db.relationship('User', uselist=False, backref="notifications")

class Notifications(Schema):
    class Meta:
        dateformat = "iso"
        fields = ('notification_id',
                  'type',
                  'launcher_name',
                  'launcher_surnames',
                  'launcher_id',
                  'friendship_status',
                  'newsfeed_activity',
                  'read',
                  'notification_date'
                  )
        datexformat = ('rfc')


notifications_schema = Notifications(many=True)

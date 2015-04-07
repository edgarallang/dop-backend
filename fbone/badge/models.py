from sqlalchemy import Column, types
from sqlalchemy.ext.mutable import Mutable
from ..extensions import db, jwt
from ..utils import get_current_time, SEX_TYPE, STRING_LEN
from ../level import Level

class Badge(db.Model):
    __tablename__ = 'badges'
    badge_id = Column(db.Integer, primary_key=True)
    name = Column(db.String(STRING_LEN), nullable=False, unique=True)
    info = Column(db.String(STRING_LEN), nullable=False)
    
    level = db.relationship("Level", uselist=False, backref="badges")
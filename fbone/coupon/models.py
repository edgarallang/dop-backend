from sqlalchemy import Column, types
from sqlalchemy.ext.mutable import Mutable
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db, jwt
from ..utils import get_current_time, SEX_TYPE, STRING_LEN

# =====================================================================
# Company

class Company(db.Model):
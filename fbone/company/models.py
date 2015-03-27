from sqlalchemy import Column, types
from sqlalchemy.ext.mutable import Mutable
from ..extensions import db
from ..utils import get_current_time, SEX_TYPE, STRING_LEN

# =====================================================================
# Company

class Company(db.Model, UserMixin):
    __tablename__ = 'companies'
    company_id = Column(db.Integer, primary_key=True)
    name = Column(db.String(STRING_LEN), nullable=False, unique=True)

    branches = db.relationship("Branch", uselist=False, backref="companies")

# =====================================================================
# Branches 

class Branch(db.Model, UserMixin):
    __tablename__ = 'branches'
    branch_id = Column(db.Integer, primary_key=True)
    company_id = Column(db.Integer, db.ForeignKey('companies.company_id'),nullable=False)
    name = Column(db.String(STRING_LEN), nullable=False, unique=True)
    category_id = Column(db.Integer, db.ForeignKey('categories.category_id'),nullable=False)

    # branches_user_id = Column(db.Integer, db.ForeignKey("branches_user.branches_user_id"))
    branches_design = db.relationship("BranchDesign", uselist=False, backref="branches")
    branches_location = db.relationship("BranchLocation", uselist=False, backref="branches")
    branches_user = db.relationship("BranchUser", uselist=False, backref="branches")

# =====================================================================
# Branches Design

class BranchDesign(db.Model, UserMixin):
    __tablename__ = 'branches_design'
    design_id = Column(db.Integer, primary_key=True)
    branch_id = Column(db.Integer, db.ForeignKey('branches.branch_id'),nullable=False)
    logo = Column(db.String(STRING_LEN), nullable=False)
    name = Column(db.String(STRING_LEN), nullable=False)
    color_a = Column(db.String(STRING_LEN), nullable=False)
    color_b = Column(db.String(STRING_LEN), nullable=False)
    color_c = Column(db.String(STRING_LEN), nullable=False)

# =====================================================================
# Branches Location

class BranchLocation(db.Model, UserMixin):
    __tablename__ = 'branches_location'
    user_location_id = Column(db.Integer, primary_key=True)
    branch_id = Column(db.Integer, db.ForeignKey('branches.branch_id'),nullable=False)
    state = Column(db.String(STRING_LEN), nullable=False)
    longitude = Column(db.Numeric, nullable=False)
    latitude = Column(db.Numeric, nullable=False)
    city = Column(db.String(STRING_LEN), nullable=False)
    address = Column(db.String(STRING_LEN), nullable=False)

# =====================================================================
# Categories 

class Category(db.Model, UserMixin):
    __tablename__ = 'categories'
    category_id = Column(db.Integer, primary_key=True)
    name = Column(db.String(STRING_LEN), nullable=False, unique=True)

    branches_category = db.relationship("Branch", uselist=False, backref="branches")

# =====================================================================
# Branches user is the person geting into the system from that specific branch

class BranchUser(db.Model, UserMixin):
    __tablename__ = 'branches_user'
    branches_user_id = Column(db.Integer, primary_key=True)
    branch_id = Column(db.Integer, db.ForeignKey('branches.branch_id'), nullable=False)
    name = Column(db.String(STRING_LEN), nullable=False, unique=True)
    email = Column(db.String(STRING_LEN), nullable=False, unique=True)

    _password = Column('password', db.String(STRING_LEN), nullable=False)

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = generate_password_hash(password)
    # Hide password encryption by exposing password field only.
    password = db.synonym('_password',
                          descriptor=property(_get_password,
                                              _set_password))

    def check_password(self, password):
        if self.password is None:
            return False
        return check_password_hash(self.password, password)

# ================================================================
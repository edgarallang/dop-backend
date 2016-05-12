from marshmallow import Schema, fields, ValidationError
from sqlalchemy import Column, types
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..utils import get_current_time, SEX_TYPE, STRING_LEN


# =====================================================================
# Company

class Company(db.Model):
    __tablename__ = 'companies'
    company_id = Column(db.Integer, primary_key = True)
    name = Column(db.String(STRING_LEN), nullable = False, unique = True)
    email = Column(db.String(STRING_LEN), nullable = False, unique = True)
    credits = Column(db.Integer)

    branches = db.relationship("Branch", uselist = False, backref = "companies")

# =====================================================================
# Branches

class Branch(db.Model):
    __tablename__ = 'branches'
    branch_id = Column(db.Integer, primary_key=True)
    company_id = Column(db.Integer, db.ForeignKey('companies.company_id'), nullable = False)
    name = Column(db.String(STRING_LEN), nullable=True, unique=True)

    # branches_user_id = Column(db.Integer, db.ForeignKey("branches_user.branches_user_id"))
    branches_design = db.relationship("BranchDesign", uselist=False, backref="branches")
    branch = db.relationship('BranchAd', uselist=False, backref = 'branches')
    # branches_location_id = db.ForeignKey('branches_location.branches_location_id')

    # branches_location = db.relationship('branches_location',
    #                     backref=db.backref("branch", lazy="dynamic"))
    #
    # def __init__(self, branches_location):
    #     self.branches_location = branches_location

# =====================================================================
# Branches Design

class BranchDesign(db.Model):
    __tablename__ = 'branches_design'
    design_id = Column(db.Integer, primary_key=True)
    branch_id = Column(db.Integer, db.ForeignKey('branches.branch_id'),nullable=False)
    logo = Column(db.String(STRING_LEN), nullable=False)
    name = Column(db.String(STRING_LEN), nullable=False)
    color_a = Column(db.String(STRING_LEN), nullable=False)
    color_b = Column(db.String(STRING_LEN), nullable=False)
    color_c = Column(db.String(STRING_LEN), nullable=False)
    banner = Column(db.String(STRING_LEN), nullable=False)

# =====================================================================
# Branches Location

class BranchLocation(db.Model):
    __tablename__ = 'branches_location'
    branch_location_id = Column(db.Integer, primary_key=True)
    branch_id = Column(db.Integer, db.ForeignKey('branches.branch_id'),nullable=False)
    state = Column(db.String(STRING_LEN), nullable=False)
    longitude = Column(db.Numeric, nullable=False)
    latitude = Column(db.Numeric, nullable=False)
    city = Column(db.String(STRING_LEN), nullable=False)
    address = Column(db.String(STRING_LEN), nullable=False)

    # branch = db.relationship('Branch',
    #                     backref=db.backref("branches_location", lazy="dynamic"))
    #
    # def __init__(self, branch):
    #     self.branch = branch

# =====================================================================
# Marketing Package

class MarketingPackage(db.Model):
    __tablename__ = 'marketing_package'
    marketing_package_id = Column(db.Integer, primary_key = True)
    duration  = Column(db.Integer)

    branchAd = db.relationship('BranchAd', uselist=False, backref = 'marketing_package')

# =====================================================================
# Branches Location

class BranchAd(db.Model):
    __tablename__ = 'branch_ad'
    branch_ad_id = Column(db.Integer, primary_key = True)
    start_date = Column(db.DateTime)
    branch_id = Column(db.Integer, db.ForeignKey('branches.branch_id'), nullable = False)
    marketing_package_id = Column(db.Integer, db.ForeignKey('marketing_package.marketing_package_id'), nullable = False)
    duration = Column(db.Integer)

# =====================================================================
# Categories

class Category(db.Model):
    __tablename__ = 'categories'
    category_id = Column(db.Integer, primary_key=True)
    name = Column(db.String(STRING_LEN), nullable=False, unique=True)

# =====================================================================

# Branches follower

class BranchesFollower(db.Model):
    __tablename__ = 'branches_follower'
    branch_follower_id = Column(db.Integer, primary_key=True)
    branch_id = Column(db.Integer, db.ForeignKey('branches.branch_id'), nullable=False)
    user_id = Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    date = Column(db.DateTime, nullable=False)

    branches_follower = db.relationship("Branch", uselist=False, backref="branches_follower")
    branches_user = db.relationship('User', uselist=False, backref='branches_follower')
# =====================================================================

# Branches user is the person geting into the system from that specific branch

class BranchUser(db.Model):
    __tablename__ = 'branches_user'
    branches_user_id = Column(db.Integer, primary_key=True)
    branch_id = Column(db.Integer, db.ForeignKey('branches.branch_id'), nullable=False)
    name = Column(db.String(STRING_LEN), nullable=False)
    email = Column(db.String(STRING_LEN), nullable=False, unique=True)
    password = Column('password', db.String(STRING_LEN), nullable=False)

    branch = db.relationship('Branch',
                        backref=db.backref("branches_user", lazy="dynamic"))

    def __init__(self, branch):
        self.branch = branch

    def check_password(self, password):
        return self.password == password


    # def _get_password(self):
    #     return self._password

    # def _set_password(self, password):
    #     self._password = generate_password_hash(password)
    # # Hide password encryption by exposing password field only.
    # password = db.synonym('_password',
    #                       descriptor=property(_get_password,
    #                                           _set_password))

    # def check_password(self, password):
    #     if self.password is None:
    #         return False
    #     return check_password_hash(self.password, password)

# ================================================================

# Serializer Schemas


def must_not_be_blank(data):
    if not data:
        raise ValidationError('Data not provided.')

class CompanySchema(Schema):
    class Meta:
        fields = ('company_id',
                  'name')

class BranchesLocation(Schema):
    # branch = fields.Nested(BranchSchema, validate=must_not_be_blank)
    class Meta:
        fields = ('branch_location_id',
                  'branch_id',
                  'state',
                  'longitude',
                  'latitude',
                  'city',
                  'address',
                  'distance',
                  'name',
                  'category_id',
                  'logo',
                  'company_id')

class BranchSchema(Schema):
    branches_location = fields.Nested(BranchesLocation, validate=must_not_be_blank)
    class Meta:
        fields = ('branch_id',
                  'company_id',
                  'name',
                  'branches_location')

class BranchUserSchema(Schema):
    # branch = fields.Nested(BranchSchema, validate=must_not_be_blank)
    class Meta:
        fields = ('branches_user_id',
                  'branch_id',
                  'user_name',
                  'email',
                  'latitude',
                  'longitude',
                  'branch_id',
                  'company_id',
                  'name',
                  'banner',
                  'logo',
                  'credits')

class BranchesProfile(Schema):
    class Meta:
        fields = ('branch_location_id',
                  'branch_id',
                  'category_id',
                  'state',
                  'longitude',
                  'latitude',
                  'city',
                  'address',
                  'name',
                  'company_id',
                  'banner',
                  'logo',
                  'following')

class BranchesProfileSearch(Schema):
    class Meta:
        fields = ('branch_location_id',
                  'branch_id',
                  'category_id',
                  'state',
                  'longitude',
                  'latitude',
                  'city',
                  'address',
                  'distance',
                  'name',
                  'company_id',
                  'banner',
                  'logo')

class BranchesAd(Schema):
    class Meta:
        fields = ('branch_id',
                  'name',
                  'company_id',
                  'banner',
                  'logo')

class BranchesFollowedSchema(Schema):
    class Meta:
        fields = ('branch_id',
                  'name',
                  'company_id',
                  'banner',
                  'logo',
                  'branch_follower_id')

class RankingUsersSchema(Schema):
    class Meta:
        fields = ('clients_coupon_id',
                  'names',
                  'surnames',
                  'birth_date',
                  'facebook_key',
                  'google_key',
                  'twitter_key',
                  'privacy_status',
                  'user_id',
                  'main_image',
                  'total_used',
                  'exp',
                  'level',
                  'is_friend',
                  'operation_id')

company_schema = CompanySchema()
companies_schema = CompanySchema(many=True)
branch_schema = BranchSchema()
branch_user_schema = BranchUserSchema(many=True)
branch_profile_schema = BranchesProfile(many=True)
branch_profile_search_schema = BranchesProfileSearch(many=True)
branch_ad_schema = BranchesAd(many=True)
branches_location_schema = BranchesLocation(many=True)
branches_followed_schema = BranchesFollowedSchema(many=True)
ranking_users_schema = RankingUsersSchema(many = True)

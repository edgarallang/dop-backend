from marshmallow import *
from ..utils import *

class BadgeSchema(Schema):
    class Meta:
        fields = ('badge_id',
                  'name',
                  'info')

badge_schema = BadgeSchema(many = True)
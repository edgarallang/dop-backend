from marshmallow import *
from ..utils import *

class BadgeSchema(Schema):
    class Meta:
        fields = ('badge_id',
                  'name',
                  'info')

class BadgesSchema(Schema):
    class Meta:
        fields = ('badge_id',
                  'name',
                  'info',
                  'user_id',
                  'reward_date',
                  'earned')

badge_schema = BadgeSchema(many = True)
badges_earned = BadgesSchema(many = True)
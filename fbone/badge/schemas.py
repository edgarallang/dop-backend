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
                  'earned',
                  'type',
                  'users_badges_id')

badge_schema = BadgeSchema(many = True)
badges_schema = BadgesSchema(many = True)
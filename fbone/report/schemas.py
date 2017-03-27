from marshmallow import *
from ..utils import *

# =====================================================================
# Report

class Report(Schema):
    class Meta:
        dateformat = ('iso')
        fields = ('day',
                  'count')

class Problems(Schema):
	class Meta:
		fields = ('branch_indiference',
				  'camera_broken',
				  'app_broken',
				  'qr_lost',
				  'names',
				  'surnames',
				  'email',
				  'branch_name',
				  'coupon_name')


report_schema = Report(many=True)
report_problems_schema = Problems(many=True)
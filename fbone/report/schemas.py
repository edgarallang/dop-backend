from marshmallow import *
from ..utils import *

# =====================================================================
# Report

class Reports(Schema):
    class Meta:
        dateformat = ('iso')
        fields = ('branch_id')


reports_schema = Reports(many=True)

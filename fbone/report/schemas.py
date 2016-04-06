from marshmallow import *
from ..utils import *

# =====================================================================
# Report

class Report(Schema):
    class Meta:
        dateformat = ('iso')
        fields = ('branch_id')


report_schema = Report(many=True)

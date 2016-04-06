from marshmallow import *
from ..utils import *

# =====================================================================
# Report

class Report(Schema):
    class Meta:
        dateformat = ('iso')
        fields = ('day',
                  'count')


report_schema = Report(many=True)

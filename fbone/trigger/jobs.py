from flask import current_app as app
from ..extensions import db

# -Company- ######################################

def ad_day_subtraction():
    import requests
    requests.put("http://localhost:5000/api/company/first/trigger")

###################################################
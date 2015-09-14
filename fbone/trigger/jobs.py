from flask import current_app as app
from ..extensions import db

# -Company- ######################################

def job_function(requests):
    requests.put("http://localhost:5000/api/company/first/trigger")
            # adArray = BranchAd.query.all()

            # for ad in branchesArray:
            #     branch = Branch.query.get(ad.branch_id)
            #     print branch.name





###################################################
from flask import current_app as app
from flask import copy_current_request_context
from ..extensions import db

# -Company- ######################################

def job_function():
    @copy_current_request_context
    def first_job():
        print 'bale berga la bida'
            # adArray = BranchAd.query.all()

            # for ad in branchesArray:
            #     branch = Branch.query.get(ad.branch_id)
            #     print branch.name





###################################################
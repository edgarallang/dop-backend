# -*- coding: utf-8 -*-

import os

from flask import Blueprint, render_template, send_from_directory, abort
from flask import current_app as APP
from flask.ext.login import login_required, current_user
from flask.ext.jwt import JWT, jwt_required

from .models import Company, Branch, BranchDesign, BranchLocation, BranchUser, Category


company = Blueprint('company', __name__, url_prefix='/')

@company.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated():
        return redirect(url_for('user.index'))

    form = SignupForm(next=request.args.get('next'))

    if form.validate_on_submit():
        user = User()
        # user.user_detail = UserDetail()
        form.populate_obj(user)

        db.session.add(user)
        db.session.commit()

        if login_user(user):
            return redirect(form.next.data or url_for('user.index'))

    return render_template('frontend/signup.html', form=form)
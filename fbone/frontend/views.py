# -*- coding: utf-8 -*-

from uuid import uuid4

from flask import (Blueprint, render_template, current_app, request,
                   flash, url_for, redirect, session, abort)
from flask.ext.mail import Message
from flask.ext.babel import gettext as _
from flask.ext.login import login_required, login_user, current_user, logout_user, confirm_login, login_fresh
from user_agents import parse

from ..user import User, UserImage, UserLevel, ForgotPassword
from ..extensions import db, mail, login_manager, oid
from .forms import SignupForm, LoginForm, RecoverPasswordForm, ReauthForm, ChangePasswordForm, OpenIDForm, CreateProfileForm


frontend = Blueprint('frontend', __name__, url_prefix='/api/frontend')


@frontend.route('/login/openid', methods=['GET', 'POST'])
@oid.loginhandler
def login_openid():
    if current_user.is_authenticated():
        return redirect(url_for('user.index'))

    form = OpenIDForm()
    if form.validate_on_submit():
        openid = form.openid.data
        current_app.logger.debug('login with openid(%s)...' % openid)
        return oid.try_login(openid, ask_for=['email', 'fullname', 'nickname'])
    return render_template('frontend/login_openid.html', form=form, error=oid.fetch_error())


@oid.after_login
def create_or_login(resp):
    user = User.query.filter_by(openid=resp.identity_url).first()
    if user and login_user(user):
        flash('Logged in', 'success')
        return redirect(oid.get_next_url() or url_for('user.index'))
    return redirect(url_for('frontend.create_profile', next=oid.get_next_url(),
            name=resp.fullname or resp.nickname, email=resp.email,
            openid=resp.identity_url))


@frontend.route('/create_profile', methods=['GET', 'POST'])
def create_profile():
    if current_user.is_authenticated():
        return redirect(url_for('user.index'))

    form = CreateProfileForm(name=request.args.get('name'),
            email=request.args.get('email'),
            openid=request.args.get('openid'))

    if form.validate_on_submit():
        user = User()
        form.populate_obj(user)
        db.session.add(user)
        db.session.commit()

        if login_user(user):
            return redirect(url_for('user.index'))

    return render_template('frontend/create_profile.html', form=form)


@frontend.route('/')
def index():
    current_app.logger.debug('debug')

    if current_user.is_authenticated():
        return redirect(url_for('user.index'))

    page = int(request.args.get('page', 1))
    pagination = User.query.paginate(page=page, per_page=10)
    return render_template('index.html', pagination=pagination)


@frontend.route('/search')
def search():
    keywords = request.args.get('keywords', '').strip()
    pagination = None
    if keywords:
        page = int(request.args.get('page', 1))
        pagination = User.search(keywords).paginate(page, 1)
    else:
        flash(_('Please input keyword(s)'), 'error')
    return render_template('frontend/search.html', pagination=pagination, keywords=keywords)


@frontend.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated():
        return redirect(url_for('user.index'))

    form = LoginForm(login=request.args.get('login', None),
                     next=request.args.get('next', None))

    if form.validate_on_submit():
        user, authenticated = User.authenticate(form.login.data,
                                    form.password.data)

        if user and authenticated:
            remember = request.form.get('remember') == 'y'
            if login_user(user, remember=remember):
                flash(_("Logged in"), 'success')
            return redirect(form.next.data or url_for('user.index'))
        else:
            flash(_('Sorry, invalid login'), 'error')

    return render_template('frontend/login.html', form=form)


@frontend.route('/reauth', methods=['GET', 'POST'])
@login_required
def reauth():
    form = ReauthForm(next=request.args.get('next'))

    if request.method == 'POST':
        user, authenticated = User.authenticate(current_user.name,
                                    form.password.data)
        if user and authenticated:
            confirm_login()
            current_app.logger.debug('reauth: %s' % session['_fresh'])
            flash(_('Reauthenticated.'), 'success')
            return redirect('/change_password')

        flash(_('Password is wrong.'), 'error')
    return render_template('frontend/reauth.html', form=form)


@frontend.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_('Logged out'), 'success')
    return redirect(url_for('frontend.index'))


@frontend.route('/signup', methods=['GET', 'POST'])
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


@frontend.route('/change_password', methods=['GET', 'POST'])
def change_password():
    user = None
    if current_user.is_authenticated():
        if not login_fresh():
            return login_manager.needs_refresh()
        user = current_user
    elif 'activation_key' in request.values and 'email' in request.values:
        activation_key = request.values['activation_key']
        email = request.values['email']
        user = User.query.filter_by(activation_key=activation_key) \
                         .filter_by(email=email).first()

    if user is None:
        abort(403)

    form = ChangePasswordForm(activation_key=user.activation_key)

    if form.validate_on_submit():
        user.password = form.password.data
        user.activation_key = None
        db.session.add(user)
        db.session.commit()

        flash(_("Your password has been changed, please log in again"),
              "success")
        return redirect(url_for("frontend.login"))

    return render_template("frontend/change_password.html", form=form)

@frontend.route('/help')
def help():
    return render_template('frontend/footers/help.html', active="help")

@frontend.route('/reset/password/<string:token>', methods=['GET'])
def reset_password(token):
    forgotPasswordUser = ForgotPassword.query.filter_by(token = token).first()

    if forgotPasswordUser:
        return render_template('frontend/reset_password.html', token = token)
    else:
        return render_template('frontend/message.html', user_found = False, message = 'El enlace ha expirado')

@frontend.route('/store/get', methods=['GET'])
def return_store():
    ua_string = request.headers.get('User-Agent')
    user_agent = parse(ua_string)
    os = user_agent.os.family
    store = 'https://itunes.apple.com/mx/app/dop/id1155231176?l=en&mt=8'
    if os == 'iOS':
        store = 'https://itunes.apple.com/mx/app/dop/id1155231176?l=en&mt=8'
    elif os == 'Android':
        store = 'https://play.google.com/store/apps/details?id=com.halleydevs.dop&hl=en'

    return redirect(store)

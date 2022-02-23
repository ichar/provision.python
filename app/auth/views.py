# -*- coding: utf-8 -*-

from flask import abort, render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_babel import gettext

from werkzeug.urls import url_quote, url_unquote

from flask import session
#from passlib.hash import pbkdf2_sha256 as hasher

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, IsNoEmail, IsPageClosed, page_redirect, errorlog, print_to, print_exception,
     default_unicode, default_encoding
     )

from . import auth
from ..import db, babel

from ..decorators import user_required
from ..utils import monthdelta, unquoted_url, decode_base64
from ..models import User, send_email, load_system_config
from ..settings import *

from .forms import LoginForm, ChangePasswordForm, ResetPasswordRequestForm, PasswordResetForm

IsResponseNoCached = 0

_EMERGENCY_EMAILS = ('webdev@rosan.ru',)

##  ===========================
##  User Authentication Package
##  ===========================

@babel.localeselector
def get_locale():
    return get_request_item('locale') or DEFAULT_LANGUAGE

def is_valid_pwd(x):
    v = len(x) > 9 or (len(x) > 7 and
        len(re.sub(r'[\D]+', '', x)) > 0 and
        len(re.sub(r'[\d]+', '', x)) > 0 and
        len(re.sub(r'[\w]+', '', x)) > 0) \
        and True or False
    return v

def is_pwd_changed(user):
    return user.last_pwd_changed and monthdelta(user.last_pwd_changed, 3) > user.last_seen and True or \
        IsBankperso and user.login in ('operator', 'adminbd',) and True or False

def send_message(user, token, **kw):
    subject = 'WebPerso Reset Password Request'
    html = render_template('auth/reset_password_email.html', user=user, token=token, **kw)

    addr_to = [user.email]
    addr_cc = _EMERGENCY_EMAILS

    return send_email(subject, html, user, addr_to, addr_cc=addr_cc)

def send_password_reset_email(user, **kw):
    token = user.get_reset_password_token()
    done = send_message(user, token, **kw)
    return done and token or ''

@auth.before_app_request
def before_request():
    g.current_user = current_user
    g.engine = None

    if IsDeepDebug:
        print('--> before_request:is_authenticated:%s is_active:%s' % (current_user.is_authenticated, current_user.is_active))

    if not request.endpoint:
        return

    if IsTrace and IsDeepDebug:
        print_to(errorlog, '--> before_request endpoint:%s' % request.endpoint)

    if request.endpoint != 'static':
        load_system_config(g.current_user)

    if current_user.is_authenticated and request.endpoint[:5] != 'auth.' and request.endpoint != 'static':
        if not current_user.confirmed:
            return redirect(url_for('auth.unconfirmed'))
        if not is_pwd_changed(current_user):
            current_user.unconfirmed()
            return redirect(url_for('auth.change_password'))
        if request.blueprint in APP_MODULES and request.endpoint.endswith('start'):
            current_user.ping()
        if IsPageClosed and (request.blueprint in page_redirect['items'] or '*' in page_redirect['items']) and \
            current_user.login not in page_redirect['logins'] and 'loader' not in request.url:
            if 'onservice' in page_redirect['base_url']:
                url = url_for('auth.onservice') + '?next=%s' % url_quote(request.full_path)
            else:
                url = '%s%s' % (page_redirect['base_url'], request.full_path)
            return redirect(url)

def get_default_url(user=None):
    next = request.args.get('next')
    url = next not in ('', '/') and next or user is not None and user.base_url or None
    if url and IsResponseNoCached:
        return '%s%svsc=%s' % (url, '?' in url and '&' or '?', vsc()[1:])
    return url or 'default'

def menu(force=None):
    kw = make_platform()
    if kw.get('is_mobile') or force:
        kw.update({
            'navigation' : get_navigation(),
            'title'      : gettext('Application Main Menu'),
            'module'     : 'auth',
            'width'      : 1280,
            'message'    : gettext('Main menu').upper(),
            'vsc'        : vsc(),
        })
        return render_template('default.html', **kw)
    return redirect(url_for('bankperso.start'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if IsDeepDebug:
        print('--> current_user.is_active:%s' % current_user.is_active)

    agent = request.user_agent

    try:
        form = LoginForm()
        login = form.login.data
    except:
        login = None

    if login and form.validate_on_submit():
        user = User.query.filter_by(login=login).first()
    else:
        user = None

    def _get_root(link):
        x = accessed_link.split('/')
        return len(x) > 1 and x[1] or link

    accessed_link = get_default_url(user)
    root = _get_root(accessed_link)

    if agent.browser is None:
        authorization = request.authorization

        login, password = '', ''

        try:
            if not authorization:
                login, password = decode_base64(request.headers.get('X-User-Authorization')).decode().split(':')
            else:
                login = authorization.username
                password = authorization.password

            if IsTrace:
                print_to(None, '!!! auth.login [%s:%s], headers:%s, remote_addr:%s' % (
                    login, 
                    password, 
                    repr(request.headers), 
                    request.remote_addr
                    ))

            user = User.query.filter_by(login=login).first()

            if user is not None and user.is_user:
                is_valid_password = user.verify_password(password)
                is_confirmed = user.confirmed
                is_enabled = user.enabled

                if is_confirmed and is_enabled and is_valid_password:
                    login_user(user)

                return redirect(accessed_link)

        except Exception as ex:
            print_to(None, '!!! auth.login.error %s [%s], headers:%s, remote_addr:%s' % (
                repr(authorization), 
                str(ex), 
                repr(request.headers), 
                request.remote_addr
                ))

            if IsPrintExceptions:
                print_exception()

        abort(401)

    elif user is not None:
        is_valid_password = user.verify_password(form.password.data)
        is_admin = user.is_administrator()
        is_confirmed = user.confirmed
        is_enabled = user.enabled

        if IsDeepDebug:
            print('--> user:%s valid:%s enabled:%s is_admin:%s' % (user and user.login, 
                is_valid_password, is_enabled, is_admin))

        IsEnabled = False

        if not user.is_user or not is_enabled:
            flash('Access to the application is denied!')
        elif not is_valid_password:
            flash('Password is incorrect!')
        elif not is_confirmed:
            flash('You should change you password!')
            accessed_link = url_for('auth.change_password')
            IsEnabled = True
        elif 'admin' in accessed_link and not is_admin:
            flash('You cannot access this page!')
        else:
            IsEnabled = True

        if IsDeepDebug:
            print('--> link:%s enabled:%s' % (accessed_link, IsEnabled))

        if IsTrace:
            print_to(errorlog, '\n==> login:%s %s enabled:%s' % (user.login, request.remote_addr, is_valid_password), request=request)

        if IsEnabled:
            try:
                login_user(user, remember=form.remember_me.data)
            except Exception as ex:
                print_to(errorlog, '!!! auth.login error: %s %s' % (login, str(ex)))
                if IsPrintExceptions:
                    print_exception()

            if accessed_link in ('default', '/'):
                return menu()
            return redirect(accessed_link)

    elif login:
        if IsTrace:
            print_to(errorlog, '\n==> login:%s is invalid!!! %s' % (login, request.remote_addr,))

        flash('Invalid username or password.')

    kw = make_platform(mode='auth')

    if kw.get('error'):
        kw.update({
            'request'       : repr(request),
            'user_agent'    : {
                'browser'   : agent.browser, 
                'platform'  : agent.platform, 
                'string'    : agent.string,
                },
            'authorization' : request.authorization,
            'endpoint'      : request.endpoint,
            'host'          : request.host,
            'remote_addr'   : request.remote_addr,
            'method'        : request.method,
            'args'          : request.args,
            'user'          : repr(user),
        })

        if IsDebug:
            """
            fo = open(errorlog, mode='a')
            json.dump(kw, fo, sort_keys=True, indent=4)
            fo.close()
            """

            print_to(errorlog, json.dumps(kw, sort_keys=True, indent=4))

        return jsonify(kw['error'])

    kw.update({
        'title'         : gettext('WebPerso Login'),
        'page_title'    : gettext('WebPerso Auth'),
        'header_class'  : 'middle-header',
        'show_flash'    : True,
        'semaphore'     : {'state' : ''},
        'sidebar'       : {'state' : 0, 'title' : ''},
        'show_password' : not IsEdge() and 1 or 0,
    })

    kw['vsc'] = vsc()

    link = 'auth/login.html'

    return render_template(link, form=form, **kw)

@auth.route('/default', methods=['GET', 'POST'])
def default():
    return menu(1)

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if IsDeepDebug:
        print('--> change password:is_active:%s' % current_user.is_active)

    form = ChangePasswordForm()

    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            if form.old_password.data == form.password.data:
                flash('Duplicate password.')
            elif not is_valid_pwd(form.password.data):
                flash('Invalid password syntax.')
            else:
                current_user.change_password(form.password.data)
                flash('Your password has been updated.')
                return default()
        else:
            flash('Invalid password.')
    elif not form.old_password.data:
        pass
    else:
        flash('ChangePasswordForm data is invalid.')

    if IsDeepDebug:
        print('--> password invalid: [%s-%s-%s]' % (form.old_password.data, form.password.data, form.password2.data))

    kw = make_platform(mode='auth')

    kw.update({
        'title'         : gettext('WebPerso Change Password'),
        'page_title'    : gettext('WebPerso Reset Password'),
        'header_class'  : 'middle-header',
        'show_flash'    : True,
        'semaphore'     : {'state' : ''},
        'sidebar'       : {'state' : 0, 'title' : ''},
        'module'        : 'auth',
        'show_password' : not IsEdge() and 1 or 0,
    })

    kw['vsc'] = vsc()

    link = 'auth/change_password.html'

    return render_template(link, form=form, **kw)

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return default()

    user = User.verify_reset_password_token(token)

    if not user:
        return redirect(url_for('auth.login'))

    form = PasswordResetForm()

    if form.validate_on_submit():
        password = form.password.data
        if not is_valid_pwd(password):
            flash('Invalid password syntax.')
        else:
            user.change_password(password)
            user.ping()
            flash('Your password has been reset.')
            return redirect(url_for('auth.login'))
    
    elif form.errors:
        for x in form.errors.get('password'):
            flash(x)

    kw = make_platform(mode='auth')

    kw.update({
        'title'         : gettext('WebPerso Change Password'),
        'page_title'    : gettext('Forced Reset Password'),
        'header_class'  : 'middle-header',
        'show_flash'    : True,
        'semaphore'     : {'state' : ''},
        'sidebar'       : {'state' : 0, 'title' : ''},
        'module'        : 'auth',
        'show_password' : not IsEdge() and 1 or 0,
    })

    kw['vsc'] = vsc()

    link = 'auth/reset_password.html'

    return render_template(link, form=form, **kw)

@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if IsDeepDebug:
        print('--> reset password request:is_active:%s' % current_user.is_active)

    if current_user.is_authenticated:
        return default()

    form = ResetPasswordRequestForm()

    link = 'auth/reset_password_request.html'

    kw = make_platform(mode='auth')

    kw.update({
        'title'         : gettext('WebPerso Change Password'),
        'page_title'    : gettext('Reset Password Request'),
        'header_class'  : 'middle-header',
        'show_flash'    : True,
        'semaphore'     : {'state' : ''},
        'sidebar'       : {'state' : 0, 'title' : ''},
        'module'        : 'auth',
    })

    if form.validate_on_submit():
        token = None
        user = User.query.filter_by(email=form.email.data).first()
        kw['greeting'] = user and ', %s' % user.full_name() or ''
        if user:
            token = send_password_reset_email(user, **kw)
        if token:
            flash('Check your email for the instructions to reset your password')
        else:
            flash('Error sending Reset Password Request email')
        kw['error'] = not token and 1 or 0
        kw['token'] = token and url_for('auth.reset_password', token=token, _external=True) or ''
        link = 'auth/reset_password_done.html'

    kw['vsc'] = vsc()

    return render_template(link, form=form, **kw)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('auth.login'))

@auth.route('/operator')
@login_required
def operator():
    logout_user()
    return redirect(url_for('persostation.register'))

@auth.route('/provision')
@login_required
def provision():
    logout_user()
    return redirect(url_for('provision.start')+'?sidebar=0&short=1')

@auth.route('/forbidden')
def forbidden():
    abort(403)

@auth.route('/onservice')
def onservice():
    if not IsPageClosed:
        next = request.args.get('next')
        return redirect(next or '/')
        
    kw = make_platform(mode='auth')

    kw.update({
        'title'        : gettext('WebPerso Login'),
        'page_title'   : gettext('WebPerso Auth'),
        'header_class' : 'middle-header',
        'show_flash'   : True,
        'semaphore'    : {'state' : ''},
        'sidebar'      : {'state' : 0, 'title' : ''},
        'module'       : 'auth',
        'message'      : page_redirect.get('message') or gettext('Software upgrade'),
    })

    kw['vsc'] = vsc()

    return render_template('auth/onservice.html', **kw)

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous:
        return redirect(url_for('auth.login'))

    kw = make_platform(mode='auth')

    kw.update({
        'title'        : gettext('WebPerso Unconfirmed'),
        'page_title'   : gettext('WebPerso Reset Password'),
        'header_class' : 'middle-header',
        'show_flash'   : True,
        'semaphore'    : {'state' : ''},
        'sidebar'      : {'state' : 0, 'title' : ''},
        'module'       : 'auth',
    })

    kw['vsc'] = vsc()

    return render_template('auth/unconfirmed.html', **kw)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('auth.default'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('auth.default'))

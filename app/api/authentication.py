# -*- coding: utf-8 -*-

from flask import g, jsonify, request
from flask_httpauth import HTTPBasicAuth

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, IsNoEmail, IsPageClosed, page_redirect, errorlog, print_to, print_exception,
     default_unicode, default_encoding
     )

from ..models import User
from . import api
from .errors import unauthorized, forbidden

auth = HTTPBasicAuth()

##  ==============================
##  Service Authentication Package
##  ==============================

@api.before_request
@auth.login_required
def before_request():
    if IsDebug and IsTrace:
        print_to(None, '--> service.before_request:is_authenticated:%s is_active:%s' % (
            g.current_user.is_authenticated, g.current_user.is_active
            ))

    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('Unconfirmed account')

@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')

@auth.verify_password
def verify_password(login_or_token, password):
    if IsDebug and IsTrace:
        print_to(errorlog, '\n--> service.verify_password [%s:%s]' % (login_or_token, password), request=request)

    if login_or_token == '':
        return False

    if password == '':
        g.current_user = User.verify_auth_token(login_or_token)
        g.token_used = True
        return g.current_user is not None

    user = User.get_by_login(login_or_token)
    if not user:
        return False

    g.current_user = user
    g.token_used = False

    return user.verify_password(password)

@api.route('/tokens/', methods=['POST'])
def get_token():
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({'token': g.current_user.generate_auth_token(expiration=3600), 'expiration': 3600})

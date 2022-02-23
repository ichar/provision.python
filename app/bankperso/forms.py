# -*- coding: utf-8 -*-

from app import app_release

try:
    from flask_wtf import FlaskForm as Form
except:
    from flask_wtf import Form

from wtforms import StringField, BooleanField, PasswordField, SelectField, validators
from wtforms.validators import DataRequired

from ..models import admin_config, User


class LoginForm(Form):
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

# -*- coding: utf-8 -*-

from app import app_release

try:
    from flask_wtf import FlaskForm as Form
except:
    from flask_wtf import Form

#from flask.ext.babel import gettext
from flask_babel import lazy_gettext as _l
from wtforms import StringField, BooleanField, PasswordField, SelectField, validators
from wtforms.validators import DataRequired

from ..models import admin_config, User


def _get_admin_config():
    """
    c = admin_config['users']['fields']
    return dict([(x, _l(c[x])) for x in c])
    """
    return admin_config['users']['fields']


class RegistrationForm(Form):
    fields = _get_admin_config()
    
    login = StringField(fields['login'], [validators.required(), validators.Length(min=4, max=25)])
    email = StringField(fields['email'], [validators.Length(min=6, max=35)])
    
    password = PasswordField('Новый пароль', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Пароль должен совпадать')
    ])

    confirm = PasswordField('Пароль еще раз')
    accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])


class UserForm(Form):
    fields = _get_admin_config()
    
    role_choices = [(str(x[0]), x[1]) for x in User.get_roles()]
    
    login = StringField(fields['login'], [validators.required(), validators.Length(min=4, max=25)])
    password = StringField(fields['password'], [validators.required(), validators.Length(min=3, max=25)])
    family_name = StringField(fields['family_name'], [validators.required(), validators.Length(max=50)])
    first_name = StringField(fields['first_name'], [validators.required(), validators.Length(max=50)])
    last_name = StringField(fields['last_name'], [validators.Length(max=50)])
    post = StringField(fields['post'], [validators.Length(max=100)])
    email = StringField(fields['email'], [validators.Length(max=50)])
    role = SelectField(fields['role'], [validators.required()], choices=role_choices)
    confirmed = BooleanField(fields['confirmed'], default=False)
    enabled = BooleanField(fields['enabled'], default=True)

# -*- coding: utf-8 -*-

from app import app_release

try:
    from flask_wtf import FlaskForm as Form
except:
    from flask_wtf import Form

from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Regexp, EqualTo, DataRequired, Email
from wtforms import ValidationError
from flask_babel import lazy_gettext

from ..models import User


class LoginForm(Form):
    login = StringField(lazy_gettext('Login'), validators=[Required(), Length(1, 64)])
    password = PasswordField(lazy_gettext('Password'), validators=[Required()])
    remember_me = BooleanField(lazy_gettext('Save connection'), default=True)
    submit = SubmitField(lazy_gettext('Log in'))


class ChangePasswordForm(Form):
    old_password = PasswordField(lazy_gettext('Old password'), validators=[Required()])
    password = PasswordField(lazy_gettext('New password'), validators=[Required(),
                                                          EqualTo('password2', message=lazy_gettext('Password must match'))])
    password2 = PasswordField(lazy_gettext('Password confirmation'), validators=[Required()])
    submit = SubmitField(lazy_gettext('Refresh'))


class ResetPasswordRequestForm(Form):
    email = StringField(lazy_gettext('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(lazy_gettext('Send request'))


class PasswordResetForm(Form):
    password = PasswordField(lazy_gettext('New password'), validators=[Required(),
                                                         EqualTo('password2', message=lazy_gettext('Password must match'))])
    password2 = PasswordField(lazy_gettext('Password confirmation'), validators=[Required()])
    submit = SubmitField(lazy_gettext('Update Login'))


class ChangeLoginForm(Form):
    login = StringField(lazy_gettext('Login'), validators=[Required(), Length(1, 64)])
    password = PasswordField(lazy_gettext('Password'), validators=[Required()])
    submit = SubmitField(lazy_gettext('Update Login'))

    def validate_login(self, field):
        if User.query.filter_by(login=field.data).first():
            raise ValidationError(lazy_gettext('Login already registered.'))

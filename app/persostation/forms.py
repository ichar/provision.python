# -*- coding: utf-8 -*-

from app import app_release

try:
    from flask_wtf import FlaskForm as Form
except:
    from flask_wtf import Form

from wtforms import StringField, BooleanField, SelectField, SelectMultipleField, RadioField, SubmitField, validators
from wtforms.fields.html5 import DateField, DateTimeField
from wtforms.validators import Required, DataRequired, Length, Regexp, EqualTo

from ..models import User


class RegisterOperIncForm(Form):
    date_from = DateField('Дата отгрузки:', 
        validators=[Required()]
        )
    client = SelectField('Клиент:', 
        choices=[], 
        validators=[Required()]
        )
    in_trigger = RadioField('', 
        choices = [('P', 'ПИН-конверты'), ('C', 'Карты')], 
        default='C', 
        id='trigger'
        )
    order = SelectField('Файл [карт]:', 
        choices=[]
        )
    batches = SelectMultipleField('Партии инкассации:', 
        choices=[(1, 'B1'), (2, 'B2'), (3, 'B3'),], 
        render_kw={'size':5, 'multiple':True}
        )

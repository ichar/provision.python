from flask import Blueprint

persostation = Blueprint('persostation', __name__)

from . import views


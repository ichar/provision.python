from flask import Blueprint

bankperso = Blueprint('bankperso', __name__)

from . import views

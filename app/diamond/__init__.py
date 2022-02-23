from flask import Blueprint

diamond = Blueprint('diamond', __name__)

from . import views


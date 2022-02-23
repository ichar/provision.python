from flask import Blueprint

preload = Blueprint('preload', __name__)

from . import views

from flask import Blueprint

configurator = Blueprint('configurator', __name__)

from . import views

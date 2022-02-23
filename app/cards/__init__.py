from flask import Blueprint

cards = Blueprint('cards', __name__)

from . import views

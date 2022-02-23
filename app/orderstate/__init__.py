from flask import Blueprint

orderstate = Blueprint('orderstate', __name__)

from . import views

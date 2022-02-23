from flask import Blueprint

semaphore = Blueprint('semaphore', __name__)

from . import views

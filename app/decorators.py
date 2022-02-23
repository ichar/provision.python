from functools import wraps
from flask import abort
from flask_login import current_user

from .models import roles

##  =============================
##  Application Global Decorators
##  =============================

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(role):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required(roles.ROOT)(f)

def user_required(f):
    return current_user.is_user

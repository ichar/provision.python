from functools import wraps
from flask import g

from ..models import roles
from .errors import forbidden

##  ======================
##  Service API Decorators
##  ======================

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user.can(role):
                return forbidden('Insufficient roles')
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def service_required(f):
    return role_required(roles.SERVICE)(f)

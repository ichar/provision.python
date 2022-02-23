# -*- coding: utf-8 -*-

from flask import jsonify, request, g, url_for, current_app, make_response

from config import (
     CONNECTION,
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, IsNoEmail, LocalDebug, basedir, errorlog, print_to, print_exception,
     default_unicode, default_encoding
     )

from . import api
from .decorators import service_required
from .errors import forbidden

##  ===================
##  Service API Package
##  ===================

def _request_data():
    data = None
    try:
        data = request.json
    except:
        try:
            data = request.data.decode(default_unicode)
        except:
            if IsPrintExceptions:
                print_exception()
    return data


@api.route('/orders/', methods=['GET'])
@service_required
def get_orders():
    response = make_response(
        'It works!',
    )

    if IsTrace:
        print_to(errorlog, '--> service.get_orders')

    del response.headers['WWW-Authenticate']
    return response

@api.route('/orders/<int:id>', methods=['GET'])
@service_required
def get_order(id):
    pass

@api.route('/status/<int:id>', methods=['GET'])
@service_required
def get_order_status(id):
    pass

@api.route('/new/', methods=['POST'])
@api.route('/orders/', methods=['POST'])
@service_required
def new_order():
    data = _request_data()

    if IsTrace:
        print_to(errorlog, '--> service.new_order, data:%s' % repr(data))

    order_id = 0
    location = url_for('api.get_order', id=order_id)

    kw = {
        'accepted' : 'new_order',
        'message':'It works!',
        'get_orders_url' : url_for('api.get_orders'), 
        'order_id' : order_id,
        'data' : data,
    }
    """
    response = make_response(
        jsonify(kw),
        201,
    )
    response.headers["Location"] = location
    response.headers['WWW-Authenticate'] = None
    """
    return jsonify(kw), 201, {'Location': location} #response

@api.route('/orders/<int:id>', methods=['PUT'])
@service_required
def edit_order(id):
    data = _request_data()

    if IsTrace:
        print_to(errorlog, '--> service.edit_order, id:%s, data:%s' % (id, repr(data)))

    kw = {
        'accepted' : 'edit_order',
        'message' :'It works!',
        'get_orders_url' : url_for('api.get_orders'), 
        'order_id' : id,
        'data' : data,
    }

    return jsonify(kw)

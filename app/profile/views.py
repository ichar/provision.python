# -*- coding: utf-8 -*-

import random

from config import (
     IsDebug, IsDeepDebug, IsTrace, LocalDebug, errorlog, print_to, print_exception,
     default_unicode, default_encoding, 
     UTC_FULL_TIMESTAMP
     )

from . import profile

from ..settings import *
from ..database import database_config, DatabaseEngine
from ..utils import getToday, getDate, getTime

from ..semaphore.views import initDefaultSemaphore

##  ===============
##  Profile Package
##  ===============

default_page = 'profile'
default_action = '800'
default_template = 'orders'
engine = None

IsLocalDebug = LocalDebug[default_page]

def before(f):
    def wrapper(**kw):
        global engine
        engine = DatabaseEngine()
        return f(**kw)
    return wrapper

@before
def refresh(**kw):
    return

def _get_page_args():
    args = {}

    try:
        args = { \
            'client'    : ('ClientID', int(get_request_item('client') or '0')),
        }
    except:
        args = { \
            'client'    : ('ClientID', 0),
        }
        flash('Please, update the page by Ctrl-F5!')

    return args

## ==================================================== ##

def _make_page_default(kw):
    file_id = int(kw.get('file_id'))
    batch_id = int(kw.get('batch_id'))

    is_admin = current_user.is_administrator()

    args = _get_page_args()

    file_name = ''
    filter = ''
    qs = ''

    # -------------------------------
    # Представление БД (default_view)
    # -------------------------------

    default_view = database_config[default_template]

    # --------------------------------------------
    # Позиционирование строки в журнале (position)
    # --------------------------------------------

    position = get_request_item('position').split(':')
    line = len(position) > 3 and int(position[3]) or 1

    # -----------------------------------
    # Параметры страницы (page, per_page)
    # -----------------------------------
    
    page, per_page = get_page_params(default_page)
    top = per_page * page
    offset = page > 1 and (page - 1) * per_page or 0

    # ------------------------
    # Поиск контекста (search)
    # ------------------------

    search = get_request_item('search')
    IsSearchEvent = False
    items = []

    if search:
        items.append("FileType like '%%%s%%'" % search)

    # XXX

    where = ''

    # ---------------------------------
    # Сортировка журнала (current_sort)
    # ---------------------------------

    current_sort = int(get_request_item('sort') or '0')
    if current_sort > 0:
        order = '%s' % default_view['columns'][current_sort]
    else:
        order = 'FileID'

    if current_sort in (0,2,5,7,8,):
        order += " desc"

    if IsDebug:
        print('--> where:[%s] order:[%s], args: %s' % (where, order, args))

    pages = 0
    total_orders = 0
    total_cards = 0
    orders = []

    # XXX

    # --------------------------------------
    # Нумерация страниц журнала (pagination)
    # --------------------------------------

    iter_pages = []
    for n in range(1, pages+1):
        if checkPaginationRange(n, page, pages):
            iter_pages.append(n)
        elif iter_pages[-1] != -1:
            iter_pages.append(-1)

    root = '%s/' % request.script_root
    query_string = 'per_page=%s' % per_page
    base = 'configurator?%s' % query_string

    modes = [(n, '%s' % default_view['headers'][x][0]) for n, x in enumerate(default_view['columns'])]
    sorted_by = default_view['headers'][default_view['columns'][current_sort]]

    pagination = {
        'total'             : '%s / %s' % (total_orders, total_cards),
        'per_page'          : per_page,
        'pages'             : pages,
        'current_page'      : page,
        'iter_pages'        : tuple(iter_pages),
        'has_next'          : page < pages,
        'has_prev'          : page > 1,
        'per_page_options'  : (5,10,20,30,40,50,100),
        'link'              : '%s%s%s%s' % (base, filter,
                                           (search and "&search=%s" % search) or '',
                                           (current_sort and "&sort=%s" % current_sort) or ''
                                           ),
        'sort'              : {
            'modes'         : modes,
            'sorted_by'     : sorted_by,
            'current_sort'  : current_sort,
        },
        'position'          : '%d:%d:%d:%d' % (page, pages, per_page, line),
    }

    kw.update({
        'base'              : base,
        'page_title'        : gettext('WebPerso Profile View'),
        'header_subclass'   : 'left-header',
        'loader'            : '/profile/loader',
        'semaphore'         : initDefaultSemaphore(),
        'args'              : args,
        'current_file'      : (file_id, file_name, batch_id),
        'navigation'        : get_navigation(),
        'config'            : database_config,
        'pagination'        : pagination,
        'orders'            : orders,
        'search'            : search or '',
    })

    sidebar = get_request_item('sidebar')
    if sidebar:
        kw['sidebar']['state'] = int(sidebar)

    return kw

## ==================================================== ##

#@profile.route('/', methods = ['GET'])
@profile.route('/profile', methods = ['GET','POST'])
@login_required
def index():
    debug, kw = init_response('WebPerso Configurator Page')
    kw['product_version'] = product_version

    command = get_request_item('command')

    if IsDebug:
        print('--> command:%s, file_id:%s, batch_id:%s' % (
            command,
            kw.get('file_id'),
            kw.get('batch_id')
        ))

    refresh()

    errors = []

    if command and command.startswith('admin'):
        pass

    kw['errors'] = '<br>'.join(errors)
    kw['OK'] = ''

    try:
        kw = _make_page_default(kw)

        if IsTrace:
            print_to(errorlog, '--> profile:%s %s %s' % (command, current_user.login, str(kw.get('current_file')),), request=request)
    except:
        print_exception()

    kw['vsc'] = (IsDebug or IsIE or IsForceRefresh) and ('?%s' % str(int(random.random()*10**12))) or ''

    if command and command.startswith('admin'):
        pass

    return make_response(render_template('profile.html', debug=debug, **kw))

@profile.after_request
def make_response_no_cached(response):
    if engine is not None:
        engine.close()
    # response.cache_control.no_store = True
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response

@profile.route('/loader', methods = ['GET','POST'])
@login_required
def loader():
    exchange_error = ''
    exchange_message = ''

    refresh()

    action = get_request_item('action') or default_action
    selected_menu_action = get_request_item('selected_menu_action') or action != default_action and action or '901'

    response = {}

    template = get_request_item('template') or default_template
    lid = get_request_item('lid')

    if IsDebug:
        print('--> action:%s %s lid:%s' % (action, template, lid))

    if IsSemaphoreTrace:
        print_to(errorlog, '--> loader:%s %s [%s:%s:%s] %s' % (action, current_user.login, template, lid, selected_menu_action, 
            getTime(UTC_FULL_TIMESTAMP)))

    state = {}

    try:
        if action == default_action:
            action = selected_menu_action

        if not action:
            pass

        elif action == '801':
            pass

    except:
        print_exception()

    response.update({ \
        'action'           : action,
        # --------------
        # Service Errors
        # --------------
        'exchange_error'   : exchange_error, 
        'exchange_message' : exchange_message,
        # -------------------------
        # Results (Semaphore state)
        # -------------------------
        'state'            : state,
    })

    return jsonify(response)

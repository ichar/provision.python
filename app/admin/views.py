# -*- coding: utf-8 -*-

import re
from config import (
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, IsNoEmail, errorlog, print_to, print_exception,
     default_unicode, default_encoding, 
     UTC_FULL_TIMESTAMP
     )

from flask import render_template, make_response, redirect, flash

from . import admin
from .. import db

from .forms import RegistrationForm, UserForm

from ..decorators import admin_required
from ..database import database_config, DatabaseEngine
from ..models import (
       User, Settings, Photo, Subdivision, Privileges,
       admin_config, admin_view_users, show_all, register_user, delete_user, 
       get_app_roles, get_subdivisions, get_roles, send_email
       )

from ..settings import *
from ..utils import getId, reprSortedDict, getDate, getToday, getHtmlCaption

from ..semaphore.views import initDefaultSemaphore

##  =============
##  Admin Package
##  =============

default_page = 'admin'
default_action = '100'
engine = None

default_columns = (DEFAULT_UNDEFINED, 'login', 'email', 'role', 'fio', 'post',)
default_sorts = {
    DEFAULT_UNDEFINED : ('---', '',),
    'login' : ('Login', '',),
    'email' : ('Email', '',),
    'role'  : ('Role', '',),
    'fio'   : ('Full person name', '',), 
    'post'  : ('Post', '',),
}

app_bankperso = 0

_EMAIL_HTML = '''
<html>
<head>
  <style type="text/css">
    h1 { font-size:18px; padding:0; margin:0 0 10px 0; }
    .hidden { display:none; }
    div.box { font:normal 12px Verdana; }
    div.box * { display:block; }
    div.message { margin-top:10px; margin-bottom:20px; font-size:12px; }
    div.line { border-top:1px dotted #888; width:100%%; height:1px; margin:10px 0 10px 0; }
    div.line hr { display:none; }
  </style>
</head>
<body>
  <div class="box">
  %(Greeting)s
  <div class="message">%(Message)s</div>
  %(Signature)s
  </div>
</body>
</html>
'''

_GREETING = '''<h3>Здравствуйте, уважаемые коллеги!</h3>'''
_SIGNATURE = '''<h3>С уважением,</h3><span>%s</span><br><span>%s</span>'''


def before(f):
    def wrapper(**kw):
        g.engine = DatabaseEngine(name='admin')
        return f(**kw)
    return wrapper

@before
def refresh(**kw):
    g.app_bankperso = is_app_bankperso()

def _get_page_args():
    args = {}

    def _get_bool(name):
        default_name = 'default_%s' % name
        if has_request_item(default_name):
            value = get_request_item(default_name, check_int=True)
        else:
            value = get_request_item(name, check_int=True)
        return value in (0,1) and str(value) or '-1'

    try:
        args.update({
            'subdivision'   : ['subdivision_id', int(get_request_item('q:subdivision_id') or '-1')],
            'app_role'      : ['app_role_id', int(get_request_item('q:app_role_id') or '-1')],
            'role'          : ['role_id', int(get_request_item('q:role_id') or '-1')],
            'confirmed'     : ['confirmed', int(_get_bool('q:confirmed'))],
            'enabled'       : ['enabled', int(_get_bool('q:enabled'))],
            'app_privilege' : ['app_privilege', int(get_request_item('q:app_privilege') or '-1')],
            'id'            : ['id', get_request_item('_id', check_int=True)],
        })

    except Exception as ex:
        args.update({
            'subdivision'   : ['subdivision_id', -1],
            'app_role'      : ['app_role_id', -1],
            'role'          : ['role_id', -1],
            'confirmed'     : ['confirmed', -1],
            'enabled'       : ['enabled', -1],
            'app_privilege' : ['app_privilege', -1],
            'id'            : ['id', None],
        })

        print_to(errorlog, '!!! admin._get_page_args:%s Exception: %s' % (g.current_user.login, str(ex)), request=request)

        flash('Please, update the page by Ctrl-F5!')

    return args

def _get_clients():
    return g.app_bankperso and g.engine.runQuery('clients', order='CName', as_dict=True, encode_columns=('CName',)) or []

## ==================================================== ##

def send_message(user, params):
    subject = params.get('subject') or gettext('Announcement')
    message = params.get('message')

    is_to_everybody = params.get('to_everybody') and True or False
    is_with_greeting = params.get('with_greeting') and True or False
    is_with_signature = params.get('with_signature') and True or False
    is_self_email = params.get('self_email') and True or False

    message = ''.join(['<p>%s</p>\n' % getHtmlCaption(s) for s in message.split('\n')])

    html = _EMAIL_HTML % {
        'Subject'   : '%s %s' % (gettext('PROVISION SYSTEM NAME'), subject), # Product title
        'Message'   : message,
        'Greeting'  : is_with_greeting and ('<div class="greeting">%s</div>' % _GREETING) or '',
        'Signature' : is_with_signature and ('<div class="signature"><hr><div>%s</div></div>' % (_SIGNATURE % (g.current_user.post, g.current_user.full_name()))) or '',
    }

    users = map(User.get_by_id, params.get('ids') or [])

    email = g.current_user.email

    addr_to = list(filter(None, [x.email for x in users if x.confirmed])) if is_to_everybody else [user.email]
    addr_cc = [email]
    addr_from = is_self_email and email or None

    return send_email(subject, html, g.current_user, addr_to, addr_cc=addr_cc, addr_from=addr_from)

@admin.route('/', methods = ['GET','POST'])
@admin.route('/index', methods = ['GET','POST'])
@login_required
@admin_required
def index():
    debug, kw = init_response('WebPerso Admin Page')
    kw['product_version'] = product_version

    command = get_request_item('command') or get_request_item('save') and 'save'

    if IsTrace:
        print_to(errorlog, '--> admin.index start:%s' % command)

    if not g.current_user.is_superuser():
        flash('Sorry, it\'s restricted for your responsibilities!')
        return redirect(url_for('auth.unconfirmed'))

    try:
        user_id = int(getId(get_request_item('user_id')) or 0)
    except:
        user_id = None

    if user_id == 1 and g.current_user.login != 'admin':
        flash('Sorry, it\'s restricted for your responsibilities!')
        return redirect(url_for('auth.unconfirmed'))

    if IsTrace:
        print_to(errorlog, '--> admin.index 0')

    refresh()

    if IsTrace:
        print_to(errorlog, '--> admin.index 0.1')

    # --------------------------------------------
    # Позиционирование строки в журнале (position)
    # --------------------------------------------

    position = get_request_item('position').split(':')
    line = len(position) > 3 and int(position[3]) or 1

    # ---------------------------------
    # Сортировка журнала (current_sort)
    # ---------------------------------

    current_sort = int(get_request_item('sort') or '0')

    # --------------------
    # Профайл пользователя
    # --------------------

    profile_clients = get_request_item('profile_clients') or ''
    photo = get_request_item('photo') or None
    settings = get_request_item('settings') or ''
    privileges = get_request_item('privileges') or ''

    if IsDeepDebug:
        print('--> %s:%s [%s] photo:%s settings:[%s] privileges:[%s]' % (
            command, user_id, profile_clients, photo and 'Y' or 'N', settings, privileges))

    if IsTrace:
        print_to(errorlog, '!!! admin:%s [%s] %s %s %s' % (
            g.current_user.login, command or '', user_id, request.remote_addr, request.method), request=request)

    user_form = UserForm()

    errors = []

    if request.method == 'POST' and command in ('add', 'save',):
        user_form = UserForm(request.form)
        IsOk, errors = register_user(user_form, user_id)
    elif command == 'delete':
        delete_user(user_id)

    forms = dict([('user', user_form,),])

    page, per_page = get_page_params(default_page)

    if IsDeepDebug:
        print('--> page %s:%s' % (page, per_page))

    # -----------------
    # Параметры фильтра
    # -----------------

    args = _get_page_args()

    where = {
        'subdivision_id' : args['subdivision'][1],
        'app_role_id'    : args['app_role'][1],
        'role_id'        : args['role'][1],
        'confirmed'      : args['confirmed'][1],
        'enabled'        : args['enabled'][1],
        'app_privilege'  : args['app_privilege'][1],
    }

    search = get_request_search()

    modes = [(n, '%s' % gettext(default_sorts[x][0]),) for n, x in enumerate(default_columns)]
    sorted_by = default_sorts[default_columns[current_sort]]

    order = current_sort and default_columns[current_sort]

    users = admin_view_users(user_id, page, per_page, context=search, where=where, order=order)

    clients = _get_clients()

    if IsTrace:
        print_to(errorlog, '--> admin.index 1')

    if command != 'delete' and user_id:
        user = User.get_by_id(user_id)

        if g.app_bankperso:
            user.set_profile_clients(profile_clients)
            profile_clients = user.get_profile_clients()

        if photo:
            user.set_photo(photo)
        else:
            photo = user.get_photo()

        if settings:
            user.set_settings(settings.split(':'))

        settings = user.get_settings()

        if privileges:
            user.set_privileges(privileges.split(':'))

        privileges = user.get_privileges()
    else:
        profile_clients = ''

    qf = ''.join(['&%s=%s' % ('q:%s' % args[x][0], args[x][1]) for x in args.keys() if args[x][1] is not None and args[x][1] > -1])

    subdivisions = []
    subdivisions.append((-1, DEFAULT_UNDEFINED,))
    subdivisions += [(x[0], x[2]) for x in get_subdivisions(order='name')]

    app_roles = []
    app_roles.append((-1, DEFAULT_UNDEFINED,))
    app_roles += sorted(get_app_roles(), key=lambda k: k[1])

    roles = []
    roles.append((-1, DEFAULT_UNDEFINED,))
    roles += sorted(get_roles(), key=lambda k: k[1])

    app_privileges = []
    app_privileges.append((-1, DEFAULT_UNDEFINED,))
    app_privileges += [(1, 'Manager',), (2, 'Consultant',), (3, 'Author',),]

    logical = [(-1, 'Everybody',), (1, 'Yes',), (0, 'No',),]

    root = '%s/' % request.script_root
    query_string = 'per_page=%s' % per_page
    base = 'index?%s' % query_string

    iter_pages = users.iter_pages(left_edge=5)
    pages = users.pages

    if IsTrace:
        print_to(errorlog, '--> admin.index 2')

    pagination = {
        'total'             : '%s ' % users.total,
        'per_page'          : per_page,
        'pages'             : pages,
        'current_page'      : page,
        'iter_pages'        : tuple(iter_pages),
        'has_next'          : users.has_next,
        'has_prev'          : users.has_prev,
        'per_page_options'  : (5,10,20,50,100),
        'link'              : '%s%s%s%s' % (base, qf, 
                                           (search and "&search=%s" % search) or '',
                                           (current_sort and "&sort=%s" % current_sort) or '',
                                            ),
        'sort'              : {
            'modes'         : modes,
            'sorted_by'     : sorted_by,
            'current_sort'  : current_sort,
        },
        'position'          : '%d:%d:%d:%d' % (page, users.pages, per_page, line),
    }

    loader = '/admin/loader'

    kw.update({
        'base'              : base,
        'page_title'        : gettext('WebPerso Administrator View'),
        'header_subclass'   : 'left-header',
        'show_flash'        : True,
        'model'             : 0,
        'loader'            : loader,
        'semaphore'         : initDefaultSemaphore(),
        'args'              : args,
        'user'              : (user_id,),
        'navigation'        : get_navigation(),
        'config'            : admin_config,
        'pagination'        : pagination,
        'forms'             : forms,
        'errors'            : errors,
        'OK'                : '',
        'users'             : users.value,
        'profile_clients'   : profile_clients,
        'clients'           : clients,
        'photo'             : photo,
        'subdivisions'      : subdivisions,
        'roles'             : roles,
        'settings'          : settings,
        'logical'           : logical,
        'privileges'        : privileges,
        'app_bankperso'     : g.app_bankperso,
        'app_roles'         : app_roles,
        'app_menus'         : APP_MENUS,
        'app_privileges'    : app_privileges,
        'search'            : search or '',
        'schedule_template' : {'documents': [], 'decrees': []},
        'schedule_params'   : {'documents': [0, 0], 'decrees': [0, 0]},
        'total_selected'    : '0 | 0.00',
    })

    sidebar = get_request_item('sidebar')
    if sidebar:
        kw['sidebar']['state'] = int(sidebar)

    kw['vsc'] = vsc(force=g.system_config.IsForceRefresh)
    kw['avatar_width'] = '80'

    if IsTrace:
        print_to(errorlog, '--> admin.index finish')

    return make_response(render_template('admin.html', debug=debug, **kw))

"""
@admin.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if register_user(request, form):
        flash('Thanks for registering')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)
"""

@admin.after_request
def make_response_no_cached(response):
    if g.engine is not None:
        g.engine.close()
    # response.cache_control.no_store = True
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response

@admin.route('/loader', methods = ['GET','POST'])
@login_required
@admin_required
def loader():
    exchange_error = '0'
    exchange_message = ''

    action = get_request_item('action') or default_action
    selected_menu_action = get_request_item('selected_menu_action') or action != default_action and action or '101'

    response = {}

    user_id = int(getId(get_request_item('user_id')) or '0')

    refresh()

    params = get_request_item('params') or ''

    if IsDeepDebug:
        print('--> action:%s file_id:%s params:%s' % (action, user_id, params))

    if IsTrace:
        print_to(errorlog, '--> loader:%s %s [%s:%s] params:%s' % (
            action, g.current_user.login, user_id, selected_menu_action, repr(params)
        ))

    if not g.current_user.is_superuser():
        return jsonify(response)

    data = {}
    profile_name = ''
    profile_clients = ''
    photo = ''
    settings = ''
    privileges = ''

    errors = []

    try:
        if action == default_action:
            action = selected_menu_action

        if not action:
            pass

        elif action == '101':
            user = user_id and User.get_by_id(user_id) or None

            if IsDeepDebug:
                print('--> %s:%s %s' % (action, user_id, user and user.login))

            if user is not None:
                data = user.get_data('register')
                profile_name = user.full_name()
                profile_clients = g.app_bankperso and user.get_profile_clients() or ''
                photo = user.get_photo()
                settings = user.get_settings()
                privileges = user.get_privileges()

        elif action == '102':
            user = user_id and User.get_by_id(user_id) or None

            if user is not None:
                photo = user.delete_photo()

        elif action == '103':
            user = user_id and User.get_by_id(user_id) or None

            if IsDeepDebug:
                print('--> %s:%s %s' % (action, user_id, user and user.login))

            if not send_message(user, params):
                errors.append('%s' % gettext('Error: Message sent with errors!'))

    except:
        print_exception()

    response.update({
        'action'           : action,
        # --------------
        # Service Errors
        # --------------
        'exchange_error'   : exchange_error, 
        'exchange_message' : exchange_message,
        # -----------------------------
        # Results (Log page parameters)
        # -----------------------------
        'user_id'          : user_id,
        # ----------------------------
        # Results (Admin page content)
        # ----------------------------
        'total'            : 0,
        'data'             : data,
        'props'            : None,
        'columns'          : None,
        'profile_name'     : profile_name,
        'profile_clients'  : profile_clients,
        'photo'            : photo,
        'settings'         : settings,
        'privileges'       : privileges,
        'errors'           : errors,
    })

    return jsonify(response)

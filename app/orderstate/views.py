# -*- coding: utf-8 -*-

import re
import random

from config import (
     CONNECTION, EXCHANGE_ROOT, IsDebug, IsDeepDebug, IsTrace, IsForceRefresh, errorlog, print_to, print_exception,
     default_unicode, default_encoding, default_iso
     )

from . import orderstate

from ..settings import *
from ..database import database_config, DatabaseEngine
from ..utils import getToday, getDate, getDateOnly, checkDate, indentXMLTree, isIterable, makeXLSContent, worder, getWhereFilter, checkPaginationRange
from ..worker import getInfoExchangeLogInfo

from ..semaphore.views import initDefaultSemaphore

##  ====================================
##  OrderState View Presentation Package
##  ====================================

default_action = '500'
engine = None

def before(f):
    def wrapper(**kw):
        global engine
        if engine is not None:
            engine.close()
        name = kw.get('engine') or 'orderstate'
        engine = DatabaseEngine(name=name, user=current_user, connection=CONNECTION[name])
        return f(**kw)
    return wrapper

@before
def refresh(**kw):
    return

def _get_columns(name):
    return ','.join(database_config[name]['columns'])

def _get_view_columns(view):
    columns = []
    for name in view['columns']:
        columns.append({
            'name'   : name,
            'header' : view['headers'].get(name)
        })
    return columns

def _get_page_args():
    args = {}

    try:
        args = { \
            'client'    : ('ClientID', int(get_request_item('client') or '0')),
            'action'    : ('ActionID', int(get_request_item('action') or '0')),
            'config'    : ('ConfigID', int(get_request_item('config') or '0')),
            'type'      : ('Type', get_request_item('type') or ''),
            'date_from' : ['RD', get_request_item('date_from') or ''],
            'date_to'   : ['RD', get_request_item('date_to') or ''],
        }
    except:
        args = { \
            'client'    : ('ClientID', 0),
            'action'    : ('ActionID', 0),
            'config'    : ('ConfigID', 0),
            'type'      : ('Type', ''),
            'date_from' : ('RD', ''),
            'date_to'   : ('RD', ''),
        }
        flash('Please, update the page by Ctrl-F5!')

    return args

def _get_order(order_id):
    default_config_item = 'orderstate-orders'
    default_view = database_config[default_config_item]

    where = 'TID=%s' % order_id
    
    cursor = engine.runQuery(default_config_item, columns=default_view['export'], top=1, where=where, as_dict=True)
    
    return cursor and cursor[0]

def _get_events(order_id, event_id=None, search=None, args=None):
    events = []
    selected_id = None

    if args:
        client = args['client']
        config = args['config']
        action = args['action']
        type = args['type']

        where = 'OrderID=%s%s%s%s%s' % (
            order_id, 
            client[1] and (" and %s='%s'" % (client[0], client[1])) or '',
            config[1] and (" and %s='%s'" % (config[0], config[1])) or '',
            action[1] and (" and %s='%s'" % (action[0], action[1])) or '',
            type[1] and (" and %s='%s'" % (type[0], type[1])) or '',
            )
    else:
        where = 'OrderID=%s' % order_id

    if search and search.startswith('a:'):
        where += " and Address like '%%%s%%'" % ''.join(search.split(':')[1:])

    cursor = engine.runQuery('orderstate-events', where=where, order='RD asc', as_dict=True,
                             worder_columns=('ToFolder',)
                             )
    if cursor:
        IsSelected = False

        for n, row in enumerate(cursor):
            if 'ErrorMessage' in row:
                row['ErrorMessage'] = row['ErrorMessage'].encode(default_iso).decode(default_encoding)

            row['Error'] = row['Result'] == 'Error' and True or False
            row['Ready'] = False #row['Result'] == 'OK' and True or False
            row['id'] = row['TID']

            if (event_id and event_id == row['TID']):
                row['selected'] = 'selected'
                IsSelected = True
            else:
                row['selected'] = ''

            events.append(row)

        if not IsSelected:
            row = events[0]
            selected_id = row['id']
            row['selected'] = 'selected'

    return events, selected_id

def _get_files(order_id, **kw):
    files = []

    where = 'OrderID=%s%s%s' % (
        order_id,
        getWhereFilter(kw.get('filter')[1], 'Address'),
        getWhereFilter(kw.get('filter')[2], 'Address'),
        )

    cursor = engine.runQuery('orderstate-files', where=where, order='TID', as_dict=True)
    if cursor:
        for n, row in enumerate(cursor):
            #row['Name'] = row['Name'].encode(default_iso).decode(default_encoding)
            row['IsError'] = row['IsError'] and 1 or 0
            files.append(row)
    return files

def _get_errors(order_id, **kw):
    errors = []

    where = 'OrderID=%s%s' % (
        order_id,
        getWhereFilter(kw.get('filter')[1], 'Address'))

    cursor = engine.runQuery('orderstate-errors', where=where, order='RD', as_dict=True)
    if cursor:
        for n, row in enumerate(cursor):
            row['Started'] = getDate(row['Started'], DEFAULT_DATETIME_INLINE_FORMAT)
            row['Finished'] = getDate(row['Finished'], DEFAULT_DATETIME_INLINE_FORMAT)
            row['ErrorMessage'] = row['ErrorMessage'].encode(default_unicode).decode(default_unicode)
            row['RD'] = getDate(row['RD'], DEFAULT_DATETIME_INLINE_FORMAT)
            errors.append(row)
    return errors

def _get_certificates(order_id, **kw):
    certificates = []
    cursor = engine.runQuery('orderstate-certificates', 
                             columns=database_config['orderstate-certificates']['export'], 
                             where='OrderID=%s' % order_id, order='RD', as_dict=True)
    if cursor:
        for n, row in enumerate(cursor):
            row['Event'] = '%s<br>%s' % (row['Address'], row['Name'])
            row['Info'] = '<br>'.join([worder(x, 50)[1] for x in row['Info'].encode(default_iso).decode(default_encoding).split('\n')])
            row['RD'] = getDate(row['RD'], DEFAULT_DATETIME_INLINE_FORMAT)
            certificates.append(row)
    return certificates

def _get_aliases(order_id, **kw):
    aliases = []
    
    client = kw.get('filter')[0] or None
    if client:
        client_id = engine.getReferenceID('orderstate-clients', 'Name', client)
    else:
        client_id = engine.getReferenceID('orderstate-orders', 'TID', order_id, tid='ClientID')
    
    if client_id:
        where = 'TID=%s' % client_id
    else:
        where = ''
    
    cursor = engine.runQuery('orderstate-aliases', where=where, as_dict=True)
    if cursor:
        for n, row in enumerate(cursor):
            if 'Title' in row:
                row['Title'] = row['Title'].encode(default_unicode).decode(default_unicode)
            aliases.append(row)
    return aliases

## ==================================================== ##

def getTabEventInfo(event_id):
    data = []
    number = str(event_id)

    try:
        if event_id:
            params = "%s, 1, ''" % (event_id)
            cursor = engine.runQuery('orderstate-eventinfo', as_dict=True, params=params)
            for n, row in enumerate(cursor):
                row['PName'] = row['PName'].encode(default_iso).decode(default_encoding)
                row['PValue'] = row['PValue'].encode(default_iso).decode(default_encoding)
                #row['RD'] = getDate(row['RD'], DEFAULT_DATETIME_INLINE_FORMAT)
                data.append(row)

            where = 'TID=%s' % event_id
            cursor = engine.runQuery('orderstate-events', columns=('Action',), where=where)

            if cursor is not None and len(cursor):
                number += ' %s' % str(cursor[0][0])
    except:
        print_exception()

    event = {'id':event_id, 'number':number}

    return number and data or [], event

def getTabFiles(order_id, **kw):
    return _get_files(order_id, **kw)

def getTabErrors(order_id, **kw):
    return _get_errors(order_id, **kw)

def getTabCertificates(order_id, **kw):
    return _get_certificates(order_id, **kw)

def getTabAliases(order_id, **kw):
    return _get_aliases(order_id, **kw)

def getTabInfoExchangeLog(columns, **kw):
    global engine
    
    file_name = ''
    client = kw.get('client') or None
    base = ''

    keys = []
    aliases = []

    date_from = getDateOnly(getToday())
    date_to = getToday()

    dates = [date_from, date_to,]

    order_id = kw.get('order_id') or None

    if 'engine' in kw:
        engine = kw.get('engine')

    original_logger = True

    configs = []

    if order_id is not None:
        #keys.append(str(order_id))

        top = 1
        where = 'TID = %s' % order_id

        # ---------------------------
        # Get Common File/Client info
        # ---------------------------

        cursor = engine.runQuery('orderstate-orders', top=top, where=where, as_dict=True)
        if cursor is not None and len(cursor):
            row = cursor[0]
            file_name = row['PackageName']
            client = row['Client']
            base = row['BaseFolder']

            if row['RD']:
                date_from = getDateOnly(row['RD'])

        if file_name:
            keys.append(file_name)

        if base:
            base = base.split('\\')[-1]

        dates = [date_from, date_to,]

        # ---------------------
        # Get Order Events info
        # ---------------------

        where = order_id and 'OrderID=%s' % order_id or None

        cursor = engine.runQuery('orderstate-events', columns=('Config', 'RD',), where=where, as_dict=True)
        if cursor:
            for n, row in enumerate(cursor):
                config = row['Config']
                if config not in configs:
                    configs.append(config)

                date = getDateOnly(row['RD'])
                if date not in dates:
                    dates.append(date)

    else:
        keys = kw.get('keys') or []
        if 'dates' in kw and kw.get('dates'):
            dates = kw['dates']

        original_logger = False

    if client:
        aliases.append(client)

        # -----------------------
        # Get Client Aliases list
        # -----------------------

        where = "Aliases like '%" + client +"%' or Name='" + client + "'"

        cursor = engine.runQuery('orderstate-aliases', where=where, as_dict=True)
        if cursor:
            for n, row in enumerate(cursor):
                if row['Aliases'] is not None and len(row['Aliases']):
                    aliases.extend(row['Aliases'].split(':'))

    if len(aliases):
        aliases = list(set(aliases))

    return getInfoExchangeLogInfo(keys=keys, split_by='\t', columns=columns, base=base, configs=configs, dates=dates, client=client, aliases=aliases,
                                  fmt=DEFAULT_DATETIME_PERSOLOG_FORMAT, 
                                  date_format=kw.get('date_format'),
                                  case_insensitive=kw.get('case_insensitive'),
                                  no_span=kw.get('no_span'),
                                  original_logger=original_logger,
                                  )

## ==================================================== ##

def _make_page_default(kw):
    order_id = int(kw.get('order_id'))
    event_id = int(kw.get('event_id'))

    is_admin = current_user.is_administrator()

    args = _get_page_args()

    file_name = ''
    filter = ''
    qs = ''

    # -------------------------------
    # Представление БД (default_view)
    # -------------------------------

    default_config_item = 'orderstate-orders'
    default_view = database_config[default_config_item]

    # --------------------------------------------
    # Позиционирование строки в журнале (position)
    # --------------------------------------------

    position = get_request_item('position').split(':')
    line = len(position) > 3 and int(position[3]) or 1

    # -----------------------------------
    # Параметры страницы (page, per_page)
    # -----------------------------------
    
    page, per_page = get_page_params()
    top = per_page * page
    offset = page > 1 and (page - 1) * per_page or 0

    # ------------------------
    # Поиск контекста (search)
    # ------------------------

    search = get_request_item('search')
    IsSearchBatch = False
    items = []

    # -----------------------------------
    # Поиск ID файла (search is a number)
    # -----------------------------------

    if search and not search.startswith('a:'):
        try:
            FileID = int(search)
            items.append('BP_FileID=%s' % FileID)
            IsSearchBatch = True
        except:
            x = len(search) > 1 and search[1] == ':' and ''.join(search.split(':')[1:]) or search
            if x:
                items.append("PackageName like '%%%s%%'" % x)

    # -------------
    # Фильтр (args)
    # -------------

    ClientID = ActionID = ConfigID = None
    date_from = date_to = ''
    params = ''

    if args:
        for key in args:
            name, value = args[key]
            id = None
            if value:
                if name == 'ClientID':
                    id = ClientID = value or None
                elif name == 'ActionID':
                    id = ActionID = value or None
                elif name == 'ConfigID':
                    id = ConfigID = value or None

            if value and key not in ('action', 'config', 'type',):
                if key == 'date_from':
                    if checkDate(value, DEFAULT_DATE_FORMAT[1]):
                        date_from = "%s 00:00" % value
                        items.append("%s >= '%s'" % (name, date_from))
                    else:
                        args['date_from'][1] = ''
                        continue
                elif key == 'date_to':
                    if checkDate(value, DEFAULT_DATE_FORMAT[1]):
                        date_to = "%s 23:59" % value
                        items.append("%s <= '%s'" % (name, date_to))
                    else:
                        args['date_to'][1] = ''
                        continue
                else:
                    items.append("%s=%s" % (name, value))

            if value:
                filter += "&%s=%s" % (key, value)

        if args['type'][1]:
            default_config_item = 'orderstate-orders:by-type'
            default_view = database_config[default_config_item]
            params = default_view['params'] % {
                'type'      : args['type'][1], 
                'client_id' : ClientID or 'null',
                'config_id' : ConfigID or 'null',
                'action_id' : ActionID or 'null',
                'date_from' : date_from,
                'date_to'   : date_to,
                'sort'      : current_sort,
            }

    if items:
        qs += ' and '.join(items)

    where = qs or ''

    # ---------------------------------
    # Сортировка журнала (current_sort)
    # ---------------------------------

    current_sort = int(get_request_item('sort') or '0')
    if current_sort > 0:
        order = '%s' % default_view['columns'][current_sort]
    else:
        order = 'RD'

    if current_sort in (0,2,4,8,):
        order += " desc"

    if IsDebug:
        print('--> where:%s %s, order:%s' % (where, args, order))

    pages = 0
    total_orders = 0
    total_cards = 0
    orders = []
    events = []
    clients = []
    actions = []
    configs = []
    types = []

    state = get_request_item('state')
    IsState = state and state != 'R0' and True or False

    args.update({ \
        'state' : ('State', state)
    })

    confirmed_order_id = 0

    # ======================
    # Выборка данных журнала
    # ======================

    if engine != None:

        # ------------------------------------------------
        # Поиск заказа по ID или номеру ТЗ (IsSearchBatch)
        # ------------------------------------------------
        
        if IsSearchBatch:
            file_id = 0

            cursor = engine.runQuery('orderstate-orders', columns=('TID',), where=where)
            for n, row in enumerate(cursor):
                file_id = row[0]

            where = 'TID=%s' % file_id

        # --------------------------------------------------
        # Кол-во записей по запросу в журнале (total_orders)
        # --------------------------------------------------

        if where:
            where += ' and '
        where += "PackageName != 'CHECK'"

        cursor = engine.runQuery(default_config_item, columns=('count(*)',), where=where, params=params)
        if cursor:
            total_orders = params and len(cursor) or cursor[0][0]

        if IsState:
            top = 1000

        # ===================
        # Типы файлов (files)
        # ===================

        cursor = engine.runQuery(default_config_item, columns=default_view['export'],
                                 top=top, where=where, order='%s' % order, as_dict=True, params=params
                                 )
        if cursor:
            IsSelected = False

            for n, row in enumerate(cursor):
                state_error = False
                state_ready = False

                if 'HasError' in row:
                    state_error = row['HasError'] == 1 and True or False
                    row['HasError'] = row['HasError'] == 1 and 'Да' or ''

                if state == 'R1' and (state_ready or state_error):
                    continue
                if state == 'R2' and not state_ready:
                    continue
                if state == 'R3' and not state_error:
                    continue

                if not IsState:
                    if offset and n < offset:
                        continue
                    if params and n >= top:
                        break

                if order_id:
                    if not confirmed_order_id and order_id == row['TID']:
                        confirmed_order_id = order_id
                    if not file_name and order_id == row['TID']:
                        file_name = row['PackageName']

                    if order_id == row['TID']:
                        row['selected'] = 'selected'
                        IsSelected = True
                else:
                    row['selected'] = ''

                if 'Aliases' in row:
                    row['Aliases'] = row['Aliases'] and re.sub(r':', '<br>', row['Aliases']) or ''

                row['BP_FileID'] = row['BP_FileID'] and '<a class="persolink" href="/bankperso?_id=%s" target="_self">BP:[%s]</a>' % (
                    row['BP_FileID'], row['BP_FileID']) or ''

                for x in row:
                    if not row[x] or str(row[x]).lower() == 'none':
                        row[x] = ''

                row['Error'] = state_error
                row['Ready'] = state_ready
                row['RD'] = getDate(row['RD'])
                row['id'] = row['TID']

                total_cards += row['Qty'] and int(row['Qty']) or 0
                orders.append(row)

            if line > len(orders):
                line = 1

            if not IsSelected and len(orders) >= line:
                row = orders[line-1]
                confirmed_order_id = order_id = row['id'] = row['TID']
                file_name = row['PackageName']
                row['selected'] = 'selected'

        if len(orders) == 0:
            order_id = 0
            file_name = ''
            event_id = 0
        elif confirmed_order_id != order_id or not order_id:
            row = orders[0]
            order_id = row['TID']
            file_name = row['PackageName']
        elif not confirmed_order_id:
            order_id = 0
            file_name = ''

        if IsState and orders:
            total_orders = len(orders)
            orders = orders[offset:offset+per_page]
            IsSelected = False
            for n, row in enumerate(orders):
                if order_id == row['TID']:
                    row['selected'] = 'selected'
                    file_name = row['PackageName']
                    IsSelected = True
                else:
                    row['selected'] = ''
            if not IsSelected:
                row = orders[0]
                row['selected'] = 'selected'
                order_id = row['OrderID']
                file_name = row['PackageName']

        if total_orders:
            pages = int(total_orders / per_page)
            if pages * per_page < total_orders:
                pages += 1

        # =====================
        # Типы событий (events)
        # =====================

        if order_id:
            events, event_id = _get_events(order_id, event_id=event_id, search=search, args=args)

        # ---------------------------------------------------------------
        # Справочники фильтра запросов (clients, actions, configs, types)
        # ---------------------------------------------------------------

        clients.append((0, DEFAULT_UNDEFINED,))
        cursor = engine.runQuery('orderstate-clients', order='Name', distinct=True)
        clients += [(x[0], x[1]) for x in cursor]

        actions.append((0, DEFAULT_UNDEFINED,))
        cursor = engine.runQuery('orderstate-actions', order='Name', distinct=True)
        actions += [(x[0], x[1]) for x in cursor]

        configs.append((0, DEFAULT_UNDEFINED,))
        where = ClientID and ("ClientID=%s" % ClientID) or ''
        cursor = engine.runQuery('orderstate-configs', where=where, order='Name', distinct=True)
        configs += [(x[0], x[1]) for x in cursor]

        types.append(DEFAULT_UNDEFINED)
        cursor = engine.runQuery('orderstate-types', order='Type', distinct=True)
        types += [x[0] for x in cursor]

        engine.dispose()

    # --------------------------------------
    # Нумерация страниц журнала (pagination)
    # --------------------------------------

    states = [
        ('R0', DEFAULT_UNDEFINED),
        ('R1', 'Файлы "В работе"'),
        ('R2', 'Завершено'),
        ('R3', 'Ошибки'),
    ]

    iter_pages = []
    for n in range(1, pages+1):
        if checkPaginationRange(n, page, pages):
            iter_pages.append(n)
        elif iter_pages[-1] != -1:
            iter_pages.append(-1)

    root = '%s/' % request.script_root
    query_string = 'per_page=%s' % per_page
    base = 'orderstate?%s' % query_string

    pagination = {
        'total'             : '%s / %s' % (total_orders, total_cards),
        'per_page'          : per_page,
        'pages'             : pages,
        'current_page'      : page,
        'iter_pages'        : tuple(iter_pages),
        'has_next'          : page < pages,
        'has_prev'          : page > 1,
        'per_page_options'  : (5,10,20,30,40,50,100),
        'link'              : '%s%s%s%s%s' % (base, filter,
                                             (search and "&search=%s" % search) or '',
                                             (current_sort and "&sort=%s" % current_sort) or '',
                                             (state and "&state=%s" % state) or '',
                                             ),
        'sort'              : {
            'modes'         : [(n, '%s' % default_view['headers'][x]) for n, x in enumerate(default_view['columns'])],
            'sorted_by'     : default_view['headers'][default_view['columns'][current_sort]],
            'current_sort'  : current_sort,
        },
        'position'          : '%d:%d:%d:%d' % (page, pages, per_page, line),
    }

    kw.update({
        'base'              : base,
        'page_title'        : gettext('WebPerso Order State View'),
        'header_subclass'   : 'left-header',
        'loader'            : '/orderstate/loader',
        'semaphore'         : initDefaultSemaphore(),
        'args'              : args,
        'current_file'      : (order_id, file_name, event_id),
        'navigation'        : get_navigation(),
        'config'            : database_config,
        'pagination'        : pagination,
        'orders'            : orders,
        'events'            : events,
        'clients'           : clients,
        'actions'           : actions,
        'configs'           : configs,
        'types'             : types,
        'states'            : states,
        'search'            : search or '',
    })

    sidebar = get_request_item('sidebar')
    if sidebar:
        kw['sidebar']['state'] = int(sidebar)

    return kw

## ==================================================== ##

#@orderstate.route('/', methods = ['GET'])
@orderstate.route('/orderstate', methods = ['GET','POST'])
@login_required
def index():
    debug, kw = init_response('WebPerso Order State Page')
    kw['product_version'] = product_version

    command = get_request_item('command')

    if IsDebug:
        print('--> command:%s, order_id:%s, event_id:%s' % (
            command,
            kw.get('order_id'),
            kw.get('event_id')
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
            print_to(errorlog, '--> orderstate:%s %s %s' % (command, current_user.login, str(kw.get('current_file')),), request=request)
    except:
        print_exception()

    kw['vsc'] = (IsDebug or IsIE or IsForceRefresh) and ('?%s' % str(int(random.random()*10**12))) or ''

    if command and command.startswith('admin'):
        pass

    elif command == 'export':
        columns = kw['config']['orders']['export']
        rows = []
        for data in kw['orders']:
            row = []
            for column in columns:
                if column == 'FinalMessage':
                    continue
                v = data[column]
                if 'Date' in column:
                    v = re.sub(r'\s+', ' ', re.sub(r'<.*?>', ' ', v))
                row.append(v)

            rows.append(row)

        rows.insert(0, columns)

        xls = makeXLSContent(rows, 'Журнал заказов (OrderState)', True)

        response = make_response(xls)
        response.headers["Content-Disposition"] = "attachment; filename=orders.xls"
        return response

    return make_response(render_template('orderstate.html', debug=debug, **kw))

@orderstate.after_request
def make_response_no_cached(response):
    if engine is not None:
        engine.close()
    # response.cache_control.no_store = True
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response

@orderstate.route('/orderstate/loader', methods = ['GET', 'POST'])
@login_required
def loader():
    exchange_error = ''
    exchange_message = ''

    refresh()

    action = get_request_item('action') or default_action
    selected_menu_action = get_request_item('selected_menu_action') or action != default_action and action or '501'

    response = {}

    order_id = int(get_request_item('order_id') or '0')
    event_id = int(get_request_item('event_id') or '0')

    filter = [
        engine.getReferenceID('orderstate-clients', key='TID', value=get_request_item('filter-client'), tid='Name'),
        engine.getReferenceID('orderstate-actions', key='TID', value=get_request_item('filter-action'), tid='Name'),
        engine.getReferenceID('orderstate-configs', key='TID', value=get_request_item('filter-config'), tid='Name'),
        get_request_item('filter-type'),
        get_request_item('filter-search-context'),
    ]

    x = filter[-1]
    
    if x and len(x) > 1 and x[1] == ':':
        filter[2] = ''.join(x.split(':')[1:])

    if IsDebug:
        print('--> action:%s order_id:%s event_id:%s filter:%s-%s-%s-%s-%s' % (
            action, order_id, event_id, filter[0], filter[1], filter[2], filter[3], filter[4]
        ))

    if IsTrace:
        print_to(errorlog, '--> loader:%s %s [%s:%s:%s]' % (action, current_user.login, order_id, event_id, selected_menu_action))

    currentfile = None
    events = []
    config = None

    data = ''
    number = ''
    columns = []

    props = None

    try:
        if action == default_action:
            order = _get_order(order_id)
            events, event_id = _get_events(order_id)
            currentfile = [order_id, order['PackageName'], event_id]
            config = _get_view_columns(database_config['orderstate-events'])
            action = selected_menu_action

        if not action:
            pass

        elif action == '501':
            data, props = getTabEventInfo(event_id)

        elif action == '502':
            columns = _get_view_columns(database_config['orderstate-files'])
            data = getTabFiles(order_id, filter=filter)

        elif action == '503':
            columns = _get_view_columns(database_config['orderstate-errors'])
            data = getTabErrors(order_id, filter=filter)

        elif action == '504':
            columns = _get_view_columns(database_config['orderstate-certificates'])
            data = getTabCertificates(order_id, filter=filter)

        elif action == '505':
            columns = _get_view_columns(database_config['orderstate-aliases'])
            data = getTabAliases(order_id, filter=filter)

        elif action == '506':
            columns = _get_view_columns(database_config['orderstate-log'])
            data = getTabInfoExchangeLog(database_config['orderstate-log']['columns'], order_id=order_id, filter=filter)

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
        'order_id'         : order_id,
        'event_id'         : event_id,
        # ---------------------------------------------
        # Default Lines List (sublines equal as events)
        # ---------------------------------------------
        'currentfile'      : currentfile,
        'sublines'         : events,
        'config'           : config,
        # --------------------------
        # Results (Log page content)
        # --------------------------
        'total'            : len(data),
        'data'             : data,
        'props'            : props,
        'columns'          : columns,
    })

    return jsonify(response)


# -*- coding: utf-8 -*-

from config import (
     CONNECTION, 
     IsDebug, IsDeepDebug, IsTrace, IsForceRefresh, IsPrintExceptions, LocalDebug,
     errorlog, print_to, print_exception,
     default_unicode, default_encoding, default_iso,
     LOCAL_EASY_DATESTAMP, LOCAL_EXCEL_TIMESTAMP, LOCAL_EXPORT_TIMESTAMP,
     UTC_FULL_TIMESTAMP, UTC_EASY_TIMESTAMP
     )

from . import persostation
from .forms import RegisterOperIncForm

from ..settings import *
from ..database import database_config, DatabaseEngine
from ..utils import (
     getToday, getDate, getDateOnly, checkDate, cdate, 
     makeCSVContent, makeXLSContent,
     checkPaginationRange, 
     )

from ..semaphore.views import initDefaultSemaphore

##  ====================
##  Persostation Package
##  ====================

default_page = 'persostation'
default_action = '800'
default_log_action = '801'
default_template = 'persostation-actions'
engine = None
dbase = None

IsLocalDebug = LocalDebug[default_page]

_views = {
    'cliens'     : 'persostation-clients',
    'orders'     : 'persostation-orders',
    'batches'    : 'persostation-batches',
    'batchtypes' : 'persostation-batchtypes',
    'actions'    : 'persostation-actions',
    'operators'  : 'persostation-operators',
}

_extra_action = ()

requested_object = {}

def before(f):
    def wrapper(**kw):
        global engine
        if engine is not None:
            engine.close()
        name = kw.get('engine') or 'configurator'
        engine = DatabaseEngine(name=name, user=current_user, connection=CONNECTION[name])
        return f(**kw)
    return wrapper

@before
def refresh(**kw):
    global dbase, requested_object
    dbase = Persostation()

    order_id = kw.get('order_id')
    if order_id is None:
        return

    requested_object = _get_order(order_id).copy()


class Persostation:

    def __init__(self):
        self.message_id = None
        self.status = None

    def register_action(self, operator, client, order, batch, action):
        """
            Register BatchTime Operator Action.

            Arguments:
                operator       -- dict, operator {login, name}

            Keyword arguments:
                bp_client_id   -- int: BP_ClientID
                bp_file_id     -- int: BP_FileID
                bp_batch_id    -- int: BP_BatchID

                client         -- string: client name
                fname          -- string: file name
                fqty           -- int: cards number
                register_date  -- string: file register datetime
                batchname      -- string: batch name
                batchtype_id   -- int: batchtype id
                batchno        -- int: batch number
                pers_tz        -- int: TZ
                element_qty    -- int: items number

                add            -- int: 1|0 add action
                delete         -- int: 1|0 delete action

            Returns:
                Stored procedure response.
                If OK `ActionID`, `Status`
        """
        if not action or not operator:
            return

        self.action_id, self.status = 0, '' 

        cursor = engine.runProcedure('persostation-register-action', 
                login=operator['login'], fullname=operator['name'], 
                bp_client_id=client.get('ClientID'),
                bp_file_id=order.get('FileID'),
                bp_batch_id=batch.get('TID'),
                client=client.get('BankName'),
                fname=order.get('FName'),
                fqty=order.get('FQty'),
                register_date=getDate(order.get('RegisterDate'), format=UTC_FULL_TIMESTAMP),
                batchname=batch.get('BatchType'),
                batchtype_id=batch.get('BatchTypeID'),
                batchno=batch.get('BatchNo'),
                pers_tz=batch.get('TZ'),
                element_qty=batch.get('ElementQty'),
                add=action == 'add' and 1 or 0,
                delete=action == 'delete' and 1 or 0,
            )

        if cursor:
            self.action_id = cursor[0][0]
            self.status = cursor[0][1]
        else:
            if IsDebug:
                print_to(None, '!!! register_action, no cursor: %s' % str(operator))

    def add(self, operator, client, order, batch):
        """
            Add a new BatchTime
        """
        self.register_action(operator, client, order, batch, action='add')

    def delete(self, operator, client, order, batch):
        """
            Delete BatchTime for given operator
        """
        self.register_action(operator, client, order, batch, action='delete')

    def search_actions(self, batches):
        if not batches:
            return []

        ids = ':'.join([str(x['id']) for x in batches])
        return engine.runProcedure('persostation-search-actions', ids=ids) or []


def _get_form_args():
    args = {}

    try:
        args.update({
            'date_from'   : ['StatusDate', get_request_item('date_from') or ''],
            'client'      : ['ClientID', int(get_request_item('client') or '0')],
            'in_trigger'  : ['InTrigger', get_request_item('in_trigger') or 'C'],
            'order'       : ['OrderID', int(get_request_item('order') or '0')],
            'active'      : get_request_item('active') or None,
        })
    except:
        args.update({
            'date_from'   : ['RegisterDate', ''],
            'client'      : ['ClientID', 0],
            'in_trigger'  : ['InTrigger', ''],
            'order'       : ['OrderID', 0],
            'active'      : None,
        })
        flash('Please, update the page by Ctrl-F5!')

    return args

def _get_page_args():
    args = {}

    try:
        args.update({
            'bank'        : ['ClientID', int(get_request_item('bank') or '0')],
            'batchtype'   : ['BatchTypeID', int(get_request_item('batchtype') or '0')],
            'date_from'   : ['RegisterDate', get_request_item('date_from') or ''],
            'date_to'     : ['RegisterDate', get_request_item('date_to') or ''],
            'operator'    : ['Operator', get_request_item('operator') or ''],
            'id'          : ['TID', int(get_request_item('_id') or '0')],
        })
    except:
        args.update({
            'bank'        : ['ClientID', 0],
            'batchtype'   : ['BatchTypeID', 0],
            'date_from'   : ['RegisterDate', ''],
            'date_to'     : ['RegisterDate', ''],
            'operator'    : ['Operator', ''],
            'id'          : ['TID', 0],
        })
        flash('Please, update the page by Ctrl-F5!')

    return args

def _form_clients(mode, **kw):
    template = 'banks'

    client_id = int(kw.get('client_id') or 0)

    clients = []
    selected_client = {}

    encode_columns = ('BankName',)
    cursor = engine.runQuery(template, order='BankName', distinct=True, as_dict=True, encode_columns=encode_columns)
    if cursor:
        for n, row in enumerate(cursor):
            if client_id and row['ClientID'] == client_id:
                selected_client = row

            clients.append(row)

        if not selected_client:
            selected_client = clients[0]

    if not mode:
        return selected_client
    return clients and [(x['ClientID'], x['BankName']) for x in clients], selected_client

def _form_orders(mode, date_from, **kw):
    template = 'orders'
    columns = database_config[template]['export']

    order_id = int(kw.get('order_id') or 0)
    client = kw.get('client')

    orders = []
    selected_order = {}

    where = '%s%s' % (
        "%s >= '%s 00:00'" % (date_from[0], date_from[1]),
        client and (' and %s=%s' % (client[0], client[1])) or '',
        )

    encode_columns = ('BankName', 'FileStatus',)
    cursor = engine.runQuery(template, columns=columns, where=where, as_dict=True, encode_columns=encode_columns)
    if cursor:
        for n, row in enumerate(cursor):
            if order_id and row['FileID'] == order_id:
                selected_order = row

            orders.append(row)

        if not selected_order:
            selected_order = orders[0]

    if not mode:
        return selected_order
    return orders and [(x['FileID'], '%s [%s]' % (x['FName'], x['FQty'])) for x in orders] or [], selected_order

def _form_batches(mode, order_id, **kw):
    template = 'batches'
    columns = database_config[template]['export']

    batch_id = int(kw.get('batch_id') or 0)
    batchtype = kw.get('batchtype')
    batchstatus = 4

    batches = []
    selected_batch = {}

    if order_id:
        where = 'FileID=%s%s%s' % (
            order_id, 
            batchtype and (' and BatchTypeID=%s' % batchtype) or '',
            batchstatus and (' and BatchStatusID=%s' % batchstatus) or ''
            )

        cursor = engine.runQuery(template, columns=columns, where=where, order='TID', as_dict=True, encode_columns=('BatchType', 'Status',))
        if cursor:
            for n, row in enumerate(cursor):
                row['StatusDate'] = getDate(row['StatusDate'], UTC_EASY_TIMESTAMP)
                row['Ready'] = 'обработка завершена' in row['Status'] and True or False
                row['id'] = row['TID']

                if batch_id and row['TID'] == batch_id:
                    selected_batch = row

                batches.append(row)

            if not selected_batch:
                selected_batch = batches[0]

        for action in dbase.search_actions(batches):
            source, key = 'TID', 'BP_BatchID'
            value = action[key]

            item = next(x for x in batches if x[source] == value)
            n = batches.index(item)

            for key in 'Operator:RD'.split(':'):
                batches[n][key] = action[key]

    def _batch_line(item):
        operator = item.get('Operator') or None
        RD = operator and getDate(item.get('RD'), UTC_EASY_TIMESTAMP) or ''

        s = 'ТЗ %s = %s, № %s, кол-во %s%s%s' % (
            item['TZ'],
            item['BatchType'],
            item['BatchNo'],
            item['ElementQty'],
            '', #item['StatusDate'],
            operator and ' = %s %s' % (operator, RD) or ''
        )
        return s

    if not mode:
        return selected_batch
    return batches and [(x['TID'], _batch_line(x)) for x in batches] or [], selected_batch

## ==================================================== ##

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

def _get_client(order_id):
    return order_id and engine.getReferenceID(default_template, key='OrderID', value=order_id, tid='ClientID') or None

def _get_order(order_id):
    columns = database_config[default_template]['export']
    where = 'OrderID=%s' % order_id
    encode_columns = ('Client',)
    cursor = engine.runQuery(default_template, columns=columns, top=1, where=where, as_dict=True, encode_columns=encode_columns)
    return cursor and cursor[0] or {}

def _get_batches(order_id, **kw):
    batches = []
    batch_id = kw.get('batch_id') or None
    pers_tz = kw.get('pers_tz') or None
    batchtype = kw.get('batchtype') or None
    file_id = kw.get('file_id') or None
    operator = kw.get('operator') or None
    selected_id = None

    view = _views['actions']
    columns = database_config[view]['export']

    where = 'OrderID=%s%s%s%s' % (
        order_id, 
        batchtype and (' and BatchTypeID=%s' % batchtype) or '',
        file_id and (' and BP_FileID=%s' % file_id) or '',
        operator and (" and Operator='%s'" % operator) or '',
        )

    cursor = engine.runQuery(view, columns=columns, where=where, order='BP_BatchID', as_dict=True, encode_columns=('BatchName',))
    if cursor:
        IsSelected = False
        
        for n, row in enumerate(cursor):
            row['Found'] = pers_tz and row['TZ'] == pers_tz
            row['id'] = row['BatchID']

            if (batch_id and batch_id == row['BatchID']) or (pers_tz and pers_tz == row['TZ'] and not IsSelected):
                row['selected'] = 'selected'
                selected_id = batch_id
                IsSelected = True
            else:
                row['selected'] = ''

            batches.append(row)

        if not IsSelected:
            row = batches[0]
            selected_id = row['id']
            row['selected'] = 'selected'

    return batches, selected_id

def _check_extra_tabs(row):
    return {}

def _valid_extra_action(action, row=None):
    tabs = _check_extra_tabs(row or requested_object)
    return (action not in _extra_action or action in list(tabs.values())) and action

## ==================================================== ##

def getTabParams(order_id, batch_id, param_name=None, format=None, **kw):
    data = []
    number = 0
    props = {'id' : batch_id}

    try:
        if order_id and batch_id:
            keys = ('OperatorName', 'RD',)
            columns = ('Operator', 'OperatorName', 'OperatorFullName', 'RD',)
            encode_columns = ('OperatorName', 'OperatorFullName',)
            where = "OrderID=%s and BatchID=%s" % (order_id, batch_id)
            cursor = engine.runQuery(_views['actions'], columns=columns, where=where, as_dict=True, encode_columns=encode_columns)

            for n, row in enumerate(cursor):
                try:
                    data = [{'PName':key, 'PType':1, 'PValue':row[key]} for key in keys]
                except:
                    print_exception()

            # -------------------
            # Информация о партии
            # -------------------

            view = _views['batches']
            columns = database_config[view]['export']
            encode_columns = ('BatchType', 'BatchName',)
            where = 'TID=%s' % batch_id
            
            cursor = engine.runQuery(view, columns=columns, top=1, where=where, as_dict=True, encode_columns=encode_columns)

            if cursor is not None and len(cursor):
                row = cursor[0]
                if row:
                    number = row['TZ']
                    props.update({
                        'number' : number,
                        'name'   : row['BatchName'],
                        'no'     : row['ElementQty'],
                    })

            view = _views['orders']
            where = 'TID=%s' % order_id
            cursor = engine.runQuery(view, top=1, where=where, as_dict=True)

            if cursor is not None and len(cursor):
                row = cursor[0]
                if row:
                    props.update({
                        'file'   : row['FName'],
                        'cards'  : row['FQty'],
                    })

    except:
        print_exception()

    return number and data or [], props

## ==================================================== ##

def _make_export(kw):
    """
        Экспорт журнала заказов в Excel
    """
    view = kw['config'][default_template]
    columns = view['columns']
    headers = [view['headers'][x][0] for x in columns]
    rows = []

    for data in kw['orders']:
        row = []
        for column in columns:
            if column not in data:
                continue
            try:
                v = data[column]
                if 'Date' in column and v:
                    v = re.sub(r'\s+', ' ', re.sub(r'<.*?>', ' ', str(v))).strip()
                    v = getDate(v, UTC_FULL_TIMESTAMP, is_date=True)
                    v = getDate(v, LOCAL_EXCEL_TIMESTAMP)
                row.append(v)
            except:
                print_exception()

        rows.append(row)

    rows.insert(0, headers)
    return rows

def _make_response_name(name=None):
    return '%s-%s' % (getDate(getToday(), LOCAL_EXPORT_TIMESTAMP), name or 'perso')

def _make_xls_content(rows, title, name=None):
    output = makeXLSContent(rows, title, True)
    ext = 'xls'
    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=%s.%s" % (_make_response_name(name), ext)
    return response

def _make_page_default(kw):
    order_id = int(kw.get('order_id'))
    batch_id = int(kw.get('batch_id'))

    is_admin = current_user.is_administrator()
    is_operator = current_user.is_operator()

    args = _get_page_args()

    file_name = ''
    filter = ''
    qs = ''

    # -------------------------------
    # Представление БД (default_view)
    # -------------------------------

    default_view = database_config[default_template]

    # -----------------------------------------
    # Поиск номера ТЗ в списке партий (pers_tz)
    # -----------------------------------------

    pers_tz = int(get_request_item('pers_tz') or '0')

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
    IsSearchBatch = False
    items = []
    preview_items = []
    FileID = None
    TZ = None

    # ----------------------------------------------
    # Поиск ID файла, номера ТЗ (search is a number)
    # ----------------------------------------------

    if search:
        try:
            FileID = TZ = int(search)
            items.append('(BP_FileID=%s OR TZ=%s)' % (FileID, TZ))
            IsSearchBatch = True
            pers_tz = TZ
        except:
            TZ = 0
            items.append("FName like '%%%s%%'" % search)

    # -----------------------------------
    # Команда панели управления (сommand)
    # -----------------------------------

    command = get_request_item('command')

    # -------------
    # Фильтр (args)
    # -------------

    ClientID = args['bank'][1]
    BatchTypeID = args['batchtype'][1]
    Operator = args['operator'][1]
    
    default_date_format = DEFAULT_DATE_FORMAT[1]
    today = getDate(getToday(), default_date_format)
    date_from = None

    if args:

        # -----------------
        # Параметры фильтра
        # -----------------

        for key in args:
            name, value = args[key]
            if value:
                if key in ('operator',):
                    items.append("%s='%s'" % (name, value))
                elif key == 'date_from':
                    if checkDate(value, DEFAULT_DATE_FORMAT[1]):
                        items.append("%s >= '%s 00:00'" % (name, value))
                        preview_items.append("%s >= '%s 00:00'" % (name, value))
                    else:
                        args['date_from'][1] = ''
                        continue
                elif key == 'date_to':
                    if checkDate(value, DEFAULT_DATE_FORMAT[1]):
                        items.append("%s <= '%s 23:59'" % (name, value))
                        preview_items.append("%s >= '%s 00:00'" % (name, value))
                    else:
                        args['date_to'][1] = ''
                        continue
                elif key in ('id', 'bank', 'batchtype'):
                    items.append("%s=%s" % (name, value))
                else:
                    items.append("%s like '%s%%'" % (name, value,))

                filter += "&%s=%s" % (key, value)

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
        order = 'OrderID'

    if current_sort in (0,2,5,7,8,):
        order += " desc"

    if IsDebug:
        print('--> where:[%s] order:[%s], args: %s' % (where, order, args))

    pages = 0
    total_orders = 0
    total_cards = 0
    orders = []
    batches = []
    banks = []
    batchtypes = []
    operators = []

    confirmed_file_id = file_id = 0
    selected_row = {}

    # ======================
    # Выборка данных журнала
    # ======================

    if engine != None:

        # ------------------------------------------------
        # Поиск заказа по ID или номеру ТЗ (IsSearchBatch)
        # ------------------------------------------------
        
        if IsSearchBatch:
            file_id = 0

            cursor = engine.runQuery(_views['batches'], columns=('BP_FileID',), where=where, distinct=True)
            for n, row in enumerate(cursor):
                file_id = row[0]

            if not file_id:
                where = 'BP_FileID=%s' % FileID

                cursor = engine.runQuery(default_template, columns=('BP_FileID',), where=where, distinct=True)
                for n, row in enumerate(cursor):
                    file_id = row[0]

            where = 'BP_FileID=%s' % file_id

        # --------------------------------------------------
        # Кол-во записей по запросу в журнале (total_orders)
        # --------------------------------------------------

        cursor = engine.runQuery(default_template, where=where, distinct=True, as_subquery=True, sql='select count(*), sum(FQty) from (%s) as tmp')
        if cursor:
            total_orders, total_cards = cursor[0]
            if total_cards is None:
                total_cards = 0

        if command == 'export':
            top = 10000

        # ===============
        # Заказы (orders)
        # ===============

        cursor = engine.runQuery(default_template, top=top, where=where, order='%s' % order, distinct=True, as_dict=True,
                                 encode_columns=('Client',))
        if cursor:
            IsSelected = False
            
            for n, row in enumerate(cursor):
                if offset and n < offset:
                    continue

                if file_id:
                    if not confirmed_file_id and file_id == row['BP_FileID']:
                        confirmed_file_id, order_id = file_id, row['OrderID']
                    if not file_name and file_id == row['BP_FileID']:
                        file_name = row['FName']

                    if file_id == row['BP_FileID']:
                        row['selected'] = 'selected'
                        selected_row = row
                        IsSelected = True
                else:
                    row['selected'] = ''

                for x in row:
                    if not row[x] or str(row[x]).lower() == 'none':
                        row[x] = ''

                row['FQty'] = str(row['FQty']).isdigit() and int(row['FQty']) or 0
                row['id'] = row['OrderID']

                orders.append(row)

            if line > len(orders):
                line = 1

            if not IsSelected and len(orders) >= line:
                row = orders[line-1]
                confirmed_file_id = file_id = row['BP_FileID']
                file_name = row['FName']
                order_id = row['id'] = row['OrderID']
                row['selected'] = 'selected'
                selected_row = row

        if len(orders) == 0:
            order_id = file_id = 0
            file_name = ''
            batch_id = 0
        elif confirmed_file_id != file_id or not order_id:
            row = orders[0]
            order_id, file_id = row['OrderID'], row['BP_FileID']
            file_name = row['FName']
        elif not confirmed_file_id:
            file_id = 0
            file_name = ''

        if total_orders:
            pages = int(total_orders / per_page)
            if pages * per_page < total_orders:
                pages += 1

        # ================
        # Партии (batches)
        # ================

        if order_id:
            batches, batch_id = _get_batches(order_id, batch_id=batch_id, pers_tz=pers_tz, batchtype=BatchTypeID, file_id=file_id, operator=Operator)

        # --------------------------------------------------------------------------------
        # Справочники фильтра запросов (banks, types, statuses, batchtypes, batchstatuses)
        # --------------------------------------------------------------------------------

        banks.append((0, DEFAULT_UNDEFINED,))
        cursor = engine.runQuery(_views['cliens'], order='Client', distinct=True, encode_columns=(1,))
        banks += [(x[0], x[1]) for x in cursor]

        batchtypes.append((0, 'Все',))
        cursor = engine.runQuery(_views['batchtypes'], order='BatchName', distinct=True, encode_columns=(1,))
        batchtypes += [(x[0], x[1]) for x in cursor]

        operators.append(('', DEFAULT_UNDEFINED,))
        cursor = engine.runQuery(_views['operators'], order='Login', distinct=True, encode_columns=(1,))
        operators += [(x[0], x[1]) for x in cursor]

        engine.dispose()

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
    base = 'persostation?%s' % query_string

    per_page_options = (5, 10, 20, 30, 40, 50, 100,)
    if is_admin:
        per_page_options += (250, 500)

    is_extra = False

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
        'per_page_options'  : per_page_options,
        'link'              : '%s%s%s%s' % (base, filter,
                                             (search and "&search=%s" % search) or '',
                                             (current_sort and "&sort=%s" % current_sort) or '',
                                             ),
        'sort'              : {
            'modes'         : modes,
            'sorted_by'     : sorted_by,
            'current_sort'  : current_sort,
        },
        'position'          : '%d:%d:%d:%d' % (page, pages, per_page, line),
    }

    loader = '/persostation/loader'

    kw.update({
        'base'              : base,
        'page_title'        : gettext('WebPerso Persostation BatchTime View'),
        'header_subclass'   : 'left-header',
        'show_flash'        : True,
        'loader'            : loader,
        'semaphore'         : initDefaultSemaphore(),
        'args'              : args,
        'current_file'      : (order_id, file_name, batch_id, pers_tz),
        'tabs'              : {},
        'navigation'        : get_navigation(),
        'config'            : database_config,
        'pagination'        : pagination,
        'orders'            : orders,
        'batches'           : batches,
        'banks'             : banks,
        'batchtypes'        : batchtypes,
        'operators'         : operators,
        'search'            : search or '',
    })

    sidebar = get_request_item('sidebar')
    if sidebar:
        kw['sidebar']['state'] = int(sidebar)

    return kw

## ==================================================== ##

#@persostation.route('/', methods=['GET'])
@persostation.route('/persostation', methods=['GET', 'POST'])
@login_required
def start():
    try:
        return index()
    except:
        if IsPrintExceptions:
            print_exception()

def index():
    debug, kw = init_response('WebPerso Persostation Page')
    kw['product_version'] = product_version

    is_admin = current_user.is_administrator()
    is_operator = current_user.is_operator()

    command = get_request_item('command')
    
    order_id = int(get_request_item('order_id') or '0')
    batch_id = int(get_request_item('batch_id') or '0')

    if IsDebug:
        print('--> command:%s, order_id:%s, batch_id:%s' % (command, order_id, batch_id))

    refresh(order_id=order_id)

    IsMakePageDefault = True
    logsearch = ''
    tagsearch = ''
    info = ''

    errors = []

    if command.startswith('admin'):
        command = command.split(DEFAULT_HTML_SPLITTER)[1]

        if get_request_item('OK') != 'run':
            command = ''

        elif not is_operator:
            flash('You have not permission to run this action!')
            command = ''

        if IsDebug:
            print('--> %s' % info)

        if IsTrace:
            print_to(errorlog, '--> command:%s %s [%s]' % (command, current_user.login, info))

    kw['errors'] = '<br>'.join(errors)
    kw['OK'] = ''

    try:
        if IsMakePageDefault:
            kw = _make_page_default(kw)

        if IsTrace:
            print_to(errorlog, '--> persostation:%s %s [%s:%s] %s %s' % (
                     command, current_user.login, request.remote_addr, kw.get('browser_info'), str(kw.get('current_file')), info,), 
                     request=request)
    except:
        print_exception()

    kw['vsc'] = vsc()

    if command:
        if not command.strip():
            pass

        elif command == 'export':
            return _make_xls_content(_make_export(kw), 'Журнал инкассации')

    return make_response(render_template('persostation.html', debug=debug, **kw))

@persostation.route('/persostation/register', methods=['GET', 'POST'])
@login_required
def register():
    title, page_title = 'WebPerso Persostation', 'Persostation Operating Time Register Form'
    debug, kw = init_response(title)

    refresh()

    if IsDeepDebug:
        print('--> register:is_active:%s' % current_user.is_active)

    args = _get_form_args()
    ok_disabled = cancel_disabled = ''

    actions = ['date_from', 'client', 'order', 'batches', None]

    try:
        active = actions.index(args['active'])
    except:
        active = 9

    date_from = args['date_from']
    client = active > 0 and args['client'] or None
    client_id = client and client[1] or None
    batchtype = args['in_trigger'][1] == 'C' and 10 or 5
    order = active > 1 and args['order'] or None
    order_id = order and order[1] or None

    ok = get_request_item('ok') and True or False
    cancel = get_request_item('cancel') and True or False

    batches = (active > 2 or ok or cancel) and request.form.getlist("batches") or None
    batch_id = batches and batches[0] or None

    form = RegisterOperIncForm()
    form.date_from.data = getDate(date_from[1], LOCAL_EASY_DATESTAMP, is_date=True) or getDateOnly(getToday())

    form.client.choices, selected_client = _form_clients(1, client_id=client_id)
    if active < 1:
        form.client.data = client_id = selected_client and selected_client['ClientID'] or None
        client = ['ClientID', client_id]

    form.order.choices, selected_order = _form_orders(1, date_from, client=client, order_id=order_id)
    if active < 2:
        form.order.data = order_id = selected_order and selected_order['FileID'] or None
        order = ['FileID', order_id]

    selected_batch = _form_batches(0, order_id, batch_id=batch_id)

    # ----------
    # Run Action
    # ----------

    is_action = (ok or cancel) and selected_client and selected_order and selected_batch and True or False
    operator = {
        'login' : current_user.login,
        'name'  : current_user.full_name(),
    }

    if is_action:
        kwargs = {
            'client' : selected_client, 
            'order'  : selected_order, 
            'batch'  : selected_batch,
        }
        if ok:
            dbase.add(operator, **kwargs)
        elif cancel:
            dbase.delete(operator, **kwargs)

    form.batches.choices, selected_batch = _form_batches(1, order_id, batchtype=batchtype)

    if len(form.batches.choices) == 0 or not selected_batch:
        ok_disabled, cancel_disabled = 'disabled', 'disabled'
    else:
        ok_disabled = 'Operator' in selected_batch and 'disabled' or ''
        cancel_disabled = operator['login'] != selected_batch.get('Operator') and 'disabled' or ''

    if IsDeepDebug:
        print('--> form data')

    kw.update({
        'title'          : gettext(title),
        'page_title'     : gettext(page_title),
        'base'           : 'register',
        'header_class'   : 'register-header',
        'show_flash'     : True,
        'semaphore'      : {'state' : ''},
        'sidebar'        : {'state' : 0, 'title' : ''},
        'is_admin'       : 0,
        'is_frame'       : 0,
        'is_demo'        : 0,
        'is_show_loader' : 0,
        'operator'       : operator['login'],
        'client'         : selected_client,
        'order'          : selected_order,
        'disabled'       : {'ok':ok_disabled, 'cancel':cancel_disabled},
    })

    kw['vsc'] = vsc(1)
    
    if IsMSIE():
        kw['css'] = 'persostation.ie'

    return render_template("persostation/register.html", form=form, **kw)

@persostation.after_request
def make_response_no_cached(response):
    if engine is not None:
        engine.close()
    # response.cache_control.no_store = True
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response

@persostation.route('/persostation/loader', methods = ['GET', 'POST'])
@login_required
def loader():
    exchange_error = ''
    exchange_message = ''

    action = get_request_item('action') or default_action
    selected_menu_action = get_request_item('selected_menu_action') or action != default_action and action or default_log_action

    response = {}

    order_id = int(get_request_item('order_id') or '0')
    batch_id = int(get_request_item('batch_id') or '0')
    batchtype = int(get_request_item('batchtype') or '0')
    operator = get_request_item('operator') or ''
    params = get_request_item('params') or None

    refresh(order_id=order_id)

    if IsDebug:
        print('--> action:%s order_id:%s batch_id:%s batchtype:%s' % (action, order_id, batch_id, batchtype))

    if IsTrace:
        print_to(errorlog, '--> loader:%s %s [%s:%s:%s:%s]%s' % (
                 action, 
                 current_user.login, 
                 order_id, 
                 batch_id, 
                 batchtype, 
                 selected_menu_action,
                 params and ' params:[%s]' % params or '',
            ))

    currentfile = None
    batches = []
    config = None

    data = ''
    number = ''
    columns = []
    total = 0

    props = None
    errors = None

    tabs = _check_extra_tabs(requested_object)

    try:
        if action == default_action:
            batches, batch_id = _get_batches(order_id, batchtype=batchtype, operator=operator)
            currentfile = [requested_object.get('OrderID'), requested_object.get('FName'), batch_id]
            config = _get_view_columns(database_config[_views['batches']])
            action = _valid_extra_action(selected_menu_action) or default_log_action

        if not action:
            pass

        elif action == '801':
            data, props = getTabParams(order_id, batch_id)

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
        'batch_id'         : batch_id,
        # ----------------------------------------------
        # Default Lines List (sublines equal as batches)
        # ----------------------------------------------
        'currentfile'      : currentfile,
        'sublines'         : batches,
        'config'           : config,
        'tabs'             : list(tabs.keys()),
        # --------------------------
        # Results (Log page content)
        # --------------------------
        'total'            : total or len(data),
        'data'             : data,
        'props'            : props,
        'columns'          : columns,
        'errors'           : errors,
    })

    return jsonify(response)

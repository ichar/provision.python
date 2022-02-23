# -*- coding: utf-8 -*-

import random
import os

from config import (
     CONNECTION, IsDebug, IsDeepDebug, errorlog, print_to, print_exception,
     default_unicode, default_encoding, default_iso
     )

from . import preload
#from .. import db

from ..settings import *
from ..database import database_config, DatabaseEngine
from ..utils import getToday, getDate, checkDate, indentXMLTree, isIterable, makeXLSContent, checkPaginationRange
from ..worker import getPersoLogFile

##  ==============================================
##  BankPerso Preloading View Presentation Package
##  ==============================================

engine = None

def before(f):
    def wrapper(**kw):
        global engine
        if engine is not None:
            engine.close()
        name = kw.get('engine') or 'preload'
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

## ==================================================== ##

def getTabPersoLog(columns, **kw):
    file_name = ''
    client = ''

    preload_id = kw.get('preload_id') or None

    top = 1
    where = 'PreloadID = %s' % preload_id

    date = getDate(getToday(), DEFAULT_DATETIME_PERSOLOG_FORMAT)

    cursor = engine.runQuery('preloads', top=top, where=where, as_dict=True)
    if cursor is not None and len(cursor):
        row = cursor[0]
        file_name = row['FName']
        client = row['BankName']
        if row['RegisterDate']:
            date = getDate(row['RegisterDate'], DEFAULT_DATETIME_PERSOLOG_FORMAT)

    if '.' in file_name:
        file_name = file_name.split('.')[0]

    perso_log = os.path.join('Log_%sPreloader' % client, '%s_%s_ToSDC.log' % (date, file_name))

    return getPersoLogFile(perso_log=perso_log, columns=columns, client=client)

## ==================================================== ##

def _make_page_default(kw):
    preload_id = int(kw.get('preload_id'))
    article = kw.get('article')

    file_name = ''

    args = { \
        'bank'      : ('BankName', get_request_item('bank')),
        'date_from' : ['RegisterDate', get_request_item('date_from') or ''],
        'date_to'   : ['RegisterDate', get_request_item('date_to') or ''],
    }
    
    page, per_page = get_page_params()

    top = per_page * page
    offset = page > 1 and (page - 1) * per_page or 0

    default_view = database_config['preloads']

    filter = ''
    qs = ''

    search = get_request_item('search')
    IsSearchBatch = False
    items = []

    if search:
        pass

    if args:
        for key in args:
            name, value = args[key]
            if value:
                if key == 'date_from':
                    if checkDate(value, DEFAULT_DATE_FORMAT[1]):
                        items.append("%s >= '%s 00:00'" % (name, value))
                    else:
                        args['date_from'][1] = ''
                        continue
                elif key == 'date_to':
                    if checkDate(value, DEFAULT_DATE_FORMAT[1]):
                        items.append("%s <= '%s 23:59'" % (name, value))
                    else:
                        args['date_to'][1] = ''
                        continue
                else:
                    items.append("%s like '%s%%'" % (name, value))

                filter += "&%s=%s" % (key, value)
        
    if items:
        qs += ' and '.join(items)

    where = qs or ''

    current_sort = int(get_request_item('sort') or '0')
    if current_sort > 0:
        order = '%s' % default_view['columns'][current_sort]
    else:
        order = 'PreloadID'

    if IsDebug:
        print('--> where:%s %s, order:%s' % (where, args, order))

    pages = 0
    total_preloads = 0
    total_cards = 0
    preloads = []
    articles = []
    banks = []

    state = get_request_item('state')
    IsState = state and state != 'R0' and True or False

    args.update({ \
        'state' : ('State', state)
    })

    confirmed_preload_id = 0

    if engine != None:
        cursor = engine.runQuery('preloads', columns=('count(*)',), where=where)
        if cursor:
            total_preloads = cursor[0][0]

        if IsState:
            top = 1000

        cursor = engine.runQuery('preloads', top=top, where=where, order='%s desc' % order, as_dict=True,
                                 encode_columns=('OrderNum',),
                                 worder_columns=('FinalMessage',),
                                 )
        if cursor:
            IsSelected = False
            for n, row in enumerate(cursor):
                state_error = row['ErrorCode'] != 0 and True or False
                row['ErrorCode'] = row['ErrorCode'] and str(row['ErrorCode']) or '0'
                state_ready = False #len(row['OrderNum']) > 0 and row['Error'] == 0 and True or False

                if state == 'R1' and (state_ready or state_error):
                    continue
                if state == 'R2' and not state_ready:
                    continue
                if state == 'R3' and not state_error:
                    continue

                if not IsState and offset and n < offset:
                    continue

                if not preload_id:
                    preload_id = row['PreloadID']
                if not confirmed_preload_id and preload_id == row['PreloadID']:
                    confirmed_preload_id = preload_id
                if not file_name and preload_id == row['PreloadID']:
                    file_name = row['FName']

                for x in row:
                    if not row[x] or str(row[x]).lower() == 'none':
                        row[x] = ''

                row['Error'] = state_error
                row['Ready'] = state_ready
                row['StartedDate'] = getDate(row['StartedDate'])
                row['FinishedDate'] = getDate(row['FinishedDate'])
                row['RegisterDate'] = getDate(row['RegisterDate'])
                row['id'] = row['PreloadID']

                if preload_id == row['PreloadID']:
                    row['selected'] = 'selected'
                    IsSelected = True
                else:
                    row['selected'] = ''

                total_cards += row['FQty'] and int(row['FQty']) or 0
                preloads.append(row)

            if not IsSelected and len(preloads) > 0:
                row = preloads[0]
                preload_id = row['id'] = row['PreloadID']
                file_name = row['FName']
                row['selected'] = 'selected'

        if len(preloads) == 0:
            preload_id = 0
            file_name = ''
            article = 0
        elif confirmed_preload_id != preload_id or not preload_id:
            row = preloads[0]
            preload_id = row['PreloadID']
            file_name = row['FName']
        elif not confirmed_preload_id:
            preload_id = 0
            file_name = ''

        if IsState and preloads:
            total_preloads = len(preloads)
            preloads = preloads[offset:offset+per_page]
            IsSelected = False
            for n, row in enumerate(preloads):
                if preload_id == row['PreloadID']:
                    row['selected'] = 'selected'
                    file_name = row['FName']
                    IsSelected = True
                else:
                    row['selected'] = ''
            if not IsSelected:
                row = preloads[0]
                row['selected'] = 'selected'
                preload_id = row['PreloadID']
                file_name = row['FName']

        if total_preloads:
            pages = int(total_preloads / per_page)
            if pages * per_page < total_preloads:
                pages += 1

        if preload_id:
            cursor = engine.runQuery('articles', where='PreloadID=%s' % preload_id, order='Article, V', as_dict=True)
            if cursor:
                IsSelected = False
                for n, row in enumerate(cursor):
                    row['V'] = row['V'].encode(default_iso).decode(default_encoding)
                    row['Error'] = row['unavailable'] and True or False
                    row['Ready'] = False
                    row['unavailable'] = row['unavailable'] and 'Отсутствует на складе' or 'Доступно'
                    row['[#]'] = n + 1

                    if (article and article == row['Article']):
                        row['selected'] = 'selected'
                        IsSelected = True
                    else:
                        row['selected'] = ''

                    articles.append(row)

                if not IsSelected:
                    row = articles[0]
                    article = row['id'] = ''
                    row['selected'] = 'selected'


        banks.append(DEFAULT_UNDEFINED)
        cursor = engine.runQuery('banks', order='BankName', distinct=True, encode_columns=(0,))
        banks += [x[0] for x in cursor]

        engine.dispose()

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
    base = 'preload?%s' % query_string

    pagination = {
        'total'             : '%s / %s' % (total_preloads, total_cards),
        'per_page'          : per_page,
        'pages'             : pages,
        'current_page'      : page,
        'iter_pages'        : tuple(iter_pages),
        'has_next'          : page < pages,
        'has_prev'          : page > 1,
        'per_page_options'  : (5,10,20,30,40,50,100,250,500),
        'link'              : '%s%s%s%s%s' % (base, filter,
                                             (search and "&search=%s" % search) or '',
                                             (current_sort and "&sort=%s" % current_sort) or '',
                                             (state and "&state=%s" % state) or ''
                                             ),
        'sort'              : {
            'modes'         : [(n, '%s' % default_view['headers'][x]) for n, x in enumerate(default_view['columns'])],
            'sorted_by'     : default_view['headers'][default_view['columns'][current_sort]],
            'current_sort'  : current_sort,
        },
    }

    kw.update({
        'base'              : base,
        'page_title'        : gettext('WebPerso Preloading View'),
        'header_subclass'   : 'left-header',
        'loader'            : '/preload/loader',
        'args'              : args,
        'current_file'      : (preload_id, file_name, article),
        'navigation'        : get_navigation(),
        'config'            : database_config,
        'preloads'          : preloads,
        'articles'          : articles,
        'pagination'        : pagination,
        'banks'             : banks,
        'states'            : states,
        'search'            : search or '',
    })

    return kw

## ==================================================== ##

#@preload.route('/', methods = ['GET'])
@preload.route('/preload', methods = ['GET','POST'])
@login_required
def index():
    debug, kw = init_response('WebPerso Preload Page')

    command = get_request_item('command')

    if IsDebug:
        print('--> command:%s, preload_id:%s, article:%s' % (
            command,
            kw.get('preload_id'),
            kw.get('article')
        ))

    refresh()

    errors = []

    if command and command.startswith('admin'):
        pass

    kw['errors'] = '<br>'.join(errors)
    kw['OK'] = ''

    try:
        kw = _make_page_default(kw)
    except:
        print_exception()

    kw['vsc'] = IsDebug and ('?%s' % str(int(random.random() * 10 ** 12))) or ''

    if command and command.startswith('admin'):
        pass

    elif command == 'export':
        columns = kw['config']['preloads']['export']
        rows = []
        for data in kw['preloads']:
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

        xls = makeXLSContent(rows, 'Журнал предобработки заказов', True)

        response = make_response(xls)
        response.headers["Content-Disposition"] = "attachment; filename=preloads.xls"
        return response

    return make_response(render_template('preload.html', debug=debug, **kw))


@preload.route('/preload/loader', methods = ['GET', 'POST'])
@login_required
def loader():
    exchange_error = ''
    exchange_message = ''

    refresh()

    action = get_request_item('action') or '401'

    response = {
        'action'  : action,
    }

    preload_id = int(get_request_item('preload_id') or '0')
    article = int(get_request_item('article') or '0')

    if IsDebug:
        print('--> action:%s preload_id:%s article:%s' % (action, preload_id, article))

    data = ''
    number = ''
    columns = []

    try:
        if not action:
            pass

        elif action == '401':
            view = database_config['persolog']
            columns = _get_view_columns(view)
            data = getTabPersoLog(columns=view['columns'], preload_id=preload_id)
    except:
        print_exception()

    response.update({
        # --------------
        # Service Errors
        # --------------
        'exchange_error'   : exchange_error,
        'exchange_message' : exchange_message,
        # -----------------------------
        # Results (Log page parameters)
        # -----------------------------
        'preload_id'       : preload_id,
        'article'          : article,
        # --------------------------
        # Results (Log page content)
        # --------------------------
        'total'            : len(data),
        'data'             : data,
        'number'           : number,
        'columns'          : columns,
    })

    return jsonify(response)

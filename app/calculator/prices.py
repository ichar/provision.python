# -*- coding: utf-8 -*-

import re

from config import (
     basedir,
     IsDebug, IsDeepDebug, IsTrace, IsForceRefresh, IsPrintExceptions, LocalDebug,
     errorlog, print_to, print_exception,
     default_unicode, default_encoding,
     LOCAL_EASY_DATESTAMP, LOCAL_EXCEL_TIMESTAMP, LOCAL_EXPORT_TIMESTAMP,
     UTC_FULL_TIMESTAMP, UTC_EASY_TIMESTAMP
     )

from . import calculator

from ..settings import *
from ..utils import (
     getToday, getDate, getDateOnly, checkDate, cdate, 
     makeXLSContent
     )

from ..semaphore.views import initDefaultSemaphore

##  ==================
##  Calculator Package
##  ==================

default_page = 'calculator'
default_locator = 'price'
default_data = 'data-0.csv'
default_action = '810'
default_log_action = '811'
default_template = 'calculator-actions'
engine = None
entries = None

IsLocalDebug = LocalDebug[default_page]

DEFAULT_BOUNDS = (500, 1000, 3000, 5000, 10000, 20000, 50000, 100000, 250000, 500000, 1000000,)
DEFAULT_TAX = 20.0
DEFAULT_CHARGE = 10.0
DEFAULT_FACTOR = 1000
DEFAULT_EXCHANGE_EURO = 75.17
DEFAULT_EXCHANGE_CROSS = 1.14
DEFAULT_AS_NUMBER = True

def before(f):
    def wrapper(**kw):
        global engine
        if engine is not None:
            engine.close()
        return f(**kw)
    return wrapper

@before
def refresh(**kw):
    global entries
    encoding = default_encoding
    source = '%s/storage/%s' % (basedir, default_data)

    measures = {
        'tax'    : DEFAULT_TAX,
        'charge' : DEFAULT_CHARGE,
        'euro'   : DEFAULT_EXCHANGE_EURO,
        'cross'  : DEFAULT_EXCHANGE_CROSS,
    }
    groups = {}
    prices = {}

    with open(source, 'r', encoding=encoding) as fin:
        for line in fin:
            if not line.strip():
                continue

            if line.startswith('['):
                m = re.match(r'\[(.*)\]', line.strip())
                if m:
                    group, name, title = m.group(1).split(':')
                    groups[group] = (name, title)
                continue

            item = line.split(';')
            name, stype = item[0].strip(), item[1]

            if stype == '0':
                measures[name] = float(item[2])
                continue

            elif stype not in prices:
                prices[stype] = []

            prices[stype].append({
                'name'  : name, 
                'price' : [int(float(x)*DEFAULT_FACTOR) for x in item[2:]],
            })

    def _get_checkbox(key):
        return [('item_%s_%s' % (key, n), x['name'], x['price']) for n, x in enumerate(prices[key])]

    def _get_radio(key):
        return [(n, x['name'], x['price']) for n, x in enumerate(prices[key])]

    if not groups:
        groups = {
            '1' : ('manufacture', 'Производство'),
            '2' : ('chip', 'Чип'),
            '3' : ('antenna', 'Опции'),
            '4' : ('perso', 'Персонализация'),
        }

    entries = {'groups' : groups, 'measures' : measures}

    for key in groups:
        entries[groups[key][0]] = _get_checkbox(key)

def _convert(value, as_number=False):
    if as_number:
        return float(value)
    return '%.3f' % value

def calculate(params, **kw):
    """
        Calculates price array.

        Results `data`:
            price   : prime cost of entries
            tax     : tax price value
            charge  : charge price value
            euro    : cost in Euro
            usd     : cost in USD
            rub     : cost in Ruble
        
        Returns:
            data -- dict, results
    """
    groups = entries['groups']
    measures = entries['measures']

    bound = DEFAULT_BOUNDS.index(int(params.get('bound') or '500'))
    items = sorted(params['items'].split(':'))
    
    chip = params.get('chip')
    if chip:
        items.append(chip)

    with_rows = kw.get('with_rows') and True or False
    checked_groups = ''
    rows = []

    if with_rows:
        x = params.get('bound')
        rows.append(('[b]Тираж:', int(x) if DEFAULT_AS_NUMBER else x))
        rows.append(['-'*20, ''],)

    price = 0

    for item in items:
        if not item or '_' not in item:
            continue

        x, group, value = item.split('_')
        key = groups[group][0]
        index = int(value)

        entry = entries[key][index]
        id, name, prices = entry

        if item != id:
            pass

        price += prices[bound]

        if with_rows:
            if group not in checked_groups:
                checked_groups += group
                rows.append(('[b]%s:' % groups[group][1], ''))
            rows.append((name, _convert(prices[bound] / DEFAULT_FACTOR, as_number=DEFAULT_AS_NUMBER)))

    price = price / DEFAULT_FACTOR
    tax = price * measures['tax'] / 100
    charge = (price + tax) * measures['charge'] / 100
    euro = price + tax + charge

    data = {
        'price'  : price,
        'tax'    : tax,
        'charge' : charge,
        'euro'   : euro,
        'usd'    : euro * measures['cross'],
        'rub'    : euro * measures['euro'],
    }

    for key in data.keys():
        data[key] = _convert(data[key])

    if with_rows:
        return data, rows

    return data

def _get_args():
    return get_request_items()

## ==================================================== ##

def _make_export(kw):
    """
        Экспорт в Excel
    """
    args = _get_args()
    measures = entries['measures']
    
    params = {
        'bound' : args.get('bound'),
        'items' : ':'.join([key for key in args.keys() if key.startswith('item')]),
        'chip'  : args.get('chip'),
    }

    data, rows = calculate(params, with_rows=True)

    headers = ['Параметр', 'Значение']
    rows += [
        ['-'*20, ''],
        ['Tax[%]', _convert(measures['tax'], as_number=DEFAULT_AS_NUMBER)],
        ['Charge[%]', _convert(measures['charge'], as_number=DEFAULT_AS_NUMBER)],
        ['EURO EXCHANGE RATE', _convert(measures['euro'], as_number=DEFAULT_AS_NUMBER)],
        ['EURO-USD CROSS', _convert(measures['cross'], as_number=DEFAULT_AS_NUMBER)],
        ['='*15, ''],
        ['[b]Себестоимость', _convert(data['price'], as_number=DEFAULT_AS_NUMBER)],
        ['[b]НДС', _convert(data['tax'], as_number=DEFAULT_AS_NUMBER)],
        ['[b]Наценка', _convert(data['charge'], as_number=DEFAULT_AS_NUMBER)],
        ['[b]ИТОГ [€]', _convert(data['euro'], as_number=DEFAULT_AS_NUMBER)],
        ['[b]ИТОГ [$]', _convert(data['usd'], as_number=DEFAULT_AS_NUMBER)],
        ['[b]ИТОГ в Рублях', _convert(data['rub'], as_number=DEFAULT_AS_NUMBER)],
    ]

    rows.insert(0, headers)
    return rows

def _make_response_name(name=None):
    return '%s-%s' % (getDate(getToday(), LOCAL_EXPORT_TIMESTAMP), name or 'calc')

def _make_xls_content(rows, title, name=None):
    output = makeXLSContent(rows, title, True)
    ext = 'xls'
    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=%s.%s" % (_make_response_name(name), ext)
    return response

def _make_page_default(kw):
    root = '%s/' % request.script_root
    query_string = ''
    base = '%s%s' % (default_locator, query_string and '?'+query_string or '')
    
    config = {}
    pagination = {}

    bounds = [(x, "{:>9,}".format(x).replace(',', ' ')) for x in DEFAULT_BOUNDS]
    measures = entries['measures']

    loader = '/%s/loader' % default_locator

    kw.update({
        'base'              : base,
        'module'            : default_locator,
        'page_title'        : gettext('WebPerso CardPrice Calculator View'),
        'header_class'      : 'calculator-header',
        'header_subclass'   : '',
        'show_flash'        : True,
        'loader'            : loader,
        'semaphore'         : initDefaultSemaphore(),
        'args'              : {},
        'navigation'        : [],
        'config'            : config,
        'pagination'        : pagination,
        'bounds'            : bounds,
        #'manufacture'       : entries['manufacture'],
        #'chip'              : entries['chip'],
        #'antenna'           : entries['antenna'],
        #'perso'             : entries['perso'],
        'tax'               : measures['tax'],
        'charge'            : measures['charge'],
        'euro'              : measures['euro'],
        'cross'             : measures['cross'],
        'search'            : '',
    })

    kw.update(entries)

    sidebar = get_request_item('sidebar')
    if sidebar:
        kw['sidebar']['state'] = int(sidebar)

    return kw

## ==================================================== ##

@calculator.route('/%s' % default_page, methods=['GET', 'POST'])
@calculator.route('/%s' % default_locator, methods=['GET', 'POST'])
@login_required
def start_ext1():
    try:
        return index()
    except:
        if IsPrintExceptions:
            print_exception()

def index():
    debug, kw = init_response('WebPerso Calculator Page')
    kw['product_version'] = product_version

    is_admin = current_user.is_administrator()

    command = get_request_item('command')

    refresh()

    IsMakePageDefault = True
    info = ''

    errors = []

    if command.startswith('admin'):
        command = command.split(DEFAULT_HTML_SPLITTER)[1]

        if get_request_item('OK') != 'run':
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
            print_to(errorlog, '--> calculator:%s %s [%s] %s %s' % ( \
                     command, current_user.login, request.remote_addr, str(kw.get('current_file')), info,), 
                     request=request)
    except:
        print_exception()

    kw['vsc'] = vsc()

    if command:
        if not command.strip():
            pass

        elif command == 'export':
            return _make_xls_content(_make_export(kw), 'Себестоимость ...')

    return make_response(render_template('calculator/%s.html' % default_locator, debug=debug, **kw))

@calculator.after_request
def make_response_no_cached(response):
    if engine is not None:
        engine.close()
    # response.cache_control.no_store = True
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response

@calculator.route('/%s/loader' % default_page, methods = ['GET', 'POST'])
@calculator.route('/%s/loader' % default_locator, methods = ['GET', 'POST'])
@login_required
def loader_ext1():
    exchange_error = ''
    exchange_message = ''

    action = get_request_item('action') or default_action
    selected_menu_action = get_request_item('selected_menu_action') or action != default_action and action or default_log_action

    response = {}

    params = get_request_item('params') or None

    refresh()

    if IsDebug:
        print('--> action:%s' % action)

    if IsTrace:
        print_to(errorlog, '--> loader:%s %s %s' % (
                 action, 
                 current_user.login, 
                 params and ' params:[%s]' % params or '',
            ))

    data = []

    errors = None

    try:
        if action == default_action:
            data = calculate(params)

        if not action:
            pass

    except:
        print_exception()

    response.update({
        'action'           : action,
        # --------------
        # Service Errors
        # --------------
        'exchange_error'   : exchange_error,
        'exchange_message' : exchange_message,
        # --------------------------
        # Results (Log page content)
        # --------------------------
        'total'            : len(data),
        'data'             : data,
        'errors'           : errors,
    })

    return jsonify(response)

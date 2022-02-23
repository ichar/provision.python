# -*- coding: utf-8 -*-

import re
from copy import deepcopy

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
default_locator = 'show'
default_data = 'data-1.csv'
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

KEY_TABS = 'Tabs'
KEY_ITEMS = 'Items'
KEY_PRICES = 'Prices'
KEY_COMMENTS = 'Comments'
KEY_IMAGES = 'Images'
KEY_CONSTANTS = 'Constants'
KEY_CONDITIONS = 'Conditions'

ITEM_DELIMETER = ';'
ITEM_TYPES = ('face', 'back')
ITEM_SPLITTER = ('|', ':', '-')

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

    measures = {
        'tax'    : DEFAULT_TAX,
        'charge' : DEFAULT_CHARGE,
        'euro'   : DEFAULT_EXCHANGE_EURO,
        'cross'  : DEFAULT_EXCHANGE_CROSS,
    }

    entries = {
        'tabs'       : {'_' : []}, 
        'groups'     : {'_' : [], 'tabs' : {}}, 
        'items'      : {'_' : [], 'groups' : {}}, 
        'prices'     : {}, 
        'comments'   : {}, 
        'images'     : {}, 
        'conditions' : {},
        'measures'   : measures,
    }

    encoding = default_encoding
    source = '%s/storage/%s' % (basedir, default_data)

    read_data(source, encoding)

##  -----------
##  Data Reader
##  -----------

def _set_price(x):
    return int(float(x)*DEFAULT_FACTOR)

def _get_item(id):
    x = id.split(ITEM_SPLITTER[2])
    tab = x[0]
    group = len(x) > 1 and '%s%s%s' % (x[0], ITEM_SPLITTER[2], x[1]) or None
    item = len(x) > 2 and id or None
    return tab, group, item

def _get_prices(item):
    prices = None
    id, values = item[0], item[1:]
    gtype = '0'
    if id in entries['items']['_'] and id in entries['items']:
        group = entries['items'][id]['group']
        gtype = entries['groups'][group]['ctype']
    if gtype == '1':
        prices = [(_set_price(p1), _set_price(p2)) for p1, p2 in [x.split('-') for x in values]]
    else:
        prices = [_set_price(p) for p in values]
    return id, prices

def _get_comments(comment):
    rows = []
    comments = [x.strip() for x in comment.split('|')]
    for n, s in enumerate(comments):
        if not s.endswith('.') and n < len(comments)-1:
            s += '.'
        rows.append(s)
    return rows

def read_data(source, encoding):
    global entries

    IsTabs = IsItems = IsPrices = IsComments = IsImages = IsMeasures = False

    with open(source, 'r', encoding=encoding) as fin:
        for line in fin:
            if not line.strip() or line.startswith('#'):
                continue

            if line.startswith('['):
                IsTabs = True if KEY_TABS in line else False
                IsItems = True if KEY_ITEMS in line else False
                IsPrices = True if KEY_PRICES in line else False
                IsComments = True if KEY_COMMENTS in line else False
                IsImages = True if KEY_IMAGES in line else False
                IsMeasures = True if KEY_CONSTANTS in line else False
                IsConditions = True if KEY_CONDITIONS in line else False
                continue

            item = [x.strip() for x in line.split(ITEM_DELIMETER)]

            if IsTabs:
                id, stype, title = item
                tab, group, item = _get_item(id)
                if not tab:
                    continue
                else:
                    ob = {'id' : id, 'stype' : stype, 'title' : title, 'selected' : id == '1' and 'selected' or ''}
                    entries['tabs'][id] = ob
                    entries['tabs']['_'].append(id)
                    entries['groups']['tabs'][id] = []

            elif IsItems:
                id, name, ctype, options, title = item
                tab, group, item = _get_item(id)
                name = name or group
                options = options and options.split('-') or None
                if not tab or not group:
                    continue
                elif not item:
                    ob = {'id' : id, 'name' : name, 'ctype' : ctype, 'options' : options, 'title' : title}
                    if id in entries['groups']:
                        pass
                    entries['groups'][id] = ob
                    entries['groups']['_'].append(ob)
                    entries['groups']['tabs'][tab].append(id)
                    entries['items']['groups'][id] = []
                else:
                    ob = {'id' : id, 'name' : name, 'ctype' : ctype, 'group' : group, 'title' : title, 'control' : {}}
                    gtype = entries['groups'][group]['ctype']
                    if not gtype or gtype == '0':
                        ob['value'] = options[0]
                        if ctype == '2':
                            ob['checked'] = options[0] == '00' and 'checked' or ''
                            ob['control']['item'] = {'id' : 'item_%s' % id, 'name' : 'item:%s' % name}
                        else:
                            ob['control']['item'] = {'id' : 'item_%s' % id, 'name' : 'item:%s' % id}
                    elif gtype == '1':
                        face, back = options
                        if ctype == '0':
                            ob['face'] = face == '1' and True or False
                            ob['back'] = back == '1' and True or False
                            ob['control']['face'] = {'id' : 'item_face_%s' % id, 'name' : 'face:%s' % id}
                            ob['control']['back'] = {'id' : 'item_back_%s' % id, 'name' : 'back:%s' % id}
                        elif ctype == '1':
                            ob['face'] = {'min' : '0', 'max' : face} if face > '0' else {}
                            ob['back'] = {'min' : '0', 'max' : back} if back > '0' else {}
                            ob['control']['face'] = {'id' : 'item_face_%s' % id, 'name' : 'face:%s' % id}
                            ob['control']['back'] = {'id' : 'item_back_%s' % id, 'name' : 'back:%s' % id}
                        elif ctype == '2':
                            ob['face'] = face
                            ob['back'] = back
                            ob['checked'] = options[0] == '00' and 'checked' or ''
                            ob['control']['face'] = {'id' : 'item_face_%s' % id, 'name' : 'item:%s' % name}
                            ob['control']['back'] = {'id' : 'item_back_%s' % id, 'name' : 'item:%s' % name}
                    entries['items'][id] = ob
                    if options:
                        for n, x in enumerate(options):
                            id_ = '%s%s%s' % (name, ITEM_SPLITTER[2], x)
                            if not id_ in entries['items']:
                                entries['items'][id_] = deepcopy(ob)
                                try:
                                    entries['items'][id_]['title'] += ' [%s]' % entries['groups'][group]['options'][n]
                                except:
                                    pass
                    entries['items']['_'].append(id)
                    entries['items']['groups'][group].append(id)

            elif IsPrices:
                id, prices = _get_prices(item)
                entries['prices'][id] = prices

            elif IsComments:
                id, comment = item
                entries['comments'][id] = _get_comments(comment)

            elif IsImages:
                id, image = item
                entries['images'][id] = image

            elif IsConditions:
                id, group, values = item
                if id not in entries['conditions']:
                    entries['conditions'][id] = {}
                entries['conditions'][id][group] = values.split(':')

            elif IsMeasures:
                id, measure = item
                entries['measures'][id] = float(measure)

##  ----------
##  Calculator
##  ----------

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
    controls = {}
    errors = {}

    groups = entries['groups']
    measures = entries['measures']
    conditions = entries['conditions']

    bound = DEFAULT_BOUNDS.index(int(params.get('bound') or '500'))
    items = sorted(params['items'].split(ITEM_SPLITTER[0]))
    options = sorted(params['options'].split(ITEM_SPLITTER[0]))

    with_rows = kw.get('with_rows') and True or False
    checked_groups = ''

    rows = []

    if with_rows:
        x = params.get('bound')
        rows.append(('[b]Тираж:', int(x) if DEFAULT_AS_NUMBER else x))
        rows.append(['-'*20, ''],)

    price = 0

    def _get_row(id):
        return ('[b]%s:' % groups[group]['title'], '')

    ids = []

    for item in items:
        if not item or ITEM_SPLITTER[1] not in item:
            continue

        key, id, value = item.split(ITEM_SPLITTER[1])
        if value and not key in ITEM_TYPES:
            id = '%s%s%s' % (id, ITEM_SPLITTER[2], value)
        tab, group, x = _get_item(id)

        prices = entries['prices'].get(id)

        if not (prices and bound < len(prices)):
            continue

        index = -1
        item_value = 0

        if key in ITEM_TYPES:
            index = ITEM_TYPES.index(key)
            item_value = prices[bound][index] * (value and int(value) or 1)
        else:
            item_value = prices[bound]

        price += item_value

        if with_rows:
            title = entries['items'][id]['title']
            if index > -1:
                title = '%s (%s)' % (title, groups[group]['options'][index])
            if group not in checked_groups:
                checked_groups += ':' + group
                rows.append(_get_row(id))
            rows.append((title, _convert(item_value / DEFAULT_FACTOR, as_number=DEFAULT_AS_NUMBER)))

        ids.append(id)

    # ----------------
    # Check Conditions
    # ----------------

    for id in ids:
        """
        for group in conditions.get(id, []):
            for items in entries['items']['groups'].get(group, []):
        
        
            if value in ids:
                errors[id] = value
                break
        """
        pass

    # -------------
    # Check Options
    # -------------

    pcharge = 0

    for option in options:
        if not option or ITEM_SPLITTER[1] not in option:
            continue

        name, value = option.split(ITEM_SPLITTER[1])

        if name == 'option_pcharge':
            pcharge = float(value)

    if with_rows:
        options = {
            'pcharge' : pcharge,
        }

    price = price / DEFAULT_FACTOR
    tax = price * measures['tax'] / 100
    charge = (price + tax) * (measures['charge'] + pcharge) / 100
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
        return data, rows, options

    return data, errors

## ==================================================== ##

def _get_args():
    return get_request_items()

def _make_export(kw):
    """
        Экспорт в Excel
    """
    args = _get_args()
    measures = entries['measures']

    def _in_keys(key, value):
        if key.startswith('item'):
            return True
        for itype in ITEM_TYPES:
            if key.startswith(itype) and (not value or float(value)):
                return True
        return False

    params = {
        'bound'   : args.get('bound'),
        'items'   : ITEM_SPLITTER[0].join(['%s%s%s' % (key, ITEM_SPLITTER[1], args[key]) for key in args.keys() 
            if _in_keys(key, args[key])]),
        'options' : ITEM_SPLITTER[0].join(['%s%s%s' % (key, ITEM_SPLITTER[1], args[key]) for key in args.keys() 
            if key.startswith('option')]),
    }

    data, rows, options = calculate(params, with_rows=True)

    pcharge = options.get('pcharge') and (' + %s' % options['pcharge']) or ''

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
        ['[b]Наценка%s' % pcharge, _convert(data['charge'], as_number=DEFAULT_AS_NUMBER)],
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

    results = [
        ('price', 'Себестоимость',),
        ('tax', 'НДС [%s%%]' % measures['tax']),
        ('charge', 'Наценка [%s%%]' % measures['charge']),
        ('euro', 'ИТОГ [€, %s%%]' % measures['euro']),
        ('usd', 'ИТОГ [$, %s%%]' % measures['cross']),
        ('rub', 'ИТОГ в Рублях'),
    ]

    options = [
        ('Прирост по наценке', [
            ('option_pcharge0', 'option_pcharge', '0.0', 'стандарт', 1),
            ('option_pcharge1', 'option_pcharge', '0.5', '0.5 %', 0),
            ('option_pcharge2', 'option_pcharge', '1.0', '1.0 %', 0),
            ('option_pcharge3', 'option_pcharge', '2.0', '2.0 %', 0),
        ]),
    ]

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
        'results'           : results,
        'options'           : options,
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
def start():
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

@calculator.route('/%s/loader' % default_locator, methods = ['GET', 'POST'])
@login_required
def loader():
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
            data, errors = calculate(params)

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

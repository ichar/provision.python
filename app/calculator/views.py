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

#from ..semaphore.views import initDefaultSemaphore

from .definitions import *
from .classes import *

##  ==================
##  Calculator Package
##  ==================

default_page = 'calculator'
default_locator = 'show'
default_data = 'data-3.csv'
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

    measures = {
        'tax'    : ['НДС [%]', DEFAULT_TAX, 1,],
        'charge' : ['Наценка [%]', DEFAULT_CHARGE, 2,],
        'euro'   : ['Курс Euro', DEFAULT_EXCHANGE_EURO, 3,],
        'cross'  : ['Кросс Euro/USD', DEFAULT_EXCHANGE_CROSS, 4,],
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
        'blocks'     : [],
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
    gtype = TYPE_GROUP_DEFAULT

    if id in entries['items']['_'] and id in entries['items']:
        group = entries['items'][id].group
        gtype = entries['groups'][group].ctype

    try:
        if gtype == TYPE_GROUP_DOUBLE:
            prices = [(_set_price(p1), _set_price(p2)) for p1, p2 in [x.split('-') for x in values]]
    except ValueError as ex:
        pass

    if not prices:
        prices = [_set_price(p) for p in values]

    return id, prices

def _get_comments(comment):
    rows = []
    if comment.startswith('<') and comment.endswith('>'):
        rows.append(comment)
    else:
        comments = [x.strip() for x in comment.split('|')]
        for n, s in enumerate(comments):
            if s.startswith('<') and s.endswith('>'):
                pass
            elif s and not s.endswith('.') and n < len(comments)-1:
                s += '.'
            rows.append(s)
    return rows

def _set_measure(id, value):
    global entries
    entries['measures'][id][1] = float(value)

def _get_measure(id):
    return entries['measures'][id][1]

def read_data(source, encoding):
    global entries

    rprice = re.compile(r'(.*)\[(.*)\]', re.I+re.DOTALL)

    IsTabs = IsItems = IsPrices = IsComments = IsImages = IsMeasures = IsConditions = IsDummy = False

    with open(source, 'r', encoding=encoding) as fin:
        for line in fin:
            if not line.strip() or line.startswith('#'):
                continue

            if line.startswith('"""'):
                IsDummy = not IsDummy
                line = ''

            if IsDummy:
                continue

            if line.startswith('['):
                IsTabs = True if KEY_TABS in line else False
                IsItems = True if KEY_ITEMS in line else False
                IsPrices = True if KEY_PRICES in line else False
                IsComments = True if KEY_COMMENTS in line else False
                IsImages = True if KEY_IMAGES in line else False
                IsMeasures = True if KEY_MEASURES in line else False
                IsConditions = True if KEY_CONDITIONS in line else False
                continue

            if '#' in line:
                line = line.split('#')[0]

            item = [x.strip() for x in line.split(ITEM_DELIMETER)]

            if not line or not item or (len(item) == 1 and item[0] == ''):
                continue

            try:
                if IsTabs:
                    id, stype, title = item
                    tab, group, item = _get_item(id)

                    if not tab:
                        continue
                    else:
                        ob = Tab(id, stype, title)
                        registry_tab(id, ob)

                elif IsItems:
                    id, name, ctype, options, title = item
                    tab, group, item = _get_item(id)

                    css = None
                    if options:
                        options = options.split(':')
                        css = len(options) > 1 and options[1] or None
                        options = options[0].split('-') or None
                    else:
                        options = None

                    if not (tab and group and tab in entries['tabs']['_']):
                        continue
                    elif not item:
                        ob = Group(id, name, ctype, title, options)
                        registry_group(id, ob, tab=tab)
                    else:
                        ob = Item(id, name, ctype, group, title)
                        gtype = entries['groups'][group].ctype
                        if ob.set_controls(gtype, options, css, items=entries['items']):
                            registry_item(id, ob, options=options)

                elif IsPrices:
                    id, prices = _get_prices(item)
                    dependence = None
                    m = rprice.search(id)
                    if m:
                        id, dependence = m.groups()
                    if id not in entries['prices']:
                        entries['prices'][id] = []
                    entries['prices'][id].append((dependence, prices))

                elif IsComments:
                    id, comment = item
                    entries['comments'][id] = [_get_comments(comment), 0]

                elif IsImages:
                    id, stype, image = item
                    entries['images'][id] = (stype or '0', ':' in image and image.split(':') or [image],)
                    if id in entries['comments']:
                        entries['comments'][id][1] = 1

                elif IsConditions:
                    id, stype, group, values = item
                    if id not in entries['conditions']:
                        entries['conditions'][id] = {}
                    if group not in entries['conditions'][id]:
                        entries['conditions'][id][group] = []
                    entries['conditions'][id][group].append((stype, values and values.split(':') or None))

                elif IsMeasures:
                    id, measure = item
                    _set_measure(id, measure)

            except:
                raise

    #sort_data()

def sort_data():
    global entries
    
    entries['tabs']['_'].sort()
    entries['groups']['_'].sort()
    entries['items']['_'].sort()

    for tab in entries['tabs']['_']:
        entries['groups']['tabs'][tab].sort()
        for group in entries['groups']['tabs'][tab]:
            entries['items']['groups'][group].sort()

def registry_tab(id, ob, **kw):
    global entries

    entries['tabs'][id] = ob
    entries['tabs']['_'].append(id)
    entries['groups']['tabs'][id] = []

def registry_group(id, ob, **kw):
    global entries

    if id in entries['groups']:
        pass

    tab = kw.get('tab')

    entries['groups'][id] = ob
    entries['groups']['_'].append(id)
    entries['groups']['tabs'][tab].append(id)
    entries['items']['groups'][id] = []

def registry_item(id, ob, **kw):
    global entries

    group = kw.get('group') or ob.group
    name = kw.get('name') or ob.name
    options = kw.get('options')

    entries['items'][id] = ob

    if options:
        for n, x in enumerate(options):
            id_ = '%s%s%s' % (name, ITEM_SPLITTER[2], x)
            if not id_ in entries['items']:
                ob_ = deepcopy(ob)
                op = entries['groups'][group].options
                subtitle = op and len(op) > n and op[n] or ''
                ob_.title += subtitle and ' [%s]' % subtitle or ''
                entries['items'][id_] = ob_
    
    entries['items']['_'].append(id)
    entries['items']['groups'][group].append(id)
    
    if ob.ctype in (TYPE_CHECKBOXCOLOR, TYPE_RADIOCOLOR):
        entries['blocks'].append(id)

##  ----------
##  Calculator
##  ----------

def _convert(value, as_number=False):
    if as_number:
        return float(value)
    return '%.3f' % value

def check_conditions(selected_ids):
    block_ids = []
    controls = {'ids' : [], 'disabled' : []}

    conditions = entries['conditions']
    blocks = entries['blocks']

    def is_disabled(stype, id, values, parent_disabled=False):
        #if parent_disabled:
        #    return True
        if stype == 'E':
            if not values:
                return 0
            elif id in values:
                return 0
            return 1
        if stype == 'D':
            if not values:
                return 1
            elif id in values:
                return 1
            return 0

    def set_block(id, oid, disabled, force=0):
        controls['ids'].append(oid)
        controls['disabled'].append([id, disabled])
        if disabled and (force or oid in selected_ids):
            block_ids.append(oid)

    def set_check(id):
        controls['disabled'].append([id, -1])

    def check_control(mode, condition, item, control):
        stype, values = condition
        parent_disabled = 0

        if mode == 1:
            parent_disabled = is_disabled(stype, item.id, values)
            set_block(control.id, control.oid, parent_disabled)

        if control.ctype == TYPE_SELECT:
            is_forced = False
            is_selected = False

            for option in control.options:
                disabled = is_disabled(stype, option.oid, values, parent_disabled=parent_disabled)
                set_block(option.id, option.oid, disabled)
                if disabled:
                    is_forced = True
                if not disabled and option.oid in selected_ids:
                    is_selected = True

            if is_forced and not is_selected: # and control.id not in controls['ids']:
                set_check(control.id)

    # ----------------
    # Check conditions
    # ----------------

    ids = sorted(list(selected_ids.keys()))

    for id in ids:
        if id not in conditions:
            if id in entries['items']:
                id = entries['items'][id].group

        if id not in conditions:
            continue

        for group in conditions[id].keys():
            for condition in conditions[id].get(group, []):

                for key in entries['items']['groups'].get(group, []):
                    item = entries['items'][key]
                    for control in item.controls.values():
                        check_control(1, condition, item, control)

                item = entries['items'].get(group)
                if not item or not hasattr(item, 'controls'):
                    continue

                for control in item.controls.values():
                    check_control(1, condition, item, control)

    # ------------
    # Forced block
    # ------------

    for id in blocks:
        item = entries['items'].get(id)
        if not item or not hasattr(item, 'controls'):
            continue

        disabled = not id in selected_ids
        item.disabled = disabled

        for key, control in item.controls.items():
            if key != 'item':
                set_block(control.id, control.oid, disabled, force=True)
    
    return block_ids, controls['disabled']

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

    bound = DEFAULT_BOUNDS.index(int(params.get('bound') or '500'))
    items = sorted(params['items'].split(ITEM_SPLITTER[0]))
    options = sorted(params['options'].split(ITEM_SPLITTER[0]))

    with_rows = kw.get('with_rows') and True or False

    rows = []

    if with_rows:
        x = params.get('bound')
        rows.append(('[b]Тираж:', int(x) if DEFAULT_AS_NUMBER else x))
        rows.append(['-'*20, ''],)

    # ----------------------
    # Extract selected items
    # ----------------------

    selected_ids = {}

    for item in items:
        if not item or ITEM_SPLITTER[1] not in item:
            continue

        key, name, value = item.split(ITEM_SPLITTER[1])
        id = name

        if value:
            if not key:
                id = None
            elif key in ITEM_TYPES or key == ITEM_CHECKBOX:
                pass
            elif key in (ITEM_SELECT, ITEM_OPTION):
                id = value
            else:
                id = '%s%s%s' % (name, ITEM_SPLITTER[2], value)
        tab, group, x = _get_item(id)

        if not id in selected_ids:
            selected_ids[id] = []

        selected_ids[id].append((key, name, tab, group, value))

    block_ids, controls = check_conditions(selected_ids)

    # ---------------
    # Calculate price
    # ---------------

    def _get_row(id):
        return ('[b]%s:' % groups[id].title, '')

    def _add_row():
        pass

    checked_groups = ''
    price = 0

    ids = sorted(selected_ids.keys())

    if IsLocalDebug:
        print('--> selected_ids:', ids)

    for id in ids:
        for key, name, tab, group, value in selected_ids[id]:
            if id in block_ids:
                continue

            parent = item = None

            if not key:
                pass
            elif key in (ITEM_SELECT, ITEM_OPTION):
                item = entries['items'][name]
            elif key == ITEM_COLOR:
                parent = entries['items'][name]
                item = parent.controls[ITEM_COLOR].options[int(value)] #- 1
            else:
                item = entries['items'][id]

            if parent and parent.disabled:
                continue

            dependence = None
            prices = None
            """
            x = entries['prices'].get(id)

            if not x:
                pass
            else:
                dependence, prices = x
                if bound >= len(prices) or (dependence and dependence not in selected_ids):
                    continue
            """
            if id in entries['prices']:
                for dependence, prices in entries['prices'][id]:
                    if not dependence or dependence in selected_ids:
                        break
                    prices = None

            #if not prices or bound >= len(prices):
            #    continue

            index = -1
            item_value = 0

            if key in ITEM_TYPES:
                index = ITEM_TYPES.index(key)

            if not prices:
                pass
            elif key in ITEM_TYPES:
                item_value = prices[bound][index] * (value and int(value) or 1)
            else:
                item_value = prices[bound]

            if IsLocalDebug and item_value:
                print('>>> price[%s]:' % id, item_value)

            price += item_value

            if parent:
                parent.current_value = item.oid

            try:
                if with_rows:
                    if key in (ITEM_SELECT, ITEM_OPTION):
                        title = '%s (%s)' % (item.title, item.value[id].title)
                    elif key == ITEM_COLOR:
                        x = int(value)
                        color = x and parent.values[x][1] or 'по умолчанию'
                        title = 'Цвет: %s' % color
                    else:
                        title = item.title
                        if index > -1:
                            title += ' [%s]' % groups[group].options[index]
                        if item.ctype == TYPE_NUMBER:
                            title += ', кол-во: %s' % value
                    if group and group not in checked_groups:
                        checked_groups += ':' + group
                        rows.append(_get_row(group))
                    rows.append((title, _convert(item_value / DEFAULT_FACTOR, as_number=DEFAULT_AS_NUMBER)))
            except:
                pass

    # -------------
    # Check Options
    # -------------

    pcharge = 0
    pdefect = 0

    for option in options:
        if not option or ITEM_SPLITTER[1] not in option:
            continue

        name, value = option.split(ITEM_SPLITTER[1])

        if name == 'option_pcharge':
            pcharge = float(value)
        elif name == 'option_defect':
            pdefect = float(value)

    if with_rows:
        options = {
            'pcharge' : pcharge,
            'pdefect' : pdefect,
        }

    def _get_price_defect(value):
        return value and (100 + value) / 100 or 1

    price = price * _get_price_defect(pdefect) / DEFAULT_FACTOR
    tax = price * _get_measure('tax') / 100
    charge = (price + tax) * (_get_measure('charge') + pcharge) / 100
    euro = price + tax + charge

    data = {
        'price'  : price,
        'tax'    : tax,
        'charge' : charge,
        'euro'   : euro,
        'usd'    : euro * _get_measure('cross'),
        'rub'    : euro * _get_measure('euro'),
    }

    for key in data.keys():
        data[key] = _convert(data[key])

    if with_rows:
        return data, rows, options

    return data, controls, errors

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
        for x in VALID_ITEMS:
            if key.startswith(x):
                return True
        if key.startswith(ITEM_COLOR):
            return True
        for x in ITEM_TYPES:
            if key.startswith(x) and float(value or 0):
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
    pdefect = options.get('pdefect') and (' + %s (брак)' % options['pdefect']) or ''

    headers = ['Параметр', 'Значение']
    rows += [
        ['-'*20, ''],
        ['Tax[%]', _convert(_get_measure('tax'), as_number=DEFAULT_AS_NUMBER)],
        ['Charge[%]', _convert(_get_measure('charge'), as_number=DEFAULT_AS_NUMBER)],
        ['EURO EXCHANGE RATE', _convert(_get_measure('euro'), as_number=DEFAULT_AS_NUMBER)],
        ['EURO-USD CROSS', _convert(_get_measure('cross'), as_number=DEFAULT_AS_NUMBER)],
        ['='*15, ''],
        ['[b]Себестоимость%s' % pdefect, _convert(data['price'], as_number=DEFAULT_AS_NUMBER)],
        ['[b]Сумма НДС', _convert(data['tax'], as_number=DEFAULT_AS_NUMBER)],
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
    query_string = ''
    base = '%s%s' % (default_locator, query_string and '?'+query_string or '')
    
    config = {}
    pagination = {}

    bounds = [(x, "{:>9,}".format(x).replace(',', ' ')) for x in DEFAULT_BOUNDS]

    """
    results = [
        ('price', 'Себестоимость',),
        ('tax', 'НДС [%s%%]' % _get_measure('tax')),
        ('charge', 'Наценка [%s%%]' % _get_measure('charge')),
        ('euro', 'ИТОГ [€, %s%%]' % _get_measure('euro')),
        ('usd', 'ИТОГ [$, %s%%]' % _get_measure('cross')),
        ('rub', 'ИТОГ в Рублях'),
    ]
    """
    results = [
        ('price', 'Себестоимость',),
        ('tax', 'Сумма НДС'),
        ('charge', 'Наценка'),
        ('euro', 'ИТОГ [€]'),
        ('usd', 'ИТОГ [$]'),
        ('rub', 'ИТОГ в Рублях'),
    ]
    
    options = [
        ('Прирост по наценке', TYPE_RADIO, [
            ('option_pcharge0', 'option_pcharge', '0.0', 'стандарт', 1),
            ('option_pcharge1', 'option_pcharge', '0.5', '0.5 %', 0),
            ('option_pcharge2', 'option_pcharge', '1.0', '1.0 %', 0),
            ('option_pcharge3', 'option_pcharge', '2.0', '2.0 %', 0),
        ]),
        ('Процент брака', TYPE_NUMBER, [
            ('option_defect0', 'option_defect', '0', 'стандарт', 0),
        ]),
    ]

    loader = '/%s/loader' % default_locator

    kw.update({
        'base'              : base,
        'back'              : 'auth/default', 
        'module'            : default_locator,
        'width'             : 1280,
        'page_title'        : gettext('WebPerso CardPrice Calculator View'),
        'header_class'      : 'calculator-header',
        'header_subclass'   : '',
        'show_flash'        : True,
        'loader'            : loader,
        'semaphore'         : None, #initDefaultSemaphore(),
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

    kw['measures'] = [(x[0], x[1]) for x in sorted(kw['measures'].values(), key=lambda x: x[2])]

    sidebar = get_request_item('sidebar')
    if sidebar:
        kw['sidebar']['state'] = int(sidebar)

    return kw

## ==================================================== ##

@calculator.route('/%s' % default_page, methods=['GET', 'POST'])
@calculator.route('/%s' % default_locator, methods=['GET', 'POST'])
#@login_required
def start():
    try:
        return index()
    except:
        if IsPrintExceptions:
            print_exception()

def index():
    debug, kw = init_response('WebPerso Calculator Page')
    kw['product_version'] = product_version

    login = 'AnonymousUser'

    is_admin = False

    try:
        is_admin = current_user.is_administrator()
        login = current_user.login
    except:
        pass

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
            print_to(errorlog, '--> command:%s %s [%s]' % (command, login, info))

    kw['errors'] = '<br>'.join(errors)
    kw['OK'] = ''

    try:
        if IsMakePageDefault:
            kw = _make_page_default(kw)

        if IsTrace:
            print_to(errorlog, '--> calculator:%s %s [%s:%s] %s %s' % ( \
                     command, login, request.remote_addr, kw.get('browser_info'), str(kw.get('current_file')), info,), 
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
#@login_required
def loader():
    exchange_error = ''
    exchange_message = ''

    action = get_request_item('action') or default_action
    selected_menu_action = get_request_item('selected_menu_action') or action != default_action and action or default_log_action

    login = 'AnonymousUser'

    try:
        login = current_user.login
    except:
        pass

    response = {}

    params = get_request_item('params') or None

    refresh()

    if IsDebug:
        print('--> action:%s' % action)

    if IsTrace:
        print_to(errorlog, '--> loader:%s %s %s' % (
                 action, 
                 login, 
                 params and ' params:[%s]' % params or '',
            ))

    data = []
    controls = None
    errors = None

    try:
        if action == default_action:
            data, controls, errors = calculate(params)

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
        'controls'         : controls,
        'errors'           : errors,
    })

    return jsonify(response)

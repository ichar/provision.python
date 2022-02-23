
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
                    ob = Tab(id, stype, title)
                    registry_tab(id, ob)

            elif IsItems:
                id, name, ctype, options, title = item
                tab, group, item = _get_item(id)
                name = name or group
                options = options and options.split('-') or None

                if not tab or not group:
                    continue
                elif not item:
                    ob = Group(id, name, ctype, title, options)
                    registry_group(id, ob, tab=tab)
                else:
                    ob = Item(id, name, ctype, group, title)
                    gtype = entries['groups'][group].ctype
                    ob.set_controls(gtype, options)
                    registry_item(id, ob, group=group, name=name, options=options)

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
    entries['groups']['_'].append(ob)
    entries['groups']['tabs'][tab].append(id)
    entries['items']['groups'][id] = []

def registry_item(id, ob, **kw):
    global entries

    group = kw.get('group')
    name = kw.get('name')
    options = kw.get('options')

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
            title = entries['items'][id].title
            if index > -1:
                title = '%s (%s)' % (title, groups[group].options[index])
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

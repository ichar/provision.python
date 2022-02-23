
from copy import deepcopy

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

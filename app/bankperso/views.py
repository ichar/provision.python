# -*- coding: utf-8 -*-

import os
import re
from operator import itemgetter
from shutil import copy2

from config import (
     CONNECTION, BP_ROOT, 
     IsDebug, IsDeepDebug, IsTrace, IsUseDecodeCyrillic, IsUseDBLog, IsPrintExceptions, IsDecoderTrace, LocalDebug,
     basedir, errorlog, print_to, print_exception,
     default_print_encoding, default_unicode, default_encoding, default_iso, image_encoding, cr,
     LOCAL_EXCEL_TIMESTAMP, LOCAL_EASY_DATESTAMP, LOCAL_EXPORT_TIMESTAMP, UTC_FULL_TIMESTAMP, DATE_STAMP, 
     INDIGO_IMAGE_PATH, POSTONLINE_DATA_PATH, email_address_list
     )

from flask_log_request_id import current_request_id

from . import bankperso

from ..settings import *
from ..database import database_config, DatabaseEngine
from ..utils import (
     getToday, getDate, getDateOnly, checkDate, del_file, spent_time, cdate, indentXMLTree, isIterable, 
     makeCSVContent, makeXLSContent, makeIDList, decoder, 
     checkPaginationRange, getMaskedPAN, getEANDBarcode, getParamsByKeys, pickupKeyInLine,
     default_indent, Capitalize, sint, image_base64, normpath, fromtimestamp, daydelta, rfind, make_config
     )
from ..worker import getClientConfig, getPersoLogInfo, getSDCLogInfo, getExchangeLogInfo, getBOM
from ..booleval import new_token
from ..barcodes import genBarcode
from ..decoders import FileImageDecoder
from ..reporter import make_materials_attachment
from ..mails import send_materials_order

from ..orderstate.views import getTabInfoExchangeLog
from ..semaphore.views import initDefaultSemaphore

##  ===================================
##  BankPerso View Presentation Package
##  ===================================

default_page = 'bankperso'
default_action = '300'
default_log_action = '301'
default_template = 'orders'

# Локальный отладчик
IsLocalDebug = LocalDebug[default_page]
# Использовать OFFSET в SQL запросах
IsApplyOffset = 1
# Принудительная загрузка статических файлов
IsForceRefresh = 0

_views = {
    'orders'             : 'orders',
    'batches'            : 'batches',
    'client'             : 'orders',
    'logs'               : 'logs',
    'image'              : 'image',
    'body'               : 'body',
    'filestatuses'       : 'filestatuses',
    'TZ'                 : 'TZ',
    'orderlog-messages'  : 'orderlog-messages',
    'orderstate-aliases' : 'orderstate-aliases',
    'clients'            : 'clients',
    'banks'              : 'banks',
    'types'              : 'types',
    'statuses'           : 'statuses',
    'batchtypelist'      : 'batchtypelist',
    'filestatuslist'     : 'filestatuslist',
    'batchstatuslist'    : 'batchstatuslist',
}

_extra_action = ('313',)


def before(f):
    def wrapper(**kw):
        name = kw.get('engine') or 'bankperso'
        g.engine = DatabaseEngine(name=name, user=g.current_user, connection=CONNECTION[name])
        g.decoder = FileImageDecoder(g.engine)
        return f(**kw)
    return wrapper

@before
def refresh(**kw):
    g.requested_object = {}

    if not g.system_config.MAX_CARDHOLDER_ITEMS:
        g.system_config.MAX_CARDHOLDER_ITEMS = MAX_CARDHOLDER_ITEMS

    file_id = kw.get('file_id')
    if file_id is None:
        return

    g.requested_object = _get_order(file_id).copy()

    g.decoder._init_state(g.requested_object, 
        tags={
            'cardholders' : database_config['cardholders']['tags'][2],
            'PAN'         : PAN_TAGS.split(':'),
            'cyrillic'    : IMAGE_TAGS_DECODE_CYRILLIC,
        }
    )

def printInfo(mode):
    if IsTrace:
        print_to(errorlog, '%s[%s: %s]' % (mode, g.requested_object.get('BankName'), g.requested_object.get('FileID')))

def html_flash(message):
    return message.replace('\n', '<br>').strip()

def _search_double_pan():
    file_id = g.requested_object.get('FileID')

    parser = g.decoder.chooseBodyParser(tag=FILEBODY_RECORD)

    if parser is None:
        return [], []

    cards = {}
    no_value = []
    
    for node in parser:
        pan = parser.find(node, 'PAN') or None
        recno = parser.find(node, 'FileRecNo') or None
        with_pin = parser.find(node, 'doPrintPin')

        if pan is None:
            no_value.append(recno)
            continue
        if not pan in cards:
            cards[pan] = []
        cards[pan].append('%s:%s' % (recno, with_pin or '-'))
        
        parser.clear(node)

    g.decoder.flash()

    return [[x]+cards[x] for x in cards if len(cards[x]) > 1], no_value

def _get_history_logs(file_id):
    """
        Makes History log content
    """
    logs = []

    cursor = g.engine.runQuery('logs', where='TID=%s' % file_id, order='LID', as_dict=True, encode_columns=('Status',))
    if cursor:
        for n, row in enumerate(cursor):
            if 'LID' in row:
                row['id'] = row['LID']
            row['ModDate'] = getDate(row['ModDate'], DEFAULT_DATETIME_INLINE_FORMAT)
            logs.append(row)
    
    return logs

def _get_cardholders(view, limit=0, **kw):
    """
        Makes cardholders data list
    """
    file_id = g.requested_object.get('FileID')
    client = g.requested_object.get('BankName')

    forced = None #client in 'CITI_BANK:' and 3 or None

    parser = g.decoder.chooseBodyParser(tag=view['root'], forced=forced)

    if parser is None:
        return [], []

    clients = view.get('clients') or {}

    columns = _get_view_columns(view)

    items = []
    exists = set()

    if limit == 0:
        limit = g.system_config.MAX_CARDHOLDER_ITEMS

    encoding = kw.get('encoding') or None

    exclude = view['exclude']

    for node in parser:
        if node is None or (limit and len(items) > limit):
            break

        item = {}

        for n, tags in enumerate(view['tags']):
            column = view['columns'][n]

            if clients and column in clients:
                if client not in clients[column]:
                    continue

            exists.add(column)

            for tag in tags:
                if isIterable(tag):
                    for key in tag:
                        if value:
                            value += ' '
                        value += parser.find(node, key, encoding=encoding) or ''
                elif client in exclude and tag in exclude[client]:
                    continue
                else:
                    value = parser.find(node, tag, encoding=encoding) or ''

                if value:
                    item[column] = column in view['func'] and view['func'][column](value) or value
                    break

        parser.clear(node)

        if 'FileRecNo' in item:
            item['id'] = item['FileRecNo']

        items.append(item)

    g.decoder.flash()

    return items, [x for x in columns if x['name'] in exists]

def _get_process_info(**kw):
    """
        Return file process info
    """
    if not g.current_user.is_operator():
        return '', None

    is_run = False
    if g.requested_object.get('FileType') in PROCESS_INFO['filetypes']:
        is_run = True
    elif '_FAST_' in g.requested_object.get('FName'):
        is_run = True

    if not is_run:
        for client in PROCESS_INFO['clients']:
            key = None
            if ':' in client:
                client, key = client.split(':')
            if g.requested_object.get('BankName') == client and (not key or key in g.requested_object.get('FName')):
                is_run = True
                break

    if not is_run:
        return '', None

    tag = kw.get('tag')
    parser = g.decoder.chooseBodyParser(tag=tag)

    if parser is None:
        return '', None

    encoding = kw.get('encoding') or None

    tags = {
        'ProcessedRecordQty' : 'Карт', 
        'PostOnlineBatches'  : 'ПочтаРоссии',
        'ProcessDateTime'    : 'Дата процессинга'
    }

    info = []
    
    postonline_data = None
    postonline_data_path = []

    for node in parser:
        if node is None:
            break

        for tag in sorted(list(tags.keys())):
            value = parser.find(node, tag, encoding=encoding) or None
            if value:
                info.append('%s: %s' % (tags[tag], value))
                if tag == 'PostOnlineBatches':
                    postonline_data = value

        parser.clear(node)

    g.decoder.flash()
    #
    #   Clean destination folder
    #
    today = getDateOnly(getToday())
    destination = normpath(os.path.join(basedir, 'app/static/files'))

    for x in os.listdir(destination):
        filename = os.path.join(destination, x)
        if not os.path.isfile(filename):
            continue
        ctime = fromtimestamp(os.path.getctime(filename))
        ext = x.split('.')[-1]
        if ext == 'pdf' and ctime  < today:
            del_file(filename)
    #
    #   Copy F103/E-1
    #
    if postonline_data:
        sources = ('F103', 'F_EMS',)
        for post in postonline_data.split(';'):
            data = post.split(':')
            if len(data) > 1:
                for s in sources:
                    src = '%s/%s/postonline/%s/%s/%s.pdf' % ( 
                        POSTONLINE_DATA_PATH, 
                        g.requested_object.get('BankName'),
                        getDate(g.requested_object.get('ReadyDate'), DATE_STAMP),
                        data[1],
                        s,
                        )
                    if os.path.exists(src) and os.path.isfile(src):
                        filename = '%s_%s_%s.pdf' % (current_request_id(), data[1], s)
    
                        try:
                            copy2(src, '%s/%s' % (destination, filename))
                            postonline_data_path.append('/static/files/%s' % filename)
                        except:
                            pass

    return info and '[%s]' % ', '.join(info) or '', postonline_data_path

def _get_indigo(view):
    """
        Makes indigo data list
    """
    parser = g.decoder.chooseBodyParser(tag=view['root'])

    if parser is None:
        return [], []

    image_path = INDIGO_IMAGE_PATH.get(g.requested_object['FileType'])
    default_image = INDIGO_DEFAULT_IMAGE
    default_mode = INDIGO_DEFAULT_MODE
    default_size = INDIGO_DEFAULT_SIZE
    default_dump = 'dump'
    default_index = 0
    image_type = INDIGO_IMAGE_TYPE

    columns = _get_view_columns(view)

    items = {}

    unique_key = view['unique']

    n = 0
    for node in parser:
        if n > MAX_INDIGO_ITEMS:
            break

        tags = {}
        for tag in view['tags']:
            value = parser.find(node, tag) or ''
            tags[tag] = tag in view['func'] and view['func'][tag](value) or value

        tags['ImagePosition'] = 'X'
        tags['ImageType'] = image_type
        tags['SRC'] = image_path

        values = {}
        for column in view['columns']:
            values[column] = (view['values'].get(column)) % tags

        u = values.get(unique_key)
        if not u in items:
            items[u] = []

        v = values.get('Value') or ''
        if v not in items[u]:
            items[u].append(v)

        n += 1

        parser.clear(node)

    def get_image_path(src, name=None):
        if src.startswith('/static/'):
            src = normpath(os.path.join(basedir, 'app', src.startswith('/') and src[1:] or src))
        return name and ('%s/%s' % (src, name)) or src

    def collect_images(folder, ext):
        images = {}

        src = get_image_path(image_path, name=folder)

        if not (os.path.exists(src) and os.path.isdir(src)):
            return images

        for ob in sorted(os.listdir(src)):
            for key in items:
                if not (ob.startswith(key) and os.path.isfile(os.path.join(src, ob)) and ob.endswith(ext)):
                    continue
                name = ob.split('_' in ob and '_' or '.')[0]
                if key not in images:
                    images[key] = []
                images[key].append(ob)

        return images

    _source_files = collect_images(None, image_type)
    _images = collect_images(default_dump, 'base64')

    def get_image(name, mode, with_base64=False):
        image = None
        is_base64 = 0

        if mode == 'file' and name.endswith(image_type):
            image = name and '%s/%s' % (image_path, name)
        elif mode == 'base64' or (mode == 'file' and name.endswith('base64')):
            src = '%s/%s' % (get_image_path(image_path, name=default_dump), name)
            if os.path.exists(src):
                with open(src, 'r') as fi:
                    image = fi.read()
                is_base64 = 1

            if not image:
                src = '%s/%s' % (get_image_path(image_path), name)
                if os.path.exists(src):
                    image = image_base64(src, image_type, size=default_size)
                    is_base64 = 2
        else:
            image = name and '%s/%s' % (image_path, name)

        if not image:
            image = mode == 'default' and default_image or None

        if with_base64:
            return image, is_base64

        return image

    def html(key, mode='default'):
        item = {}

        source_files = _source_files.get(key) or []
        images = _images.get(key) or source_files

        name = images and images[default_index]
        image, is_base64 = get_image(name, mode, with_base64=True)

        def _link(filename):
            return get_image(filename, 'file'), '%s:%s' % (is_base64 == 1 and filename == '%s.%s' % (key, image_type) and '*.base64' or filename, is_base64)

        for column in view['columns']:
            value = ''
            if column == 'Design':
                if image is not None:
                    value = '<img class="indigo_design" src="%s" title="Indigo Design" alt>' % image
                else:
                    value = '<div class="indigo_no_image"><span>IMAGE NOT FOUND</span></div>'
            elif column == 'ImageName':
                value = '<span class="indigo_image_name">%s</span>' % key
            elif column == 'Value':
                value = '<ul class="indigo_value">%s</ul>' % ('\n'.join([
                    '<li class="indigo_value_item">%s</li>' % v
                        for v in items[key]]))
            elif column == 'Count':
                value = '<span class="indigo_count">%s</span>' % len(items[key])
            elif column == 'Files':
                if image is not None:
                    value = '<ul class="indigo_value">%s</ul>' % ('\n'.join([
                            '<a class="indigo_link" onclick="javascript:indigo(\'%s\');"><li class="indigo_file_item">%s</li></a>' % (
                                _link(filename)
                            ) for n, filename in enumerate(source_files or images)
                        ]))
                else:
                    value = ''

            item[column] = value

        return item

    g.decoder.flash()

    return [html(key, default_mode) for key in sorted(items)], [column for column in columns]

def _get_ibody(limit, **kw):
    """
        Makes body file content
    """
    file_id = g.requested_object.get('FileID')

    xml = ''

    is_extra = kw.get('is_extra') and True or False
    params = kw.get('params')

    statuses = _get_filestatuses(file_id)

    status = '[лимит %sMb], статусы: %s [%s]' % (round(limit / (1024*1024), 2), ','.join([str(x) for x in statuses]), g.decoder.file_status)

    if not (SETTINGS_PARSE_XML and g.current_user.is_administrator()):
        return xml, 0, status

    parser = g.decoder.chooseBodyParser(tag=[FILEINFO, FILEBODY_RECORD, PROCESSINFO])

    if parser is None:
        return xml, 0, status

    recno = None

    if params:
        x = params.split(':')
        recno = x and len(x) > 2 and x[1] or None

    is_header_done = is_footer_done = is_break = is_done = False

    for node in parser:
        if not is_footer_done:
            value = parser.find(node, 'ProcessedRecordQty')
            if value:
                is_footer_done = True
            elif is_done:
                continue

        if not is_break:
            if recno:
                if not is_header_done:
                    value = parser.find(node, 'InputFileName')
                    if value:
                        is_header_done = True
                else:
                    value = parser.find(node, 'FileRecNo')
                    if value != recno:
                        continue
                    else:
                        xml += default_indent + '...' + cr + default_indent
                        is_done = True

        g.decoder.makeNodeContent(node, level=2, is_extra=is_extra)

        xml += parser.upload(node)

        if not is_break:
            if limit and len(xml) > limit:
                n = rfind(xml, '>', limit)
                xml = xml[:limit+n+1] + cr + '...' + cr
                break

            if recno and is_done:
                xml += '...' + cr + default_indent
                is_break = True

        parser.clear(node)

    g.decoder.flash()

    header = '%s<%s>%s%s' % (g.decoder.header(parser=parser.info()), FILEDATA, cr, default_indent)
    footer = '%s</%s>' % (cr, FILEDATA)

    return '%s%s%s' % (header, xml.strip(), footer), len(xml), status

def _get_process_err_msg():
    """
        Makes file error messages
    """
    xml = ''
    total = 0

    tags = ('PROCESS_ERR_MSG', 'error',)

    if not SETTINGS_PARSE_XML: # and g.current_user.is_administrator():
        return xml, total

    for tag in tags:
        parser = g.decoder.chooseBodyParser(tag=tag)

        if parser is None:
            return [], []

        items = [x for x in parser]
        total += len(items)

        for item in items:
            g.decoder.decodeCyrillic(item, key='errors')
            g.decoder.maskContent(item, mask='/')
            indentXMLTree(item, limit=MAX_XML_TREE_NODES)
            xml += '...' + cr + parser.upload(item)

    g.decoder.flash()

    return xml, total

def _get_db_log(source_type, view, **kw):
    """
        Makes DB log content
    """
    client = kw.get('client') or None
    file_id = kw.get('file_id') or None

    data = []

    columns = view['columns']
    keys, dates, client, filename = _get_file_keywords(file_id)
    date_format = DEFAULT_DATETIME_FORMAT

    if file_id is not None:
        where = "FileID = %s and SourceType = '%s'" % (file_id, source_type)

        refresh(engine='orderlog')

        # ---------------------------------------------
        # Get OrderLog for given source type and FileID
        # ---------------------------------------------

        cursor = g.engine.runQuery('orderlog-messages', where=where, order='EventDate', as_dict=True)
        if cursor:
            for n, row in enumerate(cursor):
                """
                ob = dict(zip(columns, [row[x] for x in columns if x in row]))
                ob['Error'] = row['IsError']
                """
                ob = { \
                    'filename' : '[%s] %s' % (row['IP'], row['LogFile']),
                    'Date'     : cdate(row['EventDate'], date_format),
                    'Code'     : row['Code'],
                    'Module'   : '%s%s' % (row['Module'], row['Count'] > 1 and '[%d]' % row['Count'] or ''),
                }

                message = row['Message']

                if not kw.get('no_span'):
                    s = ''
                    for key in keys:
                        if key in s:
                            continue
                        s += ':%s' % key
                        message = pickupKeyInLine(message, key)

                ob['Message'] = message

                data.append(ob)

    return data
    
def _get_top(per_page, page):
    if g.system_config.IsApplyOffset:
        top = per_page
    else:
        top = per_page * page
    offset = page > 1 and (page - 1) * per_page or 0
    return top, offset

##

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

    if has_request_item(EXTRA_):
        args[EXTRA_] = (EXTRA_, None)

    try:
        args.update({
            'bank'        : ['ClientID', int(get_request_item('bank') or '0')],
            'type'        : ['FileTypeID', int(get_request_item('type') or '0')],
            'status'      : ['FileStatusID', int(get_request_item('status') or '0')],
            'batchtype'   : ['BatchTypeID', int(get_request_item('batchtype') or '0')],
            'batchstatus' : ['BatchStatusID', int(get_request_item('batchstatus') or '0')],
            'date_from'   : ['RegisterDate', get_request_item('date_from') or ''],
            'date_to'     : ['RegisterDate', get_request_item('date_to') or ''],
            'ready_from'  : ['ReadyDate', get_request_item('ready_from') or ''],
            'ready_to'    : ['ReadyDate', get_request_item('ready_to') or ''],
            'yesterday'   : ['RegisterDate', get_request_item('yesterday') or 0],
            'tomorrow'    : ['RegisterDate', get_request_item('tomorrow') or 0],
            'today'       : ['RegisterDate', get_request_item('today') or 0],
            'id'          : ['FileID', int(get_request_item('_id') or '0')],
        })
    except:
        args.update({
            'bank'        : ['ClientID', 0],
            'type'        : ['FileTypeID', 0],
            'status'      : ['FileStatusID', 0],
            'batchtype'   : ['BatchTypeID', 0],
            'batchstatus' : ['BatchStatusID', 0],
            'date_from'   : ['RegisterDate', ''],
            'date_to'     : ['RegisterDate', ''],
            'ready_from'  : ['ReadyDate', ''],
            'ready_to'    : ['ReadyDate', ''],
            'yesterday'   : ['RegisterDate', 0],
            'tomorrow'    : ['RegisterDate', 0],
            'today'       : ['RegisterDate', 0],
            'id'          : ['FileID', 0],
        })
        flash('Please, update the page by Ctrl-F5!')

    return args

def _get_client(file_id):
    return file_id and g.engine.getReferenceID(default_template, key='FileID', value=file_id, tid='BankName') or None

def _get_order(file_id):
    columns = database_config[default_template]['export']
    where = 'FileID=%s' % file_id
    encode_columns = ('BankName', 'FileStatus',)
    cursor = g.engine.runQuery(default_template, columns=columns, top=1, where=where, as_dict=True, encode_columns=encode_columns)
    return cursor and cursor[0] or {}

def _get_batches(file_id, **kw):
    batches = []
    batch_id = kw.get('batch_id') or None
    pers_tz = kw.get('pers_tz') or None
    batchtype = kw.get('batchtype') or None
    batchstatus = kw.get('batchstatus') or None
    is_default_date = kw.get('is_default_date') or None
    selected_id = None

    if not (file_id and str(file_id).isdigit()):
        return batches, selected_id

    where = 'FileID=%s%s%s' % (
        file_id, 
        batchtype and (' and BatchTypeID=%s' % batchtype) or '',
        batchstatus and (' and BatchStatusID=%s' % batchstatus) or ''
        )

    cursor = g.engine.runQuery(_views['batches'], where=where, order='TID', as_dict=True, encode_columns=('BatchType', 'Status',))
    if cursor:
        is_selected = False
        
        for n, row in enumerate(cursor):
            row['StatusDate'] = getDate(row['StatusDate']) if is_default_date else getDate(row['StatusDate'], DEFAULT_DATETIME_INLINE_FORMAT)
            row['Ready'] = 'обработка завершена' in row['Status'] and True or False
            row['Found'] = pers_tz and row['TZ'] == pers_tz
            row['id'] = row['TID']

            if (batch_id and batch_id == row['TID']) or (pers_tz and pers_tz == row['TZ'] and not is_selected):
                row['selected'] = 'selected'
                selected_id = batch_id
                is_selected = True
            else:
                row['selected'] = ''

            batches.append(row)

        if not is_selected:
            row = batches[0]
            selected_id = row['id']
            row['selected'] = 'selected'

    return batches, selected_id

def _get_filestatuses(file_id, order='TID'):
    statuses = []

    cursor = g.engine.runQuery('filestatuses', where='FileID=%s' % file_id, order=order, as_dict=True)
    if cursor:
        for n, row in enumerate(cursor):
            statuses.append(row['FileStatusID'])

    return statuses

def _get_file_keywords(file_id, no_batch=False):
    keys = []
    dates = ()
    client = ''
    file_name = ''

    if file_id:
        keys.append(str(file_id))

        file_name = ''

        top = 1
        where = 'FileID = %s' % file_id

        # ---------------------------
        # Get Common File/Client info
        # ---------------------------

        cursor = g.engine.runQuery(default_template, top=top, where=where, as_dict=True)
        if cursor is not None and len(cursor):
            row = cursor[0]
            file_name = row['FName']
            client = row['BankName']

            if row['RegisterDate']:
                date_from = getDateOnly(row['RegisterDate'])
            if row['StatusDate']:
                date_to = row['StatusDate']

            dates = (date_from, date_to,)

        if file_name:
            keys.append(file_name)
            if '.' in file_name:
                keys.append(file_name.split('.')[0])

        # -------------------
        # Get Batches/TZ info
        # -------------------

        if not no_batch:
            cursor = g.engine.runQuery(_views['batches'], where='FileID=%s' % file_id, order='TID', as_dict=True)
            if cursor:
                for n, row in enumerate(cursor):
                    keys.append(str(row['TID']))
                    keys.append(str(row['TZ']))

    keys = sorted(set(keys))

    return keys, dates, client, file_name

def _get_materials(file_id, show=1, order=None):
    data = []
    props = []
    errors = []

    _UNDEFINED_ERROR = 2
    _ERROR = 1
    _WARNING = 0

    qty = 0
    batch_qty = 0

    exec_params = {'file_id' : file_id, 'show' : show}
    encode_columns = ('BatchType', 'MName',)

    cursor = None

    try:
        cursor = g.engine.runQuery('materials.order', exec_params=exec_params, order=order, as_dict=True, encode_columns=encode_columns)
    except:
        pass

    if cursor:
        for n, row in enumerate(cursor):
            batch_qty += int(row['BatchQty'])
            qty += int(row['Qty'])
            data.append(row)

    """
    rows, error_msg = g.engine.runProcedure('materials.check', 
                                          file_id=file_id, file_status_ids=makeIDList(COMPLETE_STATUSES), check=1, 
                                          no_cursor=False, with_error=True
                                          )
    
    if error_msg:
        errors.append((_ERROR, error_msg))
    """
    
    exec_params = {'file_id' : file_id, 'file_status_ids' : makeIDList(COMPLETE_STATUSES), 'check' : 1}
    rows = g.engine.runQuery('materials.check', exec_params=exec_params)

    check = (rows is not None and len(rows) == 0) and True or False

    props = {
        'headers'    : ('Тип партии', 'Кол-во в партиях', 'Материал', 'Количество',),
        'total'      : (len(data), batch_qty, qty,),
        'ClientName' : g.requested_object.get('BankName'),
        'FileName'   : g.requested_object.get('FName'),
        'Now'        : getDate(getToday(), LOCAL_EXCEL_TIMESTAMP),
        'Today'      : getDate(getToday(), DEFAULT_DATETIME_TODAY_FORMAT),
        'send'       : qty > 0 and check,
        'show'       : 0,
    }

    if not data:
        errors.append((_ERROR, gettext('Error: Materials for the given file is not defined.'),))

    errors = [x[1] for x in sorted(errors, key=itemgetter(0), reverse=True)]

    return data, props, errors

def _check_order_state(state, row):
    x = row['FileStatus'].lower()

    is_checked = False

    state_stop = 'приостановлена' in x
    state_error = 'ошибка' in x or 'отбраков' in x or 'неверный формат' in x
    state_ready = 'заказ обработан' in x or 'готов к отгрузке' in x
    state_wait = 'ожидание' in x
    state_archive = 'архивация' in x

    if state == 'R1' and (state_ready or state_archive or state_wait):
        is_checked = True
    elif state == 'R2' and not state_ready:
        is_checked = True
    elif state == 'R3' and not (state_error or state_stop):
        is_checked = True
    elif state == 'R6' and not state_wait:
        is_checked = True
    elif state == 'R7' and not state_archive:
        is_checked = True

    return is_checked, state_stop, state_error, state_ready, state_wait, state_archive

def _check_extra_tabs(row):
    tabs = {}
    if row and row.get('FileType') in INDIGO_FILETYPES:
        tabs['indigo'] = '313'
    return tabs

def _check_subprocess(res):
    stdout, stderr = [], []
    encodings = [default_encoding, default_unicode, default_print_encoding,]

    if res and len(res) > 1:
        r0, encoding = decoder(res[0], encodings)
        r1, encoding = decoder(res[1], encodings)
        
        if IsDeepDebug:
            print('errors:', r1)
            print('result:', r0)

        stdout = [x for x in r0.split('\n') if x]
        stderr = [x for x in r1.split('\n') if x]

        errors = [x.split(',')[0] for x in stderr]

    code = 0

    if errors:
        code = len(errors)

    if IsTrace:
        for x in stdout:
            print_to(errorlog, '... stdout: %s' % x)
        for x in stderr:
            print_to(errorlog, '... stderr: %s' % x)

    return code, '\n'.join(stdout), errors

def _run_subprocess(args, cwd):
    import subprocess
    from subprocess import Popen, PIPE

    code, errors = 0, []

    if IsTrace:
        print_to(errorlog, '--> subprocess: %s' % args)

    res = None

    try:
        proc = Popen(args, cwd=cwd, shell=False, stdout=PIPE, stderr=PIPE)
        proc.wait(180)

        res = proc.communicate()

    except Exception as ex:
        if IsPrintExceptions:
            print_exception()

        errors.append(str(ex))

        code = -1

    if IsDeepDebug:
        print('code:', code)

    return _check_subprocess(res)

def _valid_extra_action(action, row=None):
    tabs = _check_extra_tabs(row or g.requested_object)
    return (action not in _extra_action or action in list(tabs.values())) and action

## ==================================================== ##

def getTabParams(file_id, batch_id, param_name=None, format=None, **kw):
    """
        Get Batch Parameters list.

        Arguments:
            file_id     -- Int, ID файла-заказа
            batch_id    -- Int, ID партии
            param_name  -- String, идентификатор параметра
            format      -- Int, формат выходных данных хранимой процедуры ({1|2|3}, default: 1)

        Keyword parameters (kw):
            `is_short`              -- Bool, 1/0, short output format, equivalent of the next items:
            `without_RegisterDate`  -- Bool, 1/0, RegisterDate should be output or not
            `without_TZ_ERP`        -- Bool, 1/0, TZ ERP should be output or not
            `without_TZ`            -- Bool, 1/0, parameters TZ should be output or not
            `without_barcode`       -- Bool, 1/0, barcode should be output or not

        Returns:
            data     -- List, Список параметров партии:
                        [{
                           'PName'      -- название параметра
                           'PValue'     -- значение параметра
                           'PSortIndex' -- порядок в ТЗ
                           'PType'      -- тип параметра: 0 - параметр партии, 1 - параметр ТЗ
                           'class_name' -- html-класс
                        }, ... ]

            props    -- Dictionary, Информация о партии: 
                        {
                           'id'         -- ID партии
                           'number'     -- номер ТЗ
                           'name'       -- название типа партии
                           'no'         -- кол-во карт в партии
                           'file'       -- имя файла-заказа
                           'cards'      -- кол-во карт в файле
                           'status'     -- ID статуса
                           'activate'   -- активация партии разрешена 1|0
                        }
    """
    data = []
    parameters = {}
    number = 0

    filter_field = re.compile(r'\$\{FILTERFIELD\.(.*)\}')
    props = {'id' : batch_id}

    is_short = kw.get('is_short') and True or False
    no_materials = kw.get('no_materials') and True or False

    default_format = 1

    rows = g.engine.runQuery('batches.preview', where='TID=%s' % file_id, distinct=True)

    if rows or batch_id:
        props['exists_inactive'] = False
        props['exists_materials'] = False

    try:
        if file_id and batch_id:
            params = "%s, %s, '%s', %s, ''" % (file_id, batch_id, param_name or '', format or default_format)
            cursor = g.engine.runQuery('TZ', as_dict=True, params=params, encode_columns=('PName', 'PValue',))
            if cursor:
                for n, row in enumerate(cursor):
                    try:
                        row['class_name'] = row['PSortIndex'] == 999 and 'sort_index' or ''
                        if row['PType'] == 0 and row['PValue'][:1] != '$':
                            parameters[row['PName']] = row['PValue']

                        data.append(row)

                    except:
                        if IsPrintExceptions:
                            print_exception()

            # -----------------------------
            # Обязательные параметры партии
            # -----------------------------

            if not (is_short or kw.get('without_RegisterDate', False)):
                if 'RegisterDate' not in parameters:
                    where = 'FileID=%s' % file_id
                    cursor = g.engine.runQuery(default_template, columns=('RegisterDate',), where=where)

                    if cursor is not None and len(cursor):
                        parameters['RegisterDate'] = cursor[0][0]
                        data.append({
                            'PName'      : 'Время регистрации файла',
                            'PValue'     : '${FILTERFIELD.RegisterDate}',
                            'PSortIndex' : 990,
                            'PType'      : 0,
                            'ElementQty' : 0,
                        })

            if not (is_short or kw.get('without_TZ_ERP', False)):
                if 'TZ_ERP' not in parameters:
                    params = "%s, %s, 'ERPTZ', 0, ''" % (file_id, batch_id)
                    cursor = g.engine.runQuery('TZ', as_dict=True, params=params)

                    if cursor is not None and len(cursor):
                        row = cursor[0]
                        parameters['TZ_ERP'] = row['PValue']

            # ------------
            # Параметры ТЗ
            # ------------

            TZ = []

            if not (is_short or kw.get('without_TZ', False)):
                for row in data:
                    if row['PSortIndex'] is None:
                        row['PSortIndex'] = 0

                    if 'FILTERFIELD' in row['PValue']:
                        m = filter_field.search(row['PValue'])
                        if not m:
                            continue
                        name = m.group(1)
                        value = name in parameters and parameters[name] or None
                        if value:
                            TZ.append({
                                'PName'      : row['PName'],
                                'PValue'     : value,
                                'PSortIndex' : name == 'RegisterDate' and 999 or row['PSortIndex'],
                                'PType'      : 1,
                                'ElementQty' : row['ElementQty'],
                                'class_name' : 'filter_field',
                            })

                    elif row['PValue'] == '${ERPTZ}':
                        if 'TZ_ERP' in parameters:
                            TZ.append({
                                'PName'      : row['PName'],
                                'PValue'     : parameters['TZ_ERP'],
                                'PSortIndex' : row['PSortIndex'],
                                'PType'      : 1,
                                'ElementQty' : row['ElementQty'],
                                'class_name' : 'filter_field',
                            })

                    elif row['PName'] == 'Клиент':
                        row['PSortIndex'] = 0

            if TZ:
                data = TZ + data

            if len(data) and not is_short:
                data = sorted(data, key=lambda k: k['PSortIndex'])

            # -------------------
            # Информация о партии
            # -------------------

            view = _views['batches']
            columns = database_config[view]['export']
            encode_columns = ('BatchType','Status')
            where = 'TID=%s' % batch_id
            
            cursor = g.engine.runQuery(view, columns=columns, top=1, where=where, as_dict=True, encode_columns=encode_columns)
            if cursor is not None and len(cursor):
                row = cursor[0]
                if row:
                    number = row['TZ']
                    props.update({
                        'number' : number,
                        'name'   : row['BatchType'],
                        'no'     : row['ElementQty'],
                        'status' : row['BatchStatusID'],
                    })

            where = 'FileID=%s' % file_id
            cursor = g.engine.runQuery(default_template, top=1, where=where, as_dict=True)

            if cursor is not None and len(cursor):
                row = cursor[0]
                if row:
                    props.update({
                        'file'   : row['FName'],
                        'cards'  : row['FQty'],
                    })

            # -------------
            # Баркод ЕРП ТЗ
            # -------------

            if not (is_short or kw.get('without_barcode', False)):
                props['barcode'] = ''

                if parameters.get('TZ_ERP') and parameters['TZ_ERP'].isdigit():
                    barcode = genBarcode(
                        '{0:<#10}{1:>010}{2:>06}'.format(sint(parameters['TZ_ERP']), sint(props['number']), sint(props['no'])),
                        text='ERP_Barcode',
                    )
                    if barcode.get('output'):
                        props['barcode'] = barcode['output']
                else:
                    barcode = {}

                if IsDeepDebug:
                    print('--> barcode: %s ERP_TZ: [%s] code: [%s]' % ( 
                        len(props['barcode']), parameters.get('TZ_ERP') or '', barcode.get('code')))

            # ------------------------------------
            # Признак <активация партии разрешена>
            # ------------------------------------

            props['activate'] = props['status'] == 1 and g.current_user.is_operator() and 1 or 0

            # -----------------
            # Файл на обработку
            # -----------------

            rows = g.engine.runQuery('batches.preview', where='TID=%s and BatchStatusID=1' % file_id, distinct=True)
            props['exists_inactive'] = rows and True or False

        if not no_materials:
            rows = g.engine.runQuery('batches.preview', where='TID=%s and IsPrintMaterialOrder=0' % file_id, distinct=True)
            for row in rows:
                id = row[0]
                d, p, e = _get_materials(id, show=1)
                if p['send'] and not e:
                    props['exists_materials'] = True

    except:
        print_exception()

    return number and data or [], props

def getTabLogs(file_id):
    """
        Returns History Tab content
    """
    return _get_history_logs(file_id)

def getTabProcessInfo(tag):
    """
        Returns Process Info for History Tab content
    """
    try:
        return _get_process_info(tag=tag)
    finally:
        printInfo('process_info')

def getTabCardholders():
    """
        Returns Cardholders Tab content
    """
    try:
        return _get_cardholders(database_config['cardholders'])
    finally:
        printInfo('cardholders')

def getTabIndigo():
    """
        Returns Indigo Tab content
    """
    try:
        return _get_indigo(database_config['indigo'])
    finally:
        printInfo('indigo')

def getTabIBody(limit=MAX_XML_BODY_LEN, **kw):
    """
        Returns IBODY Tab content
    """
    try:
        return _get_ibody(limit, **kw)
    finally:
        printInfo('ibody')

def getTabProcessErrMsg():
    """
        Returns PROCESS-ERR-MSG Tab content
    """
    try:
        return _get_process_err_msg()
    finally:
        printInfo('process_err_msg')

def getTabDBLog(source_type, view, **kw):
    """
        Returns Log Tab content used DBLog
    """
    try:
        return _get_db_log(source_type, view, **kw)
    finally:
        printInfo('%s_log' % source_type.lower())

def getTabPersoLog(columns, **kw):
    """
        Returns BankPerso Log
    """
    file_name = ''
    client = kw.get('client') or None

    keys = []

    date_from = getDateOnly(getToday())
    date_to = getToday()

    file_id = kw.get('file_id') or None

    if file_id is not None:
        keys, dates, client, filename = _get_file_keywords(file_id)
    else:
        keys, dates = kw.get('keys') or [], kw.get('dates') or (date_from, date_to,)

    return getPersoLogInfo(keys=keys, split_by = '\t', columns=columns, dates=dates, client=client,
                           fmt=DEFAULT_DATETIME_PERSOLOG_FORMAT, 
                           date_format=kw.get('date_format'),
                           case_insensitive=kw.get('case_insensitive'),
                           no_span=kw.get('no_span'),
                           )

def getTabSDCLog(columns, **kw):
    """
        Returns SDC Log
    """
    file_name = ''
    client = kw.get('client') or None

    keys = []
    aliases = []

    date_from = getDateOnly(getToday())
    date_to = getToday()

    file_id = kw.get('file_id') or None

    if file_id is not None:
        keys, dates, client, filename = _get_file_keywords(file_id)
    else:
        keys, dates = kw.get('keys') or [], kw.get('dates') or (date_from, date_to,)

    if client:
        aliases.append(client)

        # -----------------------
        # Get Client Aliases list
        # -----------------------

        where = "Aliases like '%" + client +"%' or Name='" + client + "'"
    
        cursor = g.engine.runQuery('orderstate-aliases', where=where, as_dict=True)
        if cursor:
            for n, row in enumerate(cursor):
                if row['Aliases'] is not None and len(row['Aliases']):
                    aliases.extend(row['Aliases'].split(':'))

    if len(aliases):
        aliases = list(set(aliases))

    return getSDCLogInfo(keys=keys, split_by = '\t', columns=columns, dates=dates, client=client, aliases=aliases,
                         fmt=DEFAULT_DATETIME_SDCLOG_FORMAT, 
                         date_format=kw.get('date_format'),
                         case_insensitive=kw.get('case_insensitive'),
                         no_span=kw.get('no_span'),
                         )

def getTabExchangeLog(columns, **kw):
    """
        Returns Exchange Log
    """
    file_name = ''
    client = kw.get('client') or None
    split_by = '\t'

    keys = []
    aliases = []

    date_from = getDateOnly(getToday())
    date_to = getToday()

    file_id = kw.get('file_id') or None

    if file_id is not None:
        keys, dates, client, filename = _get_file_keywords(file_id, no_batch=True)
    else:
        keys, dates = kw.get('keys') or [], kw.get('dates') or (date_from, date_to,)

    if client:
        aliases.append(client)

        # -----------------------
        # Get Client Aliases list
        # -----------------------

        where = "Aliases like '%" + client +"%' or Name='" + client + "'"

        cursor = g.engine.runQuery('orderstate-aliases', where=where, as_dict=True)
        if cursor:
            for n, row in enumerate(cursor):
                if row['Aliases'] is not None and len(row['Aliases']):
                    aliases.extend(row['Aliases'].split(':'))

    if file_name:
        if file_name.startswith('OCG') or file_name.startswith('PPCARD'):
            aliases += 'JZDO'
            split_by = ' '

    if len(aliases):
        aliases = list(set(aliases))

    return getExchangeLogInfo(keys=keys, split_by=split_by, columns=columns, dates=dates, client=client, aliases=aliases,
                              fmt=DEFAULT_DATETIME_EXCHANGELOG_FORMAT, 
                              date_format=kw.get('date_format'),
                              case_insensitive=kw.get('case_insensitive'),
                              no_span=kw.get('no_span'),
                              )

def getCurrentState(limit=None, **kw):
    """
        Returns current status Order body content
    """
    is_extra = kw.get('is_extra') and True or False

    if not (SETTINGS_PARSE_XML and g.current_user.is_administrator()):
        return

    parser = g.decoder.chooseBodyParser(tag=[FILEINFO, FILEBODY_RECORD, PROCESSINFO])

    if parser is None:
        return

    yield '%s<%s>%s%s' % (g.decoder.header(parser=parser.info()), FILEDATA, cr, default_indent)

    for node in parser:
        g.decoder.makeNodeContent(node, level=2, is_extra=is_extra)

        yield parser.upload(node)

        parser.clear(node)

    g.decoder.flash()

    yield '%s</%s>' % (cr, FILEDATA)

def getFullState(with_image=False, no_body=False, limit=None, **kw):
    """
        Returns full Order body content
    """
    file_id = kw.get('file_id') #g.requested_object.get('FileID')
    statuses = _get_filestatuses(file_id)

    is_extra = kw.get('is_extra') and True or False
    no_cyrillic = kw.get('no_cyrillic') and True or False

    spacer = '# %s' % ('-' * 30)
    xml = getBOM(default_unicode)

    if with_image:
        g.decoder.decodeImage()

        if IsUseDecodeCyrillic and not no_cyrillic:
            g.decoder.decodeCyrillic(g.decoder.image, key='image')

        s = '--> BODY_IMAGE[%s]' % g.decoder.encoding
        spacer = '# %s' % ('-' * len(s))

        yield '%s%s# %s%s%s%s%s%s%s' % (spacer, cr, s, cr, spacer, cr, cr, str(g.decoder.image or ''), cr)

        g.decoder.flash()

    if not no_body:
        for file_status in statuses:
            parser = g.decoder.chooseBodyParser(file_status=file_status, tag=[FILEINFO, FILEBODY_RECORD, PROCESSINFO])

            yield '%s%s# --> FileStatusID=%s%s%s%s%s%s<%s>%s%s' % (
                spacer, cr, file_status, cr, spacer, cr, cr,
                g.decoder.header(parser=parser.info()), FILEDATA, cr, default_indent
                )

            for node in parser:
                g.decoder.makeNodeContent(node, level=2, is_extra=is_extra)

                yield parser.upload(node)

                parser.clear(node)

            g.decoder.flash()

            yield '%s</%s>%s%s' % (cr, FILEDATA, cr, cr)

def getLogSearchDump(logsearch):
    """
        Log context search
    """
    context, apply_filter, log_exchange, log_perso, log_sdc, log_infoexchange = ('',0,0,0,0,0)
    args = _get_page_args()

    def _column_format(name, logs, default_size=0):
        return '{:<%s}' % (max([0]+[len(ob[name]) for ob in logs if name in ob and ob[name]])+1 or default_size)

    def _formatted_dump(logs, columns):
        filename = ''
        dump = ''

        module_format = _column_format('Module', logs, 34)
        code_format = _column_format('Code', logs, 8)

        rows = 0
        num_columns = len(columns)-1

        for ob in logs:
            if 'exception' in ob:
                flash(ob['exception'])
                continue

            if ob['filename'] != filename:
                filename = ob['filename']
                spacer = '# %s' % ('-' * len(filename))
                dump += '%s%s# %s%s%s%s' % (spacer, cr, filename, cr, spacer, cr,)

            line = ''
            for n, x in enumerate(columns):
                column = x['name']
                if not (column and column in ob):
                    continue
                elif column == 'Date':
                    line += '{:<20}'.format(ob[column])
                elif column == 'Module':
                    line += module_format.format(ob[column])
                elif column == 'Code':
                    line += code_format.format(ob[column])
                else:
                    line += '{}'.format(ob[column].strip())
                if n < num_columns:
                    line += '\t'

            dump += line + cr
            rows += 1

        dump += '%s%s: %d%s' % (cr, gettext('Total lines'), rows, cr)

        return dump

    try:
        if len(logsearch):
            x = logsearch.split('::')
            context = x[0].strip()
            apply_filter = x[1] == '1' and 1 or 0
            log_exchange = x[2] == '1' and 1 or 0
            log_perso = x[3] == '1' and 1 or 0
            log_sdc = x[4] == '1' and 1 or 0

            if len(x) > 5:
                log_infoexchange = x[5] == '1' and 1 or 0
    except:
        pass

    info = 'logsearch:%s apply_filter:%s logs:%s%s%s%s' % (context, apply_filter, log_exchange, log_perso, log_sdc, log_infoexchange)

    if IsDeepDebug:
        print('--> %s' % info)

    dump = getBOM(default_unicode)

    if not context or len(context) < 5:
        return dump + gettext('Illegal search context') + '!'

    # --------------------------
    # Check LogSearch parameters
    # --------------------------

    token = new_token()
    token._init_state(context.lower())

    client_id = args.get('bank')[1]
    client = client_id and g.engine.getReferenceID('clients', key='TID', value=client_id, tid='CName') or ''

    date_format = LOCAL_EASY_DATESTAMP

    x = args.get('date_from')[1]
    date_from = checkDate(x, date_format) and getDate(x, date_format, is_date=True) or None

    x = args.get('date_to')[1]
    date_to = checkDate(x, date_format) and getDate(x, date_format, is_date=True) or None

    dates = (date_from or date_to) and [date_from, date_to,]

    # ---------
    # Dump Logs
    # ---------

    items = (
        (log_exchange, 'exchangelog', getTabExchangeLog, 'Exchange Logs',),
        (log_perso, 'persolog', getTabPersoLog, 'BankPerso Logs',),
        (log_sdc, 'sdclog', getTabSDCLog, 'SDC Logs',),
        (log_infoexchange, 'infoexchangelog', getTabInfoExchangeLog, 'InfoExchange Logs (OutReceiver)',),
    )

    for logtype, name, handler, title in items:
        if not logtype:
            continue

        view = database_config[name]
        columns = _get_view_columns(view)

        logs = handler(view['export'], keys=token, client=client, dates=dates, 
                       date_format=UTC_FULL_TIMESTAMP,
                       case_insensitive=True,
                       no_span=True,
                       engine=g.engine,
                       )

        if logs:
            s = '%s [%s]' % (title, context)
            spacer = '# %s' % ('=' * len(s))
            dump += cr + \
                '%s%s# %s%s%s%s' % (spacer, cr, s, cr, spacer, cr) + \
                _formatted_dump(logs, columns) + cr

    if len(dump) < 4:
        dump += gettext('No data') + '!'

    return dump

def getTagSearchDump(file_id, tagsearch, **kw):
    """
        Output from given Order body selected Tags list
    """
    xml = ''

    is_extra = kw.get('is_extra') and True or False

    if not tagsearch:
        return ''

    parser = g.decoder.chooseBodyParser(tag=FILEBODY_RECORD)

    if parser is None:
        return ''

    level1 = '%s%s' % (cr, default_indent)
    level2 = '%s%s' % (cr, default_indent * 2)
    spacer = '%s...' % level2

    tags = tagsearch.split(DEFAULT_HTML_SPLITTER)

    for node in parser:
        recno = parser.find(node, FILERECNO)

        items = [x for tag in tags for x in parser.findall(node, tag) if tag]

        content = ''

        for item in items:
            if not is_extra:
                g.decoder.maskContent(item, tag=item.tag)
            content += '%s%s' % (level2, parser.upload(item).strip())

        xml += '%s<%s>%s<%s>%s</%s>%s%s%s%s</%s>' % (
            level1,
            FILEBODY_RECORD,
            level2,
            FILERECNO, 
            recno, 
            FILERECNO,
            spacer,
            content,
            spacer,
            level1,
            FILEBODY_RECORD,
        )

        parser.clear(node)

    g.decoder.flash()

    return '%s%s' % (g.decoder.header(parser=parser.info(), tags=','.join(tags)), xml)

def calculateMaterials(file_id, order=None):
    """
        Get `Materials Order` Parameters list
    """
    return _get_materials(file_id, order=order)

def sendMaterialsOrder(file_id, order=None):
    """
        Send `Materials Order` mail request to the Warehouse
    """
    data, props, errors = _get_materials(file_id, show=0, order=order)

    _UNDEFINED_ERROR = 2
    _ERROR = 1
    _WARNING = 0

    subject = 'Заявка на расходные материалы'
    style = None
    filename = props['FileName']

    errors = []

    try:
        document = make_materials_attachment(subject, data, props, style=style)

        if not send_materials_order(subject, props, document, filename,
                                    addr_from=email_address_list.get('adminbd'),
                                    addr_to=email_address_list.get('warehouse'),
            ):
            errors.append((_ERROR, gettext('Error: Materials request email error.'),))
        else:
            rows, error_msg = g.engine.runProcedure('materials.approval', 
                                                  file_id=file_id, 
                                                  file_status_ids='', 
                                                  no_cursor=True, 
                                                  with_error=True
                                                  )
            if error_msg:
                errors.append(error_msg)

    except:
        if IsPrintExceptions:
            print_exception()

        errors.append((_UNDEFINED_ERROR, gettext('Error: Unexpected error.'),))

    errors = [x[1] for x in sorted(errors, key=itemgetter(0), reverse=True)]

    return errors

def calculateContainerList(file_id, is_group=False, **kw):
    """
        Generates `Container List` output form
    """
    data = {}
    props = {}
    errors = []

    if 'data' in kw:
        data = kw.get('data')

    _UNDEFINED_ERROR = 2
    _ERROR = 1
    _WARNING = 0

    filter_field = re.compile(r'\$\{FILTERFIELD\.(.*)\}')
    rtype = re.compile(r'((дизайн|вид)\s*[№#]?\s*([\d]+))', re.I+re.DOTALL)

    PERSO_BATCH_TYPE = 7
    PLASTIC_TYPE_KEYWORD = 'Тип пластика'
    CARD_TYPE_KEYWORD = 'Тип карт'
    QTY_NAME = 'ElementQty'
    
    batches, selected_id = _get_batches(file_id, batchtype=PERSO_BATCH_TYPE)

    TZ = kw.get('TZ', [])
    items = kw.get('items', [])

    keyword = ''
    total = 0

    def _get_type_keyword(items):
        for key in (PLASTIC_TYPE_KEYWORD, CARD_TYPE_KEYWORD):
            if len([1 for item in items if item['PName'] == key]) > 0:
                return key

    try:
        for batch in batches:
            batch_id = batch['id']

            batch_data, batch_props = getTabParams(file_id, batch_id) #, param_name=CARD_TYPE_KEYWORD, format=3, is_short=True

            if not keyword:
                keyword = _get_type_keyword(batch_data)

            name = ''

            for item in batch_data:
                if name and item['PName'] == name or item['PName'] == keyword:
                    value = item['PValue'] or ''

                    if 'FILTERFIELD' in value:
                        m = filter_field.search(item['PValue'])
                        name = m and m.group(1) or ''
                        continue

                    m = rtype.search(value)
                    value = Capitalize(m and m.group(1) or value)

                    if value not in data:
                        data[value] = 0

                        items.append((
                            m and int(m.group(3)) or 0, 
                            value
                            ))

                    qty = item.get(QTY_NAME) or 0
                    data[value] += qty
                    total += qty

            TZ.append(batch['TZ'])

        if not is_group and total != g.requested_object['FQty']:
            errors.append((_ERROR, gettext('Error: Final sum of batches Qty is unmatched.'),))

    except:
        if IsPrintExceptions:
            print_exception()

        errors.append((_UNDEFINED_ERROR, gettext('Error: Unexpected error.'),))

    finally:
        props = {
            'items'      : [x[1] for x in sorted(items, key=itemgetter(0))],
            'ClientName' : g.requested_object.get('BankName') or '',
            'FileName'   : g.requested_object.get('FName') or '',
            'FQty'       : g.requested_object.get('FQty') or 0,
            'TZ'         : ', '.join([str(x) for x in TZ]),
            'Now'        : getDate(getToday(), LOCAL_EXCEL_TIMESTAMP),
            'Today'      : getDate(getToday(), DEFAULT_DATETIME_TODAY_FORMAT),
            'show'       : 0,
        }

    errors = [x[1] for x in sorted(errors, key=itemgetter(0), reverse=True)]

    return data, props, errors

def calculateGroupContainerList(file_ids=None):
    """
        Generates `Container List` output form for files group
    """
    data = {}
    props = {}
    errors = []

    _UNDEFINED_ERROR = 2
    _ERROR = 1
    _WARNING = 0

    TZ = []
    items = []

    client_name = ''
    filenames = []
    fqty = 0
    tzs = []

    for file_id in file_ids:
        order = _get_order(file_id)

        data, p, e = calculateContainerList(file_id, is_group=True, data=data, items=items)

        if e:
            errors.append((_ERROR, e,))
            break

        if client_name and (client_name != p['ClientName'] or client_name != order['BankName']):
            errors.append((_ERROR, gettext('Error: Clients for selected files are not unique.'),))
            break
        else:
            client_name = p['ClientName']

        filenames.append(order['FName'])
        fqty += order['FQty']
        tzs.append(p['TZ'])

    if len(items) > 0:
        props = {
            'items'      : [x[1] for x in sorted(items, key=itemgetter(0))],
            'ClientName' : client_name,
            'FileName'   : '<br>'.join(filenames),
            'FQty'       : fqty,
            'TZ'         : ''.join(['<p>%s</p>' % x for x in tzs]),
            'Now'        : getDate(getToday(), LOCAL_EXCEL_TIMESTAMP),
            'Today'      : getDate(getToday(), DEFAULT_DATETIME_TODAY_FORMAT),
            'show'       : 0,
        }

    errors = [x[1] for x in sorted(errors, key=itemgetter(0), reverse=True)]

    return data, props, errors

def changeDeliveryDate(changedate):
    errors = []

    client = g.requested_object['BankName'].lower()

    if client.lower() not in ('postbank',):
        errors.append("Для клиента '%s' данная операция не поддерживается." % client)
        return 0, None, errors

    LOCAL_DATESTAMP = '%d.%m.%Y'

    attrs = {
        'client'     : client,
        'filetype'   : g.requested_object['FileType'],
        'status'     : g.requested_object['FileStatusID'],
        'forced'     : g.requested_object['FileID'],
        'changedate' : getDate(getDate(changedate, LOCAL_DATESTAMP, is_date=True), LOCAL_DATESTAMP),
    }

    cwd = g.system_config.EXTPERSO_STARTER_FOLDER or "C:/apps/perso"
    config = "perso.config.default"
    command = "CSD::%(filetype)s::%(status)d-0-0::[everything,ext.order_generate.%(client)s.change_delivery_date,\'%(changedate)s\',%(forced)d]" % attrs

    args = [os.path.join(cwd, "run.exe"), cwd, config, command]

    return _run_subprocess(args, cwd)

def changeDeliveryAddress(changeaddress):
    errors = []

    client = g.requested_object['BankName'].lower()

    if client.lower() not in ('postbank',):
        errors.append("Для клиента '%s' данная операция не поддерживается." % client)
        return 0, None, errors

    address, recno, branch = changeaddress.split('::')

    if not recno.isdigit():
        recno = None

    attrs = {
        'client'    : client,
        'filetype'  : g.requested_object['FileType'],
        'status'    : g.requested_object['FileStatusID'],
        'forced'    : g.requested_object['FileID'],
        'address'   : ','.join([x.strip() for x in address.split(',')]),
        'recno'     : recno, 
        'branch'    : branch,
    }

    cwd = g.system_config.EXTPERSO_STARTER_FOLDER or "C:/apps/perso"
    config = "perso.config.default"
    command = "CDA::%(filetype)s::%(status)d-0-0::[everything,ext.order_generate.%(client)s.change_delivery_address,\'%(address)s\',%(recno)s,\'%(branch)s\',%(forced)d]" % attrs

    args = [os.path.join(cwd, "run.exe"), cwd, config, command]

    return _run_subprocess(args, cwd)

def repeatUnloadedReport(file_id):
    errors = []

    client = g.requested_object['BankName'].lower()

    if client.lower() not in ('postbank',):
        errors.append("Для клиента '%s' данная операция не поддерживается." % client)
        return 0, None, errors

    attrs = {
        'client'    : client,
        'filetype'  : g.requested_object['FileType'],
        'status'    : g.requested_object['FileStatusID'],
        'forced'    : g.requested_object['FileID'],
        'id'        : 'postbank_report',
    }

    cwd = g.system_config.EXTPERSO_STARTER_FOLDER or "C:/apps/perso"
    config = "perso.config.default"
    command = "RUR::%(filetype)s::%(status)d-0-0::[\'%(id)s\',%(forced)d]" % attrs

    args = [os.path.join(cwd, "run.exe"), cwd, config, command]

    code, stdout, errors = _run_subprocess(args, cwd)

    if not code and ':' in stdout:
        stdout = '%s: %s' % (gettext('Total unloaded files'), stdout.split(':')[1])

    return code, stdout, errors

## ==================================================== ##

def _make_report_kp(kw):
    """
        Отчет: Статистика КП БинБанка
    """
    headers = ['КЛИЕНТ', 'ID файла', 'ФАЙЛ', 'КП', 'Кол-во',]
    rows = []

    for order in kw.get('orders'):
        row = []
        file_id = order['FileID']

        items = {}

        batches, selected_id = _get_batches(file_id)
        for batch in batches:
            batch_id = batch['id']

            data, props = getTabParams(file_id, batch_id)
            for item in data:
                if not (item['PType'] == 1 and item['PName'] == 'КП'):
                    continue
                key = item['PValue'].strip() or 'undefined'
                if not key.startswith('$'):
                    if key not in items:
                        items[key] = 0

                    items[key] += props['no']

        for key in sorted(items.keys()):
            rows.append([
                order['BankName'],
                file_id,
                order['FName'],
                key,
                items[key],
            ])

    rows.insert(0, headers)
    return rows

def _make_report_branch_list(kw):
    """
        Отчет: Статистика отгрузки по филиалам (Левобережный)
    """
    headers = ['Код филиала', 'Тип карты', 'Адрес доставки (Филиал)', 'Кол-во',]
    rows = []

    _BRANCH = 'Доставка'
    _CARD_TYPE = 'PlasticType'
    _ID_VSP = 'ID_VSP'
    
    separator = ','

    parser = g.decoder.chooseBodyParser(tag=FILEBODY_RECORD)

    def _get_item(node, tags, default=None, encoding=None):
        value = None
        for tag in tags:
            value = parser.find(node, tag, encoding=encoding)
            if value:
                break
        return value or default

    if parser is not None:
        items = {}

        for node in parser:
            g.decoder.decodeCyrillic(node)

            id_vsp = _get_item(node, ('ID_VSP', 'DEST_CODE', 'BRANCH_SEND_TO', 'ADD1_BRANCH', 'BranchID'))
            if not id_vsp:
                continue

            branch_name = _get_item(node, ('BRANCH', 'DEST_BRANCH', 'DEST_NAME', 'DeliveryAddress', 'FACTADRESS', 'FactAddress', 'CompanyName', 'CardholderAddress'), 
                                    encoding=default_encoding)

            if branch_name:
                pass #branch_name = branch_name.encode(default_encoding, 'ignore').decode()
            else:
                branch_name = gettext('undefined')

            card_type = _get_item(node, ('PlasticType', 'CardType', 'PLASTIC_CODE', 'PROD_ID'), default='OTHER')
            """
            if separator in branch_name:
                try:
                    branch_name = [x.strip() for x in branch_name.split(separator) if not x.isdigit()][0]
                except:
                    pass
            """
            if id_vsp not in items:
                items[id_vsp] = {}
            if card_type not in items[id_vsp]:
                items[id_vsp][card_type] = {}
            if branch_name not in items[id_vsp][card_type]:
                items[id_vsp][card_type][branch_name] = 0

            items[id_vsp][card_type][branch_name] += 1

            parser.clear(node)

        for key in sorted(items.keys()):
            for card in sorted(items[key].keys()):
                for branch in sorted(items[key][card].keys()):
                    rows.append([
                        key, card, branch, items[key][card][branch],
                    ])

    g.decoder.flash()

    rows = sorted(rows, key=itemgetter(0))

    rows.insert(0, headers)
    return rows

def _make_report_design_list(kw):
    """
        Отчет: Статистика отгрузки по дизайнам
    """
    headers = ['Дата отгрузки', 'Код дизайна', 'Кол-во карт', 'ТЗ']
    rows = []

    where = kw.get('where')
    state = kw.get('state')

    date_format = LOCAL_EASY_DATESTAMP
    batchtype = 7
    
    total_files = 0
    total_batches = 0
    total = 0

    columns = database_config[default_template]['export']
    encode_columns = ('FileStatus',)
    order = 'FileID'

    cursor = g.engine.runQuery(default_template, columns=columns, where=where, order=order, encode_columns=encode_columns, as_dict=True) or []

    items = {}

    for row in cursor:
        file_id = row['FileID']

        is_checked, state_stop, state_error, state_ready, state_wait, state_archive = _check_order_state(state, row)
        if is_checked:
            continue

        total_files += 1

        ready_date = getDate(row['ReadyDate'], format=date_format)

        batches, selected_id = _get_batches(file_id, batchtype=batchtype)
        for batch in batches:
            batch_id = batch['id']
            tz = ':%s' % batch['TZ']
            total_batches += 1

            qty = batch['ElementQty']

            data, props = getTabParams(file_id, batch_id, is_short=True, no_materials=True)
            for item in data:
                if item['PType'] == 1:
                    continue
                if item['PName'] not in ('ProductDesign',):
                    continue

                design = item['PValue']

                if ready_date not in items:
                    items[ready_date] = {}
                if design not in items[ready_date]:
                    items[ready_date][design] = [0, []]

                items[ready_date][design][0] += qty

                if tz not in items[ready_date][design][1]:
                    items[ready_date][design][1].append(tz)

                total += qty

    for date in sorted(items.keys()):
        for design in sorted(items[date].keys()):
            rows.append([
                date,
                design,
                items[date][design][0],
                ''.join(items[date][design][1]),
            ])

    rows.append(['-'*100])
    rows.append(['Всего:', 'файлов: %s, партий: %s' % (total_files, total_batches), total, ''])

    rows.insert(0, headers)
    return rows

def _make_export(kw):
    """
        Экспорт журнала заказов в Excel
    """
    view = kw['config']['orders']
    columns = view['columns']
    headers = [view['headers'][x][0] for x in columns]
    rows = []

    for data in kw['orders']:
        row = []
        for column in columns:
            try:
                v = data[column]
                if 'Date' in column and v:
                    v = re.sub(r'\s+', ' ', re.sub(r'<.*?>', ' ', v)).strip()
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

def _make_xls_content(rows, title, name=None, ctype=None):
    if len(rows) > g.system_config.MAX_CARDHOLDER_ITEMS or ctype == 'csv':
        output = makeCSVContent(rows, title, True)
        ext = 'csv'
    else:
        output = makeXLSContent(rows, title, True)
        ext = 'xls'
    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=%s.%s" % (_make_response_name(name), ext)
    return response

def _make_page_default(kw, back_where=None):
    file_id = int(kw.get('file_id'))
    batch_id = int(kw.get('batch_id'))

    is_admin = g.current_user.is_administrator()
    is_operator = g.current_user.is_operator()

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
    top, offset = _get_top(per_page, page)

    # ------------------------
    # Поиск контекста (search)
    # ------------------------

    search = get_request_search()
    is_search_batch = False
    items = []
    preview_items = []
    TZ = None

    # -----------------------------------
    # Команда панели управления (сommand)
    # -----------------------------------

    command = kw.get('command') or get_request_item('command')

    # ----------------------------------------------
    # Поиск ID файла, номера ТЗ (search is a number)
    # ----------------------------------------------

    if search:
        try:
            FileID = TZ = int(search)
            if back_where and command in ('design-list',):
                items.append('(FileID=%s)' % FileID)
            else:
                items.append('(FileID=%s OR TZ=%s)' % (FileID, TZ))
            is_search_batch = True
            pers_tz = TZ
        except:
            TZ = 0
            op = search.startswith('!') and 'not ' or ''
            items.append("FName %slike '%%%s%%'" % (op, search))

    # -------------
    # Фильтр (args)
    # -------------

    ClientID = args['bank'][1]
    FileTypeID = args['type'][1]
    FileStatusID = args['status'][1]
    BatchTypeID = args['batchtype'][1]
    BatchStatusID = args['batchstatus'][1]

    is_yesterday = is_tomorrow = is_today = False
    
    default_date_format = DEFAULT_DATE_FORMAT[1]
    today = getDate(getToday(), default_date_format)
    date_from = None

    def _evaluate_date(s, x, format=default_date_format):
        d = getDate(s, format, is_date=True)
        return getDate(daydelta(d, x), format)

    if args:

        # -------------------
        # Фильтр текущего дня
        # -------------------

        date_from = args.get('date_from')[1]
        if date_from:
            is_yesterday = args['yesterday'][1] and True or False
            is_tomorrow = args['tomorrow'][1] and True or False

        if is_yesterday:
            args['date_from'][1] = args['date_to'][1] = date_from = _evaluate_date(date_from, -1)
        if is_tomorrow:
            args['date_from'][1] = args['date_to'][1] = date_from = _evaluate_date(date_from, 1)

        is_today = (args['today'][1] or (date_from == today and not is_yesterday)) and True or False

        if is_today:
            args['date_from'][1] = date_from = today
            args['date_to'] = ['', None]

        if not (is_yesterday or is_tomorrow or is_today):
            date_from = None

        # -----------------
        # Параметры фильтра
        # -----------------

        for key in args:
            if key == EXTRA_ or key in DATE_KEYWORDS:
                continue
            name, value = args[key]
            if value:
                if key in ('batchtype', 'batchstatus',):
                    pass
                elif key in ('date_from', 'ready_from',):
                    if checkDate(value, DEFAULT_DATE_FORMAT[1]):
                        items.append("%s >= '%s 00:00'" % (name, value))
                        preview_items.append("%s >= '%s 00:00'" % (name, value))
                    else:
                        args[key][1] = ''
                        continue
                elif key in ('date_to', 'ready_to',):
                    if checkDate(value, DEFAULT_DATE_FORMAT[1]):
                        items.append("%s <= '%s 23:59'" % (name, value))
                        preview_items.append("%s >= '%s 00:00'" % (name, value))
                    else:
                        args[key][1] = ''
                        continue
                elif key in ('id', 'bank', 'type', 'status',):
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
        order = 'FileID'

    if current_sort in (0,2,5,7,8,):
        order += " desc"

    if IsDeepDebug:
        print('--> where:[%s] order:[%s], args: %s' % (where, order, args))

    pages = 0
    total_orders = 0
    total_cards = 0
    orders = []
    batches = []
    banks = []
    types = []
    statuses = []
    batchtypes = []
    batchstatuses = []
    xml = ''

    # ----------------------
    # Условие отбора (state)
    # ----------------------

    state = get_request_item('state')
    is_state = state and state != 'R0' and True or False

    args.update({
        'state' : ('State', state)
    })

    if back_where:
        kw.update({'where' : where, 'order' : order, 'state' : state})
        return kw

    # --------------------
    # Файлы <на обработку>
    # --------------------

    if state and state in 'R4:R5':
        rows = g.engine.runQuery('batches.preview', where='BatchStatusID=1', distinct=True)
        ids = [x[0] for x in rows]
        if state == 'R4':
            exec_params = {'file_id' : 'null', 'file_status_ids' : makeIDList(COMPLETE_STATUSES), 'check' : 2}
            rows = g.engine.runQuery('materials.check', exec_params=exec_params)

            for id in [x[0] for x in rows]:
                if id not in ids:
                    data, props, errors = _get_materials(id, show=1)
                    if props['send'] and not errors:
                        ids.append(id)

        if ids:
            where = '%s%sFileID in (%s)' % ( \
                where, 
                where and ' and ' or '', 
                ','.join([str(x) for x in sorted(ids)])
                )

    confirmed_file_id = 0
    selected_row = {}

    # ======================
    # Выборка данных журнала
    # ======================

    if g.engine != None:

        # ------------------------------------------------
        # Поиск заказа по ID или номеру ТЗ (is_search_batch)
        # ------------------------------------------------
        
        if is_search_batch:
            file_id = 0

            cursor = g.engine.runQuery(_views['batches'], columns=('FileID',), where=where)
            for n, row in enumerate(cursor):
                file_id = row[0]

            if not file_id:
                where = 'FileID=%s' % FileID

                cursor = g.engine.runQuery(default_template, columns=('FileID',), where=where)
                for n, row in enumerate(cursor):
                    file_id = row[0]

            where = 'FileID=%s' % file_id

        # --------------------------------------------------
        # Кол-во записей по запросу в журнале (total_orders)
        # --------------------------------------------------

        cursor = g.engine.runQuery(default_template, columns=('count(*)', 'sum(FQty)',), where=where)
        if cursor:
            total_orders, total_cards = cursor[0]
            if total_cards is None:
                total_cards = 0

        if is_state:
            top, offset = 1000, None
        if command == 'export':
            top = 10000

        # ===============
        # Заказы (orders)
        # ===============

        cursor = g.engine.runQuery(default_template, top=top, offset=offset, where=where, order='%s' % order, as_dict=True,
                                 encode_columns=('BankName','FileStatus'))
        if cursor:
            is_selected = False

            if is_state:
                top, offset = _get_top(per_page, page)

            for n, row in enumerate(cursor):
                #if is_state and len(orders) > per_page:
                #    continue

                is_checked, state_stop, state_error, state_ready, state_wait, state_archive = _check_order_state(state, row)
                if is_checked:
                    continue

                if file_id:
                    if not confirmed_file_id and file_id == row['FileID']:
                        confirmed_file_id = file_id
                    if not file_name and file_id == row['FileID']:
                        file_name = row['FName']

                    if file_id == row['FileID']:
                        row['selected'] = 'selected'
                        selected_row = row
                        is_selected = True
                else:
                    row['selected'] = ''

                for x in row:
                    if not row[x] or str(row[x]).lower() == 'none':
                        row[x] = ''

                row['Stop'] = state_stop
                row['Error'] = state_error
                row['Ready'] = state_ready
                row['Wait'] = state_wait
                row['Archive'] = state_archive
                row['StatusDate'] = getDate(row['StatusDate'])
                row['RegisterDate'] = getDate(row['RegisterDate'])
                row['ReadyDate'] = getDate(row['ReadyDate'])
                row['FQty'] = str(row['FQty']).isdigit() and int(row['FQty']) or 0
                row['id'] = row['FileID']

                orders.append(row)

            if line > len(orders):
                line = 1

            if not is_selected and len(orders) >= line:
                row = orders[line-1]
                confirmed_file_id = file_id = row['id'] = row['FileID']
                file_name = row['FName']
                row['selected'] = 'selected'
                selected_row = row

        if len(orders) == 0:
            file_id = 0
            file_name = ''
            batch_id = 0
        elif confirmed_file_id != file_id or not file_id:
            row = orders[0]
            file_id = row['FileID']
            file_name = row['FName']
        elif not confirmed_file_id:
            file_id = 0
            file_name = ''

        if is_state and orders:
            total_orders = len(orders)
            total_cards = 0
            orders = orders[offset:offset+per_page]
            is_selected = False

            for n, row in enumerate(orders):
                if file_id == row['FileID']:
                    row['selected'] = 'selected'
                    file_name = row['FName']
                    selected_row = row
                    is_selected = True
                else:
                    row['selected'] = ''
                total_cards += row['FQty']

            if not is_selected and orders:
                row = orders[0]
                row['selected'] = 'selected'
                file_id = row['FileID']
                file_name = row['FName']
                selected_row = row

        if total_orders:
            pages = int(total_orders / per_page)
            if pages * per_page < total_orders:
                pages += 1

        # ================
        # Партии (batches)
        # ================

        if file_id:
            batches, batch_id = _get_batches(file_id, batch_id=batch_id, pers_tz=pers_tz, batchtype=BatchTypeID, batchstatus=BatchStatusID,
                                             is_default_date=True)

        # --------------------------------------------------------------------------------
        # Справочники фильтра запросов (banks, types, statuses, batchtypes, batchstatuses)
        # --------------------------------------------------------------------------------

        banks.append((0, DEFAULT_UNDEFINED,))
        cursor = g.engine.runQuery('banks', order='BankName', distinct=True, encode_columns=(1,))
        banks += [(x[0], x[1]) for x in cursor]

        types.append((0, DEFAULT_UNDEFINED,))
        where = ClientID and ('ClientID = %s' % ClientID) or ''
        cursor = g.engine.runQuery('types', where=where, order='CName', distinct=True)
        types += [(x[0], x[1]) for x in cursor]

        statuses.append((0, DEFAULT_UNDEFINED,))
        cursor = g.engine.runQuery('statuses', order='CName', distinct=True, encode_columns=(1,))
        statuses += [(x[0], x[1]) for x in cursor]

        batchtypes.append((0, DEFAULT_UNDEFINED,))
        cursor = g.engine.runQuery('batchtypelist', order='CName', distinct=True, encode_columns=(1,))
        batchtypes += [(x[0], x[1]) for x in cursor]

        batchstatuses.append((0, DEFAULT_UNDEFINED,))
        cursor = g.engine.runQuery('batchstatuslist', order='CName', distinct=True, encode_columns=(1,))
        batchstatuses += [(x[0], x[1]) for x in cursor]

        g.engine.dispose()

    # ----------------------
    # Условия отбора заказов
    # ----------------------

    states = [
        ('R0', DEFAULT_UNDEFINED),
        ('R1', 'Файлы "В работе"'),
        ('R6', 'Файлы "В ожидании"'),
        ('R2', 'Завершено'),
        ('R3', 'Ошибки'),
        ('R7', 'Архив'),
    ]

    if is_operator:
        states.insert(1, ('R4', 'Файлы "На обработку"'))
        states.insert(4, ('R5', 'Активно'))

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
    base = 'bankperso?%s' % query_string

    per_page_options = (5, 10, 20, 30, 40, 50, 100,)
    if is_admin:
        per_page_options += (250, 500)

    is_extra = has_request_item(EXTRA_)

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
        'link'              : '%s%s%s%s%s' % (base, filter,
                                             (search and "&search=%s" % search) or '',
                                             (current_sort and "&sort=%s" % current_sort) or '',
                                             (state and "&state=%s" % state) or '',
                                              ),
        'sort'              : {
            'modes'         : modes,
            'sorted_by'     : sorted_by,
            'current_sort'  : current_sort,
        },
        'position'          : '%d:%d:%d:%d' % (page, pages, per_page, line),
        'today'             : {
            'selected'      : is_today,
            'date_from'     : date_from,
            'has_prev'      : is_today or is_yesterday,
            'has_next'      : date_from and date_from < today and True or False,
        },
    }

    loader = '/bankperso/loader'

    if is_extra:
        pagination['extra'] = 1
        loader += '?%s' % EXTRA_

    kw.update({
        'base'              : base,
        'page_title'        : gettext('WebPerso Order Registry View'),
        'header_subclass'   : 'left-header',
        'show_flash'        : True,
        'model'             : 0,
        'loader'            : loader,
        'semaphore'         : initDefaultSemaphore(),
        'args'              : args,
        'current_file'      : (file_id, file_name, batch_id, pers_tz),
        'tabs'              : _check_extra_tabs(selected_row).keys(),
        'navigation'        : get_navigation(),
        'config'            : database_config,
        'pagination'        : pagination,
        'orders'            : orders,
        'batches'           : batches,
        'banks'             : banks,
        'types'             : types,
        'statuses'          : statuses,
        'batchtypes'        : batchtypes,
        'batchstatuses'     : batchstatuses,
        'batches_tab'       : args['batchstatus'][1] and 'active' or 'all',
        'states'            : states,
        'xml'               : xml,
        'search'            : search or '',
        'schedule_template' : {'documents': [], 'decrees': []},
        'schedule_params'   : {'documents': [0, 0], 'decrees': [0, 0]},
        'total_selected'    : '0 | 0.00',
    })

    sidebar = get_request_item('sidebar')
    if sidebar:
        kw['sidebar']['state'] = int(sidebar)

    kw['style']['show_scroller'] = 1

    return kw

## ==================================================== ##

@bankperso.route('/demo', methods = ['GET','POST'])
def demo(**kw):
    connection = CONNECTION[kw.get('engine') or 'bankperso']
    """
    conn = pymssql.connect(connection['server'], connection['user'], connection['password'], connection['database'])
    cursor = conn.cursor(as_dict=False)
    cursor.execute('SELECT count(*) FROM [BankDB].[dbo].[WEB_OrdersStatus_vw]')
    total_orders = cursor.fetchone()[0]
    """
    refresh()
    
    cursor = g.engine.execute('SELECT count(*) FROM [BankDB].[dbo].[WEB_OrdersStatus_vw]')
    total_orders = cursor.fetchone()[0]

    banks = []
    types = []
    statuses = []
    params = []
    TZ = []

    file_id = 218107
    batch_id = 1184030

    def encode(value):
        return value and isinstance(value, str) and value.encode(default_iso).decode(default_encoding) or value or ''

    try:
        cursor = g.engine.runQuery('banks', order='BankName', distinct=True)
        c1 = cursor
        banks += [x[1] for x in c1]

        cursor = g.engine.runQuery('types', order='CName', distinct=True, encode_columns=(1,))
        c2 = cursor
        types += [x[1] for x in c2]
        
        cursor = g.engine.runQuery('statuses', order='CName', distinct=True, encode_columns=(1,))
        c3 = cursor
        statuses += [x[1] for x in c3]
        
        encode_columns = ('PName', 'PValue', 'TValue')
        cursor = g.engine.runQuery('params', as_dict=True, params="%s, %s, '', 0, ''" % (file_id, batch_id), encode_columns=encode_columns)
        c4 = cursor
        for row in c4:
            params.append(row)
        
        encode_columns = ('PName', 'PValue')
        cursor = g.engine.runQuery('TZ', as_dict=True, params="%s, %s, '', 1, ''" % (file_id, batch_id), encode_columns=encode_columns)
        c5 = cursor
        for row in c5:
            key = row['PName']
            if key in database_config['TZ']['rename']:
                x = database_config['TZ']['rename'][key]
                row['PName'] = x[0]
                row['PSortIndex'] = x[1]
            TZ.append(row)

        exclude = database_config['TZ']['exclude']
        TZ = sorted([x for x in TZ if x['PType'] in (0,1) and x['PName'] not in exclude], key=lambda x: x['PSortIndex'],
                    reverse=False)
    except:
        print_exception()

    else:
        if IsDebug:
            print_to(None, '--> demo check: %s' % 'OK')

    kw = { 
        'title'        : 'demo',
        'connection'   : connection,
        'config'       : database_config,
        'banks'        : banks,
        'types'        : types,
        'statuses'     : statuses,
        'params'       : params,
        'TZ'           : TZ,
        'total'        : total_orders,
    }
    return render_template('demo.html', **kw)

@bankperso.route('/', methods = ['GET'])
@bankperso.route('/bankperso', methods = ['GET','POST'])
@login_required
def start():
    try:
        return index()
    except:
        raise

def index():
    debug, kw = init_response('WebPerso Main Page')
    kw['product_version'] = product_version

    is_admin = g.current_user.is_administrator()
    is_operator = g.current_user.is_operator()

    command = get_request_item('command')
    
    file_id = int(get_request_item('file_id') or '0')
    batch_id = int(get_request_item('batch_id') or '0')

    if IsDeepDebug:
        print('--> command:%s, file_id:%s, batch_id:%s' % (command, file_id, batch_id))

    refresh(file_id=file_id)

    IsMakePageDefault = True
    back_where = False
    specified = ''
    info = ''

    code, stdout, errors = -1, '', []

    if command and get_request_item('OK') != 'run':
        command = ''

    if command.startswith('admin'):
        command = command.split(DEFAULT_HTML_SPLITTER)[1]

        if not is_operator:
            flash('You have not permission to run this action!')
            command = ''

        elif command == 'activate':

            # -------------------------
            # Activate selected batches
            # -------------------------

            selected_batch_ids = get_request_item('selected_batch_ids') or ''
            info = 'selected_batch_ids:%s' % selected_batch_ids

            for batch_id in selected_batch_ids.split(DEFAULT_HTML_SPLITTER):
                rows, error_msg = g.engine.runProcedure('activate', batch_id=batch_id, no_cursor=True, with_error=True)

                if error_msg:
                    errors.append(error_msg)

        elif command == 'changedate':
            specified = get_request_item('specified') or ''
            info = 'changedate:%s' % specified

            # --------------------------
            # Change Delivery Date items
            # --------------------------

            code, stdout, errors = changeDeliveryDate(specified)

        elif command == 'changeaddress':
            specified = get_request_item('specified') or ''
            info = 'changeaddress:%s' % specified

            # -----------------------------
            # Change Delivery Address items
            # -----------------------------

            code, stdout, errors = changeDeliveryAddress(specified)

        elif command == 'report of':
            info = 'repeat of:%s' % file_id

            # ----------------------
            # Repeat Unloaded Report
            # ----------------------

            code, stdout, errors = repeatUnloadedReport(file_id)

        elif not is_admin:
            flash('You have not permission to run this action!')
            command = ''

        elif command == 'create':
            info = 'file_id:%s' % file_id

            # --------------
            # Re-Create file
            # --------------

            g.engine.runProcedure('createfile', file_id=file_id, no_cursor=True)

        elif command == 'delete':
            info = 'file_id:%s' % file_id

            # -----------
            # Delete file
            # -----------

            g.engine.runProcedure('deletefile', file_id=file_id, no_cursor=True)

        elif command == 'change-filestatus':
            new_file_status = int(get_request_item('status_file_id') or '0')
            keep_history = get_request_item('status_keep_history') or '0'
            check_file_status = 'null'
            info = 'new_file_status:%s' % new_file_status

            # ---------------------
            # Change status of file
            # ---------------------

            statuses = _get_filestatuses(file_id)

            run_batch = 0

            if statuses:
                if new_file_status in statuses:
                    check_file_status = new_file_status
                elif new_file_status < statuses[-1]:
                    check_file_status = new_file_status
                if new_file_status < 6:
                    run_batch = 1

            g.engine.runProcedure('changefilestatus', file_id=file_id, new_file_status=new_file_status, 
                                check_file_status=check_file_status, run_batch=run_batch, keep_history=keep_history, no_cursor=True)

        elif command == 'change-batchstatus':
            new_batch_status = int(get_request_item('status_batch_id') or '0')
            info = 'new_batch_status:%s' % new_batch_status

            # ----------------------
            # Change status of batch
            # ----------------------

            g.engine.runProcedure('changebatchstatus', file_id=file_id, batch_id=batch_id, 
                                new_batch_status=new_batch_status, no_cursor=True)

        elif command == 'logsearch':
            specified = get_request_item('specified') or ''
            info = 'logsearch:%s' % specified

            # --------------------
            # Dump LogSearch items
            # --------------------

            IsMakePageDefault = False

        elif command == 'tagsearch':
            specified = get_request_item('specified') or ''
            info = 'tagsearch:%s' % specified

            # --------------------
            # Dump TagSearch items
            # --------------------

            IsMakePageDefault = False

        if IsDeepDebug:
            print('--> %s' % info)

        if IsTrace:
            print_to(errorlog, '--> command:%s %s [%s]' % (command, g.current_user.login, info))

    elif command.startswith('service'):
        command = command.split(DEFAULT_HTML_SPLITTER)[1]

        if command in ('design-list',):
            kw['command'] = command
            back_where = True

    kw['errors'] = '<br>'.join(errors)
    kw['OK'] = ''

    try:
        if IsMakePageDefault:
            kw = _make_page_default(kw, back_where=back_where)

        if IsTrace:
            print_to(errorlog, '--> bankperso:%s %s [%s:%s] %s %s' % (
                     command, g.current_user.login, request.remote_addr, kw.get('browser_info'), str(kw.get('current_file')), info,), 
                     request=request)
    except:
        if IsPrintExceptions:
            print_exception()

    kw['vsc'] = vsc(force=g.system_config.IsForceRefresh)

    if command:
        is_extra = has_request_item(EXTRA_)

        if not command.strip():
            pass

        elif command == 'activate':
            if kw['errors']:
                flash('Batch action done with errors!')
            else:
                kw['OK'] = html_flash(gettext('Message: Action is perfomed successfully.'))

        elif command == 'unload':
            filename = 'body%s.dump' % file_id
            return Response(
                stream_with_context(getCurrentState(is_extra=is_extra)),
                headers={"Content-Disposition" : "attachment; filename=" + filename}
            )

        elif command == 'imageunload':
            filename = 'image%s.dump' % file_id
            return Response(
                getFullState(with_image=True, no_body=True, limit=None, is_extra=is_extra, no_cyrillic=True, file_id=file_id),
                headers={"Content-Disposition" : "attachment; filename=" + filename}
            )

        elif command == 'fullunload':
            filename = 'full%s.dump' % file_id
            return Response(
                getFullState(with_image=True, limit=None, is_extra=is_extra, no_cyrillic=True, file_id=file_id),
                headers={"Content-Disposition" : "attachment; filename=" + filename}
            )

        elif command == 'logsearch':
            dump = getLogSearchDump(specified)
            response = make_response(dump)
            response.headers["Content-Disposition"] = "attachment; filename=%s.dump" % _make_response_name('logsearch')
            return response

        elif command == 'tagsearch':
            dump = getTagSearchDump(file_id, specified, is_extra=is_extra)
            response = make_response(dump)
            response.headers["Content-Disposition"] = "attachment; filename=%s.dump" % _make_response_name('tagsearch')
            return response

        elif command == 'changedate':
            if kw['errors']:
                pass
            elif code:
                flash('Change date done with errors!')
            else:
                kw['OK'] = html_flash(gettext('Message: Delivery date is changed successfully.'))

        elif command == 'changeaddress':
            if kw['errors']:
                pass
            elif code:
                flash('Change address done with errors!')
            else:
                kw['OK'] = html_flash('%s\n%s' % (gettext('Message: Delivery address is changed successfully.'), stdout))

        elif command == 'report of':
            if kw['errors']:
                pass
            elif code:
                flash('Report was done with errors!')
            else:
                kw['OK'] = html_flash('%s\n%s' % (gettext('Message: Report was done successfully.'), stdout))

        elif command == 'kp':
            return _make_xls_content(_make_report_kp(kw), 'Статистика КП', 'kp')

        elif command == 'branch-list':
            try:
                filename = kw.get('current_file')[1] or ''
            except:
                filename = ''
            return _make_xls_content(_make_report_branch_list(kw), filename or 'Статистика отгрузки по филиалам', 'branch_list', ctype='csv')

        elif command == 'design-list':
            return _make_xls_content(_make_report_design_list(kw), 'Статистика отгрузки по дизайнам', 'design_list', ctype='csv')

        elif command == 'search-double':
            try:
                filename = kw.get('current_file')[1] or ''
            except:
                filename = ''
            cards, no_value = _search_double_pan()
            cards.insert(0, ['PAN', 'FileRecNo:with PIN'])
            if no_value:
                cards.append([])
                cards.append(['No PAN...'])
                cards = cards + no_value
            return _make_xls_content(cards, filename or 'Дубли PAN', 'Double PAN')

        elif command == 'cardholders':
            try:
                filename = kw.get('current_file')[1] or ''
            except:
                filename = ''
            data, columns = _get_cardholders(database_config['cardholders'], limit=None) #, encoding=default_encoding
            cardholders = [[item.get(x['name']) or '' for x in columns] for item in data]
            cardholders.insert(0, [x.get('header') for x in columns])
            return _make_xls_content(cardholders, filename or 'Лист персонализации', 'Cardholders')

        elif command == 'export':
            return _make_xls_content(_make_export(kw), 'Журнал заказов', ctype='csv')

    return make_response(render_template('bankperso.html', debug=debug, **kw))

@bankperso.route('/changelog', methods = ['GET'])
def changelog():
    output = ''
    try:
        with open(os.path.join(basedir, 'changelog.txt'), 'rb') as fp:
            output = fp.readlines()
    except:
        if IsPrintExceptions:
            print_exception()

    response = make_response('\r\n'.join([x.decode(default_unicode).rstrip() for x in output]))
    response.headers["Content-Disposition"] = "attachment; filename=changelog.%s.txt" % product_version.replace(',', '')
    return response

@bankperso.after_request
def make_response_no_cached(response):
    try:
        if g.decoder is not None:
            g.decoder.flash()
        if g.engine is not None:
            g.engine.close()
    except:
        pass
    # response.cache_control.no_store = True
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response

@bankperso.route('/bankperso/loader', methods = ['GET', 'POST'])
@login_required
def loader():
    exchange_error = ''
    exchange_message = ''

    is_extra = has_request_item(EXTRA_)

    action = get_request_item('action') or default_action
    selected_menu_action = get_request_item('selected_menu_action') or action != default_action and action or default_log_action

    response = {}

    file_id = int(get_request_item('file_id') or '0')
    batch_id = int(get_request_item('batch_id') or '0')
    batchtype = int(get_request_item('batchtype') or '0')
    batchstatus = int(get_request_item('batchstatus') or '0')
    params = get_request_item('params') or None

    refresh(file_id=file_id)

    if IsDeepDebug:
        print('--> action:%s file_id:%s batch_id:%s batchtype:%s batchstatus:%s' % (action, file_id, batch_id, batchtype, batchstatus))

    if IsTrace:
        print_to(errorlog, '--> loader:%s %s [%s:%s:%s:%s:%s]%s' % (
                 action, 
                 g.current_user.login, 
                 file_id, batch_id, 
                 batchtype, 
                 batchstatus, 
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
    status = ''
    path = None

    props = None
    errors = None

    tabs = _check_extra_tabs(g.requested_object)

    try:
        if action == default_action:
            batches, batch_id = _get_batches(file_id, batchtype=batchtype, batchstatus=batchstatus)
            currentfile = [g.requested_object.get('FileID'), g.requested_object.get('FName'), batch_id]
            config = _get_view_columns(database_config['batches'])
            action = _valid_extra_action(selected_menu_action) or default_log_action

        if not action:
            pass

        elif action == '201':
            cursor = g.engine.runQuery('filestatuslist', order='TID', distinct=True, encode_columns=(2,))
            data = [{'id':x[0], 'value':x[2]} for x in cursor]

        elif action == '202':
            cursor = g.engine.runQuery('batchstatuslist', order='TID', distinct=True, encode_columns=(1,))
            data = [{'id':x[0], 'value':x[1]} for x in cursor]

        elif action == '301':
            data, props = getTabParams(file_id, batch_id)

        elif action == '302':
            view = database_config['logs']
            columns = _get_view_columns(view)
            data = getTabLogs(file_id)

        elif action == '303':
            data, columns = getTabCardholders()

        elif action == '304':
            data, total, status = getTabIBody(is_extra=is_extra, params=params)

        elif action == '305':
            data, total = getTabProcessErrMsg()

        elif action == '306':
            view = database_config['persolog']
            columns = _get_view_columns(view)
            if IsUseDBLog:
                data = getTabDBLog('Bankperso', view, file_id=file_id)
            else:
                data = getTabPersoLog(view['export'], file_id=file_id, case_insensitive=True)

        elif action == '307':
            view = database_config['sdclog']
            columns = _get_view_columns(view)
            if IsUseDBLog:
                data = getTabDBLog('SDC', view, file_id=file_id)
            else:
                data = getTabSDCLog(view['export'], file_id=file_id, case_insensitive=True)

        elif action == '308':
            view = database_config['exchangelog']
            columns = _get_view_columns(view)
            if False and IsUseDBLog:
                data = getTabDBLog('Exchange', view, file_id=file_id)
            else:
                data = getTabExchangeLog(view['export'], file_id=file_id, case_insensitive=True)

        elif action == '309':
            view = database_config['materials.order']
            columns = _get_view_columns(view)
            data, props, errors = calculateMaterials(file_id=file_id)

        elif action == '310':
            errors = sendMaterialsOrder(file_id=file_id)

        elif action == '311':
            data, props, errors = calculateContainerList(file_id=file_id)

        elif action == '312':
            file_ids = [int(x) for x in params.split(DEFAULT_HTML_SPLITTER)]
            data, props, errors = calculateGroupContainerList(file_ids=file_ids)

        elif action == '313':
            data, columns = getTabIndigo()

        elif action == '314':
            status, path = getTabProcessInfo(tag='ProcessInfo')

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
        'file_id'          : file_id,
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
        'status'           : status,
        'path'             : path,
        'props'            : props,
        'columns'          : columns,
        'errors'           : errors,
    })

    return jsonify(response)

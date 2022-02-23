# -*- coding: utf-8 -*-

import re
import random
from operator import itemgetter

from config import (
     CONNECTION, BP_ROOT, 
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, LocalDebug,
     errorlog, print_to, print_exception,
     default_print_encoding, default_unicode, default_encoding, default_iso, image_encoding, cr,
     LOCAL_FULL_TIMESTAMP, LOCAL_EXCEL_TIMESTAMP, LOCAL_EASY_TIMESTAMP, LOCAL_EASY_DATESTAMP, LOCAL_EXPORT_TIMESTAMP, 
     UTC_FULL_TIMESTAMP, UTC_EASY_TIMESTAMP, DATE_STAMP
     )

from . import cards

from ..settings import *
from ..database import database_config, DatabaseEngine
from ..utils import (
     getToday, getDate, getDateOnly, checkDate, cdate, indentXMLTree, isIterable, makeXLSContent, makeIDList, 
     checkPaginationRange, getMaskedPAN, reprSortedDict, spent_time, make_config
     )

from ..semaphore.views import initDefaultSemaphore

##  ===============================
##  Cards View Presentation Package
##  ===============================

default_page = 'cards'
default_action = '700'
default_template = 'cards.batches'

# Локальный отладчик
IsLocalDebug = LocalDebug[default_page]
# Использовать OFFSET в SQL запросах
IsApplyOffset = 1
# Принудительная загрузка статических файлов
IsForceRefresh = 0

TEMPLATE_TID_INDEX   = 0
TEMPLATE_QUERY_INDEX = 1
TEMPLATE_FKEY_INDEX  = 2
TEMPLATE_VIEW_INDEX  = 3

_views = {
    'batches' : ('TID', 'pers_id',  'PersBatchID',     'cards.batches',),
    'opers'   : ('TID', 'oper_id',  'PersBatchOperID', 'cards.pers-batch-opers'),
    'logs'    : ('TID', 'batch_id', 'BatchID',         'cards.batches-log'),
    'units'   : ('TID', 'batch_id', 'BatchID',         'cards.batch-units'),
    'params'  : ('TID', 'batch_id', 'BatchID',         'cards.batch-params'),
}

##  --------------------------------------------------------------------------------------------------
##  batch_id:   [ID ТЗ ???] BatchList_tb.TID, PersBatchList_tb.BatchID WEB_Batches_vw.BatchID (BatchID)
##  pers_id:    [ID партии] PersBatchList_tb.TID, WEB_Batches_vw.TID (PersBatchID)
##  --------------------------------------------------------------------------------------------------

def before(f):
    def wrapper(**kw):
        name = kw.get('engine') or 'cards'
        g.engine = DatabaseEngine(name=name, user=g.current_user, connection=CONNECTION[name])
        return f(**kw)
    return wrapper

@before
def refresh(**kw):
    g.requested_batch = {}

    pers_id = kw.get('pers_id')
    if pers_id is None:
        return

    g.requested_batch = _get_batch(pers_id).copy()

def getBatchInfo(pers_id):
    #getDate(g.requested_batch.get('StatusDate'), UTC_EASY_TIMESTAMP)
    #g.requested_batch.get('FName')
    return 'ID [%s-%s]' % (pers_id, g.requested_batch.get('BatchID') or 0)

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
            'client'     : ('Client', get_request_item('client') or ''),
            'filename'   : ('FName', get_request_item('filename') or ''),
            'status'     : ('StatusID', int(get_request_item('status') or '0')),
            'persstatus' : ('PersStatus', get_request_item('persstatus') or ''),
            'perstype'   : ('PersTypeID', int(get_request_item('perstype') or '0')),
            'date_from'  : ('StatusDate', get_request_item('date_from') or ''),
            'date_to'    : ('StatusDate', get_request_item('date_to') or ''),
            'pan'        : ('PAN', get_request_item('pan') or ''),
            'id'         : ('TID', int(get_request_item('_id') or '0')),
        })
    except:
        args.update({
            'client'     : ('Client', ''),
            'filename'   : ('FName', ''),
            'status'     : ('StatusID', 0),
            'persstatus' : ('PersStatus', ''),
            'perstype'   : ('PersTypeID', 0),
            'date_from'  : ('StatusDate', ''),
            'date_to'    : ('StatusDate', ''),
            'pan'        : ('PAN', ''),
            'id'         : ('TID', 0),
        })
        flash('Please, update the page by Ctrl-F5!')

    return args

def _get_batch(id):
    columns = database_config[default_template].get('export')
    where = 'TID=%s' % id
    encode_columns = ('Client','FName','PersType','Status','PersStatus',)
    cursor = g.engine.runQuery(default_template, columns=columns, top=1, where=where, as_dict=True, encode_columns=encode_columns)
    return cursor and cursor[0] or {}

def _get_batch_ids(pers_ids):
    where = 'TID in (%s)' % makeIDList(pers_ids)
    cursor = g.engine.runQuery(default_template, where=where, columns=('BatchID',))
    return cursor and [row[0] for row in cursor] or []

def _get_bankperso_batches(ids=None, file_id=None, **kw):
    batchtype_id = ','.join([str(x) for x in kw.get('batchtype_id') or (7,14)])
    if file_id is not None:
        where = 'BatchTypeID in (%s) AND FileID=%s' % (batchtype_id, file_id)
    elif ids:
        where = 'TZ in (%s) AND BatchTypeID in (%s) AND FileStatusID not in (%s)' % (
            makeIDList(ids), batchtype_id, makeIDList(COMPLETE_STATUSES))
    else:
        return []

    cursor = g.engine.runQuery('batches', where=where, order='TID desc', as_dict=True, 
                             encode_columns=('Status',),
                             columns=database_config['batches'].get('export'))
    return cursor or []

def _get_client(id):
    return id and g.engine.getReferenceID(default_template, key='TID', value=id, tid='Client') or None

def _get_opers(pers_id, **kw):
    opers = []
    oper_id = kw.get('oper_id') or None
    pers_tz = kw.get('pers_tz') or None
    selected_id = None

    is_simple = kw.get('is_simple') and True or False

    where = 'PersBatchID=%s' % pers_id

    cursor = g.engine.runQuery('cards.pers-batch-opers', where=where, order='PersOperTypeID', as_dict=True,
                             encode_columns=('Status',))
    if cursor:
        is_selected = False
        
        for n, row in enumerate(cursor):
            if is_simple:
                pass
            else:
                row['StatusDate'] = getDate(row['StatusDate'], DEFAULT_DATETIME_INLINE_FORMAT)
                row['Ready'] = 'обработка завершена' in row['Status'] and True or False
                row['Found'] = pers_tz and row['TID'] == pers_tz
                row['id'] = row['TID']

                if (oper_id and oper_id == row['TID']):
                    row['selected'] = 'selected'
                    selected_id = oper_id
                    is_selected = True
                else:
                    row['selected'] = ''

            opers.append(row)

        if not is_simple and not is_selected:
            row = opers[0]
            selected_id = row['id']
            row['selected'] = 'selected'

    if is_simple:
        return opers

    return opers, selected_id

def _get_batchstatuses(id, order='StatusID'):
    statuses = []

    cursor = g.engine.runQuery('cards.batch-statuses', where='TID=%s' % id, order=order, as_dict=True)
    if cursor:
        for n, row in enumerate(cursor):
            statuses.append(row['StatusID'])

    return statuses

def _get_logs(batch_id):
    view = 'cards.batches-log'
    logs = []

    cursor = g.engine.runQuery(view, where='BatchID=%s' % batch_id, order='LID', as_dict=True)
    if cursor:
        for n, row in enumerate(cursor):
            row['id'] = row['LID']
            row['Status'] = row['Status'].encode(default_iso).decode(default_encoding)
            row['StatusDate'] = getDate(row['StatusDate'], DEFAULT_DATETIME_INLINE_FORMAT)
            row['ModDate'] = getDate(row['ModDate'], DEFAULT_DATETIME_INLINE_FORMAT)

            logs.append(row)

    return logs

def _get_oper_logs(pers_id):
    view = 'cards.batch-opers-log'
    logs = []

    cursor = g.engine.runQuery(view, where='PersBatchID=%s' % pers_id, order='LID', as_dict=True)
    if cursor:
        for n, row in enumerate(cursor):
            row['id'] = row['LID']
            row['Status'] = row['Status'].encode(default_iso).decode(default_encoding)
            row['StatusDate'] = getDate(row['StatusDate'], DEFAULT_DATETIME_INLINE_FORMAT)
            row['ModDate'] = getDate(row['ModDate'], DEFAULT_DATETIME_INLINE_FORMAT)

            logs.append(row)

    return logs

def _get_units(batch_id):
    view = 'cards.batch-units'
    units = []

    cursor = g.engine.runQuery(view, where='BatchID=%s' % batch_id, order='TID', as_dict=True)
    if cursor:
        for n, row in enumerate(cursor):
            row['id'] = row['TID']
            row['PAN'] = getMaskedPAN(row['PAN'])
            row['Status'] = row['Status'].encode(default_iso).decode(default_encoding)
            row['StatusDate'] = getDate(row['StatusDate'], DEFAULT_DATETIME_INLINE_FORMAT)

            units.append(row)

    return units

def _get_params(batch_id, **kw):
    view = 'cards.batch-params'
    params = []

    where = kw.get('where') or ('BatchID=%s' % batch_id)

    cursor = g.engine.runQuery(view, where=where, order='PType', as_dict=True)
    if cursor:
        for n, row in enumerate(cursor):
            row['id'] = row['TID']
            row['PName'] = row['PName'].encode(default_iso).decode(default_encoding)
            row['PValue'] = row['PValue'].encode(default_iso).decode(default_encoding)

            params.append(row)

    return params

def _get_top(per_page, page):
    if g.system_config.IsApplyOffset:
        top = per_page
    else:
        top = per_page * page
    offset = page > 1 and (page - 1) * per_page or 0
    return top, offset

## ==================================================== ##

def getTabOperParams(pers_id, oper_id):
    """
        Get Oper Parameters list.

        Arguments:
            pers_id  -- ID ТЗ персонализации
            oper_id  -- ID операции
        
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
                           'id'     -- ID партии
                           'number' -- номер ТЗ
                           'name'   -- название типа партии
                           'no'     -- кол-во карт в партии
                           'file'   -- имя файла-заказа
                           'cards'  -- кол-во карт в файле
                        }
    """
    data = []
    props = {'id' : oper_id}

    try:
        if pers_id and oper_id:
            where = 'TID=%s' % oper_id
            cursor = g.engine.runQuery('cards.pers-batch-opers', columns=('PersOperTypeID',), top=1, where=where)
            oper_type_id = cursor[0][0] if cursor is not None and len(cursor) else None

            if oper_type_id is not None:
                where = 'PersBatchID=%s AND BatchOperTypeID=%s' % (pers_id, oper_type_id)
                cursor = g.engine.runQuery('cards.batch-oper-params', where=where, as_dict=True)

                for n, row in enumerate(cursor):
                    try:
                        row['PName'] = row['PName'].encode(default_iso).decode(default_encoding)
                        row['PValue'] = row['PValue'].encode(default_iso).decode(default_encoding)
                        row['PSortIndex'] = 0
                        row['PType'] = 1
                        row['class_name'] = ''

                        data.append(row)
                    except:
                        print_exception()

            # -------------------
            # Информация о партии
            # -------------------

            where = 'TID=%s' % pers_id
            encode_columns = ('PersType',)

            cursor = g.engine.runQuery(default_template, top=1, where=where, as_dict=True, encode_columns=encode_columns)
            if cursor:
                row = cursor[0]
                if row:
                    number = row['TZ']
                    props.update({
                        'number' : number,
                        'name'   : row['PersType'],
                        'no'     : row['PQty'],
                        'file'   : row['FName'],
                        'cards'  : row['BQty'],
                    })

    except:
        print_exception()

    return data or [], props

def getTabLogs(batch_id):
    return _get_logs(batch_id)

def getTabOperLogs(pers_id):
    return _get_oper_logs(pers_id)

def getTabUnits(batch_id):
    return _get_units(batch_id)

def getTabParams(batch_id):
    return _get_params(batch_id)

def getFileBatches(pers_id=None):
    """
        Returns `PersBatchID` list for the file selected by requested batch (pers_id).
        Note: Check existing of `IDX_BatchList_OrderFName` index.
    """
    if pers_id is not None:
        filename = _get_batch(pers_id).get('FName')
    else:
        filename = g.requested_batch.get('FName')

    PERS_STATUS_RUN = 'обработка не начиналась'

    where = "FName='%s'" % (filename or '')
    cursor = g.engine.runQuery(default_template, where=where, columns=('TID', 'PersStatus',), encode_columns=('PersStatus',), as_dict=True)
    data = cursor and [row['TID'] for row in cursor if row['PersStatus'] == PERS_STATUS_RUN] or []

    filename = filename.split()[0]

    props = {'file_id' : g.engine.getReferenceID('orders', key='FName', value=filename, tid='FileID') or ''}

    return data, props

def activateBatches(pers_ids, params=None):
    """
        Check & Activate selected Batches.

        Arguments:
            pers_ids -- List, Selected `PersBatchID` pers_ids to activate (String)
            file_id  -- Int, params:file id to check batches for a file entirely
        
        Returns:
            data     -- List, Stored procedures response+Batches paramaters list:
                        [view1, view2, ...], 
                        
                <0,1,...> -- List (mapped list), view (response) values: 
                        
                        {<column1> : <value>, <column2> : <value>, ...}

            props    -- Dict, Response info, 
            
                <key>     -- Dict, `view` (stored procedure) name: 
                        {
                            'index'   -- Int, data list view index
                            'columns' -- List, view columns list
                        }

            Other Keywords in `props`:

                `batches` -- Dict, selected batches from default_template: 
                
                        {<pers_id> : <batch>, ...}

                `params`  -- Tuple, parameters list by `batch_id`:
                
                        {<batch_id> : ((<PName>, <PValue>), ...), ...}

                `opers`   -- Tuple, parameters list by `pers_id`:
                
                        {<pers_id> : ((<Oper>,), ...), ...}

            errors   -- List, Errors list: ['error', ...], sorted by error code: 2,1,0.
    """
    file_id = params and isinstance(params, dict) and params.get('file_id') or None
    
    data = []
    props = {}
    errors = []

    ids = sorted([int(x) for x in pers_ids])

    rfname = re.compile(r'(\([\d]+\s*шт\))', re.I+re.DOTALL)
    rbin = re.compile(r'.*?БИН\s*?(\d{6}).*?', re.I+re.DOTALL)
    views = ('cards.plastic-params', 'cards.plastic-params-new',)
    sql_params = {'pers_ids' : makeIDList(pers_ids)}
    batch_ids = _get_batch_ids(ids)

    _INDEX = 1
    _ENCODED = 3
    _DEFAULT_VALUE = 4
    _CONFIRMED_ERROR = 3
    _UNDEFINED_ERROR = 2
    _ERROR = 1
    _WARNING = 0

    dbconfig = None
    params = fields = columns = encode_columns = None

    IsError = 0

    check_params = {}
    sumQty = sumQtyControl = 0
    responses = None
    total_cards = ''
    has_mir = False

    def _get_query_params():
        params = dbconfig['params'] % sql_params
        fields = dbconfig['fields']
        columns = [x[0] for x in sorted(fields.items(), key=itemgetter(_INDEX))]
        encode_columns = [x for x in columns if fields[x][_ENCODED]]
        return params, fields, columns, encode_columns

    def _get_items(cursor):
        items = []
        for n, row in enumerate(cursor):
            for column in columns:
                if row[column] is None:
                    row[column] = fields[column][_DEFAULT_VALUE]
            items.append(row)
        return items

    def _is_param_valid(row, param):
        name, id, error = param.split(':')
        if not id in row:
            errors.append((_WARNING, gettext('Warning: Missing parameter:') + id,))
            return False
        elif check_params.get(name):
            if row[id] != check_params[name]:
                errors.append((_ERROR, gettext('Error: %s.' % error),))
                return False
        elif not row[id]:
            errors.append((_WARNING, gettext('Warning: Parameter is empty:') + id,))
            return False
        else:
            check_params[name] = row[id]
        return True

    try:
        indexes = []

        # ------------------------
        # Get Batch view responses
        # ------------------------

        for index, view in enumerate(views):
            dbconfig = database_config[view]
            params, fields, columns, encode_columns = _get_query_params()

            items = _get_items(g.engine.runQuery(
                    view,
                    columns=columns,
                    params=params,
                    encode_columns=encode_columns,
                    as_dict=True,
                    top=1,
                ))

            if 'BatchesInfo' in columns:
                pass

            data.append(items)

            props[view] = {
                'index'   : index,
                'columns' : columns,
            }

            indexes.append(index)

        # ---------------------
        # Get Batches Info list
        # ---------------------

        cursor = g.engine.runQuery(default_template, 
                                 columns=database_config[default_template].get('export'), 
                                 where='TID in (%s)' % sql_params['pers_ids'], 
                                 order='TID', 
                                 encode_columns=('Client','FName','PersType','Status','PersStatus',),
                                 as_dict=True,
                                 )

        batches = cursor and dict(zip([int(id) for id in ids], cursor)) or {}

        props['batches'] = batches

        # ---------------
        # Get Params list
        # ---------------
        
        params = {}

        for batch_id in batch_ids:
            params[batch_id] = tuple([(x['PName'], x['PValue']) for x in _get_params(batch_id)])

        props['params'] = params

        # --------------
        # Get Opers list
        # --------------
        
        opers = {}

        for id in ids:
            opers[id] = tuple([(x['Oper'],) for x in _get_opers(id, is_simple=1)])

        props['opers'] = opers

        # ---------------
        # Get Blanks list
        # ---------------

        blanks = []

        for i, row in enumerate(data[0]):
            batch_id = row['BatchID']

            name, blank = '', None
            for param in params[batch_id]:
                if param[0] == 'Бланк листовки':
                    name, blank = param[0], param[1]
                    break

            if not blank:
                continue

            # -----------------------------
            # Check Batch ID (TZ) in BankDB
            # -----------------------------

            PersoTZ, TZ = None, row['SysBatchID']

            try:
                exec_params = {'tz' : TZ, 'batchtype_id' : 10, 'param_name' : name}
                cursor = g.engine.runQuery('search.batch_by_param', exec_params=exec_params, as_dict=True)
                PersoTZ = cursor and cursor[0].get('PERS_TZ') or None
            except:
                pass

            blanks.append({
                'SysBatchID'  : PersoTZ or TZ,
                'PersBatchID' : row['PersBatchID'],
                'BQty'        : row['BQty'],
                'Blank'       : blank,
            })

        props['blanks'] = blanks

        # ----------
        # Check data
        # ----------

        responses = len(indexes) == len(views) and data[0:len(indexes)] or None

        if not responses or len(list(filter(None, responses))) < len(responses):
            errors.append((_UNDEFINED_ERROR, gettext('Error: Empty or missed responses list.'),))
            IsError = 1
            raise 1

        total_bankperso_batches = len(_get_bankperso_batches(file_id=file_id))

        if IsLocalDebug:

            # -----------------------------
            # Local Debug Data Construction
            # -----------------------------

            for n, response in enumerate(responses):
                for i, row in enumerate(response):
                    if n == 0:
                        id = row['PersBatchID']
                        b = batches[id]

                        row['ClientName'] = b['Client']
                        row['FileName'] = b['FName']
                        row['FQty'] = b['PQty']
                        row['SumQty'] = b['PQty']
                        row['Urgency'] = 'Внимание! Тест!!!'
                        row['ReadyDate'] = getDate(b['StatusDate'], DEFAULT_DATETIME_READY_FORMAT)
                    else:
                        b = responses[0][i]

                        row['ClientName'] = b['ClientName']
                        row['FileName'] = b['FileName']
                        row['ReadyDate'] = b['ReadyDate']

        else:
            bankperso_batches = _get_bankperso_batches(ids=[x['SysBatchID'] for x in responses[0]])

            # -------------------------------
            # Validate BankPerso associations
            # -------------------------------

            if file_id and total_bankperso_batches > len(responses[0]):
                errors.append((_CONFIRMED_ERROR, gettext('Error: Not all batches selected to process the file.'),))
                #IsError = 1
                #raise 1

            if len(bankperso_batches) != len(responses[0]):
                errors.append((_UNDEFINED_ERROR, gettext('Error: Perhaps, processing of selected orders was finished.'),))
                IsError = 1
                raise 1

            # --------------------
            # Check Batch Statuses
            # --------------------

            status = None

            for batch in bankperso_batches:
                if not status:
                    status = batch['BatchStatusID']
                if status == batch['BatchStatusID']:
                    continue

                errors.append((_ERROR, gettext('Error: Selected batches with different status.'),))
                IsError = 1
                raise 1

        for n, response in enumerate(responses):
            for row in response:
                if n == 0:
                    if not (row['ClientName'] and row['FileName'] and row['FQty']):
                        errors.append((_UNDEFINED_ERROR, gettext('Error: Batch contains empty basic parameters:') + row['PersBatchID'],))
                        continue

                    if not _is_param_valid(row, 'client_id:ClientIDStr:Client ID is not unique'):
                        break
                    if not _is_param_valid(row, 'client_name:ClientName:Client name is not unique'):
                        break
                    if not _is_param_valid(row, 'filename:FileName:There were selected batches from a few Order files'):
                        break

                    if not row['ReadyDate'].strip():
                        row['ReadyDate'] = ' '*20;

                    if row['SumQty'] == 0:
                        errors.append((_ERROR, gettext('Error: Batch SumQty is zero.'),))
                    else:
                        sumQty += row['SumQty']

                else:
                    sumQtyControl += row['Qty']

        if sumQty < sumQtyControl or sumQtyControl == 0:
            errors.append((_UNDEFINED_ERROR, gettext('Error: Final sum of batches is unmatched.'),))

        if not check_params.get('client_name'):
            errors.append((_ERROR, gettext('Error: Client name is not present.'),))

        if not check_params.get('filename'):
            errors.append((_ERROR, gettext('Error: File name is not present.'),))

        # -------------------
        # Plastic type groups
        # -------------------
        
        group = ''
        
        for n, item in enumerate(responses[0]):
            x = '%s:%s:%s' % (item['CardsName'], item['CardsType'], item['PlasticType']) #
            if x != group:
                group = x
                item['rowspan'] = 1
                item['SumQty'] = item['BQty']
                rowspan = n
            else:
                responses[0][rowspan]['rowspan'] += 1
                item['CardsName'] = item['CardsType'] = item['PlasticType'] = ''

                responses[0][rowspan]['SumQty'] += item['BQty']

                item['SumQty'] = 0

        props['r1:rowspan'] = (1,2,3,9)

        # ---
        # BIN
        # ---
        """
        bins = []

        for row in responses[0]:
            bin = None

            if 'BIN' in row:
                bin = row['BIN']
            elif 'PlasticType' in row:
                plastic_type = row['PlasticType']
                m = rbin.match(plastic_type)
                if m:
                    bin = m.groups()[0]

            if bin:
                bins.append((bin, row.get('FQty'),))
        """
        bins = {}

        total_mir_batches = 0
        total_mir_cards = 0
        total_cards = 0

        for batch_id in batch_ids:
            units = _get_units(batch_id)

            with_mir = False

            for unit in units:
                bin = unit['PAN'][0:4]
                if bin not in bins:
                    bins[bin] = 0
                bins[bin] += 1

                if bin.startswith('2'):
                    total_mir_cards += 1
                    with_mir = True

                total_cards += 1

            if with_mir:
                total_mir_batches += 1

        bins = bins.items()

        # ---------
        # Check МИР
        # ---------

        has_mir = sum([x for bin, x in bins if bin.startswith('2')]) > 0 and True or False

        # -------------------
        # Total Batches/Cards
        # -------------------

        total_batches = len(props['batches'].keys())

        if total_bankperso_batches == total_batches and total_cards == sumQtyControl:
            total_cards = [
                '%s/%s' % (total_batches, total_cards),
                total_mir_batches > 0 and ('%s/%s' % (total_mir_batches, total_mir_cards)) or '',
            ]
        else:
            total_cards = ['', '']

        if responses:
            b = responses[0][0]

            filename = b['FileName'].strip()
            m = rfname.search(filename)
            if m is None:
                filename = '%s (%s шт)' % (filename, b['FQty'])

            props.update({
                'has_mir'      : has_mir,
                'has_protocol' : sumQtyControl > 10 and True or False,
                'ids'          : ids,
                'ClientName'   : b['ClientName'],
                'FileName'     : filename,
                'ReadyDate'    : b['ReadyDate'],
                'Total'        : sumQtyControl, #sumQty XXX !
                'Now'          : getDate(getToday(), LOCAL_EXCEL_TIMESTAMP),
                'Today'        : getDate(getToday(), DEFAULT_DATETIME_TODAY_FORMAT),
                'TotalCards'   : total_cards,
                'show'         : 0,
            })

    except:
        if IsError:
            pass
        elif IsPrintExceptions:
            print_exception()

        print_to(None, repr(responses))

    confirms = [x[1] for x in sorted(errors, key=itemgetter(0), reverse=True) if x[0] == _CONFIRMED_ERROR]

    errors = [x[1] for x in sorted(errors, key=itemgetter(0), reverse=True) if x[0] < _CONFIRMED_ERROR]

    return responses, props, errors, confirms

## ==================================================== ##

def _make_response_name(name=None):
    return '%s-%s' % (getDate(getToday(), LOCAL_EXPORT_TIMESTAMP), name or 'cards')

def _make_xls_content(rows, title, name=None):
    xls = makeXLSContent(rows, title, True)
    response = make_response(xls)
    response.headers["Content-Disposition"] = "attachment; filename=%s.xls" % _make_response_name(name)
    return response

def _make_page_default(kw):
    pers_id = int(kw.get('pers_id'))
    oper_id = int(kw.get('oper_id'))

    is_admin = g.current_user.is_administrator()

    args = _get_page_args()

    file_name = ''
    filter = ''
    qs = ''

    # -------------------------------
    # Представление БД (default_view)
    # -------------------------------

    default_view = database_config[default_template]

    # ---------------------------------------------
    # Поиск номера ТЗ в списке партий (pers_tz)
    # ---------------------------------------------

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
    TZ = None

    # -----------------------------------------------
    # Поиск ID партии, номера ТЗ (search is a number)
    # -----------------------------------------------

    if search:
        try:
            TID = BatchID = TZ = int(search)
            items.append('(TID=%s OR BatchID=%s OR TZ=%s)' % (TID, BatchID, TZ))
            is_search_batch = True
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

    Client = args['client'][1]
    StatusID = args['status'][1]
    PersTypeID = args['perstype'][1]
    PAN = args['pan'][1]

    StatusDate = None

    if args:
        for key in args:
            if key in (EXTRA_,):
                continue
            name, value = args[key]
            if value:
                if key in ('...'):
                    pass
                elif key == 'pan':
                    view = database_config[_views['units'][3]]['view'] # '[Cards].[dbo].[BatchUnits_tb]'
                    v = ' or '.join(["PAN like '%s'" % re.sub(r'[*]+', r'%%', x) for x in value.split(';')])
                    x = 'BatchID in (select distinct BatchID from %s where %s)' % (view, v)
                    items.append(x)
                elif key == 'date_from':
                    if checkDate(value, DEFAULT_DATE_FORMAT[1]):
                        items.append("%s >= '%s 00:00'" % (name, value))
                        StatusDate = value
                    else:
                        args['date_from'][1] = ''
                        continue
                elif key == 'date_to':
                    if checkDate(value, DEFAULT_DATE_FORMAT[1]):
                        items.append("%s <= '%s 23:59'" % (name, value))
                    else:
                        args['date_to'][1] = ''
                        continue
                elif key in ('id', 'perstype', 'status',):
                    items.append("%s=%s" % (name, value))
                elif key in ('client', 'persstatus',):
                    items.append("%s='%s'" % (name, value))
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
        order = 'TID'

    if current_sort in (0,3,4,5,9,10):
        order += " desc"

    if IsDebug:
        print('--> where:[%s] order:[%s], args: %s' % (where, order, args))

    pages = 0
    total_pers = 0
    total_cards = 0
    batches = []
    opers = []
    clients = []
    filenames = []
    statuses = []
    persstatuses = []
    perstypes = []
    xml = ''

    # ----------------------
    # Условие отбора (state)
    # ----------------------

    state = get_request_item('state')
    is_state = state and state != 'R0' and True or False

    args.update({
        'state' : ('State', state)
    })

    confirmed_pers_id = 0

    # ======================
    # Выборка данных журнала
    # ======================

    if g.engine != None:

        # ---------------------------------------------------
        # Поиск партии по ID или номеру ТЗ (is_search_batch)
        # ---------------------------------------------------
        
        if is_search_batch:
            pers_id = 0

            cursor = g.engine.runQuery('cards.pers-batch-opers', columns=('PersBatchID',), where='TID=%s' % TZ, top=1)
            for n, row in enumerate(cursor):
                pers_id = row[0]

            if not pers_id:
                cursor = g.engine.runQuery(default_template, columns=('TID',), where=where)
                for n, row in enumerate(cursor):
                    pers_id = row[0]

            where = 'TID=%s' % pers_id

        # ------------------------------------------------
        # Кол-во записей по запросу в журнале (total_pers)
        # ------------------------------------------------

        cursor = g.engine.runQuery(default_template, columns=('count(*)', 'sum(BQty)',), where=where, no_traceback=True)
        if cursor:
            total_pers, total_cards = cursor[0]
            if total_cards is None:
                total_cards = 0

        if is_state:
            top, offset = 1000, None
        if command == 'export':
            top = 10000

        # ================
        # Заказы (batches)
        # ================

        cursor = g.engine.runQuery(default_template, top=top, offset=offset, where=where, order='%s' % order, as_dict=True,
                                 encode_columns=('Client','FName','PersType','Status','PersStatus',),
                                 columns=database_config[default_template].get('export'))
        if cursor:
            is_selected = False
            
            for n, row in enumerate(cursor):
                #if not is_state and offset and n < offset:
                #    continue

                x = row['Status'].lower()

                state_error = 'брак' in x
                state_ready = 'отправлен отчет' in x

                if state == 'R1' and (state_ready or state_error):
                    continue
                if state == 'R2' and not state_ready:
                    continue
                if state == 'R3' and not state_error:
                    continue

                if pers_id:
                    if not confirmed_pers_id and pers_id == row['TID']:
                        confirmed_pers_id = pers_id
                    if not file_name and pers_id == row['TID']:
                        file_name = row['FName']

                    if pers_id == row['TID']:
                        row['selected'] = 'selected'
                        is_selected = True
                else:
                    row['selected'] = ''

                row['TZ'] = row['TZ'] and '<a class="persolink" href="/bankperso?sidebar=0&search=%s" target="_self">%s</a>' % (
                    row['TZ'], row['TZ']) or ''

                for x in row:
                    if not row[x] or str(row[x]).lower() == 'none':
                        row[x] = ''

                row['Error'] = state_error
                row['Ready'] = state_ready
                row['StatusDate'] = getDate(row['StatusDate'])
                row['BQty'] = str(row['BQty']).isdigit() and int(row['BQty']) or 0
                row['PQty'] = str(row['PQty']).isdigit() and int(row['PQty']) or 0
                row['id'] = row['TID']

                batches.append(row)

            if line > len(batches):
                line = 1

            if not is_selected and len(batches) >= line:
                row = batches[line-1]
                confirmed_pers_id = pers_id = row['id'] = row['TID']
                file_name = row['FName']
                row['selected'] = 'selected'

        if len(batches) == 0:
            file_name = ''
            pers_id = 0
        elif confirmed_pers_id != pers_id or not pers_id:
            row = batches[0]
            pers_id = row['TID']
            file_name = row['FName']
        elif not confirmed_pers_id:
            pers_id = 0
            file_name = ''

        if is_state and batches:
            total_pers = len(batches)
            total_cards = 0
            batches = batches[offset:offset+per_page]
            is_selected = False

            for n, row in enumerate(batches):
                if pers_id == row['TID']:
                    row['selected'] = 'selected'
                    file_name = row['FName']
                    is_selected = True
                else:
                    row['selected'] = ''
                total_cards += row['BQty']

            if not is_selected:
                row = batches[0]
                row['selected'] = 'selected'
                pers_id = row['TID']
                file_name = row['FName']

        if total_pers:
            pages = int(total_pers / per_page)
            if pages * per_page < total_pers:
                pages += 1

        # ================
        # Операции (opers)
        # ================

        if pers_id:
            opers, oper_id = _get_opers(pers_id, oper_id=oper_id, pers_tz=pers_tz, perstype=PersTypeID)

        # ----------------------------------------------------------------
        # Справочники фильтра запросов (clients, perstypes, statuses)
        # ----------------------------------------------------------------

        clients.append(DEFAULT_UNDEFINED)
        cursor = g.engine.runQuery('cards.clients', order='Client', distinct=True, encode_columns=(0,))
        clients += [x[0] for x in cursor]
        """
        filenames.append(DEFAULT_UNDEFINED)
        items = []
        if Client:
            items.append("Client='%s'" % Client)
        if StatusDate:
            items.append("StatusDate>='%s'" % getDate(getDate(StatusDate, LOCAL_EASY_DATESTAMP, is_date=True), DATE_STAMP))
        where = ' AND '.join(items)
        cursor = g.engine.runQuery('cards.files', columns=('FileName',), where=where, order='FileName', encode_columns=(0,))
        filenames += [x[0] for x in cursor]
        """
        statuses.append((0, DEFAULT_UNDEFINED,))
        cursor = g.engine.runQuery('cards.statuses', order='CName', distinct=True, encode_columns=(1,))
        statuses += [(x[0], x[1]) for x in cursor]

        persstatuses.append(DEFAULT_UNDEFINED)
        cursor = g.engine.runQuery('cards.persstatuses', order='CName', encode_columns=(0,))
        persstatuses += [x[0] for x in cursor]

        perstypes.append((0, DEFAULT_UNDEFINED,))
        cursor = g.engine.runQuery('cards.perstypes', order='CName', distinct=True, encode_columns=(1,))
        perstypes += [(x[0], x[1]) for x in cursor]

        g.engine.dispose()

    # ----------------------
    # Условия отбора заказов
    # ----------------------

    states = [
        ('R0', DEFAULT_UNDEFINED),
        ('R1', 'первичная'),
        ('R2', 'брак'),
    ]

    refresh(pers_id=pers_id)

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
    base = 'cards?%s' % query_string

    per_page_options = (5, 10, 20, 30, 40, 50, 100,)
    if is_admin:
        per_page_options += (250, 500)

    is_extra = has_request_item(EXTRA_)

    modes = [(n, '%s' % default_view['headers'][x][0]) for n, x in enumerate(default_view['columns'])]
    sorted_by = default_view['headers'][default_view['columns'][current_sort]]

    pagination = {
        'total'             : '%s / %s' % (total_pers, total_cards),
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
    }

    loader = '/cards/loader'

    if is_extra:
        pagination['extra'] = 1
        loader += '?%s' % EXTRA_

    kw.update({
        'base'              : base,
        'page_title'        : gettext('WebPerso Cards Batch View'),
        'header_subclass'   : 'left-header',
        'show_flash'        : True,
        'model'             : 0,
        'loader'            : loader,
        'semaphore'         : initDefaultSemaphore(template='cards.semaphore'),
        'args'              : args,
        'current_file'      : (pers_id, getBatchInfo(pers_id), oper_id, pers_tz),
        'navigation'        : get_navigation(),
        'config'            : database_config,
        'pagination'        : pagination,
        'batches'           : batches,
        'opers'             : opers,
        'clients'           : clients,
        'filenames'         : filenames,
        'statuses'          : statuses,
        'persstatuses'      : persstatuses,
        'perstypes'         : perstypes,
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

@cards.route('/cards', methods = ['GET','POST'])
@login_required
def start():
    try:
        return index()
    except:
        raise

def index():
    debug, kw = init_response('WebPerso Cards Admin Page')
    kw['product_version'] = product_version

    is_admin = g.current_user.is_administrator()
    is_operator = g.current_user.is_operator()

    command = get_request_item('command')
    
    pers_id = int(get_request_item('pers_id') or '0')
    oper_id = int(get_request_item('oper_id') or '0')

    if IsDebug:
        print('--> command:%s, pers_id:%s, oper_id:%s' % (command, pers_id, oper_id))

    refresh(pers_id=pers_id)

    IsMakePageDefault = True
    logsearch = ''
    tagsearch = ''
    info = ''

    errors = []

    if command and command.startswith('admin'):
        command = command.split(DEFAULT_HTML_SPLITTER)[1]

        if get_request_item('OK') != 'run':
            command = ''

        elif not is_operator:
            flash('You have not permission to run this action!')
            command = ''
        
        elif command == 'activate':
            selected_pers_ids = get_request_item('selected_pers_ids') or ''
            info = 'selected_pers_ids:%s' % selected_pers_ids

            # -------------------------
            # Activate selected batches
            # -------------------------

            for pers_id in selected_pers_ids.split(DEFAULT_HTML_SPLITTER):
                rows, error_msg = g.engine.runProcedure('cards.activate', pers_id=pers_id, no_cursor=True, with_error=True)

                if error_msg:
                    errors.append(error_msg)

        elif command == 'reject':
            selected_pers_ids = get_request_item('selected_pers_ids') or ''
            info = 'selected_pers_ids:%s' % selected_pers_ids

            # --------------------------------------
            # Reject activation for selected batches
            # --------------------------------------

            for pers_id in selected_pers_ids.split(DEFAULT_HTML_SPLITTER):
                rows, error_msg = g.engine.runProcedure('cards.reject', pers_id=pers_id, no_cursor=True, with_error=True)

                if error_msg:
                    errors.append(error_msg)

        if IsDebug:
            print('--> %s' % info)

        if IsTrace:
            print_to(errorlog, '--> command:%s %s [%s]' % (command, g.current_user.login, info))

    kw['errors'] = '<br>'.join(errors)
    kw['OK'] = ''

    try:
        if IsMakePageDefault:
            kw = _make_page_default(kw)

        if IsTrace:
            print_to(errorlog, '--> cards:%s %s [%s:%s] %s %s' % ( 
                     command, g.current_user.login, request.remote_addr, kw.get('browser_info'), str(kw.get('current_file')), info,), 
                     request=request)
    except:
        print_exception()

    kw['vsc'] = vsc(force=g.system_config.IsForceRefresh)

    if command:
        is_extra = has_request_item(EXTRA_)

        if not command.strip():
            pass

        elif command == 'activate':
            if kw['errors']:
                flash('Batch activation done with errors!')
            else:
                kw['OK'] = gettext('Message: Activation is perfomed successfully.')

        elif command == 'reject':
            if kw['errors']:
                flash('Reject for the given batch is not done!')
            else:
                kw['OK'] = gettext('Message: Reject performed successfully.')

        elif command == 'export':
            return _make_xls_content(_make_export(kw), 'Журнал персонализации')

    return make_response(render_template('cards.html', debug=debug, **kw))

@cards.after_request
def make_response_no_cached(response):
    if g.engine is not None:
        g.engine.close()
    # response.cache_control.no_store = True
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response

@cards.route('/cards/loader', methods = ['GET', 'POST'])
@login_required
def loader():
    exchange_error = ''
    exchange_message = ''

    is_extra = has_request_item(EXTRA_)

    action = get_request_item('action') or default_action
    selected_menu_action = get_request_item('selected_menu_action') or action != default_action and action or '701'

    response = {}

    pers_id = int(get_request_item('pers_id') or '0')
    oper_id = int(get_request_item('oper_id') or '0')
    perstype = int(get_request_item('perstype') or '0')

    refresh(pers_id=pers_id)

    params = get_request_item('params') or ''

    if IsDebug:
        print('--> action:%s pers_id:%s oper_id:%s perstype:%s params:%s' % (
            action, pers_id, oper_id, perstype, params
        ))

    if IsTrace:
        print_to(errorlog, '--> loader:%s %s [%s:%s:%s:%s]%s' % (
            action, g.current_user.login, pers_id, oper_id, perstype, selected_menu_action,
            params and (' params:%s' % reprSortedDict(params, is_sort=True)) or ''
        ))

    batch_id = g.requested_batch and g.requested_batch['BatchID'] or None

    currentfile = None
    opers = []
    config = None

    data = ''
    number = ''
    columns = []
    total = None
    status = ''
    path = ''

    props = None
    errors = None
    confirms = None

    try:
        if action == default_action:
            opers, oper_id = _get_opers(pers_id, perstype=perstype)
            currentfile = [g.requested_batch.get('TID'), getBatchInfo(pers_id), oper_id]
            config = _get_view_columns(database_config['cards.pers-batch-opers'])
            action = selected_menu_action

        if not action:
            pass

        elif action == '701':
            data, props = getTabOperParams(pers_id, oper_id)

        elif action == '702':
            view = database_config['cards.batch-opers-log']
            columns = _get_view_columns(view)
            data = getTabOperLogs(pers_id)

        elif action == '703':
            view = database_config['cards.batch-units']
            columns = _get_view_columns(view)
            data = getTabUnits(batch_id)

        elif action == '704':
            view = database_config['cards.batch-params']
            columns = _get_view_columns(view)
            data = getTabParams(batch_id)

        elif action == '705':
            data, props = getFileBatches()

        elif action in '710':
            items = get_request_item('selected-items').split(':') or []

            if IsTrace:
                print_to(errorlog, '--> activate items:%s' % items)

            currentfile = [g.requested_batch.get('TID'), getBatchInfo(pers_id), oper_id]
            data, props, errors, confirms = activateBatches(items, params)

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
        'pers_id'          : pers_id,
        'oper_id'          : oper_id,
        # ----------------------------------------------
        # Default Lines List (sublines equal as opers)
        # ----------------------------------------------
        'currentfile'      : currentfile,
        'sublines'         : opers,
        'config'           : config,
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
        'confirms'         : confirms,
    })

    return jsonify(response)

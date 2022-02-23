# -*- coding: utf-8 -*-

import re
import random

from config import (
     CONNECTION, 
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, LocalDebug, 
     errorlog, print_to, print_exception,
     default_unicode, default_encoding, default_iso
     )

from . import configurator

from ..settings import *
from ..database import database_config, DatabaseEngine
from ..utils import (
     getToday, getDate, checkDate, indentXMLTree, isIterable, makeXLSContent,
     getWhereFilter, checkPaginationRange,
     sortedDict, reprSortedDict, makeSqlWhere, make_config
     )

from ..semaphore.views import initDefaultSemaphore

from .references import *
from .generator import FileTypeSettingsGenerator

##  ======================================
##  Configurator View Presentation Package
##  ======================================

default_page = 'configurator'
default_action = '600'
default_template = 'configurator-files-default'

# Локальный отладчик
IsLocalDebug = LocalDebug[default_page]
# Использовать OFFSET в SQL запросах
IsApplyOffset = 1
# Принудительная загрузка статических файлов
IsForceRefresh = 0

_views = {
    'files'     : 'configurator-files',
    'batches'   : 'configurator-batches',
}


def before(f):
    def wrapper(**kw):
        name = kw.get('engine') or 'configurator'
        g.engine = DatabaseEngine(name=name, user=g.current_user, connection=CONNECTION[name])
        return f(**kw)
    return wrapper

@before
def refresh(**kw):
    g.requested_object = {}

    file_id = kw.get('file_id')
    if file_id is None:
        return
    
    g.requested_object = _get_file(file_id).copy()

def requested_file_type_id():
    return g.requested_object.get('TID')

def _get_columns(name):
    return ','.join(database_config[name]['columns'])

def _get_view_columns(view):
    columns = []
    for name in view['columns']:
        columns.append({
            'name'   : name,
            'header' : view['headers'].get(name) or '',
        })
    return columns

def _get_page_args():
    args = {}

    if has_request_item(EXTRA_):
        args[EXTRA_] = (EXTRA_, None)

    try:
        args = { \
            'client'    : ('ClientID', int(get_request_item('client') or '0')),
            'filetype'  : ('FileTypeID', int(get_request_item('filetype') or '0')),
            'batchtype' : ('BatchTypeID', int(get_request_item('batchtype') or '0')),
            'tag'       : ('TName', get_request_item('tag')),
            'tagvalue'  : ('TValue', get_request_item('tagvalue')),
        }
    except:
        args = { \
            'client'    : ('ClientID', 0),
            'filetype'  : ('FileTypeID', 0),
            'batchtype' : ('BatchTypeID', 0),
            'tag'       : ('TName', ''),
            'tagvalue'  : ('TValue', ''),
        }
        flash('Please, update the page by Ctrl-F5!')

    return args

def _load_params(params):
    command, mode, query, items, id, state = '', '', '', {}, None, None

    if isinstance(params, dict):
        command = params.get('command')
        mode = params.get('mode')
        query = params.get('query')
        items = params.get('items')
        id = params.get('id') or None
        state = params.get('state') or None
    else:
        x = params.split(DEFAULT_HTML_SPLITTER)
        command = x[0]
        mode = x[1]
        query = len(x) > 2 and x[2] or None
        items = len(x) > 3 and x[3] or None
        id = len(x) > 4 and x[4] or None
        state = len(x) > 5 and x[5] or None

    return command, mode, query, items, id, state

def _cursor_evaluate(view, columns, tid, where, order, encode_columns, with_selected):
    rows = []

    cursor = g.engine.runQuery(view, columns=columns, where=where, order=order, 
                             encode_columns=encode_columns,
                             as_dict=True,
                             )
    if cursor:
        selected_id = None

        for n, row in enumerate(cursor):
            if 'TID' in row:
                row['id'] = row['TID']

            if with_selected:
                if (tid and tid == row['TID']):
                    row['selected'] = 'selected'
                    selected_id = tid
                else:
                    row['selected'] = ''

            rows.append(row)

        if with_selected and not selected_id:
            #selected_id = rows[0]['id']
            rows[0]['selected'] = 'selected'

    return rows

def _get_file(file_id):
    view = _views['files']
    columns = database_config[view]['export']
    where = 'TID=%s' % file_id
    cursor = g.engine.runQuery(view, columns=columns, top=1, where=where, as_dict=True)
    return cursor and cursor[0] or {}

def _get_batches(file_id, batch_id=None, **kw):
    batches = []
    selected_id = None

    tid = kw.get('tid')
    no_selected = kw.get('no_selected') or False

    where = 'FileTypeID=%s%s%s' % (
        file_id, 
        batch_id and (' and BatchTypeID=%s' % batch_id) or '',
        tid and (' and TID=%s ' % tid) or '',
        )

    cursor = g.engine.runQuery('configurator-batches', columns=kw.get('columns'), where=where, order='CreateBatchSortIndex',
                             encode_columns=('BatchType','BatchCreateType','BatchResultType'),
                             as_dict=True,
                             )
    if cursor:
        is_selected = False
        
        for n, row in enumerate(cursor):
            row['id'] = row['TID']

            if not no_selected:
                if (tid and tid == row['TID']):
                    row['selected'] = 'selected'
                    selected_id = tid
                    is_selected = True
                else:
                    row['selected'] = ''

            batches.append(row)

        if not (no_selected or is_selected):
            row = batches[0]
            selected_id = row['id']
            row['selected'] = 'selected'

    return batches, selected_id

def _get_processes(file_id, **kw):
    view = kw.get('view')
    attrs = kw.get('attrs') or {}

    tid = kw.get('tid')
    BatchTypeID = attrs.get('BatchTypeID') or None
    with_selected = kw.get('with_selected') or False

    where = 'FileTypeID=%s%s%s' % (
        file_id, 
        BatchTypeID and (' and BatchTypeID=%s' % BatchTypeID) or '',
        tid and (' and TID=%s ' % tid) or '',
        )

    columns = kw.get('columns')
    order = 'BatchTypeID'
    encode_columns = ('BatchType', 'CurrFileStatus', 'NextFileStatus', 'CloseFileStatus', 'ActivateBatchStatus_', 'ARMBatchStatus_', 'Memo',)

    return _cursor_evaluate(view, columns, tid, where, order, encode_columns, with_selected)

def _get_opers(file_id, **kw):
    view = kw.get('view')
    attrs = kw.get('attrs') or {}

    tid = kw.get('tid')
    BatchTypeID = attrs.get('BatchTypeID') or None
    with_selected = kw.get('with_selected') or False

    where = 'FileTypeID=%s%s%s' % (
        file_id, 
        BatchTypeID and (' and BatchTypeID=%s' % BatchTypeID) or '',
        tid and (' and TID=%s ' % tid) or '',
        )

    columns = kw.get('columns')
    order = 'OperSortIndex, BatchTypeID'
    encode_columns = ('BatchType', 'OperTypeName', 'OperType',)

    return _cursor_evaluate(view, columns, tid, where, order, encode_columns, with_selected)

def _get_operparams(file_id, **kw):
    view = kw.get('view')
    attrs = kw.get('attrs') or {}

    tid = kw.get('tid')
    BatchTypeID = attrs.get('BatchTypeID') or None
    with_selected = kw.get('with_selected') or False

    where = 'FileTypeID=%s%s%s' % (
        file_id, 
        BatchTypeID and (' and BatchTypeID=%s' % BatchTypeID) or '',
        tid and (' and TID=%s ' % tid) or '',
        )

    columns = kw.get('columns')
    order = 'BatchTypeID'
    encode_columns = ('BatchType', 'OperTypeName', 'OperType', 'PName', 'PValue', 'Comment',)

    return _cursor_evaluate(view, columns, tid, where, order, encode_columns, with_selected)

def _get_filters(file_id, **kw):
    view = kw.get('view')
    attrs = kw.get('attrs') or {}

    tid = kw.get('tid')
    BatchTypeID = attrs.get('BatchTypeID') or None
    tag = attrs.get('Tag') or None
    with_selected = kw.get('with_selected') or False

    where = 'FileTypeID=%s%s%s%s' % (
        file_id, 
        BatchTypeID and (' and BatchTypeID=%s' % BatchTypeID) or '',
        tag and (" and TName='%s'" % tag) or '',
        tid and (' and TID=%s ' % tid) or '',
        )

    columns = kw.get('columns')
    order = 'BatchTypeID, TName'
    encode_columns = ('BatchType', 'TName', 'CriticalValues',)

    return _cursor_evaluate(view, columns, tid, where, order, encode_columns, with_selected)

def _get_tags(file_id, **kw):
    view = kw.get('view')
    attrs = kw.get('attrs') or {}

    tid = kw.get('tid')
    tag = attrs.get('Tag') or None
    with_selected = kw.get('with_selected') or False

    where = 'FileTypeID=%s%s%s' % (
        file_id, 
        tag and (" and TName='%s'" % tag) or '',
        tid and (' and TID=%s ' % tid) or '',
        )

    columns = kw.get('columns')
    order = 'TName'
    encode_columns = ('TName', 'TMemo',)

    return _cursor_evaluate(view, columns, tid, where, order, encode_columns, with_selected)

def _get_tagvalues(file_id, **kw):
    view = kw.get('view')
    attrs = kw.get('attrs') or {}

    tid = kw.get('tid')
    tag = attrs.get('Tag') or None
    tagvalue = attrs.get('TagValue') or None
    with_selected = kw.get('with_selected') or False

    where = 'FileTypeID=%s%s%s%s' % (
        file_id, 
        tag and (" and TName='%s'" % tag) or '',
        tagvalue and (" and TValue='%s'" % tagvalue) or '',
        tid and (' and TID=%s ' % tid) or '',
        )

    columns = kw.get('columns')
    order = 'TName'
    encode_columns = ('TName', 'TValue', 'TMemo', 'TagValue',)

    return _cursor_evaluate(view, columns, tid, where, order, encode_columns, with_selected)

def _get_tzs(file_id, **kw):
    view = kw.get('view')
    attrs = kw.get('attrs') or {}

    tid = kw.get('tid')
    tag = attrs.get('Tag') or None
    tagvalue = attrs.get('TagValue') or None
    with_selected = kw.get('with_selected') or False

    where = 'FileTypeID=%s%s%s%s' % (
        file_id, 
        tag and (" and TName='%s'" % tag) or '',
        tagvalue and (" and TValue='%s'" % tagvalue) or '',
        tid and (' and TID=%s ' % tid) or '',
        )

    columns = kw.get('columns')
    order = 'TName, TValue, PSortIndex'
    encode_columns = ('TName', 'TValue', 'TagValue', 'PName', 'PValue', 'Comment',)

    return _cursor_evaluate(view, columns, tid, where, order, encode_columns, with_selected)

def _get_erpcodes(file_id, **kw):
    view = kw.get('view')
    attrs = kw.get('attrs') or {}

    tid = kw.get('tid')
    BatchTypeID = attrs.get('BatchTypeID') or None
    tag = attrs.get('Tag') or None
    tagvalue = attrs.get('TagValue') or None
    with_selected = kw.get('with_selected') or False

    where = 'FileTypeID=%s%s%s%s%s' % (
        file_id, 
        BatchTypeID and (' and BatchTypeID=%s' % BatchTypeID) or '',
        tag and (" and TName='%s'" % tag) or '',
        tagvalue and (" and TValue='%s'" % tagvalue) or '',
        tid and (' and TID=%s ' % tid) or '',
        )

    columns = kw.get('columns')
    order = 'BatchTypeID, TName, TValue'
    encode_columns = ('BatchType', 'TName', 'TValue', 'TagValue',)

    return _cursor_evaluate(view, columns, tid, where, order, encode_columns, with_selected)

def _get_materials(file_id, **kw):
    view = kw.get('view')
    attrs = kw.get('attrs') or {}

    tid = kw.get('tid')
    BatchTypeID = attrs.get('BatchTypeID') or None
    tag = attrs.get('Tag') or None
    tagvalue = attrs.get('TagValue') or None
    with_selected = kw.get('with_selected') or False

    where = 'FileTypeID=%s%s%s%s%s' % (
        file_id, 
        BatchTypeID and (' and BatchTypeID=%s' % BatchTypeID) or '',
        tag and (" and TName='%s'" % tag) or '',
        tagvalue and (" and TValue='%s'" % tagvalue) or '',
        tid and (' and TID=%s ' % tid) or '',
        )

    columns = kw.get('columns')
    order = 'BatchTypeID, TName, TValue, PName'
    encode_columns = ('BatchType', 'TName', 'TValue', 'TagValue', 'PName',)

    return _cursor_evaluate(view, columns, tid, where, order, encode_columns, with_selected)

def _get_posts(file_id, **kw):
    view = kw.get('view')
    attrs = kw.get('attrs') or {}

    tid = kw.get('tid')
    tag = attrs.get('Tag') or None
    tagvalue = attrs.get('TagValue') or None
    with_selected = kw.get('with_selected') or False

    where = 'FileTypeID=%s%s%s%s' % (
        file_id, 
        tag and (" and TName='%s'" % tag) or '',
        tagvalue and (" and TValue='%s'" % tagvalue) or '',
        tid and (' and TID=%s ' % tid) or '',
        )

    columns = kw.get('columns')
    order = 'TName, TValue, PName'
    encode_columns = ('TName', 'TValue', 'TagValue', 'PName', 'PValue', 'Comment',)

    return _cursor_evaluate(view, columns, tid, where, order, encode_columns, with_selected)

def _get_tagopers(file_id, **kw):
    view = kw.get('view')
    attrs = kw.get('attrs') or {}

    tid = kw.get('tid')
    tag = attrs.get('Tag') or None
    tagvalue = attrs.get('TagValue') or None
    with_selected = kw.get('with_selected') or False

    where = 'FileTypeID=%s%s%s%s' % (
        file_id, 
        tag and (" and TName='%s'" % tag) or '',
        tagvalue and (" and TValue='%s'" % tagvalue) or '',
        tid and (' and TID=%s ' % tid) or '',
        )

    columns = kw.get('columns')
    order = 'TName, TValue, PName, OperSortIndex'
    encode_columns = ('TName', 'TValue', 'TagValue', 'PName', 'PValue', 'Oper', 'Comment',)

    return _cursor_evaluate(view, columns, tid, where, order, encode_columns, with_selected)

def _get_tagoperparams(file_id, **kw):
    view = kw.get('view')
    attrs = kw.get('attrs') or {}

    tid = kw.get('tid')
    tag = attrs.get('Tag') or None
    tagvalue = attrs.get('TagValue') or None
    with_selected = kw.get('with_selected') or False

    where = 'FileTypeID=%s%s%s%s' % (
        file_id, 
        tag and (" and TName='%s'" % tag) or '',
        tagvalue and (" and TValue='%s'" % tagvalue) or '',
        tid and (' and TID=%s ' % tid) or '',
        )

    columns = kw.get('columns')
    order = 'TName, TValue, Oper, PName, PValue'
    encode_columns = ('TName', 'TValue', 'TagValue', 'Oper', 'OperTypeValue', 'OperValue', 'PName', 'PValue',)

    return _cursor_evaluate(view, columns, tid, where, order, encode_columns, with_selected)

def _get_processparams(file_id, **kw):
    view = kw.get('view')
    attrs = kw.get('attrs') or {}

    tid = kw.get('tid')
    tag = attrs.get('Tag') or None
    tagvalue = attrs.get('TagValue') or None
    with_selected = kw.get('with_selected') or False

    where = 'FileTypeID=%s%s%s%s' % (
        file_id, 
        tag and (" and TName='%s'" % tag) or '',
        tagvalue and (" and TValue='%s'" % tagvalue) or '',
        tid and (' and TID=%s ' % tid) or '',
        )

    columns = kw.get('columns')
    order = 'TName, TValue, PName, PSortIndex'
    encode_columns = ('TName', 'TValue', 'TagValue', 'PName', 'PValue', 'Comment',)

    return _cursor_evaluate(view, columns, tid, where, order, encode_columns, with_selected)

def _get_top(per_page, page):
    if g.system_config.IsApplyOffset:
        top = per_page
    else:
        top = per_page * page
    offset = page > 1 and (page - 1) * per_page or 0
    return top, offset

## ==================================================== ##

def getTabBatchInfo(batch_id):
    data = []
    number = str(batch_id)

    try:
        if batch_id:
            params = "%s, 1, ''" % (batch_id)

            cursor = g.engine.runQuery('configurator-batchinfo', as_dict=True, params=params, encode_columns=('PName', 'PValue',))
            if cursor:
                for n, row in enumerate(cursor):
                    if row['PType'] == -1:
                        row['PName'] = '<nobr>%s</nobr>' % row['PName']
                        row['PValue'] = '<span class="counting">%s</span>' % row['PValue']

                    data.append(row)
    except:
        print_exception()

    props = {'id' : batch_id, 'number' : number}

    return number and data or [], props

def getTabProcesses(**kw):
    return _get_processes(requested_file_type_id(), **kw)

def getTabOpers(**kw):
    return _get_opers(requested_file_type_id(), **kw)

def getTabOperParams(**kw):
    return _get_operparams(requested_file_type_id(), **kw)

def getTabFilters(**kw):
    return _get_filters(requested_file_type_id(), **kw)

def getTabTags(**kw):
    return _get_tags(requested_file_type_id(), **kw)

def getTabTagValues(**kw):
    return _get_tagvalues(requested_file_type_id(), **kw)

def getTabTZs(**kw):
    return _get_tzs(requested_file_type_id(), **kw)

def getTabERPCodes(**kw):
    return _get_erpcodes(requested_file_type_id(), **kw)

def getTabMaterials(**kw):
    return _get_materials(requested_file_type_id(), **kw)

def getTabPosts(**kw):
    return _get_posts(requested_file_type_id(), **kw)

def getTabTagOpers(**kw):
    return _get_tagopers(requested_file_type_id(), **kw)

def getTabTagOperParams(**kw):
    return _get_tagoperparams(requested_file_type_id(), **kw)

def getTabProcessParams(**kw):
    return _get_processparams(requested_file_type_id(), **kw)

## ==================================================== ##

def runReference(attrs, params):
    """
        Reference class adapter.
        
        Arguments:
            attrs   -- Dict, query attributes
            params  -- Dict or String, with the keys:
            
                command    : String, valid is {add|update|remove}
                mode       : String, name of the reference class
                query      : String, search string like: '(bank || client) && citi'
                items      : Dict, field values: {key : value, ...}
                id         : String or Int, reference item Primary Key value
                state      : String or Int, state of object

            filter  -- List, loader filter items

        Returns (look at `reference.AbstractReference`):
            data    -- List, searched items
            props   -- Dict, properties

                id         : String, PK field name
                value      : String, value field name
                mode       : String, name of the reference class
                query      : String, original search string
                table      : String, the table name (reference.view)
                title      : String, title of the reference
                errors     : List, list of errors

            config  -- Dict, config object
            columns -- List, editable columns list

        Test:
            ob = DicClients(g.engine)
            errors = ob.addItem([('value', 'xxx'),])
            errors = ob.updateItem(388, [('value', 'x1'),])
            errors = ob.removeItem(388)
            clients = ob.getItems()
    """
    command, mode, query, items, id, state = _load_params(params)
    
    reference = reference_factory.get(mode)
    if reference is None:
        return [], None, None, None

    ob = reference(g.engine)

    errors = []
    data = []

    if items is not None:
        if command == 'add':
            id, errors = ob.addItem(items)
        elif command == 'update' and id is not None:
            errors = ob.updateItem(id, items)

    elif command == 'remove' and id is not None:
        errors = ob.removeItem(id)

    if command == 'link' and ob.has_links:
        data = ob.getLinks(query, attrs, id)

    else:
        data = ob.getItems(query, id)

    props = {'id' : ob.id, 'value' : ob.value, 'mode' : mode, 'query' : query, 'table' : ob.table, 'title' : ob.title, 'errors' : errors}

    return data, props, ob.config, ob.editable_columns

def runConfigItem(attrs, params):
    """
        Configurator class adapter.
        
        Arguments:
            attrs   -- Dict, query attributes
            params  -- Dict or String, with the keys:
            
                command    : String, valid is {add|update|remove}
                mode       : String, name of the reference class (Config-object)
                query      : String, search string like: '(bank || client) && citi'
                items      : Dict, field values: {key : value, ...}
                id         : String or Int, reference item Primary Key value
                state      : String or Int, state of object

        Returns (look at `reference.AbstractReference`):
            data    -- List, searched items
            props   -- Dict, properties:
            
                id         : Int, selected item 
                class_name : String, HTML object class name
                columns    : Mapped list, list of columns to show on screen
                total      : Int, total items in the table with query
                errors     : List, list of errors
            
            config  -- Dict, config object
            columns -- List, editable columns list
    """
    command, mode, query, items, id, state = _load_params(params)
    
    file_id = requested_file_type_id()

    reference = reference_factory.get(mode)
    if reference is None:
        return [], None, None, None

    ob = reference(g.engine)

    columns = []
    errors = []
    data = []

    class_name = ''
    no_selected = False
    total = 0

    if items is not None:
        if command == 'save':
            if id is None:
                id, errors = ob.addItem(items)
            else:
                errors = ob.updateItem(id, items)

    elif command == 'remove' and id is not None:
        errors = ob.removeItem(id)

    elif command == 'blank':
        data = ob.getBlank(attrs, default=g.requested_object)
        
        data['FileTypeID'] = g.requested_object.get('TID')
        data['FileType'] = g.requested_object.get('FileType')

        if (':%s:' % mode.strip()) in ':tzs:erpcodes:materials:posts:tagopers:processparams:':
            data['TagValue'] = ''

        data = [data]

        no_selected = True
        id = None

    # -----------------------------------------------
    # Select data from the given Config-object (mode)
    # -----------------------------------------------

    view = ob.configurator
    columns = database_config[view]['export']
    with_selected = True
    tid = id

    if mode == 'batches':
        if id:
            data, selected_id = _get_batches(file_id, tid=tid, columns=columns, no_selected=no_selected)

        class_name = 'subline'
        where = makeSqlWhere({'FileTypeID' : file_id})
        total = ob.count(where)

    elif mode == 'processes':
        if id:
            data = _get_processes(file_id, tid=tid, columns=columns, view=view, attrs=attrs, with_selected=with_selected)

        class_name = 'tabline'
        where = makeSqlWhere({'LinkID' : file_id})
        total = ob.count(where)

    elif mode == 'opers':
        if id:
            data = _get_opers(file_id, tid=tid, columns=columns, view=view, attrs=attrs, with_selected=with_selected)

        class_name = 'tabline'
        where = makeSqlWhere({'FBLinkID' : attrs.get('FBLinkID')})
        total = ob.count(where)

    elif mode == 'operparams':
        if id:
            data = _get_operparams(file_id, tid=tid, columns=columns, view=view, attrs=attrs, with_selected=with_selected)

        class_name = 'tabline'
        where = makeSqlWhere({'FBOLinkID' : attrs.get('FBOLinkID')})
        total = ob.count(where)

    elif mode == 'tags':
        if id:
            data = _get_tags(file_id, tid=tid, columns=columns, view=view, attrs=attrs, with_selected=with_selected)

        class_name = 'tabline'
        where = makeSqlWhere({'FileTypeID' : file_id})
        total = ob.count(where)

    elif mode == 'tagvalues':
        if id:
            data = _get_tagvalues(file_id, tid=tid, columns=columns, view=view, attrs=attrs, with_selected=with_selected)

        class_name = 'tabline'
        where = makeSqlWhere({'FTLinkID' : attrs.get('FTLinkID')})
        total = ob.count(where)

    elif mode == 'filters':
        if id:
            data = _get_filters(file_id, tid=tid, columns=columns, view=view, attrs=attrs, with_selected=with_selected)

        class_name = 'tabline'
        where = makeSqlWhere({'FBLinkID' : attrs.get('FBLinkID'), 'FTLinkID' : attrs.get('FTLinkID')})
        total = ob.count(where)

    elif mode == 'tzs':
        if id:
            data = _get_tzs(file_id, tid=tid, columns=columns, view=view, attrs=attrs, with_selected=with_selected)

        class_name = 'tabline'
        where = makeSqlWhere({'FTVLinkID' : attrs.get('FTVLinkID'), 'TagParamID' : attrs.get('TagParamID')})
        total = ob.count(where)

    elif mode == 'erpcodes':
        if id:
            data = _get_erpcodes(file_id, tid=tid, columns=columns, view=view, attrs=attrs, with_selected=with_selected)

        class_name = 'tabline'
        where = makeSqlWhere({'FTVLinkID' : attrs.get('FTVLinkID'), 'BatchTypeID' : attrs.get('BatchTypeID')})
        total = ob.count(where)

    elif mode == 'materials':
        if id:
            data = _get_materials(file_id, tid=tid, columns=columns, view=view, attrs=attrs, with_selected=with_selected)

        class_name = 'tabline'
        where = makeSqlWhere({'FTVLinkID' : attrs.get('FTVLinkID'), 'BatchTypeID' : attrs.get('BatchTypeID'), 'TagParamID' : attrs.get('TagParamID')})
        total = ob.count(where)

    elif mode == 'posts':
        if id:
            data = _get_posts(file_id, tid=tid, columns=columns, view=view, attrs=attrs, with_selected=with_selected)

        class_name = 'tabline'
        where = makeSqlWhere({'FTVLinkID' : attrs.get('FTVLinkID'), 'TagParamID' : attrs.get('TagParamID')})
        total = ob.count(where)

    elif mode == 'tagopers':
        if id:
            data = _get_tagopers(file_id, tid=tid, columns=columns, view=view, attrs=attrs, with_selected=with_selected)

        class_name = 'tabline'
        where = makeSqlWhere({'FTVLinkID' : attrs.get('FTVLinkID'), 'TagParamID' : attrs.get('TagParamID')})
        total = ob.count(where)

    elif mode == 'tagoperparams':
        if id:
            data = _get_tagoperparams(file_id, tid=tid, columns=columns, view=view, attrs=attrs, with_selected=with_selected)

        class_name = 'tabline'
        where = makeSqlWhere({'FTV_OPER_ID' : attrs.get('FTVLinkID')})
        total = ob.count(where)

    elif mode == 'processparams':
        if id:
            data = _get_processparams(file_id, tid=tid, columns=columns, view=view, attrs=attrs, with_selected=with_selected)

        class_name = 'tabline'
        where = makeSqlWhere({'FTVLinkID' : attrs.get('FTVLinkID'), 'TagParamID' : attrs.get('TagParamID')})
        total = ob.count(where)

    columns = _get_view_columns(database_config[view])

    props = {'id' : id, 'class_name' : class_name, 'columns' : columns, 'total' : total, 'errors' : errors}

    return data, props, ob.config, ob.sorted_columns

## ==================================================== ##

def _create_scenario():
    """
        Generate a new Application Config scenario
    """
    errors = None

    try:
        generator = FileTypeSettingsGenerator(CONNECTION[default_page], g.requested_object)
        configtype = request.form.get('configtype')

        if not configtype:
            pass
        elif configtype == 'cardstandard':
            errors = generator.createCardStandardScenario(request.form)
        elif configtype == 'easy':
            errors = generator.createEasyScenario(request.form)
    except:
        if IsPrintExceptions:
            print_exception()

    return errors

def _remove_scenario():
    errors = None

    try:
        generator = FileTypeSettingsGenerator(CONNECTION[default_page], g.requested_object)
        errors = generator.removeScenario()
    except:
        if IsPrintExceptions:
            print_exception()

    return errors

def _create_design():
    """
        Generate a new CardStandard product design
    """
    errors = None

    try:
        generator = FileTypeSettingsGenerator(CONNECTION[default_page], g.requested_object)
        errors = generator.createNewDesign(request.form)
    except:
        if IsPrintExceptions:
            print_exception()

    return errors

def _make_page_default(kw):
    file_id = int(kw.get('file_id'))
    batch_id = int(kw.get('batch_id'))

    is_admin = g.current_user.is_administrator()

    args = _get_page_args()

    file_name = ''
    filter = ''
    qs = ''

    template = default_template

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
    is_search_event = False
    items = []

    if search:
        items.append("FileType like '%%%s%%'" % search)

    # -------------
    # Фильтр (args)
    # -------------

    ClientID = FileTypeID = BatchTypeID = None
    TagName = args['tag'][1]

    if args:
        for key in args:
            name, value = args[key]
            id = None
            if name == 'ClientID':
                id = ClientID = value or None
            elif name == 'FileTypeID':
                id = FileTypeID = value or None
            elif name == 'BatchTypeID':
                id = BatchTypeID = value or None

            if id and name in ('ClientID', 'FileTypeID',): #
                items.append("%s=%s" % (name, id))

            elif id and name in ('BatchTypeID',):
                items.append("%s=%s" % (name, id))
                template = _views['files']

            if value:
                filter += "&%s=%s" % (key, value)

    if items:
        qs += ' and '.join(items)

    where = qs or ''

    # -------------------------------
    # Представление БД (default_view)
    # -------------------------------

    default_view = database_config[template]

    # ---------------------------------
    # Сортировка журнала (current_sort)
    # ---------------------------------

    current_sort = int(get_request_item('sort') or '0')
    if current_sort > 0:
        order = '%s' % default_view['columns'][current_sort-1]
    else:
        order = 'Client, FileType'

    if current_sort in (1,):
        order += " desc"

    if IsDebug:
        print('--> where:%s %s, order:%s' % (where, args, order))

    pages = 0
    total_files = 0
    total_batches = 0
    files = []
    batches = []
    clients = []
    filetypes = []
    batchtypes = []
    tags = []
    tagvalues = []

    confirmed_file_id = 0

    # ======================
    # Выборка данных журнала
    # ======================

    if g.engine != None:

        # -------------------------------------------------
        # Кол-во записей по запросу в журнале (total_files)
        # -------------------------------------------------

        cursor = g.engine.runQuery(template, columns=('count(*)',), where=where, distinct=True)
        if cursor:
            total_files = cursor[0][0]

        # ===================
        # Типы файлов (files)
        # ===================

        cursor = g.engine.runQuery(template, columns=database_config[template]['columns'], 
                                 top=top, offset=offset, where=where, order=order, as_dict=True,
                                 encode_columns=('Client', 'ReportPrefix',),
                                 distinct=True)
        if cursor:
            is_selected = False

            for n, row in enumerate(cursor):
                #if offset and n < offset:
                #    continue

                if file_id:
                    if not confirmed_file_id and file_id == row['TID']:
                        confirmed_file_id = file_id
                    if not file_name and file_id == row['TID']:
                        file_name = row['FileType']

                    if file_id == row['TID']:
                        row['selected'] = 'selected'
                        is_selected = True
                else:
                    row['selected'] = ''

                for x in row:
                    if not row[x] or str(row[x]).lower() == 'none':
                        row[x] = ''

                row['id'] = row['TID']
                #row['Client'] = row['Client'].encode(default_iso).decode(default_encoding)

                files.append(row)

            if line > len(files):
                line = 1

            if not is_selected and len(files) >= line:
                row = files[line-1]
                confirmed_file_id = file_id = row['id'] = row['TID']
                file_name = row['FileType']
                row['selected'] = 'selected'

        if len(files) == 0:
            file_id = 0
            file_name = ''
            batch_id = 0
        elif confirmed_file_id != file_id or not file_id:
            row = files[0]
            file_id = row['TID']
            file_name = row['FileType']
        elif not confirmed_file_id:
            file_id = 0
            file_name = ''

        if total_files:
            pages = int(total_files / per_page)
            if pages * per_page < total_files:
                pages += 1

        # =====================
        # Типы партий (batches)
        # =====================

        cursor = g.engine.runQuery('configurator-batches', columns=('count(*)',), where=where)
        if cursor:
            total_batches = cursor[0][0]

        if file_id:
            batches, batch_id = _get_batches(file_id, batch_id=BatchTypeID)

        # ------------------------------------------------------------------------------
        # Справочники фильтра запросов (clients, filetypes, batchtypes, tags, tagvalues)
        # ------------------------------------------------------------------------------

        clients.append((0, DEFAULT_UNDEFINED,))
        cursor = g.engine.runQuery('configurator-clients', order='CName', distinct=True, encode_columns=(1,))
        clients += [(x[0], x[1],) for x in cursor]

        filetypes.append((0, DEFAULT_UNDEFINED,))
        where = ClientID and ("ClientID=%s" % ClientID) or ''
        cursor = g.engine.runQuery('configurator-filetypes', where=where, order='CName', distinct=True, encode_columns=(1,))
        filetypes += [(x[0], x[1],) for x in cursor]

        batchtypes.append((0, DEFAULT_UNDEFINED,))
        cursor = g.engine.runQuery('configurator-batchtypes', order='CName', distinct=True, encode_columns=(1,))
        batchtypes += [(x[0], x[1]) for x in cursor]

        tags.append(DEFAULT_UNDEFINED)
        """
        where = ' AND '.join([x for x in [
            ClientID and ('ClientID=%s' % ClientID),
            FileTypeID and ('FileTypeID=%s' % FileTypeID),
        ] if x])
        """
        where = makeSqlWhere({'ClientID' : ClientID, 'FileTypeID' : FileTypeID})
        cursor = g.engine.runQuery('configurator-tags', columns=('TName',), where=where, order='TName', distinct=True, encode_columns=(0,))
        tags += [x[0] for x in cursor]

        tagvalues.append(DEFAULT_UNDEFINED)
        """
        where = ' AND '.join([x for x in [
            ClientID and ('ClientID=%s' % ClientID),
            FileTypeID and ('FileTypeID=%s' % FileTypeID),
            TagName and ('TName=\'%s\'' % TagName),
        ] if x])
        """
        where = makeSqlWhere({'ClientID' : ClientID, 'FileTypeID' : FileTypeID, 'TName' : TagName})
        cursor = g.engine.runQuery('configurator-tagvalues', columns=('TValue',), where=where, order='TValue', distinct=True, encode_columns=(0,))
        tagvalues += [x[0] for x in cursor]

        g.engine.dispose()

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
    base = 'configurator?%s' % query_string

    modes = [(n+1, '%s' % default_view['headers'][x][0]) for n, x in enumerate(default_view['columns'])]
    modes.insert(0, (0, 'По умолчанию'))
    sorted_by = default_view['headers'][default_view['columns'][current_sort]]

    pagination = {
        'total'             : '%s / %s' % (total_files, total_batches),
        'per_page'          : per_page,
        'pages'             : pages,
        'current_page'      : page,
        'iter_pages'        : tuple(iter_pages),
        'has_next'          : page < pages,
        'has_prev'          : page > 1,
        'per_page_options'  : (5,10,20,30,40,50,100),
        'link'              : '%s%s%s%s' % (base, filter,
                                           (search and "&search=%s" % search) or '',
                                           (current_sort and "&sort=%s" % current_sort) or ''
                                           ),
        'sort'              : {
            'modes'         : modes,
            'sorted_by'     : sorted_by,
            'current_sort'  : current_sort,
        },
        'position'          : '%d:%d:%d:%d' % (page, pages, per_page, line),
    }

    kw.update({
        'base'              : base,
        'page_title'        : gettext('WebPerso Configurator View'),
        'header_subclass'   : 'left-header',
        'show_flash'        : True,
        'model'             : 0,
        'loader'            : '/configurator/loader',
        'semaphore'         : initDefaultSemaphore(),
        'args'              : args,
        'current_file'      : (file_id, file_name, batch_id),
        'navigation'        : get_navigation(),
        'config'            : database_config,
        'pagination'        : pagination,
        'files'             : files,
        'batches'           : batches,
        'clients'           : clients,
        'filetypes'         : filetypes,
        'batchtypes'        : batchtypes,
        'tags'              : tags,
        'tagvalues'         : tagvalues,
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

@configurator.route('/configurator', methods = ['GET','POST'])
@login_required
def start():
    try:
        return index()
    except:
        raise

def index():
    debug, kw = init_response('WebPerso Configurator Page')
    kw['product_version'] = product_version

    is_admin = g.current_user.is_administrator()
    is_operator = g.current_user.is_operator()

    command = get_request_item('command')

    file_id = int(get_request_item('file_id') or '0')
    batch_id = int(get_request_item('batch_id') or '0')

    if IsDebug:
        print('--> command:%s, file_id:%s, batch_id:%s' % (
            command,
            kw.get('file_id'),
            kw.get('batch_id')
        ))

    refresh(file_id=file_id)

    errors = []

    if command and command.startswith('admin'):
        command = command.split(DEFAULT_HTML_SPLITTER)[1]

        if get_request_item('OK') != 'run':
            command = ''

        elif not is_admin:
            flash('You have not permission to run this action!')
            command = ''

        elif command == 'createscenario':
            errors = _create_scenario()

        elif command == 'removescenario':
            errors = _remove_scenario()

        elif command == 'createdesign':
            errors = _create_design()

    kw['errors'] = errors and '<br>'.join(errors) or ''
    kw['OK'] = ''

    try:
        kw = _make_page_default(kw)

        if IsTrace:
            print_to(errorlog, '--> configurator:%s %s [%s:%s] %s' % (
                command, g.current_user.login, request.remote_addr, kw.get('browser_info'), str(kw.get('current_file')),), 
                request=request)
    except:
        print_exception()

    kw['vsc'] = vsc(force=g.system_config.IsForceRefresh)

    if command:
        is_extra = has_request_item(EXTRA_)

        if not command.strip():
            pass

        elif command in 'createscenario:removescenario:createdesign':
            if kw['errors']:
                flash('Config Generator done with errors!')
            else:
                kw['OK'] = gettext('Message: Configuration was %s successfully.' % (
                    command == 'removescenario' and 'removed' or 'created'))

        elif command == 'export':
            columns = kw['config']['files']['export']
            rows = []
            for data in kw['files']:
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

            xls = makeXLSContent(rows, 'Конфигуратор BankPerso', True)

            response = make_response(xls)
            response.headers["Content-Disposition"] = "attachment; filename=configurator.xls"
            return response

    return make_response(render_template('configurator.html', debug=debug, **kw))

@configurator.after_request
def make_response_no_cached(response):
    if g.engine is not None:
        g.engine.close()
    # response.cache_control.no_store = True
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response

@configurator.route('/configurator/loader', methods = ['GET', 'POST'])
@login_required
def loader():
    exchange_error = ''
    exchange_message = ''

    action = get_request_item('action') or default_action
    selected_menu_action = get_request_item('selected_menu_action') or action != default_action and action or '601'

    response = {}

    file_id = int(get_request_item('file_id') or '0')
    batch_id = int(get_request_item('batch_id') or '0')

    refresh(file_id=file_id)

    active_links = get_request_item('active_links') or {}

    attrs = {
        'FileTypeID'            : file_id,
        'FileTypeBatchTypeID'   : batch_id,
        'FBLinkID'              : batch_id or active_links.get('FBLinkID') or 0,
        'FBOLinkID'             : active_links.get('FBOLinkID') or 0,
        'FTLinkID'              : active_links.get('FTLinkID') or 0,
        'FTVLinkID'             : active_links.get('FTVLinkID') or 0,
        'TagParamID'            : active_links.get('TagParamID') or 0,
        'BatchTypeID'           : active_links.get('BatchTypeID') or int(get_request_item('filter-batchtype') or 0),
        'Tag'                   : get_request_item('filter-tag'),
        'TagValue'              : get_request_item('filter-tagvalue'),
    }
    attrs = sortedDict(attrs)

    params = get_request_item('params') or ''

    if IsDebug:
        print('--> action:%s file_id:%s batch_id:%s attr:%s params:%s' % (
            action, file_id, batch_id, attrs, params,
        ))

    if IsTrace:
        print_to(errorlog, '--> loader:%s %s [%s:%s:%s] attrs:%s%s' % ( 
            action, g.current_user.login, file_id, batch_id, selected_menu_action, 
            reprSortedDict(attrs),
            params and (' params:%s' % reprSortedDict(params, is_sort=True)) or ''
            ), encoding=default_unicode)

    currentfile = None
    batches = []
    config = None

    data = ''
    number = ''
    columns = []
    total = None
    status = ''
    path = ''

    props = None

    try:
        if action == default_action:
            batches, selected_id = _get_batches(file_id, batch_id=attrs['BatchTypeID'])
            currentfile = [g.requested_object.get('TID'), g.requested_object.get('FileType'), selected_id]
            config = _get_view_columns(database_config['configurator-batches'])
            action = selected_menu_action
            batch_id = selected_id

        if not action:
            pass

        elif action == '601':
            data, props = getTabBatchInfo(batch_id)

        elif action == '602':
            view = 'configurator-processes'
            columns = _get_view_columns(database_config[view])
            data = getTabProcesses(attrs=attrs, view=view, with_selected=True)

        elif action == '603':
            view = 'configurator-opers'
            columns = _get_view_columns(database_config[view])
            data = getTabOpers(attrs=attrs, view=view, with_selected=True)

        elif action == '604':
            view = 'configurator-operparams'
            columns = _get_view_columns(database_config[view])
            data = getTabOperParams(attrs=attrs, view=view, with_selected=True)

        elif action == '605':
            view = 'configurator-filters'
            columns = _get_view_columns(database_config[view])
            data = getTabFilters(attrs=attrs, view=view, with_selected=True)

        elif action == '606':
            view = 'configurator-tags'
            columns = _get_view_columns(database_config[view])
            data = getTabTags(attrs=attrs, view=view, with_selected=True)

        elif action == '607':
            view = 'configurator-tagvalues'
            columns = _get_view_columns(database_config[view])
            data = getTabTagValues(attrs=attrs, view=view, with_selected=True)

        elif action == '608':
            view = 'configurator-tzs'
            columns = _get_view_columns(database_config[view])
            data = getTabTZs(attrs=attrs, view=view, with_selected=True)

        elif action == '609':
            view = 'configurator-erpcodes'
            columns = _get_view_columns(database_config[view])
            data = getTabERPCodes(attrs=attrs, view=view, with_selected=True)

        elif action == '610':
            view = 'configurator-materials'
            columns = _get_view_columns(database_config[view])
            data = getTabMaterials(attrs=attrs, view=view, with_selected=True)

        elif action == '611':
            view = 'configurator-posts'
            columns = _get_view_columns(database_config[view])
            data = getTabPosts(attrs=attrs, view=view, with_selected=True)

        elif action == '612':
            view = 'configurator-processparams'
            columns = _get_view_columns(database_config[view])
            data = getTabProcessParams(attrs=attrs, view=view, with_selected=True)

        elif action == '613':
            view = 'configurator-tagopers'
            columns = _get_view_columns(database_config[view])
            data = getTabTagOpers(attrs=attrs, view=view, with_selected=True)

        elif action == '614':
            view = 'configurator-tagoperparams'
            columns = _get_view_columns(database_config[view])
            data = getTabTagOperParams(attrs=attrs, view=view, with_selected=True)

        elif action == '620':
            data, props, config, columns = runReference(attrs, params)

        elif action == '621':
            data, props, config, columns = runConfigItem(attrs, params)

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
        # --------------------------
        # Results (Log page content)
        # --------------------------
        'total'            : len(data),
        'data'             : data,
        'status'           : status,
        'path'             : path,
        'props'            : props,
        'columns'          : columns,
    })

    return jsonify(response)

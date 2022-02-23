# -*- coding: utf-8 -*-

__all__ = ['AbstractReference',]

import types
import re
from operator import itemgetter

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, errorlog, print_to, print_exception,
     default_unicode, default_encoding, 
     )

from .settings import gettext
from .database import getReferenceConfig
from .booleval import Token, new_token
from .utils import isIterable

_UNDEFINED_ERROR = 2
_ERROR = 1
_WARNING = 0

##  ========================
##  Abstract Reference Class
##  ========================

def addSqlFilterItem(where, key, value, fields, operator=None):
    if not key:
        return ''
    field = fields.get(key)
    if field is None or value is None:
        return ''
    selector = field.get('selector')
    return selector and value is not None and ('%s%s' % (where and (operator or ' AND ') or '', selector % str(value))) or ''

def getSqlOrder(fields):
    orders = []
    for name in fields:
        field = fields[name]
        if field.get('order'):
            index = 0
            order = field['order']
            if '-' in order:
                x = order.split('-')
                index = x[0] and x[0].isdigit() and int(x[0]) or 0
                order = x[1]

            orders.append((name, index, order or 'asc'))

    return orders and \
        ', '.join(['%s %s' % (name, order) for name, index, order in sorted(orders, key=itemgetter(1), reverse=False)]) or ''


class AbstractReference(object):

    def __init__(self, engine, view, id=None):
        self.engine = engine
        self.view = view

        self._id = id or 'TID'
        self._config = getReferenceConfig(self.view)

        self._fields = self._config.get('fields')
        self._table = self._config.get('view')

    def _is_ready(self):
        return self.engine and self._table and True or False

    def _get_errors(self, errors):
        return [x[1] for x in sorted(errors, key=itemgetter(0), reverse=True)]

    @property
    def id(self):
        return self._id
    @property
    def value(self):
        return 'CName'
    @property
    def is_error(self):
        return self.engine.is_error
    @property
    def driver(self):
        return self.engine.driver
    @property
    def table(self):
        return self._table
    @property
    def config(self):
        return self._config
    @property
    def columns(self):
        return self._config['columns']
    @property
    def sorted_columns(self):
        return self.columns
    @property
    def headers(self):
        return self._config['headers']
    @property
    def fields(self):
        return self._config['fields']
    @property
    def title(self):
        pass
    @property
    def searchable(self):
        """ Searchable Text fields list or single field name """
        return None
    @property
    def numeric(self):
        return None
    @property
    def editable_columns(self):
        return None
    @property
    def service_columns(self):
        return None
    @property
    def filtered_columns(self):
        return None
    @property
    def has_links(self):
        return False

    def _check_search_query(self, value):
        q = []
        if isinstance(value, str):
            #
            # Query items can be `Token` class instance such as: (bank || client) && citi
            #
            token = new_token()
            token._init_state(value)
            tokens = token.get_token()

            if IsDeepDebug:
                print('--> %s' % repr(tokens))

            n = 1
            for x in tokens:
                if callable(x) or isinstance(x, types.FunctionType):
                    item = ('operator%s' % n, x(1,0) and ' OR ' or ' AND ')
                elif x in '()':
                    item = ('_%s' % n, x)
                    n += 1
                else:
                    if x.isdigit():
                        item = (self.numeric or self.id, int(x))
                    else:
                        item = (self.searchable or self.value, x)

                q.append(item)

            if IsDeepDebug:
                print('--> %s' % repr(q))

        elif isinstance(value, list):
            #
            # Query is a list: [(<key>, <value>),...]
            #
            q = value[:]

        return q

    def _set_where(self, query):
        where = ''
        has_items = False
        if query:
            operator = None
            for key, value in self._check_search_query(query):
                if isIterable(key):
                    s = ' OR '.join([addSqlFilterItem(0, x, value, self._fields) for x in key])
                    where += '(%s)' % s
                    has_items = True
                elif key.startswith('_'):
                    where += value
                elif key.startswith('operator'):
                    where += value
                else:
                    where += addSqlFilterItem(has_items, key, value, self._fields, operator)
        return where

    def _set_order(self, order=None):
        return order or getSqlOrder(self._fields) or ''

    def _set_encoding(self):
        return [key for key in self._fields if self._fields[key].get('encoding')]

    def getBlank(self, attrs, default=None):
        row = {}

        blank_field_values = {
            'int' : 0,
            'varchar' : '',
            'text' : '',
        }

        for name in self.columns:
            header = self.headers[name]
            field = self.fields[name]

            value = blank_field_values.get(field['type'], '')

            if name in attrs:
                value = attrs[name]

            row[name] = value
            alias = header['alias']

            if alias:
                if alias == name and header['link'] and header['style'] == 'varchar':
                    row[name] = ''
                else:
                    field = self.fields.get(alias)
                    if field:
                        value = blank_field_values.get(field['type'], '')

                        if alias in attrs:
                            value = attrs[name]
                        elif default and alias in default:
                            value = default[name]

                        row[alias] = value

        return row

    def _selected(self, rows, id):
        if rows and id:
            selected_id = int(id)

            for row in rows:
                if row.get(self.id) == selected_id:
                    row['selected'] = 'selected'
                else:
                    row['selected'] = ''

    def getLinks(self, query, attrs, id, **kw):
        """
            Get linked reference items list with SQL-query.

            Arguments:
                query   -- List|String, query parameters: [('key':'value'), ...] or search string
                attrs   -- Dict, query attributes:

                'FileTypeID'          : Int, file type ID
                'FileTypeBatchTypeID' : Int, file type batch type ID
                'FBLinkID'            : Int, file type batch type ID
                ...
                'BatchTypeID'         : Int, filtered batch type ID
                'Tag'                 : Int or String, filtered tag ID/Name
                'TagValue'            : String, filtered tag value

                id      -- Int or String, selected item id

            Class attributes:
                filtered_columns -- List, list of columns used to filter data by the query

            Returns:
                rows    -- List, mappings list: [{'key':'value', ...}].
        """
        rows = []

        try:
            columns = self.columns
            filtered_columns = self.filtered_columns or columns
            where = self._set_where(query)

            s = ' AND '.join(['%s=%s' % (name, isinstance(value, int) and value or ("'%s'" % value))
                    for name, value in attrs.items() if name in filtered_columns and value]
                )

            if s:
                where = where and '(%s) AND (%s)' % (where, s) or s

            order = self._set_order(kw.get('order'))
            encode_columns = self._set_encoding()

            rows = self.engine.runQuery(self.view, columns=columns, where=where, order=order, 
                                        encode_columns=encode_columns, 
                                        as_dict=True,
                                        config=self.config,
                                        )
            self._selected(rows, id)

        except:
            if IsPrintExceptions:
                print_exception()

        return rows

    def getItems(self, query, id, **kw):
        """
            Returns reference items list with SQL-query.

            Arguments:
                query   -- List|String, query parameters: [('key':'value'), ...] or search string
                id      -- Int or String, selected item id

            Returns:
                rows    -- List, mappings list: [{'key':'value', ...}].
        """
        rows = []

        try:
            columns = kw.get('columns') or self.columns
            where = kw.get('where') or self._set_where(query)
            order = kw.get('order') or self._set_order(kw.get('order'))
            encode_columns = self._set_encoding()

            rows = self.engine.runQuery(self.view, columns=columns, where=where, order=order, 
                                        encode_columns=encode_columns, 
                                        as_dict=True,
                                        config=self.config,
                                        )
            if id:
                self._selected(rows, id)

        except:
            if IsPrintExceptions:
                print_exception()

            raise

        return rows

    def calculateId(self):
        cursor = self.engine.runQuery(self.view, columns=(self._id,), top=1, order='%s DESC' % self.id,
                                      config=self.config,
                                      )
        id = cursor and int(cursor[0][0]) or 0
        return id + 1

    def getItemById(self, id):
        rows = []

        try:
            columns = self.columns
            where = '%s=%s' % (self.id, id)
            encode_columns = self._set_encoding()

            rows = self.engine.runQuery(self.view, columns=columns, where=where, encode_columns=encode_columns, as_dict=True,
                                        config=self.config,
                                        )

        except:
            if IsPrintExceptions:
                print_exception()

            raise

        return rows and rows[0]

    def count(self, where=None):
        cursor = self.engine.runQuery(self.view, columns=('count(*)',), where=where,
                                      config=self.config,
                                      )
        return cursor and cursor[0] or 0

    def _dbtype(self, name):
        if self.fields.get(name)['type'] in ('varchar', 'datetime', 'text,'):
            return 'varchar'
        if self.headers.get(name)['link']:
            return 'null'
        else:
            return 'int'

    def _default_value(self, name):
        if self._dbtype(name) == 'varchar':
            return ''
        if self._dbtype(name) == 'null':
            return 'null'
        else:
            return 0

    def _value(self, items, name):
        value = items.get(name)
        if value and isinstance(value, str):
            value = re.sub(r'([\"\'])', '\"', value)
        return value or self._default_value(name)

    def addItem(self, items, id=None, **kw):
        """
            Add new item into the reference.

            Arguments:
                id      -- Int|String, PK, `None` is used for calculated value
                items   -- Dict, field values: {name : value, ...}

            Keyword arguments:
                with_identity -- Boolean: PK is <Identity> field
                calculated_pk -- Boolean: PK should be calculated integer as max scope value
                explicit_pk   -- Boolean: PK is editable field

            Returns:
                id      -- Int, PK of a new item
                errors  -- List, Errors list: ['error', ...], sorted by error code: 2,1,0. Empty is success.
        """
        errors = []

        # --------------------
        # SQL-command template
        # --------------------

        command = 'INSERT INTO ' + self._table + '(%s) VALUES(%s)'

        # -----------------------------------
        # Get item values and set SQL-command
        # -----------------------------------

        columns = list(self.editable_columns or []) + list(self.service_columns or [])

        if not self._is_ready():
            errors.append((_ERROR, gettext('Error: Class has not editable columns')))

        explicit_pk = kw.get('explicit_pk') and True or False

        values = items and ', '.join([
            '%s' % (self._dbtype(name) in 'varchar' and ("'%s'" % str(self._value(items, name))) or self._value(items, name))
                for name in columns if name != self.id]) or ''
        sql = ''

        calculated_pk = kw.get('calculated_pk') and True or False
        with_identity = kw.get('with_identity') and True or False

        if not self._is_ready():
            errors.append((_ERROR, gettext('Error: Class is not ready')))

        elif id is None:
            if calculated_pk:
                id = self.calculateId()
            elif explicit_pk:
                id = self._value(items, self.id)
            elif not with_identity:
                errors.append((_ERROR, gettext('Error: Missing Primary Key for insert')))

        if not values:
            errors.append((_WARNING, gettext('Warning: No values present')))
        elif id:
            values = '%s, %s' % (id, values)
            if not self.id in columns:
                columns.insert(0, self.id)

        no_cursor = True

        if not errors:
            sql = command % (', '.join(columns), values)

            if IsDeepDebug:
                print('--> with_identity:%s' % with_identity)

            if with_identity:
                if self.driver == 'pyodbc':
                    pass
                else:
                    sql += ' SELECT SCOPE_IDENTITY()'
                    no_cursor = False

            # --------------
            # Execute $ Exit
            # --------------

            rows = self.run(sql, errors, no_cursor=no_cursor)

            if with_identity:
                if self.driver == 'pyodbc':
                    rows = self.engine.runQuery(self.table, top=1, columns=('TID',), order='TID desc', config=self.config)
                if rows:
                    id = int(rows[0][0])

            if IsDeepDebug:
                print('--> new item: ID[%s]' % id)

        return id, self._get_errors(errors)

    def updateItem(self, id, items):
        """
            Update item values into the reference.

            Arguments:
                id      -- Int|String, PK, `None` is used for calculated value
                items   -- Dict, field values: {name : value, ...}

            Returns:
                errors  -- List, Errors list: ['error', ...], sorted by error code: 2,1,0. Empty is success.
        """
        errors = []

        # --------------------
        # SQL-command template
        # --------------------

        command = 'UPDATE ' + self._table + ' SET %s WHERE ' + self.id + '=%s'

        # ---------------------------------------
        # Get item values, ID and set SQL-command
        # ---------------------------------------

        columns = self.editable_columns or []

        if not self._is_ready():
            errors.append((_ERROR, gettext('Error: Class has not editable columns')))

        values = items and ', '.join([
            '%s=%s' % (name, 
                       self._dbtype(name) in 'varchar' and ("'%s'" % str(self._value(items, name))) or self._value(items, name)) 
                for name in columns if name != self.id and name in self.fields and name in items]) or '' # and items[name]
        sql = ''

        if not self._is_ready():
            errors.append((_ERROR, gettext('Error: Class is not ready')))

        elif id is None:
            errors.append((_ERROR, gettext('Error: Missing Primary Key for update')))

        if not values:
            errors.append((_WARNING, gettext('Warning: No values present')))

        if not errors:
            sql = command % (values, id)

            # --------------
            # Execute $ Exit
            # --------------

            rows = self.run(sql, errors)

        return self._get_errors(errors)

    def removeItem(self, id):
        """
            Delete item with given id from the reference.

            Arguments:
                id      -- Int|String, PK, `None` is used for calculated value

            Returns:
                errors  -- List, Errors list: ['error', ...], sorted by error code: 2,1,0. Empty is success.
        """
        errors = []

        # --------------------
        # SQL-command template
        # --------------------

        command = 'DELETE FROM ' + self._table + ' WHERE ' + self.id + '=%s'

        # -------------------------------
        # Get item ID and set SQL-command
        # -------------------------------

        sql = ''

        if not self._is_ready():
            errors.append((_ERROR, gettext('Error: Class is not ready')))

        elif id is None:
            errors.append((_ERROR, gettext('Error: Missing Primary Key for update')))

        if not errors:
            sql = command % id

            # --------------
            # Execute $ Exit
            # --------------

            rows = self.run(sql, errors)

        return self._get_errors(errors)

    def run(self, sql, errors, **kw):
        """
            Run SQL-command.

            Arguments:
                sql     -- String, sql-command text
                errors  -- List, errors (mutable)
        """
        if not (sql and self._is_ready()):
            return None

        try:
            rows, error_msg = self.engine.runCommand(sql, with_error=True, **kw)

            if error_msg:
                errors.append((_UNDEFINED_ERROR, error_msg))

        except:
            if IsPrintExceptions:
                print_exception()

            raise

        return rows

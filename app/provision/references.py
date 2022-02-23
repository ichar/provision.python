# -*- coding: utf-8 -*-

__all__ = ['reference_factory',]

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, errorlog, print_to, print_exception,
     default_unicode, default_encoding
     )

from ..settings import gettext
from ..references import AbstractReference
from ..utils import isIterable

_UNDEFINED_ERROR = 2
_ERROR = 1
_WARNING = 0

_onplace = 'onplace'
_down = 'down'
_up = 'up'

_splitter = '.'


##  ====================
##  Provision.References
##  ====================

def addQueryOperator(query, operator=None):
    if query:
        for n in range(0, len(query)-1):
            query.insert(n*2+1, ('operator', ' %s ' % (operator or 'AND')))

def to_ascii(s):
    return s and s.encode(default_encoding, 'ignore').decode(default_encoding) or ''


class TreeReference(AbstractReference):

    _default_node_mask = '%04d'
    _default_code = -1

    def __init__(self, engine, view, id=None):
        super().__init__(engine, view, id=id)

        self._cache = {}

    @property
    def node_code(self):
        return 'NodeCode'
    @property
    def node_level(self):
        return 'NodeLevel'
    @property
    def node_params(self):
        return 'Params'
    @property
    def parent_node_code(self):
        return 'ParentNodeCode'
    @property
    def parent_node_level(self):
        return 'ParentNodeLevel'
    @property
    def direction(self):
        return 'Direction'
    @property
    def children(self):
        return 'Children'
    @property
    def parent(self):
        return 'Parent'

    @staticmethod
    def down(direction):
        return not direction or direction == _down
    @staticmethod
    def onplace(direction):
        return direction == _onplace
    @staticmethod
    def up(direction):
        return direction == _up

    def get_node_code(self, code, index=None):
        """
            Returns Node Self Code value by the given original code, or Parent Node Original Code by positional index.

            Arguments:
                code        -- String, node original code: '0000.0001 ... 9999'

            Keyword arguments:
                index       -- Int, parent level index

            Returns:
                code        -- String.
        """
        if not code or index == 0:
            return ''
        levels = code.split(_splitter)
        if index:
            return len(levels) > index and _splitter.join(levels[0:index]) or ''
        return levels[-1] or ''

    def get_node_level(self, code):
        """
            Returns Node Level value by the given code.

            Arguments:
                code        -- String, node original code with delimeters

            Returns:
                level       -- Int or 0.
        """
        return code and len(code.split(_splitter)) or 0

    def setNodeCode(self, parent, node=None, direction=None):
        """
            Set Node Original Code value by the given parent original code, node self code and moving direction.

            Arguments:
                parent      -- String, parent node original code with delimeter: '0000.0001 ... 9999'
                code        -- String, node self code: '0000'
                direction   -- String, direction: 'up|down|onplace'

            Returns:
                code        -- String.
        """
        if self.onplace(direction):
            return parent or ''
        if self.up(direction):
            return parent and _splitter.join(parent.split(_splitter)[:-1])
        return '%s%s%s' % (parent or '', parent and _splitter or '', node or '')

    def setNodeLevel(self, level, direction):
        """
            Set Node Level value by the given node level and moving direction.

            Arguments:
                level       -- Int, node level value
                direction   -- String, direction

            Returns:
                level       -- Int or 0.
        """
        x = int(level or '0') + (self.down(direction) and 1 or self.up(direction) and -1 or 0)
        return x > 0 and x or 1

    def _children_items(self, id, code, order=None):
        query = code and [(self.node_code, code),] or None

        if IsDeepDebug:
            print('--> _children_items: %s, code:[%s]' % (id, code))

        return super().getItems(query=query, id=id, order=order)

    def getChildren(self, id, code, order=None):
        return [x.get(self.id) for x in self._children_items(id, code, order=order)]

    def _update_children(self, code):
        errors = []

        sql = "UPDATE [%(database)s].[dbo].[DIC_StockList_tb] " \
              "SET %(children)s=[%(database)s].[dbo].[GET_RowsNodeCount_fn](%(node_code)s) WHERE %(node_code)s like '%(code)s%%'" % {
                'database'  : self.engine.database,
                'node_code' : self.node_code,
                'code'      : code,
                'children'  : self.children,
            }

        rows = super().run(sql, errors=errors, no_cursor=True)

        return not errors and True or False

    def _parent_items(self, id, code, order=None):
        parent_codes, s = [], ''

        for n, x in enumerate(code.split(_splitter)):
            s += '%s%s' % (n > 0 and _splitter or '', x)
            parent_codes.append(s)

        nested_code = ':'.join(parent_codes)

        where = "%(node_code)s in (select item from [%(database)s].[dbo].[GET_SplittedStrings_fn]('%(nested_code)s', ':'))" % {
                'database'    : self.engine.database,
                'nested_code' : nested_code,
                'node_code'   : self.node_code,
            }

        if not order:
            order = '%s desc' % self.node_code

        if IsDeepDebug:
            print('--> _parent_items: %s, code:[%s], where:%s, order:%s' % (id, code, where, order))

        rows = super().getItems(None, id=id, where=where, order=order)

        return parent_codes, nested_code, rows

    def addItem(self, items, id=None, **kw):
        id, errors = super().addItem(items=items, id=id, **kw)

        code = items and items.get(self.node_code) or ''

        self._update_children(code)

        return id, errors

    def updateItem(self, id, items):
        return super().updateItem(id=id, items=items)

    def removeItem(self, id):
        errors = []

        sql = "SELECT 1 FROM [%(database)s].[dbo].[WEB_Orders_vw] WHERE StockListNodeCode like (" \
              "select top 1 %(node_code)s+'%%' from [%(database)s].[dbo].[DIC_StockList_tb] where TID=%(id)s)" % {
                'database'    : self.engine.database,
                'node_code'   : self.node_code,
                'id'          : str(id),
            }

        rows = super().run(sql, errors=errors, no_cursor=False)

        if rows:
            errors.append(gettext('Error: Item cannot be removed by references existence reason'))
            return errors

        errors = super().removeItem(id=id)

        self._update_children('')

        return errors

    def getItems(self, query, id, **kw):
        """
            Returns reference items list with SQL-query.

            Arguments:
                query   -- List|String, query parameters: [('key':'value'), ...] or search string
                id      -- Int or String, selected item id

            Keyword arguments:
                items   -- Dict, field values: {name : value, ...}
                state   -- String|Int, state of the object

            Returns:
                rows    -- List, mappings list: [{'key':'value', ...}].
        """
        params = query and isIterable(query) and dict(query) or kw.get('items') or {}

        direction, level, parent_code, node_query, order = '', -1, '', None, ''

        if query and not params:
            node_query = to_ascii(query)

        else:
            direction = params.get(self.direction)

            level = self.setNodeLevel(params.get(self.node_level), direction)
            parent_code = self.setNodeCode(params.get(self.parent_node_code), params.get(self.node_code), direction)

            node_query = [
                (self.node_code, parent_code),
                (self.node_level, level),
            ]

            addQueryOperator(node_query)

            if (self.up(direction) or self.onplace(direction)) and not id:
                id = params.get(self.id) or kw.get('state')

        order = level > 1 and self.value or ''

        rows = super().getItems(query=node_query, id=id, order=order, **kw)

        is_selected = False

        for row in rows:
            if level == -1:
                x = row[self.node_level]
                parent_level = x > 1 and x - 1 or 1
                has_children = row[self.children] > 0

                row[self.parent_node_level] = parent_level
                row[self.parent_node_code] = self.get_node_code(row[self.node_code], index=parent_level)
                row[self.direction] = has_children and _down or parent_level > 0 and _onplace or _down
                row[self.parent] = has_children and 1 or 0

            else:
                row[self.parent_node_level] = level - 1
                row[self.parent_node_code] = parent_code
                row[self.direction] = _down
                row[self.parent] = row[self.children] > 0 and 1 or 0

            row[self.node_code] = self.get_node_code(row[self.node_code])

            if row.get('selected'):
                is_selected = True

        if not is_selected and len(rows) > 0:
            rows[0]['selected'] = 'selected'

        if level > 1:
            parent_codes, nested_code, parents = self._parent_items(id, parent_code)

            for n, row in enumerate(parents):
                # XXX new node level for first item only
                row[self.node_level] = level
                row[self.node_code] = self.get_node_code(row[self.node_code])

                level -= 1

                row[self.parent_node_level] = level
                row[self.parent_node_code] = parent_codes[len(parents)-(n+1)]
                row[self.direction] = _up
                row[self.parent] = 1
                row['style'] = 'parent'

                rows.insert(0, row)

        return rows

    def getNodeItems(self, id, **kw):
        """
            Returns children of node by id
        """
        node = id and self.getItemById(id) or None

        query = []

        if node:
            code = node[self.node_code]
            level = node[self.node_level] + 1
        else:
            code = ''
            level = 1

        query.append((self.node_code, code))

        if level:
            query.append((self.node_level, level))

        addQueryOperator(query, operator='AND')

        order = self.node_code

        rows = super().getItems(query=query, id=id, order=order) or []

        if kw.get('with_root') and node:
            rows.insert(0, node)

        return rows

    def setNewNode(self, items):
        """
            Update Tree-object new node items.

            Arguments:
                items   -- Dict, field values: {name : value, ...}

            Returns:
                errors  -- List, Errors list: ['error', ...], sorted by error code: 2,1,0. Empty is success.
        """
        value, name, errors = '', self.node_code, []

        level = int(items.get(self.node_level) or 1)
        parent_node_code = items.get(self.parent_node_code) or ''

        command = "SELECT max(%(node_code)s) FROM %(table)s WHERE %(node_code)s like '%(parent_node_code)s%%' and %(node_level)s=%(level)d"
        
        values = {
            'node_code'        : self.node_code,
            'table'            : self._table,
            'parent_node_code' : parent_node_code,
            'node_level'       : self.node_level,
            'level'            : level,
        }
        
        sql = command % values

        rows = self.run(sql, errors, no_cursor=False)

        if rows:
            max_code = int(self.get_node_code(rows[0][0]) or self._default_code)
        else:
            max_code = self._default_code

        code = '%s%s%s' % (
            parent_node_code, 
            parent_node_code and _splitter or '', 
            self._default_node_mask % (max_code + 1)
        )

        if IsDeepDebug:
            print('--> new node: %s[%s], items:%s' % (name, code, repr(items)))

        if not errors:
            items.update({
                self.node_code  : code,
                self.node_level : level,
            })

        return errors

    def _node_items(self, id, code, order=None):
        query = code and [(self.node_code, code),] or [(self.id, id),] or None

        if IsDeepDebug:
            print('--> _node_items: %s, code:[%s]' % (id, code))

        return super().getItems(query=query, id=id, order=order)

    def _check_parents(self, id, code):
        parents = None

        if id in self._cache:
            parents = self._cache[id]
        else:
            rows = self._node_items(id, code, order=self.node_code)

            if rows:
                parent_code = rows[0].get(self.node_code)
                parent_codes, nested_code, parents = self._parent_items(id, parent_code, order=self.node_code)

                self._cache[id] = parents

        return parents

    @staticmethod
    def _get_node_tag(locator, blank, id, title, query_string, **kw):
        return '<a %s target="_%s" href="/%s/stock/%s%s">%s</a>' % ( 
                    'cls' in kw and 'class="%s"' % kw['cls'] or '',
                    blank or 'self',
                    locator, 
                    id, 
                    query_string or '',
                    title,
                    )

    def getNodeClassCode(self, id):
        """
            Returns qualified Node Class Code by ID

            Arguments:
                id          -- Int or String, selected item id

            Returns:
                code        -- String, node original code: '0000.0001 ... 9999'
        """
        code = ''

        parents = self._check_parents(id, code=None)

        if parents:
            code = _splitter.join([x.get(self.node_code) for x in parents[-1:]])

        return code

    def getNodeClassParams(self, id):
        """
            Returns qualified Node Class Params (RefCode1C) by ID

            Arguments:
                id          -- Int or String, selected item id

            Returns:
                params list -- String, node original params: 'X1:X2:...'
        """
        params = ''

        parents = self._check_parents(id, code=None)

        def _get_params(value):
            return value or ''

        if parents:
            params = ':'.join(filter(None, [_get_params(x.get(self.node_params)) for x in parents]))

        return params

    def getNodeClassName(self, id, code=None):
        """
            Returns qualified Node Class Name by ID or NodeCode.

            Arguments:
                id          -- Int or String, selected item id

            Keyword arguments:
                code        -- String, node original code: '0000.0001 ... 9999'

            Returns:
                name        -- String, node name with delimeters
                parent_code -- String, parent node code with delimeters
        """
        name, parent_code = '', ''

        parents = self._check_parents(id, code)

        if parents:
            if not code:
                name = _splitter.join([x.get(self.value) for x in parents])
                parent_code = _splitter.join([x.get(self.node_code) for x in parents[0:-1]])
            else:
                name = _splitter.join([x.get(self.value) for x in parents if code.startswith(x.get(self.node_code))])
                parent_code = self.get_node_code(code, -1)

        return name, parent_code

    def getNodeClassTag(self, locator, id, code=None, blank=None, query_string=None, **kw):
        """
            Returns qualified Node Class HTML Tag by NodeCode.

            Arguments:
                locator     -- String, application name used for a link
                id          -- Int or String, selected item id

            Keyword arguments:
                code        -- String, node original code: '0000.0001 ... 9999'

            Returns:
                tag         -- String, reentrant subnodes HTML content
        """
        tag = ''

        parents = self._check_parents(id, code)

        if parents:
            for x in parents:
                if tag:
                    tag += '.'
                tag += self._get_node_tag(locator, blank, x.get(self.id), x.get(self.value), query_string, **kw)

        return tag

    def getRenderedNodes(self, locator, id, code=None, blank=None, query_string=None):
        """
            Returns qualified Node Class Name and HTML Tag by ID.

            Arguments:
                locator     -- String, application name used for a link
                id          -- Int or String, selected item id

            Keyword arguments:
                code        -- String, node original code: '0000.0001 ... 9999'

            Returns:
                name        -- String, node name with delimeters
                parent_code -- String, parent node code with delimeters
                tag         -- String, reentrant subnodes HTML content
        """
        columns = (self.id, self.value, self.node_level, self.node_code)
        query = [('_', "%s like '%%'" % self.node_code)]
        order = self.node_code

        if id:
            # Add node code query parsing for given id XXX
            pass

        nodes = {}

        current_level = 0
        node_names = []
        node_tags = []

        rows = super().getItems(query=query, id=id, order=order, columns=columns)

        for row in rows:
            node_level = row[self.node_level]
            name = row[self.value]

            id = row[self.id]

            if node_level > current_level:
                node_names.append(name)
                node_tags.append(self._get_node_tag(locator, blank, id, name, query_string))
            else:
                if node_level < current_level:
                    for n in range(0, current_level-node_level):
                        del node_names[-1]
                        del node_tags[-1]
                node_names[-1] = name
                node_tags[-1] = self._get_node_tag(locator, blank, id, name, query_string)

            current_level = node_level

            nodes[id] = {
                'name' : (_splitter.join(node_names), self.get_node_code(row[self.node_code], -1)),
                'tag'  : _splitter.join(node_tags),
            }

        return nodes

    def calculateOrdersOfNode(self, id, code=None):
        """
            Calculate Orders price of Node by ID or NodeCode

            Arguments:
                id          -- Int or String, selected item id

            Keyword arguments:
                code        -- String, node original code: '0000.0001 ... 9999'

            Returns:
                price       -- Float, price total
        """
        pass

##  ======================
##  ProvisionDB.References
##  ======================

class DicStockList(TreeReference):

    def __init__(self, engine):
        super(DicStockList, self).__init__(engine, 'provision.stocklist')

    def addItem(self, items, id=None, **kw):
        return super(DicStockList, self).addItem(items, calculated_pk=False, with_identity=True)

    @property
    def value(self):
        return 'Name'

    @property
    def title(self):
        return 'Номенклатурный классификатор'

    @property
    def searchable(self):
        return ('Name', 'Title', 'NodeCode', 'RefCode1C', 'ShortName', 'Comment')

    @property
    def numeric(self):
        return ('TID', 'NodeLevel',)

    @property
    def editable_columns(self):
        return ['Name', 'RefCode1C', 'ShortName', 'Comment', 'EditedBy']

    @property
    def service_columns(self):
        return ['NodeLevel', 'NodeCode', 'Children']

    @property
    def hidden_columns(self):
        return self._config.get('hidden_columns') or []


reference_factory = {
    # ----------
    # References
    # ----------
    'stocklist' : DicStockList,
}

# -*- coding: utf-8 -*-

import re
from decimal import *
from operator import itemgetter

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, errorlog, print_to, print_exception,
     default_unicode, default_encoding,
     )

from ..settings import *
from ..utils import (
     isIterable, getToday, Capitalize, spent_time,
     getDate, getString, getHtmlString, getHtmlCaption, getMoney, getCurrency
     )


class Base:

    def __init__(self, engine, *args, **kwargs):
        if IsDeepDebug:
            print('Base init')

        super().__init__(*args, **kwargs)

        self.engine = engine
        self.login = g.current_user.login

    def _init_state(self, attrs, factory, *args, **kwargs):
        if IsDeepDebug:
            print('Base initstate')

    @property
    def driver(self):
        return self.engine.driver

    @staticmethod
    def set_factory(key, factory):
        if factory is not None and isinstance(factory, dict):
            x = factory.get(key)
            if x is not None and callable(x):
                return x
        return None


class BarcodeReader(Base):

    def __init__(self, engine, **kw):
        if IsDeepDebug:
            print('BarcodeReader init')

        super().__init__(engine)

        self._errors = []

        self._locator = None
        self._page = None
        self._stocklist = None

        self._order_id = None
        self._item_id = None
        self._date = None

        self.review_statuses = (1,2,3,4,5,6)

        self._attrs = {}

        self._cache = {}

    def _init_state(self, attrs=None, factory=None):
        if IsDeepDebug:
            print('BarcodeReader initstate')

        super()._init_state(attrs, factory)

        if attrs:
            self._locator = attrs.get('locator')
            self._page = attrs.get('page')
            self._stocklist = attrs.get('stocklist')

        self._extra = 1
        self._colored = 0

        if factory:
            for key in factory.keys():
                setattr(self, '_%s' % key, self.set_factory(key, factory))

        self._seller_id = None

    @property
    def page(self):
        return self._page
    @property
    def is_error(self):
        return self.engine.is_error
    @property
    def order_id(self):
        return self._order_id
    @property
    def item_id(self):
        return self._item_id
    @property
    def locator(self):
        return self._locator
    @property
    def blank(self):
        return 'blank'
    @property
    def attrs(self):
        return self._attrs
    @property
    def stocklist(self):
        return self.page.stocklist
    @property
    def query_string(self):
        return '?seller=%s' % self._seller_id
    @property
    def sql_params(self):
        return ''

    def _get_attrs(self):
        self._attrs['title'] = 'Информация о заявке снабжения %05s' % self.order_id

    def _get_where(self):
        where = 'TID=%s' % self._order_id or 0

        if IsTrace and IsDeepDebug:
            print_to(None, '--> barcode reader:%s, where=%s' % (self.login, where))

        return where

    @staticmethod
    def get_types():
        pass

    def getNodeClassName(self, id, code=None):
        """
            Proxy method for TreeReference
        """
        if id not in self._cache:
            self._cache[id] = {}

        if 'name' not in self._cache[id]:
            self._cache[id]['name'] = self.stocklist.getNodeClassName(id, code=code)

        return self._cache[id]['name']

    def getNodeClassTag(self, locator, id, code=None, blank=None):
        """
            Proxy method for TreeReference
        """
        if id not in self._cache:
            self._cache[id] = {}

        if 'tag' not in self._cache[id]:
            self._cache[id]['tag'] = self.stocklist.getNodeClassTag(locator, id, code=code, blank=blank, query_string=self.query_string)

        return self._cache[id]['tag']

    def get_node_level(self, code):
        """
            Proxy method for TreeReference
        """
        return self.stocklist.get_node_level(code)

    def registry(self):
        return {
            'selected_columns' : 'TID:Total'
        }

    def date_state(self, item):
        rd = ''
        states = ('исполнено', 'оплачено', 'согласовано', 'обосновано', 'создано',)

        for i, k in enumerate([4, 3, 2, 1, 0]):
            if item['dates'][k][2]:
                rd = '%s (%s)' % (item['dates'][k][2], states[i])
                break

        return rd or ''

    def parse(self, barcode):
        x = barcode.split(':')

        if len(x) != 3:
            return

        try:
            self._order_id = int(x[0])
            self._item_id = int(x[1])
            self._date = getDate(x[2], format=self.page.barcode_date_format, is_date=True)
        except:
            if IsPrintExceptions:
                print_exception()

        self._get_attrs()

    def print_orders(self, params):
        pass

    def refresh(self):
        pass

    def render(self, sort_by_total_rub=0, **kw):
        """
            Render BarcodeReader data by the given ID
        """
        orders = []
        titles = {}
        items = {}

        self._started = getToday()

        if IsTrace:
            print_to(None, '>>> barcode reader started')

        columns = (
            'np', 
            #'TID', 
            'showbar', 
            'Article', 
            'Qty', 
            'Subdivision', 
            #'Sector', 
            'Price', 
            'Currency', 
            'Total', 
            #'Condition', 
            #'RD',
        )

        content_state = kw.get('content_state') and 'collapsed' or 'expanded'

        currency = 'RUB'
        currency_header = self.page.get_header('OrderPrice')

        where = self._get_where()

        total = 0
        sum_price = Decimal(0.0)
        n = 0

        seller_info = {}

        for order in self._get_orders(where=where, order=kw.get('order') or 'TID desc'):
            order_id = order['TID']
            """
            if not order['Price']:
                continue
            """
            n += 1

            order['np'] = n

            seller_id = order['SellerID']
            no_seller = seller_id in seller_info and True or False

            info = self._info(order_id=order_id, no_extra=True, no_seller=no_seller, stock=self, order=order)
            item = info[1]

            if seller_id:
                if not no_seller:
                    seller_info[seller_id] = (item['seller_name'], item['seller_link'],)
                else:
                    item['seller_name'] = seller_info[seller_id][0]
                    item['seller_link'] = seller_info[seller_id][1]
            else:
                item['seller_name'] = ''
                item['seller_link'] = ''

            price = re.sub(r'\s', '', item.get(currency) or '')
            item['price'] = item.get(currency) or 0

            total += 1
            sum_price += price and Decimal(price) or 0

            if not (order.get('Price') and item['price']):
                order['Price'] = '0'

            if not order.get('Currency'):
                order['Currency'] = currency

            order['TotalRub'] = self._calc_rub(order['Total'], order['Currency'])
            order['Total'] = getCurrency(order['Total'], points=1) or '0.00'

            order['showbar'] = ''
            order['classes'] = {
                'showbar'  : content_state,
                'Currency' : order['Currency'],
                'Qty'      : 'qty',
            }

            item['num'] = self._get_order_link(order, name=item['num'])
            item['equipment_title'] = item['equipment_title'] or ''
            item['stocklist_tag'] = ''

            status = item['status']

            if 'stocklist' in item:
                stocklist = item['stocklist']
                item['stocklist_tag'] = self.getNodeClassTag(self.locator, stocklist.get('id'), code=stocklist.get('code'), blank=self.blank)

            item['date'] = getDate(self._date, format=DEFAULT_DATE_FORMAT[1])
            item['item_id'] = self._item_id

            item['RD'] = self.date_state(item)

            items[order_id] = item

            orders.append(order)

            if IsTrace and IsDeepDebug:
                print_to(None, '>>> barcode reader %02d: %s' % (n, getToday()))

            titles[order_id] = {
                'np'          : '№ п/п',
                'showbar'     : '',
                'Article'     : self.page.get_header('Article'), 
                'Qty'         : 'Количество', 
                'Subdivision' : self.page.get_header('Subdivision'), 
                'Price'       : self.page.get_header('PriceType'), 
                'Currency'    : self.page.get_header('CurrencyType'), 
                'Total'       : 'Сумма = %s' % status[1].upper(), 
            }

        if sort_by_total_rub:
            orders = sorted(orders, key=itemgetter('TotalRub'), reverse=True)
            n = 0
            for order in orders:
                n += 1
                order['np'] = n

        keys = [
            'num',
            'equipment_title',
            'stocklist_tag',
            'seller_link',
            'purpose',
            'subdivision',
            'author',
            'RD',
            'condition',
            'price',
            'date',
            'item_id',
        ]

        if self.page.model == 0:
            keys.insert(6, 'sector')

        headers = {
            'num'             : {'class' : 'num', 'title' : self.page.get_header('num')},
            'equipment_title' : {'class' : 'equipment_title', 'title' : self.page.get_header('Equipment')},
            'stocklist_tag'   : {'class' : 'stocklist', 'title' : self.page.get_header('StockName')},
            'seller_link'     : {'class' : 'seller', 'title' : self.page.get_header('Seller')},
            'purpose'         : {'class' : 'purpose', 'title' : self.page.get_header('Purpose')},
            'subdivision'     : {'class' : 'subdivision', 'title' : self.page.get_header('Subdivision')},
            'sector'          : {'class' : 'sector', 'title' : self.page.get_header('Sector')},
            'author'          : {'class' : 'author', 'title' : self.page.get_header('AuthorName')},
            'RD'              : {'class' : 'RD', 'title' : self.page.get_header('OrderDate')},
            'condition'       : {'class' : 'condition', 'title' : self.page.get_header('Condition')},
            'price'           : {'class' : 'price', 'title' : currency_header},
            'date'            : {'class' : 'date', 'title' : 'Дата оприходования'},
            'item_id'         : {'class' : 'item_id', 'title' : 'ID счета'},
        }

        data = {
            'attrs'     : self.attrs,
            'columns'   : columns,
            'titles'    : titles,
            'headers'   : headers,
            'keys'      : keys,
            'orders'    : orders,
            'items'     : items,
            'total'     : total,
            'sum_price' : sum_price and getCurrency(getMoney(str(sum_price))) or '0.00',
            'currency'  : currency,
            'types'     : self.get_types(),
            'registry'  : self.registry(),
        }

        self._finished = getToday()

        if IsTrace:
            print_to(None, '>>> barcode reader finished: %s sec' % spent_time(self._started, self._finished))

        return data

    def render_html(self):
        where = 'TID=%s' % self.order_id

        orders = self._get_orders(where=where)

        content = '<div>%s</div>' % '<br>'.join(['<span>%s</span>' % x['Article'] for x in orders])

        return 'BarcodeReader ID: %s, Total orders: %d %s<br>Is_Error:%s' % (self.id, len(orders), content, self.is_error)

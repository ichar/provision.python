# -*- coding: utf-8 -*-

import re
from decimal import *
from operator import itemgetter

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, errorlog, print_to, print_exception,
     default_unicode, default_encoding
     )

from ..settings import *
from ..utils import (
     isIterable, getToday, Capitalize, spent_time,
     getString, getHtmlString, getHtmlCaption, getMoney, getCurrency
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

    ##
    ##  INTERFACE
    ##

    def _before(self, **kw):
        pass

    def _after(self, **kw):
        pass

    def run(self, method, **kw):
        self._started = getToday()

        if IsTrace:
            print_to(None, '>>> stock started')

        try:
            self._before(**kw)
            return method(**kw)
        except:
            raise
        finally:
            self._after(**kw)

            self._finished = getToday()

            if IsTrace:
                print_to(None, '>>> stock finished: %s sec' % spent_time(self._started, self._finished))


class Expires(Base):

    default_template = 'provision-cost-orders'

    def __init__(self, engine):
        if IsDeepDebug:
            print('Expires init')

        super().__init__(engine)

        self._errors = []

        self._locator = None
        self._page = None
        self._stocklist = None

        self.review_statuses = (1,2,3,4,5,6)

        self._orders = []
        self._params = []
        self._payments = []

        self._order = None
        self._order_id = None
        self._order_model = None

        self._attrs = {}

        self._cache = {}

    def _init_state(self, attrs=None, factory=None):
        if IsDeepDebug:
            print('Expires initstate')

        super()._init_state(attrs, factory)

        if attrs:
            self._locator = attrs.get('locator')
            self._page = attrs.get('page')
            self._stocklist = attrs.get('stocklist')

        if factory:
            for key in factory.keys():
                setattr(self, '_%s' % key, self.set_factory(key, factory))

        self._get_attrs()

        if self.stocklist is not None:
            self._cache = self.stocklist.getRenderedNodes(self.locator, 0, blank=self.blank, query_string=self.query_string)

    @property
    def page(self):
        return self._page
    @property
    def is_error(self):
        return self.engine.is_error
    @property
    def id(self):
        return self._id
    @property
    def locator(self):
        return self._locator
    @property
    def blank(self):
        return 'self'
    @property
    def attrs(self):
        return self._attrs
    @property
    def orders(self):
        return self._orders
    @property
    def params(self):
        return self._params['data'] or []
    @property
    def payments(self):
        return self._payments['data'] or []
    @property
    def stocklist(self):
        return self._stocklist
    @property
    def stocks(self):
        return self._stocks
    @property
    def stock_id(self):
        return self._attrs.get(self._stocklist.id)
    @property
    def stock_code(self):
        return self._attrs.get(self._stocklist.node_code)

    @staticmethod
    def get_order_id(order):
        return order.get('TID')
    @staticmethod
    def get_order_model(order):
        return order.get('MD')
    @staticmethod
    def get_order_currency(order):
        return order.get('Currency')
    @staticmethod
    def get_order_condition(order):
        return order.get('ConditionCode')
    @staticmethod
    def get_order_paid(order):
        return order.get('Paid')

    def get_order_total(self, order):
        return order.get('Total')

    def _before(self, **kw):
        self.set_orders(**kw)

    def _check_is_valid(self, order):
        self._set_order(order)
        return self._is_valid()

    def _is_valid(self):
        return True

    def _param(self, code):
        if code in self._cache['params']:
            return self._cache['params']['code']
        v = None
        for p in self.params:
            if p.get('Code') == code:
                v = p.get('Value')
                break
        self._cache['params']['code'] = v
        return v

    def _set_order(self, order):
        self._order = order
        self._order_id = self.get_order_id(order)
        self._order_model = self.get_order_model(order)

    def set_params(self):
        self._cache['params'] = {}
        self._params = self._get_params(self._order_id)

    def set_payments(self):
        self._cache['payments'] = {}
        self._payments = self._get_payments(self._order_id)

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

    ##
    ##  INTERFACE
    ##

    def set_orders(self, **kw):
        """
            Sets orders matched for the given Params
        """
        pass

    def _get_attrs(self):
        pass

    def registry(self):
        pass

    def sort(self):
        return self.render(sort_by_total_rub=1)

    def render(self, sort_by_total_rub=0, **kw):
        pass

    def render_html(self):
        pass


class OrdersInExpire(Expires):
    
    def __init__(self, engine, **kw):
        if IsDeepDebug:
            print('OrdersInExpire init')

        super().__init__(engine)

    def _init_state(self, attrs=None, factory=None):
        if IsDeepDebug:
            print('OrdersInExpire initstate')

        super()._init_state(attrs, factory)

        self._extra = 1
        self._colored = 0

    @property
    def query_string(self):
        return '?seller=%s' % self.id
    @property
    def sql_params(self):
        return ''

    def _get_attrs(self):
        self._attrs = self._get_seller(self.id)
        self._attrs['title'] = 'Информация о контрагенте %s' % self._attrs['Name']

    def _get_where(self):
        where = 'SellerID=%s%s and Status<9%s' % ( 
            self.id, self.page.is_no_price and ' and %s' % self.page.subdivision_documents() or '',
            self.sql_params
            )

        if IsTrace:
            print_to(None, '--> sellers:%s, where=%s' % (self.login, where))

        return where

    @staticmethod
    def refreshed_items(seller, with_html=None):
        data = dict(('seller_%s' % x.lower(), seller and seller.get(x) or '') for x in (
            'Code', 'Title', 'Address', 'Contact', 'URL', 'Phone', 'Email',
            ))

        if seller and with_html:
            for key in ('Address', 'URL',):
                name = 'seller_%s' % key.lower()
                data[name] = getHtmlCaption(name)

        return data

    @staticmethod
    def date_state(item):
        rd = ''
        states = ('исполнено', 'оплачено', 'согласовано', 'обосновано', 'создано',)

        for i, k in enumerate([4, 3, 2, 1, 0]):
            if item['dates'][k][2]:
                rd = '%s (%s)' % (item['dates'][k][2], states[i])
                break

        return rd or ''

    @staticmethod
    def _selected_columns(status):
        titles = {'TID':'ID платежа', 'Total':'Сумма платежа'}
        return dict([(x, '%s = %s' % (titles[x], status)) for x in ('TID', 'Total',)])

    @staticmethod
    def _get_sum_price(total, sum_price, to_pay, currency):
        return '%s: %s %s %s (%s) %s' % (
            gettext('Total orders'), 
            total, 
            gettext('with price'), 
            sum_price and getCurrency(getMoney(str(sum_price))) or '0.00',
            to_pay and getCurrency(getMoney(str(to_pay))) or '0.00',
            currency
            )

    def _get_price(self, order, sum_price, to_pay, currency, statuses=None):
        if not order.get('Currency'):
            order['Currency'] = currency

        s = order['Total'] or 0.0

        if order['Price'] is None:
            order['Price'] = 0

        order['Total'] = getCurrency(s, points=1) or '0.00'

        price = self._calc_rub(s, order['Currency'])

        sum_price += price and Decimal(price) or 0

        if order['Status'] in (statuses or self.review_statuses):
            to_pay += price and Decimal(price) or 0

        return price, sum_price, to_pay

    def print_orders(self, params):
        data = {}
        props = {'attrs' : self.attrs}

        columns = 'np:TID:Article:Subdivision:Qty:Price:Currency:Total:Created:Status'.split(':')

        high = ' '.join(filter(None, ['high', self._extra and 'extra', self._colored and 'colored']))

        props['columns'] = {
            'np'            : {'td' : '', 'title' : '№', 'header' : ''}, 
            'TID'           : {'td' : '', 'title' : 'Номер заявки', 'header' : ''}, 
            'Article'       : {'td' : '', 'title' : 'Наименование товара', 'header' : ''}, 
            'Subdivision'   : {'td' : '', 'title' : 'Инициатор', 'header' : ''}, 
            'Qty'           : {'td' : '', 'title' : 'Количество', 'header' : ''}, 
            'Price'         : {'td' : '', 'title' : 'Цена', 'header' : '', 'div' : ' nowrap %s' % high},  
            'Currency'      : {'td' : '', 'title' : 'Валюта платежа', 'header' : '', 'div' : ' nowrap %s' % high}, 
            'Total'         : {'td' : '', 'title' : 'Сумма', 'header' : '', 'div' : ' nowrap %s' % high},  
            'Created'       : {'td' : ' hidden', 'title' : 'Дата', 'header' : ' hidden'},
            'Status'        : {'td' : ' nowrap', 'title' : 'Статус', 'header' : ''},
        }

        currency = 'RUB'
        statuses = (2,)

        total = 0
        sum_price = Decimal(0.0)
        to_pay = Decimal(0.0)
        n = 0

        where = self._get_where()

        ids = None

        rows = []

        for order in self._get_orders(where=where, order='TID desc'):
            order_id = order['TID']

            if ids and order_id not in ids:
                continue

            status = self._get_order_status(order['Status'])
            status_name = status[1].upper()

            price, sum_price, to_pay = self._get_price(order, sum_price, to_pay, currency, statuses=statuses)

            total += 1

            data[str(order_id)] = {
                'class'    : status[0], 
                'title'    : self._selected_columns(status[1].upper()),
                'Currency' : ' %s' % order['Currency'],
            }

            for column in ('Tax',):
                order[column] = getCurrency(order[column], points=1) or '0.00'

            n += 1

            order['np'] = n
            order['Created'] = self._get_date(order['Created'], format='<nobr>%Y-%m-%d</nobr>')
            order['Status'] = status_name

            rows.append(order)

        data['columns'] = columns
        data['rows'] = rows

        data['sum_price'] = self._get_sum_price(total, sum_price, to_pay, currency)

        props['show'] = 0

        return {'data' : data, 'props' : props}

    def render(self, sort_by_total_rub=0, **kw):
        """
            Render OrdersInExpire data by the given ID
        """
        orders = []
        titles = {}
        items = {}

        self._started = getToday()

        if IsTrace:
            print_to(None, '>>> seller started')

        columns = (
            'np',
            #'TID', 
            'Article', 
            'Qty', 
            'Subdivision', 
            'Price', 
            'Currency', 
            'Total', 
            #'Condition', 
            #'RD',
        )

        currency = 'RUB'
        currency_header = 'Цена в рублях'

        where = self._get_where()

        total = 0
        sum_price = Decimal(0.0)
        n = 0

        for order in self._get_orders(where=where, order=kw.get('order') or 'TID desc'):
            order_id = order['TID']
            """
            if not order['Price']:
                continue
            """
            n += 1

            order['np'] = n

            info = self._info(order_id=order_id, no_extra=True, stock=self, order=order)
            item = info[1]

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

            order['classes'] = {
                'Currency' : order['Currency'],
                'Qty'      : 'qty',
            }

            item['num'] = self._get_order_link(order, name=item['num'])
            item['equipment_title'] = item['equipment_title'] or ''
            item['stocklist_tag'] = ''

            status = item['status']

            if 'stocklist' in item:
                stocklist = item['stocklist']
                item['stocklist_tag'] = self.getNodeClassTag(self.locator, stocklist['id'], code=stocklist['code'], blank=self.blank)

            item['RD'] = self.date_state(item)

            items[order_id] = item

            orders.append(order)

            if IsTrace and IsDeepDebug:
                print_to(None, '>>> seller %02d: %s' % (n, getToday()))

            titles[order_id] = {
                'np'          : '№ п/п',
                'Article'     : 'Наименование товара', 
                'Qty'         : 'Количество', 
                'Subdivision' : 'Инициатор платежа', 
                'Price'       : 'Цена за единицу', 
                'Currency'    : 'Валюта платежа', 
                'Total'       : 'Сумма = %s' % status[1].upper(), 
            }

        if sort_by_total_rub:
            orders = sorted(orders, key=itemgetter('TotalRub'), reverse=True)
            n = 0
            for order in orders:
                n += 1
                order['np'] = n

        keys = (
            'num',
            'equipment_title',
            'stocklist_tag',
            'purpose',
            'subdivision',
            'author',
            'RD',
            'condition',
            'price',
        )

        headers = {
            'num'             : {'class' : 'num', 'title' : 'Номер заявки'},
            'equipment_title' : {'class' : 'equipment_title', 'title' : 'Описание'},
            'stocklist_tag'   : {'class' : 'stocklist', 'title' : 'Класс товара'},
            'purpose'         : {'class' : 'purpose', 'title' : 'Обоснование'},
            'subdivision'     : {'class' : 'subdivision', 'title' : 'ПОТРЕБИТЕЛЬ'},
            'author'          : {'class' : 'author', 'title' : 'Заказчик'},
            'RD'              : {'class' : 'RD', 'title' : 'Дата заказа'},
            'condition'       : {'class' : 'condition', 'title' : 'Условия оплаты'},
            'price'           : {'class' : 'price', 'title' : currency_header},
        }

        data = {
            'seller'    : self.attrs,
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
            print_to(None, '>>> seller finished: %s sec' % spent_time(self._started, self._finished))

        return data

    def render_html(self):
        where = 'SellerID=%s' % self.id

        orders = self._get_orders(where=where)

        content = '<div>%s</div>' % '<br>'.join(['<span>%s</span>' % x['Article'] for x in orders])

        return 'OrdersInExpire ID: %s, Total orders: %d %s<br>Is_Error:%s' % (self.id, len(orders), content, self.is_error)

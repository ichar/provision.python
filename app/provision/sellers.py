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


class Seller(Base):

    def __init__(self, engine, id, **kw):
        if IsDeepDebug:
            print('Seller init')

        super().__init__(engine)

        self._id = id
        self._errors = []

        self._locator = None
        self._page = None
        self._stocklist = None

        self.review_statuses = (1,2,3,4,5,6)

        self._attrs = {}

        self._cache = {}

    def _init_state(self, attrs=None, factory=None):
        if IsDeepDebug:
            print('Seller initstate')

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
    def stocklist(self):
        return self._stocklist
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

        if IsTrace and IsDeepDebug:
            print_to(None, '--> sellers:%s, where=%s' % (self.login, where))

        return where

    @staticmethod
    def get_types():
        items = [
            (0, '---', '',), 
            (1, 'Общество с ограниченной ответственностью', 'ООО',), 
            (2, 'Публичное акционерное общество', 'ПАО',), 
            (3, 'Непубличное акционерное общество', 'ЗАО',), 
            (4, 'Акционерное общество', 'АО',), 
            (5, 'Индивидуальный предприниматель', 'ИП',), 
            (6, 'Государственное учреждение', 'ГУ',), 
            (7, 'Федеральное государственное унитарное предприятие', 'ФГУП',), 
            (11, 'Corporation', 'CO',),
            (12, 'Limited Liability Company', 'LLC',),
            (13, 'Foreign Corporation', 'FC',),
            (14, 'Joint Venture', 'JV',),
            (15, 'Incorporated', 'Inc.',),
            (16, 'Limited (Europe)', 'LTD',),
            (17, 'Gesellschaft mit beschränkter Haftung (Германия, Австрия, Швейцария)', 'GmbH',),
            (18, 'Aktiengesellschaft (Германия, Австрия, Швейцария)', 'AG',),
        ]
        return [(i, c and '%s (%s)' % (n,c) or n, c) for i,n,c in items]

    @staticmethod
    def render_name(name, ctype=None):
        s = ','
        seller_name = name.split(s)[0] if s in name else name
        types = Seller.get_types()
        seller_types = dict((x[0], tuple(types[n][1:])) for n, x in enumerate(types))
        return '%s%s' % (seller_name.strip(), ctype and ctype in seller_types and ', %s' % seller_types[ctype][1] or '')

    @staticmethod
    def render_link(locator, id, name, blank=None):
        return '<a target="_%s" href="/%s/seller/%s">%s</a>' % (blank or 'blank', locator, id, name)

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

    def getOrdersInfo(self):
        columns = ('TID', 'Currency', 'Total', 'Tax',)
        where = self._get_where()
        orders = self._get_orders(columns=columns, where=where)
        total_orders = len(orders)
        price = sum([self._calc_rub(order['Total'] or 0.0, order['Currency']) for order in orders])
        return '<span class="%s">Заказов: %s = %s руб.</span>' % (
            (total_orders > 10 and price > 10**6 or price > 10**7) and 'seller-orders-important' or 'seller-orders-info',
            total_orders, 
            getCurrency(price, points=1),
        )

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
            'Name'    : self.attrs.get('Name') or '',
            'Title'   : self.attrs.get('Title') or '',
            'Address' : self.attrs.get('Address') or '',
            'Code'    : self.attrs.get('Code') or '',
            'Type'    : self.attrs.get('Type') or 0,
            'Contact' : self.attrs.get('Contact') or '',
            'URL'     : self.attrs.get('URL') or '',
            'Phone'   : self.attrs.get('Phone') or '',
            'Email'   : self.attrs.get('Email') or '',
        }

    @staticmethod
    def date_state(item):
        rd = ''
        states = ('исполнено', 'оплачено', 'согласовано', 'обосновано', 'создано',)

        if 'dates' not in item:
            return ''

        items = len(item['dates'])
        for i, k in enumerate([4, 3, 2, 1, 0]):
            if k < items and item['dates'][k][2]:
                rd = '%s (%s)' % (item['dates'][k][2], states[i])
                break

        return rd or ''

    @staticmethod
    def _selected_columns(status):
        titles = {'TID':'ID платежа', 'Total':'Сумма платежа'}
        return dict([(x, '%s = %s' % (titles[x], status)) for x in ('TID', 'Total',)])

    @staticmethod
    def _get_sum_price(total, sum_price, to_pay, currency):
        return '%s: %s %s <span class="total_price">%s (%s)</span> %s' % (
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

    def update(self):
        """
            Update Seller registry attributes
        """
        self._errors = []

        self._attrs = self._get_seller(self.id)

        name = getString(get_request_item('name') or '')
        title = getString(get_request_item('title') or '')
        address = getString(get_request_item('address') or '')
        code = (get_request_item('code') or '').strip()
        ctype = int(get_request_item('type', check_int=True) or '0')
        contact = getString(get_request_item('contact') or '')
        url = getString(get_request_item('url') or '', save_links=True)
        phone = getString(get_request_item('phone') or '')
        email = getString(get_request_item('email') or '')

        if code and not code.isdigit():
            self._errors.append(gettext('Error: Code 1C is invalid.'))
            code = self.attrs.get('Code') or ''

        if IsTrace:
            print_to(None, '--> seller update:%s %s, name:%s, title:%s, address:%s, code:%s, ctype:%d, contact:%s, url:%s, phone:%s, email:%s' % (
                self._id, self.login,
                name,
                title,
                address,
                code,
                ctype,
                contact,
                url,
                phone,
                email,
                ))

        cursor, error_msg = self.page.runProcedure('provision-update-seller', 
                id=self.id,
                cname=name,
                title=title,
                address=address,
                code=code,
                ctype=ctype,
                contact=contact,
                url=url,
                phone=phone,
                email=email,
                login=self.login, 
                with_log=True,
                with_error=True,
            )

        if cursor:
            self.action_id = cursor[0][0]
            self.status = cursor[0][1]
        else:
            if IsTrace:
                print_to(None, '!!! seller_update, no cursor: %s' % str(self.login))

        if error_msg and engine.engine_error:
            self._errors.append(error_msg)

        self._attrs = self._get_seller(self.id)

        return self._errors

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

            status = g.page.get_status(order['Status'])
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

    def sort(self):
        return self.render(sort_by_total_rub=1)

    def render(self, sort_by_total_rub=0, **kw):
        """
            Render Seller data by the given ID
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

        for order in self._get_orders(where=where, order=kw.get('order') or 'TID desc'):
            order_id = order['TID']
            """
            if not order['Price']:
                continue
            """
            n += 1

            order['np'] = n

            info = self._info(order_id=order_id, no_extra=True, no_seller=True, stock=self, order=order)
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
                item['stocklist_tag'] = self.getNodeClassTag(self.locator, stocklist['id'], code=stocklist['code'], blank=self.blank)

            item['RD'] = self.date_state(item)

            items[order_id] = item

            orders.append(order)

            if IsTrace and IsDeepDebug:
                print_to(None, '>>> seller %02d: %s' % (n, getToday()))

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
            'purpose',
            'subdivision',
            'author',
            'RD',
            'condition',
            'price',
        ]

        if self.page.model == 0:
            keys.insert(5, 'sector')

        headers = {
            'num'             : {'class' : 'num', 'title' : self.page.get_header('num')},
            'equipment_title' : {'class' : 'equipment_title', 'title' : self.page.get_header('Equipment')},
            'stocklist_tag'   : {'class' : 'stocklist', 'title' : self.page.get_header('StockName')},
            'purpose'         : {'class' : 'purpose', 'title' : self.page.get_header('Purpose')},
            'subdivision'     : {'class' : 'subdivision', 'title' : self.page.get_header('Subdivision')},
            'sector'          : {'class' : 'sector', 'title' : self.page.get_header('Sector')},
            'author'          : {'class' : 'author', 'title' : self.page.get_header('AuthorName')},
            'RD'              : {'class' : 'RD', 'title' : self.page.get_header('OrderDate')},
            'condition'       : {'class' : 'condition', 'title' : self.page.get_header('Condition')},
            'price'           : {'class' : 'price', 'title' : currency_header},
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

        data['is_page_manager'] = self.page.is_page_manager

        self._finished = getToday()

        if IsTrace:
            print_to(None, '>>> seller finished: %s sec' % spent_time(self._started, self._finished))

        return data

    def render_html(self):
        where = 'SellerID=%s' % self.id

        orders = self._get_orders(where=where)

        content = '<div>%s</div>' % '<br>'.join(['<span>%s</span>' % x['Article'] for x in orders])

        return 'Seller ID: %s, Total orders: %d %s<br>Is_Error:%s' % (self.id, len(orders), content, self.is_error)

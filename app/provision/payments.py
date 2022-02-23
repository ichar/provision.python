# -*- coding: utf-8 -*-

import re
from decimal import *
from operator import itemgetter

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, errorlog, print_to, print_exception,
     DATE_STAMP, default_unicode, default_encoding
     )

from ..settings import *
#from ..database import database_config, getReferenceConfig
from ..utils import (
     isIterable, getDate, getToday, getDateOnly, daydelta, Capitalize, spent_time, cleanHtml,
     getString, getHtmlString, getHtmlCaption, getMoney, getCurrency
     )

#from .references import *


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


class PaymentsReview(Base):
    
    def __init__(self, engine, date, **kw):
        if IsDeepDebug:
            print('Payments init')

        super().__init__(engine)

        self._current_date = date == 'current' and getToday() or getDate(date, DATE_STAMP, is_date=True)
        self._date = getDate(self._current_date, DEFAULT_DATE_FORMAT[1])

        self._errors = []

        self._locator = None
        self._page = None

        self.review_statuses = (1,2,3)

        self._attrs = {}

    def _init_state(self, attrs=None, factory=None, *args, **kwargs):
        if IsDeepDebug:
            print('Payments initstate')

        super()._init_state(attrs, factory)

        if attrs:
            self._locator = attrs.get('locator')
            self._page = attrs.get('page')

        self._extra = 1
        self._colored = 0

        if factory:
            for key in factory.keys():
                setattr(self, '_%s' % key, self.set_factory(key, factory))

        self._get_attrs()

    @property
    def page(self):
        return self._page
    @property
    def is_error(self):
        return self.engine.is_error
    @property
    def date(self):
        return self._date
    @property
    def locator(self):
        return self._locator
    @property
    def forward(self):
        return getDate(daydelta(self._current_date, 1), DATE_STAMP)
    @property
    def back(self):
        return getDate(daydelta(self._current_date, -1), DATE_STAMP)
    @property
    def review_date(self):
        return getDate(self._current_date, DATE_STAMP)
    @property
    def attrs(self):
        return self._attrs

    def _get_attrs(self):
        self._attrs['review_date'] = self.review_date
        self._attrs['date'] = getDate(self._current_date, format='<nobr>%Y-%m-%d %B, %a</nobr>')
        self._attrs['title'] = 'Реестр платежей на %s' % self.review_date
        self._attrs['details'] = 'Согласование текущих платежей на дату'
        self._attrs['company'] = 'АО "РОЗАН ФАЙНЭНС"'
        self._attrs['comment'] = ''

    @staticmethod
    def payment_type(order):
        model = order.get('MD', 0)
        return model == 10 and 'Входящий платеж' or model == 1 and 'Внутренний платеж' or 'Исходящий платеж'

    @staticmethod
    def get_types():
        pass

    def _checkbox(self, id, name, value, checked=None):
        attrs = {'id' : id, 'name' : name, 'value' : value, 'checked' : checked and 'checked' or ''}
        tag = '<div class="value"><input type="checkbox" id="%(id)s" name="%(name)s" value="%(value)s" %(checked)s><span></span></div>' % attrs
        return tag

    def _get_status(self, status, index=0):
        x = g.page.get_payment_status(status)
        return x and x[index]

    def get_payments(self, **kw):
        template = 'provision-review-payments'
        columns = self.page.database_config(template)['columns']
        encode_columns = ('Article', 'Seller', 'Subdivision', 'Purpose', 'Comment',)

        items = ['Status>0']

        if self.date:
            items.append("PaymentDate='%s'" % self.date)
        if self.page.is_no_price:
            items.append(self.page.subdivision_documents())

        items.append(self.page.qualified_documents(with_permissions=1))

        aq = self.page.access_query({}) if not self.page.is_office_direction else ''

        if aq:
            where = '%s and Status<7' % aq
            cursor = self._get_orders(columns=('TID',), where=where, order='TID') or []
            ids = ','.join([str(x['TID']) for x in cursor])
            if ids:
                items.append("OrderID in (%s)" % ids)
            else:
                return []

        where = ' and '.join(filter(None, items))

        if IsTrace:
            print_to(None, '--> payments:%s, where=%s' % (self.login, where))

        order = kw.get('order') or 'TID'

        return self.page.runQuery(template, columns=columns, where=where, order=order, as_dict=True, encode_columns=encode_columns)

    def get_changes(self, id):
        template = 'provision-review-payment-changes'
        columns = self.page.database_config(template)['columns']

        where = "PaymentID=%s" % id

        return self.page.runQuery(template, columns=columns, where=where, order='TID desc', as_dict=True)

    def date_state(self, item):
        rd = ''
        states = ('исполнено', 'оплачено', 'согласовано', 'обосновано', 'создано',)

        for i, k in enumerate([4, 3, 2, 1, 0]):
            if item['dates'][k][2]:
                rd = '%s (%s)' % (item['dates'][k][2], states[i])
                break

        return rd or ''

    def update(self, command, params=None):
        """
            Update Payment registry attributes
        """
        self._errors = []

        status = command == 'accept' and 2 or command == 'reject' and 3 or 0

        data = []

        if status:
            ids = params and params.get('checks') or get_request_item('check', is_iterable=True)

            if IsTrace:
                print_to(None, '--> check ids:%s' % ids)

            payments = dict([(row['TID'], row) for row in self.get_payments()])

            for id in [int(x) for x in ids]:
                current_status = id in payments and payments[id]['Status'] or None

                if not (current_status in self.review_statuses and current_status != status):
                    continue

                if current_status == 5:
                    continue

                cursor, error_msg = self.page.runProcedure('provision-register-payment-status', 
                    id=id,
                    login=self.login, 
                    status=status,
                    with_error=True,
                    with_log=True,
                )

                if cursor and cursor[0][1].startswith('Refreshed'):
                    data.append(id)

                if error_msg and self.engine.engine_error:
                    self._errors.append(error_msg)

            attrs = self.attrs

            attrs['date'] = cleanHtml(attrs['date'])

            self._send_review_mail(status, note='', **attrs)

        return self._errors, data

    def log(self, params):
        payment_id = params.get('id')

        data = self.get_changes(payment_id)

        for row in data:
            status = g.page.get_payment_status(row['Status'])

            row['RD'] = getDate(row['RD'], DEFAULT_DATETIME_INLINE_FORMAT)
            row['StatusName'] = status[1].upper()

        return data

    @staticmethod
    def registry():
        return {
            'selected_columns' : 'TID:Total'
        }

    @staticmethod
    def _selected_columns(status):
        titles = {'TID':'ID платежа', 'Total':'Сумма платежа'}
        return dict([(x, '%s = %s' % (titles[x], status)) for x in ('TID', 'Total',)])

    def _get_sum_price(self, total, sum_price, to_pay, currency):
        return '%s: <span class="total_count">%s</span> %s <span class="total_price">%s</span>&nbsp;<span class="total_topay" title="Не оплачено">(%s)</span>&nbsp;%s' % (
            gettext('Total payments'), 
            total, 
            gettext('with price'), 
            sum_price and getCurrency(getMoney(str(sum_price)), driver=self.driver) or '0.00',
            to_pay and getCurrency(getMoney(str(to_pay)), driver=self.driver) or '0.00',
            currency
            )

    def _get_price(self, payment, sum_price, to_pay, currency, statuses=None):
        if not payment.get('Currency'):
            payment['Currency'] = currency

        s = payment['Total'] or 0.0

        payment['Total'] = getCurrency(s, points=1, driver=self.driver) or '0.00'

        price = self._calc_rub(s, payment['Currency'], rate=payment['Rate'])

        sum_price += price and Decimal(price) or 0

        if payment['Status'] in (statuses or self.review_statuses):
            to_pay += price and Decimal(price) or 0

        return price, sum_price, to_pay

    def refresh(self, **kw):
        data = {}

        currency = 'RUB'

        total = 0
        sum_price = Decimal(0.0)
        to_pay = Decimal(0.0)

        for payment in self.get_payments(**kw):
            payment_id = payment['TID']

            status = g.page.get_payment_status(payment['Status'])
            status_name = status[1].upper()

            price, sum_price, to_pay = self._get_price(payment, sum_price, to_pay, currency)

            total += 1

            data[str(payment_id)] = {
                'class' : status[0], 
                'title' : self._selected_columns(status[1].upper()),
            }

        data['sum_price'] = self._get_sum_price(total, sum_price, to_pay, currency)

        return data

    def print_payments(self, params):
        data = {}
        props = {'attrs' : self.attrs}

        columns = 'np:TID:OrderID:Seller:Article:Subdivision:Comment:Currency:Total:Rate:TotalRub:PaymentDate:Status'.split(':')

        high = ' '.join(filter(None, ['high', self._extra and 'extra', self._colored and 'colored']))

        props['columns'] = {
            'np'            : {'td' : '', 'title' : '№', 'header' : ''}, 
            'TID'           : {'td' : '', 'title' : 'ID', 'header' : ''}, 
            'Seller'        : {'td' : ' nowrap', 'title' : 'Кому', 'header' : ''}, 
            'Article'       : {'td' : '', 'title' : 'За что', 'header' : ''}, 
            'Subdivision'   : {'td' : '', 'title' : 'Инициатор', 'header' : ''}, 
            'OrderID'       : {'td' : '', 'title' : 'Номер заявки', 'header' : ''}, 
            'Comment'       : {'td' : '', 'title' : 'Примечание', 'header' : ''}, 
            'Currency'      : {'td' : '', 'title' : 'Валюта платежа', 'header' : '', 'div' : ' nowrap %s' % high}, 
            'Rate'          : {'td' : '', 'title' : 'Курс ЦБ', 'header' : ' nowrap', 'div' : ' Rate nowrap %s' % high}, 
            'Total'         : {'td' : '', 'title' : 'СУММА', 'header' : '', 'div' : ' nowrap %s' % high},  
            'TotalRub'      : {'td' : '', 'title' : 'ВСЕГО (РУБ)', 'header' : ' nowrap', 'div' : ' Rate nowrap %s' % high},  
            'PaymentDate'   : {'td' : ' hidden', 'title' : 'Дата', 'header' : ' hidden'},
            'Status'        : {'td' : ' nowrap', 'title' : 'Статус', 'header' : ''},
        }

        currency = 'RUB'
        statuses = (2,)

        total = 0
        sum_price = Decimal(0.0)
        to_pay = Decimal(0.0)
        n = 0

        ids = params and [int(x) for x in params.get('checks', [])] or None

        rows = []

        for payment in self.get_payments():
            payment_id = payment['TID']

            if ids and payment_id not in ids:
                continue

            status = g.page.get_payment_status(payment['Status'])
            status_name = status[1].upper()

            price, sum_price, to_pay = self._get_price(payment, sum_price, to_pay, currency, statuses=statuses)

            total += 1

            data[str(payment_id)] = {
                'class'    : status[0], 
                'title'    : self._selected_columns(status[1].upper()),
                'Currency' : ' %s' % payment['Currency'],
            }

            for column in ('Tax',):
                payment[column] = getCurrency(payment[column], points=1, driver=self.driver) or '0.00'

            n += 1

            payment['np'] = n
            payment['PaymentDate'] = self._get_date(payment['PaymentDate'], format='<nobr>%Y-%m-%d</nobr>')
            payment['Status'] = status_name
            payment['TotalRub'] = getCurrency(price, points=1, driver=self.driver) or '0.00'

            rows.append(payment)

        data['columns'] = columns
        data['rows'] = rows

        data['sum_price'] = self._get_sum_price(total, sum_price, to_pay, currency)

        props['show'] = 0

        return {'data' : data, 'props' : props}

    def sort(self):
        return self.render(order='TotalRub DESC')

    def render(self, **kw):
        """
            Render Payment data by the given ID
        """
        payments = []
        statuses = {}
        titles = {}
        items = {}

        self._started = getToday()

        if IsTrace:
            print_to(None, '>>> payments started')

        columns = (
            'np', 
            'checkbox', 
            'TID', 
            'showbar', 
            'Seller', 
            #'Article', 
            'Subdivision', 
            #'OrderID', 
            'Comment', 
            'Currency', 
            'Total', 
            'PaymentDate',
        )
        
        content_state = kw.get('content_state') and 'collapsed' or 'expanded'
        
        blank = 'blank'

        currency = 'RUB'
        currency_header = 'Цена в рублях'

        total = 0
        sum_price = Decimal(0.0)
        to_pay = Decimal(0.0)
        n = 0

        seller_info = {}

        for payment in self.get_payments(**kw):
            if self.is_error:
                pass

            payment_id = payment['TID']
            order_id = payment['OrderID']

            order = self._get_order(order_id)

            seller_id = order['SellerID']
            no_seller = seller_id in seller_info and True or False

            info = self._info(order_id=order_id, no_extra=True, no_seller=no_seller, stock=None, blank=blank, order=order)
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

            item['payment_type'] = self.payment_type(order)
            item['num'] = self._get_order_link(order, name=item['num'])
            item['article'] = getHtmlCaption(order['Article'])

            payment['id'] = payment_id
            payment['TID'] = '%05d' % payment_id
            payment['Seller'] = self._get_seller_link(order)
            payment['Comment'] = getHtmlCaption(payment['Comment'])

            status = self.page.get_payment_status(payment['Status'])
            statuses[payment_id] = status and status[0] or ''

            price, sum_price, to_pay = self._get_price(payment, sum_price, to_pay, currency)

            rate = payment['Currency'] != currency and ' = %s = RATE: [ %s ] CROSS: [ %s ]' % (
                payment['Currency'], 
                payment['Rate'],
                self._get_exchange_rate('RUB:%s' % payment['Currency']), 
                ) or ''
            item['price'] = '%s%s' % (getCurrency(price, points=1, driver=self.driver) or '0.00', rate.replace(' ', '&nbsp;'))

            total += 1
            n += 1

            order['dates'] = self._get_order_dates(order_id=order_id, format='<nobr>%Y-%m-%d</nobr> <nobr>%H:%M</nobr>')
            item['RD'] = self.date_state(order)

            payment['np'] = n
            payment['checkbox'] = self._checkbox('check:%s' % payment_id, 'check', payment_id, 
                checked=payment['Status'] in self.review_statuses)
            payment['PaymentDate'] = self._get_date(payment['PaymentDate'], format='<nobr>%Y-%m-%d</nobr>')

            payment['showbar'] = ''
            payment['classes'] = {
                'showbar'  : content_state,
                'Currency' : payment['Currency']
            }

            items[payment_id] = item

            payments.append(payment)

            if IsTrace and IsDeepDebug:
                print_to(None, '>>> payments %02d: %s' % (n, self.date))

            titles[payment_id] = self._selected_columns(status[1].upper())

            titles[payment_id].update({
                'np'          : '№ п/п',
                'showbar'     : '',
                'Seller'      : 'Организация', 
                'Subdivision' : 'Инициатор платежа', 
                'Comment'     : 'Примечание к оплате', 
                'Currency'    : 'Валюта платежа', 
                'PaymentDate' : 'Срок оплаты',
            })

        keys = [
            'payment_type',
            'num',
            'article',
            'seller_link',
            'equipment_title',
            #'stocklist_tag',
            'purpose',
            #'subdivision',
            'author',
            'RD',
            'condition',
            'price',
        ]

        if self.page.model == 0:
            keys.insert(6, 'sector')

        headers = {
            'payment_type'    : {'class' : 'payment_type', 'title' : 'Тип платежа'},
            'num'             : {'class' : 'num', 'title' : self.page.get_header('num')},
            'article'         : {'class' : 'article', 'title' : self.page.get_header('Article')},
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
        }

        data = {
            'attrs'     : self.attrs,
            'columns'   : columns,
            'titles'    : titles,
            'headers'   : headers,
            'keys'      : keys,
            'payments'  : payments,
            'statuses'  : statuses,
            'items'     : items,
            'total'     : total,
            'currency'  : currency,
            'sum_price' : self._get_sum_price(total, sum_price, to_pay, currency),
            'types'     : self.get_types(),
            'registry'  : self.registry(),
        }

        self._finished = getToday()

        if IsTrace:
            print_to(None, '>>> payments finished: %s sec' % spent_time(self._started, self._finished))

        return data

    def render_html(self):
        where = "PaymentDate='%s'" % self.date

        payments = self._get_payments(where=where)

        content = '<div>%s</div>' % '<br>'.join(['<span>%s</span>' % x['Article'] for x in payments])

        return 'date: %s, Total payments: %d %s<br>Is_Error:%s' % (self.date, len(payments), content, self.is_error)

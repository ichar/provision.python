# -*- coding: utf-8 -*-

import re
from decimal import *
from operator import itemgetter

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, errorlog, print_to, print_exception, 
     LOCAL_EASY_DATESTAMP, DATE_STAMP,
     default_unicode, default_encoding
     )

from ..settings import *
from ..utils import (
     isIterable, getToday, Capitalize, spent_time,
     getToday, getDate, getDateOnly, monthdelta, daydelta, weeknumber, weekday, weekdays,
     getString, getHtmlString, getHtmlCaption, getURLQueryString, getMoney, getCurrency
     )

from .references import *

_DEFAULT_STYLES = """
<style type="text/css">
body, html { font:normal 12px arial; }
table { font:inherit; }
.inline { margin-top:20px; }
.inline div { 
    display:inline-block; 
    border:1px solid #ccc;
}
.title { width:100px; }
.item { display:table-row; }

.data { min-width:150px; max-width:800px; vertical-align:top; }
.high { font:bold 13px sans-serif; text-align:right; padding-right:10px; }
.nowrap { white-space:nowrap; }
a { font-size:14px; }
</style>
"""


class Base:

    def __init__(self, engine, *args, **kwargs):
        if IsDeepDebug:
            print('Base init')

        super().__init__(*args, **kwargs)

        self.engine = engine
        self.login = g.current_user.login

    def _init_state(self, attrs, factory):
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
            print_to(None, '>>> audit started')

        try:
            self._before(**kw)
            return method(**kw)
        except:
            raise
        finally:
            self._after(**kw)

            self._finished = getToday()

            if IsTrace:
                print_to(None, '>>> audit finished: %s sec' % spent_time(self._started, self._finished))


class Audit(Base):

    default_template = 'provision-cost-orders'
    default_statuses = ()

    def __init__(self, engine, id):
        if IsDeepDebug:
            print('Audit init')

        super().__init__(engine)

        self._order = None

        self._id = id
        self._errors = []

        self._locator = None
        self._page = None
        self._stocklist = None
        
        self._attrs = {}
        self._children = []

        self._node_code = ''
        self._today = getDateOnly(getToday())

        self._stocks = []
        self._orders = []
        self._params = []
        self._payments = []

        self._stock = None
        self._stock_id = None

        self._order = None
        self._order_id = None
        self._order_model = None

        self._default_currency = 'RUB'

        self._model = {}

        self._data = {}

        self._cache = {}

    def _init_state(self, attrs=None, factory=None):
        if IsDeepDebug:
            print('Audit initstate')

        super()._init_state(attrs, factory)

        if attrs:
            self._created_after = attrs.get('created_after')
            self._locator = attrs.get('locator')
            self._page = attrs.get('page')
            if attrs.get('debug'):
                self._debug = attrs['debug'] and 1 or 0
            else:
                self._debug = None
            self._target = attrs.get('target') or '_blank'

        if factory:
            for key in factory.keys():
                setattr(self, '_%s' % key, self.set_factory(key, factory))

        reference = reference_factory.get('stocklist')
        self._stocklist = reference(self.engine)

        self._get_audit_params()

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
    def node_code(self):
        return self._node_code
    @property
    def today(self):
        return self._today
    @property
    def locator(self):
        return self._locator
    @property
    def attrs(self):
        return self._attrs
    @property
    def ids(self):
        return [self.id] + (self._children or [])
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
    @property
    def stock_children(self):
        return self._stock['Children']
    @property
    def is_cross(self):
        return g.system_config.IsCross
    @property
    def statuses(self):
        return ','.join([str(x) for x in self.default_statuses])

    def _get_audit_params(self):
        pass

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

    def get_order_total(self, order=None, is_default_currency=None, is_cross=None):
        ob = order or self._order
        total = ob.get('Total')
        currency = self.get_order_currency(ob)
        return is_default_currency and self._calc_rub(total, currency, is_cross=is_cross) or total

    def get_order_status(self, order=None):
        ob = order or self._order
        return ob.get('Status')

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

    def set_orders(self, **kw):
        """
            Sets orders matched for the given StockListNodeCode
        """
        self._node_code = self.getNodeClassCode(kw.get('stock_id') or self.id)

        where = "StockListNodeCode like '%s%%'" % self.node_code

        if kw.get('where'):
            where += " and %s" % kw['where']

        if kw.get('order'):
            order = kw['order']
        else:
            order = 'StockListNodeCode'

        self._orders = [order for order in self._get_orders(where=where, order=order, template=self.default_template) 
            if self.get_order_model(order) == 0]

    def set_params(self):
        self._cache['params'] = {}
        self._params = self._get_params(self._order_id)

    def set_payments(self):
        self._cache['payments'] = {}
        self._payments = self._get_payments(self._order_id)

    def get_stock_id(self, stock):
        return stock.get(self.stocklist.id)

    def get_stock_code(self, stock):
        return stock.get(self.stocklist.node_code)

    def get_stock_level(self, stock):
        return stock.get(self.stocklist.node_level)

    def get_node_level(self, code):
        """
            Proxy method for TreeReference
        """
        return self.stocklist.get_node_level(code)

    def getNodeClassCode(self, id):
        """
            Proxy method for TreeReference
        """
        return self.stocklist.getNodeClassCode(id)

    def getNodeClassName(self, id, code=None):
        """
            Proxy method for TreeReference
        """
        if id not in self._cache:
            self._cache[id] = {}

        if 'name' not in self._cache[id]:
            self._cache[id]['name'] = self.stocklist.getNodeClassName(id, code=code)

        return self._cache[id]['name']

    def getNodeClassTag(self, locator, id, code=None, blank=None, query_string=None):
        """
            Proxy method for TreeReference
        """
        if id not in self._cache:
            self._cache[id] = {}

        if 'tag' not in self._cache[id]:
            self._cache[id]['tag'] = self.stocklist.getNodeClassTag(locator, id, code=code, blank=blank, 
                query_string=query_string, cls='rendered_link')

        return self._cache[id]['tag']

    def workdaydelta(self, days, date=None):
        now = date or self.today
        for x in range(0, days):
            now = daydelta(now, 1)
            today = getDate(now, DATE_STAMP)
            while (now.isoweekday() > 5 or today in CALENDAR_HOLIDAYS) and today not in CALENDAR_WORKDAYS:
                now = daydelta(now, 1)
                today = getDate(now, DATE_STAMP)
        return now

    def daydate(self, date):
        return getDate(date, format='%Y%m%d')

    def weekdate(self, date):
        return weeknumber(date, with_year=True)

    def monthdate(self, date):
        return getDate(date, format='%Y%m')

    def get_progress(self, key, total, value):
        return key != self._total_header and (total > 0 and round(100 * value/total, 2) or value > 0 and 0.01 or 0) or 0

    ##
    ##  INTERFACE
    ##

    def render_params(self):
        return '<span class="nowrap">%s</span>' % ';'.join(['%s:%s' % (x, self._param(x)) for x in 'DP:DF:SF'.split(':') if self._param(x)])

    def render_date(self, date):
        return '<span class="nowrap">%s</span>' % getDate(date, LOCAL_EASY_DATESTAMP)

    def render_key_link(self, id, key, base=None):
        return key

    def render_links(self, ids=None, model=None, key=None, link=None):
        if model is None:
            model = self._model.get(key)
        return '<a target="_blank" href="/%s?_ids=%s">%s</a>' % (
            self.page.get_model_locator(model), ':'.join([str(id) for id, model in ids]), link or gettext('all'))

    def render_link(self, id=None, model=None, link=None):
        if model is None:
            model = self._order_model
        return '<a target="_blank" href="/%s?_id=%d">%s</a>' % (
            self.page.get_model_locator(model), id or self._order_id, link or self._order_id)

    def render(self, **kw):
        pass

    def render_html(self):
        """
            Render Audit data by the given ID
        """
        return self._html([x for x in self.orders if self._check_is_valid(x)])

    def _html(self, orders, columns=None):
        styles = _DEFAULT_STYLES

        if not columns:
            columns = 'TID:StockListID:Article:StockListNodeCode:Status:Total:Currency'

        header = '<div><strong>StockList ID: %s, NodeClassName: %s, Total orders: %d/%d</strong></div><br>' % (
            self.id, 
            self.stocklist.getNodeClassName(self.id, code=self.node_code), 
            len(self.orders), 
            len(orders)
            )

        content = ''

        if self._debug:
            content = '<table cellpadding="5" bordercolor="#ccc" border="1">%s</table>' % ''.join(['<tr>%s</tr>' % ''.join(['<td>%s</td>' % (x.get(c) or '') 
                for c in columns.split(':')]) 
                    for x in orders])

            content = '%s<br>Is_Error:%s' % (content, self.is_error)

        data = '<table cellpadding="5" bordercolor="#ccc" border="1">%s</table>' % ''.join([
               '<tr class="item"><td class="title">%s</td><td class="data high">%s</td><td class="data">%s</td></tr>' % (
                self.render_key_link(self._data[key][2], key), 
                getCurrency(self._data[key][0]), 
                ': '.join([self.render_link(id=id, model=model, link=str(id)) for id, model in self._data[key][1]])
            ) 
            for key in sorted(self._data.keys())])
        
        return '%s%s%s<br><div class="inline">%s</div><br /><hr><a target="_blank" href="https://fincalculator.ru/kalendar">Производственный календарь</a>' % (
            styles, header, content, data)


class AuditPlanCosts(Audit):

    default_statuses = (2, 5) # ,6

    def __init__(self, engine, id, **kw):
        super().__init__(engine, id)

        self._period = kw.get('period') or '53'
        self._interval = kw.get('interval') or 'week'

    def _init_state(self, attrs=None, factory=None):
        super()._init_state(attrs, factory)

        p = self._period and self._period.isdigit() and int(self._period) or 0
        today = self.today

        if not self._interval:
            self._period = today
        elif self._interval == 'day':
            self._period = daydelta(today, p)
        elif self._interval == 'week':
            self._period = daydelta(today, p * 7)
        elif self._interval == 'month':
            self._period = monthdelta(today, p)
        else:
            self._period = monthdelta(today, 6)

        self._where = 'Status in (%s)' % self.statuses
        self._order = 'StockListNodeCode, TID desc'

    @property
    def period(self):
        return self._period
    @property
    def interval(self):
        return self._interval

    def _get_audit_params(self):
        self._audit_period = '<span class="nowrap">%s %s</span>' % (
            gettext('from'),
            getDate(self._created_after, LOCAL_EASY_DATESTAMP),
            #gettext('to'),
            #gettext('today time'),
            )
        self._total_header = '= Всего, EUR[€]:'

    def order_condition(self):
        """
            Условия оплаты
        """
        return self.get_order_condition(self._order)

    def order_paid(self):
        """
            Дата оплаты
        """
        return self.get_order_paid(self._order)

    @staticmethod
    def _condition(condition):
        """
            Спецификации условий оплаты: <PREFIX:DAYS OR PERCENT>
        """
        d = ':'
        if condition and d in condition:
            prefix, value = condition.split(d)
            return prefix.upper(), value and value.isdigit() and int(value) or 0
        return condition, 0

    def _is_valid(self):
        """
            Включить заказ в расчет при условии:
            - сумма по заявке больше нуля
            - статус заявки корректный
            - заявка согласована
            - дата создания в отчетном периоде
            - заявка не закрыта
        """
        if not (self.get_order_total() 
            and self.get_order_status() in self.default_statuses 
            and self._order.get('Approved') 
            and self._order.get('Created') > self._created_after 
            and not self.page.is_finished(self._order)
            ):
            return False

        self.set_params()
        self.set_payments()

        return True

    def get_interval(self, date):
        """
            Временной интервал в периоде
        """
        x = ''
        if not self.interval:
            pass
        elif self.interval == 'day':
            x = self.daydate(date)
        elif self.interval == 'week':
            x = self.weekdate(date)
        elif self.interval == 'month':
            x = self.monthdate(date)
        return x

    def add(self, interval, value, date):
        if not (interval and value and date):
            return
        if date > self.period:
            return
        if interval not in self._data:
            self._data[interval] = [0, [], None]
        self._data[interval][0] += value
        self._data[interval][1].append((self._order_id, self._order_model))

        if interval not in self._model:
            self._model[interval] = self._order_model

    def calculateByParams(self, value):
        """
            Расчет по параметрам оплаты
        """
        date = None
        
        if self._param('DP'):
            date = getDate(self._param('DP'), format=LOCAL_EASY_DATESTAMP, is_date=True)
        if self._param('DF'):
            date = getDate(self._param('DF'), format=LOCAL_EASY_DATESTAMP, is_date=True)

        if not date:
            date = self.today

        interval = self.get_interval(date)

        self.add(interval, value, date)

    def calculateByCondition(self, value):
        """
            Расчет по условиям оплаты
        """
        prefix, days = self._condition(self.order_condition())

        date = None

        if not prefix or not days:
            date = self.workdaydelta(0)
        elif prefix == 'BEFORE':
            date = self.workdaydelta(0)
        elif prefix == 'POST':
            date = self.workdaydelta(days)

        if not date:
            date = self.today

        interval = self.get_interval(date)

        self.add(interval, value, date)

    def calculateByOther(self, value):
        """
            Расчет текущих платежей без условий
        """
        date = self.today

        interval = self.get_interval(date)

        self.add(interval, value, date)

    def order_payments(self):
        """
            Платежи по оплате (неисполненные)
        """
        payments = []

        currency = self.get_order_currency(self._order)
        prefix, percent = self._condition(self.order_condition())
        #
        # Параметр "Сумма к оплате" или Всего по заявке
        #
        try:
            total = getMoney(self._param('SF'), with_raise=True) or self.get_order_total()
        except:
            if IsTrace:
                print_to(None, '!!! error, order_id: %s' % self._order_id)
            total = 0
        #
        # Всего к оплате с учетом исполненных платежей (хвост)
        #
        value = self._get_payment_total(self._order_id, total, currency, is_cross=self.is_cross)

        if value:
            currency = self._default_currency
        #
        # Предоплата (в рублях)
        #
        if prefix == 'BEFORE':
            total_rub = self.get_order_total(is_default_currency=True, is_cross=self.is_cross)
            if value >= total_rub:
                value = value * (percent or 100) / 100

        payments.append(self._calc_euro(value, currency, is_cross=self.is_cross))

        return payments

    def calculate(self, **kw):
        """
            Render Audit data by the given ID
        """
        costs, total = [], 0.0

        for order in self.orders:
            if not self._check_is_valid(order):
                continue

            condition = self.order_condition()
            paid = self.order_paid()

            stock_total = 0.0

            for p in self.order_payments():
                if paid and p <= 0:
                    continue
                elif self._param('DP') or self._param('DF'):
                    self.calculateByParams(p)
                elif condition:
                    self.calculateByCondition(p)
                else:
                    self.calculateByOther(p)

                stock_total += p

            order['Total'] = getCurrency(stock_total)
            order['Params'] = self.render_params()
            order['PaidDate'] = self.render_date(paid)
            order['TID'] = self.render_link()

            total += stock_total

            costs.append(order)

        self._data[self._total_header] = (total, [], 'Заявок: %s' % len(costs))

        return costs

    def render_key_link(self, id, key, base=None):
        return id and '<a target="%s" href="/provision/calendar/%s%s">%s</a>' % (
            self._target, 
            id, 
            self._debug != None and ('?debug=%s' % self._debug) or '', 
            key
        ) or key

    def render(self, **kw):
        """
            Render Audit data by the given ID
        """
        title = kw.get('title')
        base = kw.get('base')

        query_string = getURLQueryString(base)

        current_interval = self.get_interval(self.today)

        costs = self.run(self.calculate, where=self._where, order=self._order, **kw)
        data, keys = {}, []

        total_value = self._data[self._total_header][0]

        for key in self._data.keys():
            total, ids, stock_id = self._data[key]

            percents = '* * * *'

            if key != self._total_header:
                percents = '%.2f' % round((100 / total_value) * total, 2)

            if self.interval == 'week' and '-' in key:
                y, w = key.split('-')
                item_key = 'Неделя %s [%s]' % (w, ' - '.join(weekdays(w, y)))
                keys.append(key)
            elif key.isdigit():
                item_key = key
                keys.append(key)
            else:
                item_key = key

            ids = sorted(ids)

            progress = self.get_progress(key, total_value, total)

            data[key] = [
                getCurrency(total),
                ids and '%s:: %s' % (
                    ', '.join([self.render_link(id=id, model=model, link=str(id)) for id, model in ids]),
                    self.render_links(ids, key=key),
                ) or '',
                key,
                item_key, #self.render_key_link(stock_id, item_key),
                ids and 'всего заявок [<span>%s</span>]:: %s' % (
                    len(ids),
                    self.render_links(ids, key=key),
                ) or '',
                progress > 0.05 and '%s%%' % progress or progress > 0 and '1px' or 0,
                percents,
                key < current_interval and 'overdue' or key == current_interval and 'current' or '',
                key < current_interval and gettext('Overdue') or key == current_interval and gettext('Current interval') or '',
            ]

        keys = sorted(keys) + [self._total_header]

        data[self._total_header][2] = 'Заявок: %s' % len(costs)

        output = {
            'columns' : ['title', 'total', 'percents', 'orders'],
            'headers' : ['Период', 'Сумма за период', '<span class="header_percents">%</span>', 'Номера заявок снабжения'],
            'styles'  : {'title' : 'monospace'},
            'keys'    : keys,
            'data'    : data,
            'audit'   : {
                'period'         : self._audit_period, 
                'rendered_title' : self.rendered_title(title, base, query_string),
                'created_after'  : getDate(self._created_after, LOCAL_EASY_DATESTAMP)
            },
        }
        return output

    def rendered_title(self, title, base, query_string):
        return title

    def render_html(self, **kw):
        columns = 'TID:StockListID:Article:StockListNodeCode:Status:Total:Currency:PaidDate:ConditionCode:Params'
        costs = self.run(self.calculate, where=self._where, order=self._order, **kw)
        return self._html(costs, columns=columns)


class AuditFactCosts(Audit):

    default_statuses = (2, 5, 6, 7)
    
    def __init__(self, engine, id, **kw):
        super().__init__(engine, id)

    def _init_state(self, attrs=None, factory=None):
        super()._init_state(attrs, factory)

    @property
    def stock_name(self):
        """
            Наименование класса товара
        """
        return self._attrs['rendered_name']

    def _get_audit_params(self):
        self._audit_period = '<span class="nowrap">%s %s</span>' % (
            gettext('from'),
            getDate(self._created_after, LOCAL_EASY_DATESTAMP),
            #gettext('to'),
            #gettext('today time'),
            )
        self._total_header = '= Всего, EUR[€]:'

    def _get_attrs(self):
        view = 'provision-stocks'
        columns = self.page.database_config(view)['export']

        id = self._stock_id

        where = 'TID=%s' % id
        encode_columns = ('Name', 'Title', 'ShortName', 'Comment')

        cursor = self.page.runQuery(view, columns=columns, top=1, where=where, as_dict=True, encode_columns=encode_columns)

        if cursor and len(cursor) > 0:
            self._attrs = cursor[0]

        self.getNodeClassName(id, code=self.attrs.get('NodeCode'))

        self._attrs['rendered_name'] = self._cache[id]['name'][0]
        self._attrs['rendered_link'] = ''

    def order_paid(self):
        """
            Дата оплаты
        """
        return self.get_order_paid(self._order)

    def _is_valid(self):
        """
            Включить заказ в расчет при условии:
            - сумма по заявке больше нуля
            - статус заявки корректный
            - заявка согласована
            - дата создания в отчетном периоде
            - заявка закрыта
        """
        if not (self.get_order_total() 
            and self.get_order_status() in self.default_statuses 
            and self._order.get('Approved') 
            and self._order.get('Created') > self._created_after
            #and self.page.is_finished(self._order)
            ):
            return False
        return True

    def _before(self, **kw):
        self._stocks = self._stocklist.getNodeItems(self.id, with_root=kw.get('with_root'))

    def _set_stock(self, stock):
        self._stock = stock
        self._stock_id = self.get_stock_id(stock)

        self._get_attrs()

    def add(self, value):
        stock = self.stock_name
        if stock not in self._data:
            self._data[stock] = [0, [], self._stock_id, self.stock_children]
        self._data[stock][0] += value
        self._data[stock][1].append((self._order_id, self._order_model))

        if stock not in self._model:
            self._model[stock] = self._order_model

    def calculatePayment(self, value):
        """
            Расчет по платежам
        """
        self.add(value)

    def order_payments(self):
        """
            Платежи по оплате (исполненные)
        """
        payments = []

        currency = self.get_order_currency(self._order)
        #
        # Всего по заявке
        #
        total = self.get_order_total()
        #
        # Всего по исполненным платежам (оплачено)
        #
        value = self._get_paid_total(self._order_id, total, currency)

        currency = self._default_currency
        value = value or total

        payments.append(self._calc_euro(value, currency, is_cross=self.is_cross))

        return payments

    def calculate(self, **kw):
        costs, total = [], 0

        with_root = kw.get('with_root')

        for n, stock in enumerate(self.stocks):
            self._set_stock(stock)

            is_root = with_root and n == 0 and self.stock_code

            where = "Status in (%s) and StockListID is not null and StockListNodeCode%s" % (
                self.statuses, (is_root and "='%s'" or " like '%s%%'") % self.stock_code)

            self.set_orders(where=where, order='StockListNodeCode, TID')

            for order in self.orders:
                self._set_order(order)

                if not self._is_valid():
                    continue

                stock_total = 0

                paid = self.order_paid()

                for p in self.order_payments():
                    if not (paid or p):
                        continue

                    self.calculatePayment(p)

                    stock_total += p

                total += stock_total

                order['Total'] = getCurrency(stock_total)
                order['TID'] = self.render_link()

                costs.append(order)

            if is_root and self.stock_name in self._data:
                self._data[self.stock_name][3] = 0

        self._data[self._total_header] = (total, [], None, 0)

        return costs

    def render_key_link(self, id, key, base=None):
        return id and '<a class="rendered_link" target="%s" href="%s">%s</a>' % (
            self._target, 
            '%s%s' % (
                base % id,
                self._debug != None and ('&debug=%s' % self._debug) or '', 
            ),
            key
        ) or key

    def render(self, **kw):
        """
            Render Audit data by the given ID
        """
        title = kw.get('title')
        base = kw.get('base')

        query_string = getURLQueryString(base)

        with_root = self.id > 0

        costs = self.run(self.calculate, with_root=with_root, **kw)
        data, keys = {}, []

        total_value = self._data[self._total_header][0]

        for key in self._data.keys():
            total, ids, stock_id, stock_children = self._data[key]

            percents = '* * * *'

            if key != self._total_header:
                percents = '%.2f' % round((100 / total_value) * total, 2)
                keys.append(key)

            ids = sorted(ids)

            progress = self.get_progress(key, total_value, total)

            data[key] = [
                getCurrency(total),
                ids and '%s:: %s' % (
                    ', '.join([self.render_link(id=id, model=model, link=str(id)) for id, model in ids]),
                    self.render_links(ids, key=key),
                ) or '',
                stock_id,
                stock_children == 0 and key or self.render_key_link(stock_id, key, base=base),
                ids and 'всего заявок [<span>%s</span>]:: %s' % (
                    len(ids),
                    self.render_links(ids, key=key),
                ) or '',
                progress > 0.05 and '%s%%' % progress or progress > 0 and '1px' or 0,
                percents,
                '',
                '',
            ]

        keys = sorted(keys) + [self._total_header]

        data[self._total_header][2] = 'Заявок: %s' % len(costs)

        output = {
            'columns' : ['title', 'total', 'percents', 'orders'],
            'headers' : ['Класс товара', 'Сумма за период', '<span class="header_percents">%</span>', 'Номера заявок снабжения'],
            'styles'  : {},
            'keys'    : keys,
            'data'    : data,
            'audit'   : {
                'period'         : self._audit_period, 
                'rendered_title' : self.rendered_title(title, base, query_string), 
                'created_after'  : getDate(self._created_after, LOCAL_EASY_DATESTAMP)
            },
        }
        return output

    def rendered_title(self, title, base, query_string):
        s = self.getNodeClassTag(self.locator, self.id, query_string=query_string).replace('/stock/', '/statist/')
        if self.id > 0:
            s = '<a class="rendered_link" target="%s" href="%s">%s</a>.%s' % (self._target, base % 0, title, s)
        else:
            s = title
        return s

    def render_html(self, **kw):
        columns = 'TID:StockListID:Article:StockListNodeCode:Status:Total:Currency'
        costs = self.run(self.calculate, **kw)
        return self._html(costs, columns=columns)

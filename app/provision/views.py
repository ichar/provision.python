# -*- coding: utf-8 -*-

import os
import random
import string
from copy import deepcopy
from operator import itemgetter

from config import (
     CONNECTION,
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, IsNoEmail, LocalDebug,
     basedir, errorlog, print_to, print_exception,
     default_unicode, default_encoding,
     LOCAL_EASY_DATESTAMP, LOCAL_EXCEL_TIMESTAMP, LOCAL_EXPORT_TIMESTAMP,
     UTC_FULL_TIMESTAMP, UTC_EASY_TIMESTAMP, DATE_STAMP, DEFAULT_ROOT,
     )

from . import provision

from ..settings import *
from ..database import DatabaseEngine, Connection, DBEngine
from ..models import User, ExchangeRate, get_users, get_users_dict, load_system_config
from ..decoders import FileDecoder
from ..mails import send_simple_mail
from ..utils import (
     getToday, getDate, getDateOnly, getUID, checkDate, cdate, minutedelta, normpath,
     Capitalize, unCapitalize, makeCSVContent, makeXLSContent, makeSearchQuery,
     checkPaginationRange, reprSortedDict, unquoted_url, is_unique_strings,
     sortedDict, isIterable, xsplit, make_config, 
     cleanHtml, makeLink, getLink, getLinks, cleanLinks, checkLink, getString, getSQLString, getHtmlString, getHtmlCaption, 
     sMoney, getMoney, getFloatMoney, getExcelMoney, getCurrency
     )

from ..semaphore.views import initDefaultSemaphore

from .references import *
from .sellers import Seller
from .stocks import Stock
from .payments import PaymentsReview
from .barcode import BarcodeReader
from .audit import AuditPlanCosts, AuditFactCosts
from .decrees import Decree

from .page_default import PageDefault
from .page_provision import PageProvision
#from .page_personal import PagePersonal
#from .page_diamond import PageDiamond
from .page_purchase import PagePurchase
from .page_sale import PageSale
from .page_workflow import PageWorkflow

from ..auth.profile import UserProfile

##  ========================
##  Provision Orders Package
##  ========================

default_page = 'provision'
default_locator = 'provision'
default_action = '830'
default_log_action = '831'
default_print_action = '850'
default_template = 'provision-orders'

# Локальный отладчик
IsLocalDebug = LocalDebug[default_page]

_views = {
    'orders'          : 'provision-orders',
    'reviews'         : 'provision-reviews',
    'decrees'         : 'provision-decrees',
    'activities'      : 'provision-activities',
    'companies'       : 'provision-companies',
    'subdivisions'    : 'provision-subdivisions',
    'sectors'         : 'provision-sectors',
    'categories'      : 'provision-categories',
    'sellers'         : 'provision-sellers',
    'equipments'      : 'provision-equipments',
    'conditions'      : 'provision-conditions',
    'params'          : 'provision-params',
    'param_values'    : 'provision-param-values',
    'payments'        : 'provision-payments',
    'refers'          : 'provision-refers',
    'comments'        : 'provision-comments',
    'vendors'         : 'provision-vendors',
    'authors'         : 'provision-order-authors',
    'order-params'    : 'provision-order-params',
    'order-items'     : 'provision-order-items',
    'order-payments'  : 'provision-order-payments',
    'order-refers'    : 'provision-order-refers',
    'order-comments'  : 'provision-order-comments',
    'order-reviewers' : 'provision-order-reviewers',
    'order-documents' : 'provision-order-documents',
    'order-unreads'   : 'provision-order-unreads',
    'order-changes'   : 'provision-order-changes',
    'order-vendors'   : 'provision-order-vendors',
    'dates'           : 'provision-order-dates',
    'download'        : 'provision-download-image',
    'schedule'        : 'provision-schedule',
    'stocks'          : 'provision-stocks',
    'stocks-children' : 'provision-stocks-children',
    'cost-orders'     : 'provision-cost-orders',
    'review-payments' : 'provision-review-payments',
}

_extra_action = (default_print_action,)

_default_encode_columns = ('Author', 'Account', 'Article', 'Category', 'Company', 'Condition', 'Equipment', 'Purpose', 'Seller', 'SellerAddress', 'SellerContact', 'SellerTitle', 'SellerURL', 'Subdivision', 'Sector', 'EditedBy',)

_SQL = {
    'Orders'         : {
        'delete'     : 'DELETE FROM [ProvisionDB].[dbo].[Orders_tb] {where}',
        'set-status' : 'UPDATE [ProvisionDB].[dbo].[Orders_tb] SET Status=%d {where}'
    },
    'Params'         : {
        'delete'     : 'DELETE FROM [ProvisionDB].[dbo].[Params_tb] WHERE OrderID in (select TID from [ProvisionDB].[dbo].[Orders_tb] {where})',
    },
    'Items'          : {
        'delete'     : 'DELETE FROM [ProvisionDB].[dbo].[Items_tb] WHERE OrderID in (select TID from [ProvisionDB].[dbo].[Orders_tb] {where})',
    },
    'Payments'       : {
        'delete'     : 'DELETE FROM [ProvisionDB].[dbo].[Payments_tb] WHERE OrderID in (select TID from [ProvisionDB].[dbo].[Orders_tb] {where})',
    },
    'Comments'       : {
        'delete'     : 'DELETE FROM [ProvisionDB].[dbo].[Comments_tb] WHERE OrderID in (select TID from [ProvisionDB].[dbo].[Orders_tb] {where})',
    },
    'Reviews'        : {
        'delete'     : 'DELETE FROM [ProvisionDB].[dbo].[Reviews_tb] WHERE OrderID in (select TID from [ProvisionDB].[dbo].[Orders_tb] {where})',
    },
    'Reviewers'      : {
        'delete'     : 'DELETE FROM [ProvisionDB].[dbo].[Reviewers_tb] WHERE OrderID in (select TID from [ProvisionDB].[dbo].[Orders_tb] {where})',
    },
    'OrderDates'     : {
        'delete'     : 'DELETE FROM [ProvisionDB].[dbo].[OrderDates_tb] WHERE OrderID in (select TID from [ProvisionDB].[dbo].[Orders_tb] {where})',
    },
    'OrderChanges'   : {
        'delete'     : 'DELETE FROM [ProvisionDB].[dbo].[OrderChanges_tb] WHERE OrderID in (select TID from [ProvisionDB].[dbo].[Orders_tb] {where})',
    },
    'OrderDocuments' : {
        'delete'     : 'DELETE FROM [ProvisionDB].[dbo].[OrderDocuments_tb] WHERE OrderID in (select TID from [ProvisionDB].[dbo].[Orders_tb] {where})',
    },
    'Unreads'        : {
        'delete'     : 'DELETE FROM [ProvisionDB].[dbo].[Unreads_tb] WHERE OrderID in (select TID from [ProvisionDB].[dbo].[Orders_tb] {where})',
    },
}

_EMAIL_EOL = '\r\n'

_GENERATORS = {
    'A' : '№п/п;Обоснование;Наименование товара;Количество;Единици измерения;Желаемая дата поступления;Дата составления заявки;Исполнитель ;Направление закупки;Склад поступления;Цена за единицу;общее описание;Поставщик;Условия оплаты;сумма оплаты с учетом НДС;;Валюта платежа;№ счета;Необходимая дата оплаты;Дата согласования;Дата передачи заказа в работу;Дата прередачи заказа на доставку ;Предположительная дата поступления;Фактическая дата поступления;Возможная дата оплаты;Фактиическая дата оплаты;Комментарий;;',
    'B' : '№п/п;Обоснование;Наименование товара;Количество;Желаемая дата поступления;Дата составления заявки;Исполнитель ;Направление закупки;Склад поступления;Цена за единицу;Общее описание;Поставщик;Условия оплаты;сумма оплаты с учетом НДС;;Валюта платежа;№ счета;Необходимая дата оплаты;Дата согласования;Дата передачи заказа в работу;Дата прередачи заказа на доставку ;Предположительная дата поступления;Фактическая дата поступления;Возможная дата оплаты;Фактиическая дата оплаты;Комментарий;;',
    'C' : '№п/п;Обоснование;Наименование товара;Количество;Желаемая дата поступления;Дата составления заявки;Исполнитель ;Направление закупки;Склад поступления;Цена за единицу;Общее описание;Поставщик;Валюта платежа;Условия оплаты;сумма оплаты с учетом НДС;;№ счета;Необходимая дата оплаты;Дата согласования;Дата передачи заказа в работу;Дата прередачи заказа на доставку ;Предположительная дата поступления;Фактическая дата поступления;Возможная дата оплаты;Фактиическая дата оплаты;Комментарий;;',
    'D' : '№п/п;Обоснование;Наименование товара;Количество;Единица измерения;Желаемая дата поступления;Дата составления заявки;Исполнитель ;Направление закупки;Склад поступления;Цена за единицу;Общее описание;Поставщик;Условия оплаты;сумма оплаты с учетом НДС;;Валюта платежа;№ счета;Необходимая дата оплаты;Дата согласования;Дата передачи заказа в работу;Дата прередачи заказа на доставку ;Предположительная дата поступления;Фактическая дата поступления;Возможная дата оплаты;Фактиическая дата оплаты;Комментарий;;;;;;;;;;;;;;;',
    'E' : '№п/п;Обоснование;Наименование товара;Количество;Единица измерения;Желаемая дата поступления;Дата составления заявки;Исполнитель ;Направление закупки;Склад поступления;Цена за единицу;Общее описание;Поставщик;Валюта платежа;Условия оплаты;сумма оплаты с учетом НДС;;№ счета;Необходимая дата оплаты;Дата согласования;Дата передачи заказа в работу;Дата прередачи заказа на доставку ;Предположительная дата поступления;Фактическая дата поступления;Возможная дата оплаты;Фактиическая дата оплаты;Комментарий;;',
    'F' : '№п/п;Обоснование;Наименование товара;Количество;дата составления заказа;Желаемая дата поступления;Исполнитель ;Направление закупки;Склад поступления;Цена за единицу;Общее описание;Поставщик;Условия оплаты;сумма оплаты с учетом НДС;;Валюта платежа;№ счета;Необходимая дата оплаты;Дата согласования;Дата передачи заказа в работу;Дата прередачи заказа на доставку ;Предположительная дата поступления;Фактическая дата поступления;Возможная дата оплаты;Фактиическая дата оплаты;Комментарий;;;',
    'G' : '№п/п;Обоснование;Наименование товара;Количество;Дата составления заказа;Желаемая дата поступления;Исполнитель ;Направление закупки;Склад поступления;Цена за единицу;Общее описание;Поставщик;Валюта платежа;Условия оплаты;сумма оплаты с учетом НДС;;№ счета;Необходимая дата оплаты;Дата согласования;Дата передачи заказа в работу;Дата прередачи заказа на доставку ;Предположительная дата поступления;Фактическая дата поступления;Возможная дата оплаты;Фактиическая дата оплаты;Комментарий;;',
    'H' : '№;Наименование товара;Количество, шт.;Обоснование;Отдел;Цена за единицу;Валюта платежа;Сумма без учета НДС;Сумма с учетом НДС;Условия оплаты;Поставщик;Согласовано',
    'I' : '№п/п;Обоснование;Наименование товара;Количество;Дата составления заказа;Желаемая дата поступления;Исполнитель ;Направление закупки;Склад поступления;Цена за единицу;Общее описание;Поставщик;Валюта платежа;Условия оплаты;сумма оплаты с учетом НДС;;№ счета;Необходимая дата оплаты;Дата согласования;Дата передачи заказа в работу;Дата прередачи заказа на доставку ;Предположительная дата поступления;Фактическая дата поступления;Возможная дата оплаты;Фактиическая дата оплаты;Комментарий;;',
    '1' : ';;;;;;;;;;;;;;Первый платеж (предоплата);Второй платеж;;;;;;;;;;Заказчик;Снабжение;Бухгалтерия',
    '2' : ';;;;;;;;;;;;;Первый платеж (предоплата);Второй платеж;;;;;;;;;;;Заказчик;Снабжение;Бухгалтерия;',
}


def before(f):
    def wrapper(*args, **kw):
        try:
            name = g.page.id
            g.engine = DatabaseEngine(name=name, user=g.current_user, connection=CONNECTION[name])
        except:
            g.engine = None
        name = 'storage'
        if name in CONNECTION:
            g.storage = DatabaseEngine(name=name, user=g.current_user, connection=CONNECTION[name])
        else:
            g.storage = g.engine
        return f(*args, **kw)
    return wrapper

def refreshOrder(**kw):
    order_id = kw.get('order_id')
    if not order_id:
        return

    g.requested_object = _get_order(order_id).copy()

@before
def refresh(**kw):
    g.instance = Provision(g.current_user)

    g.exchange_rate = {}

    rates = {
        'RUB:EUR' : 0.011204,
        'RUB:USD' : 0.0132,
        'RUB:CHF' : 0.012425,
        'RUB:GBP' : 0.0098,
        
        'USD:EUR' : 0.8477,
        'USD:CHF' : 0.9389,
        'USD:GBP' : 0.74,
        'USD:RUB' : 75.7576,
        
        'CHF:EUR' : 0.9023,
        'CHF:USD' : 1.0644,
        'CHF:GBP' : 0.8,
        'CHF:RUB' : 80.4819,
        
        'EUR:USD' : 1.1792,
        'EUR:CHF' : 1.10713,
        'EUR:GBP' : 0.84,
        'EUR:RUB' : 89.2576,
        
        'GBP:EUR' : 1.19,
        'GBP:USD' : 1.35,
        'GBP:CHF' : 1.25,
        'GBP:RUB' : 103.2887,
        
        'EUR:EUR' : 1.0,
        'USD:USD' : 1.0,
        'CHF:CHF' : 1.0,
        'GBP:GBP' : 1.0,
        'RUB:RUB' : 1.0,
    }

    ExchangeRate.refresh(1)

    for rate in rates:
        g.exchange_rate[rate] = ExchangeRate.get_cross(rate) or rates[rate]

    stocklist = reference_factory.get('stocklist')(g.engine)

    image_loader = OrderImageLoader()
    image_loader._init_state()

    g.page._init_state(g.engine, 
        attrs={
            'locator'                     : default_locator,
            'views'                       : _views,
            'encode_columns'              : _default_encode_columns,
            'system_config'               : g.system_config,
            'stocklist'                   : stocklist,
            'image_loader'                : image_loader,
        }, 
        factory={
            'get_top'                     : _get_top,
            'get_max_page'                : _get_max_page,
            'calc_rub'                    : calc_rub,
            'calc_euro'                   : calc_euro,
            'calc_from_rub'               : calc_from_rub,
            'calc_from_euro'              : calc_from_euro,
            'get_activity'                : _get_activity,
            'get_condition'               : _get_condition,
            'get_user'                    : _get_user,
            'get_seller_link'             : _get_seller_link,
            'get_orders'                  : _get_orders,
            'get_reviews'                 : _get_reviews,
            'get_subdivisions'            : _get_subdivisions,
            'get_sectors'                 : _get_sectors,
            'get_date'                    : _get_date,
            'get_order_params'            : _get_order_params,
            'get_order_items'             : _get_order_items,
            'get_order_documents'         : _get_order_documents,
            'get_paid_total'              : _get_paid_total,
            'output_total_selected'       : _output_total_selected,
            'refreshOrder'                : refreshOrder,
        }
    )

    g.requested_object = {}
    g.total_selected = [0, 0.0]

    refreshOrder(**kw)

    g.page.point('refresh')

def calc_euro(total, currency, is_cross=None):
    v = (total and (isinstance(total, str) and getMoney(total) or float(total)) or 0.0)
    if is_cross:
        rate = 1 / _get_exchange_rate('EUR:%s' % currency)
    else:
        rate = _get_exchange_rate('%s:EUR' % currency)
    return v * rate

def calc_rub(total, currency, is_cross=None, rate=None, exchange_rate=None):
    v = (total and (isinstance(total, str) and getMoney(total) or float(total)) or 0.0)
    if exchange_rate:
        v = v / exchange_rate
    if rate:
        pass
    elif is_cross:
        rate = 1 / _get_exchange_rate('RUB:%s' % currency)
    else:
        rate = _get_exchange_rate('%s:RUB' % currency)
    return v * rate

def calc_from_euro(total, currency, is_cross=None):
    v = (total and (isinstance(total, str) and getMoney(total) or float(total)) or 0.0)
    if is_cross:
        x = '%s:EUR' % currency
        rate = 1 / _get_exchange_rate(x)
    else:
        x = 'EUR:%s' % currency
        rate = _get_exchange_rate()
    #print('calc_from_euro.rate:', x, rate)
    return v * rate

def calc_from_rub(total, currency, is_cross=None):
    v = (total and (isinstance(total, str) and getMoney(total) or float(total)) or 0.0)
    if is_cross:
        x = 'RUB:%s' % currency
        rate = 1 / _get_exchange_rate(x)
    else:
        x = '%s:RUB' % currency
        rate = _get_exchange_rate(x)
    #print('calc_from_rub.rate:', x, rate)
    return v / rate

def select_items(order_id, template, encode_columns, handler=None, engine=None, **kw):
    items = []
    selected_id = int(kw.get('id') or 0)
    selected_name = kw.get('name')
    selected_code = kw.get('code')

    model = None
    if 'model' in kw:
        model = kw['model'] or 0

    view = _views[template]
    config = g.page.database_config(view)
    columns = config['export']

    params = kw.get('params')

    no_selected = kw.get('no_selected') and True or False

    if order_id:
        where = 'OrderID=%d%s%s%s%s' % (
            int(order_id), 
            selected_id and ' and TID=%d' % selected_id or '',
            selected_name and " and Name='%s'" % selected_name or '',
            selected_code and " and Code='%s'" % selected_code or '',
            model is not None and ' and MD=%s' % model or '',
            )

        if params:
            where += ''.join([" and %s" % x for x in params])

        order = kw.get('order') or 'TID'

        cursor = g.page.runQuery(view, columns=columns, where=where, order=order, as_dict=True, encode_columns=encode_columns, engine=engine)
        if cursor:
            IsSelected = False
            
            for n, row in enumerate(cursor):
                row['id'] = row['TID']

                if handler is not None:
                    handler(config, row)

                if not IsSelected and selected_id and row['id'] == selected_id and not no_selected:
                    row['selected'] = 'selected'
                    IsSelected = True

                items.append(row)

            if not IsSelected and not no_selected:
                row = items[0]
                selected_id = row['id']
                row['selected'] = 'selected'

    data = { 
        'data'        : items, 
        'columns'     : columns, 
        'config'      : _get_view_columns(g.page.database_config(_views[template])), 
        'total'       : len(items),
        'reference'   : None,
        'status'      : None,
        'selected_id' : selected_id or None,
    }

    return data


class ApplicationGenerator(DBEngine):

    _default_login = 'autoload'
    _default_order_size = 19
    _subqueries = ('item', 'param', 'payment', 'comment',)

    def __init__(self, connection):
        super().__init__(connection=connection)

        self.login = self._default_login
        self.default_values = {}

        self.headers = []
        self.columns = {}

        self.today = getDateOnly(getToday(), DEFAULT_DATE_FORMAT[1])

        self.size = 0

    @staticmethod
    def get_currency(value):
        v = value and value.lower() or None
        return v and (
            v in 'usd:доллары:$' and 'USD' or 
            v in 'euro:евро' and 'EUR' or 
            v in 'chf:франки' and 'CHF' or
            v in 'gbp:фунты' and 'GBP'
            ) or 'RUB'

    def check_mode(self, line, file):
        model = None
        for key in _GENERATORS.keys():
            if line.lower() in _GENERATORS[key].lower():
                model = key
                break
        if not model:
            return

        for n, x in enumerate([s.strip().lower() for s in _GENERATORS[model].split(';')]):
            if x and len(self.headers) > n:
                self.headers[n] = x
                continue
            self.headers.append(x)

        if len(self.headers) > 1:
            for n in range(len(self.headers)-1, -1, -1):
                if not self.headers[n]:
                    del self.headers[n]
                else:
                    break

        for n, key in enumerate(self.headers):
            column, header = None, ''

            if not key:
                pass
            elif key in '№:№п/п':
                column, header = '#', 'Номер заявки'
            elif key == 'обоснование':
                column, header = 'purpose', 'Обоснование'
            elif key == 'наименование товара':
                column, header = 'article', 'Наименование товара'
            elif key in 'количество:количество, шт.':
                column, header = 'qty', 'Количество'
            elif key == 'отдел':
                column, header = 'subdivision', 'Отдел'
            elif key in 'единици измерения:единица измерения':
                column, header = 'units', 'Единицы измерения'
            elif key == 'желаемая дата поступления':
                column, header = 'date_ready', 'Желаемая дата поступления'
            elif key == 'необходимая дата оплаты':
                column, header = 'date_payment_1', 'Необходимая дата оплаты'
            elif key == 'возможная дата оплаты':
                column, header = 'date_payment_2', 'Возможная дата оплаты'
            elif key in 'фактиическая дата оплаты:фактическая дата оплаты':
                column, header = 'date_payment_3', 'Фактическая дата оплаты'
            elif key == 'предположительная дата поступления':
                column, header = 'date_shipment', 'Предположительная дата поступления'
            elif key == 'дата согласования':
                column, header = 'date_accepted', 'Дата согласования'
            elif key in 'дата составления заявки:дата составления заказа':
                column, header = 'date_created', 'Дата заявки'
            elif key == 'исполнитель':
                column, header = 'author', 'Исполнитель'
            elif key == 'направление закупки':
                column, header = 'country', 'Направление закупки'
            elif key == 'склад поступления':
                column, header = 'warehouse', 'Склад поступления'
            elif key == 'цена за единицу':
                column, header = 'price', 'Цена за единицу'
            elif key in 'общее описание:общее описание':
                column, header = 'information', 'Общее описание'
            elif key == 'поставщик':
                column, header = 'seller', 'Поставщик'
            elif key == 'условия оплаты':
                column, header = 'condition', 'Условия оплаты'
            elif key == 'валюта платежа':
                column, header = 'currency', 'Валюта платежа'
            elif key in '№ счета:номер счета':
                column, header = 'account', 'Номер счета'
            elif key in 'первый платеж (предоплата):предоплата':
                column, header = 'payment1', 'Первый платеж (предоплата)'
            elif key == 'второй платеж':
                column, header = 'payment2', 'Второй платеж'
            elif key == 'заказчик':
                column, header = 'comment1', 'Заказчик'
            elif key == 'снабжение':
                column, header = 'comment2', 'Снабжение'
            elif key == 'бухгалтерия':
                column, header = 'comment3', 'Бухгалтерия'
            else:
                continue

            if column:
                self.columns[column] = (n, header)

        m = re.match(r'.*\((.*)\).*', file.filename)

        if m and m.group(1):
            self.default_values['subdivision'] = Capitalize(m.group(1), as_is=True)

        self.default_values['author'] = self._default_login

        self.size = len(self.columns)

    def get_values(self, items, saveback):
        values = {}

        def _value(name, with_header=None, as_date=None):
            index = name in self.columns and self.columns[name][0] or -1
            value = index > -1 and ' '.join(items[index].split()) or self.default_values.get(name) or ''
            if as_date:
                value = _conv_date(value)
            if with_header:
                return (index > -1 and self.columns[name][1] or '', value,)
            return value

        def _date_payment():
            return _value('date_payment_1', as_date=True) or \
                   _value('date_payment_2', as_date=True) or \
                   _value('date_payment_3', as_date=True) or \
                   self.today

        def _article():
            return Capitalize(cleanLinks(getString(_value('article'))), as_is=True)

        def _purpose():
            return _value('purpose') and Capitalize(getString(_value('purpose')), as_is=True) or ''

        def _price():
            return getMoney(_value('price'))

        def _qty():
            return _value('qty') and \
                   int(not _value('qty').isdigit() and \
                   re.sub(r'([\d]*).*', r'\1', re.sub(r'\s', '', _value('qty'))) or _value('qty')) or 1

        def _get_line():
            if _value('article'):
                author = _value('author')
                subdivision = re.sub(r'(\w+)\s+\((\w+)\)', r'\1|\2', _value('subdivision'))

                price = _price()
                qty = _qty()

                if not (price > 0 and qty > 0) and g.system_config.IsLoaderExplicit:
                    return 0

                total = _get_total(price, qty)
                tax = _get_tax(total)

                condition = _value('condition') or 'Без условий'
                seller = _value('seller') and _get_title(_value('seller')) or ''

                if not seller and g.system_config.IsLoaderExplicit:
                    return 0

                currency = self.get_currency(_value('currency'))

                values['#'] = int(items[0])
                values['author'] = self._default_login
                values['article'] = _article()
                values['qty'] = qty
                values['purpose'] = _purpose()
                values['subdivision'] = subdivision
                values['equipment'] = _value('information')
                values['price'] = price
                values['total'] = total
                values['tax'] = tax
                values['condition'] = condition
                values['seller'] = seller
                values['currency'] = currency
                values['account'] = _value('account')
                #
                #   Параметры
                #
                values['param'] = {
                    'account'        : (_value('account', with_header=True),),
                    'date_ready'     : (_value('date_ready', with_header=True, as_date=True),),
                    'date_created'   : (_value('date_created', with_header=True, as_date=True),),
                    'date_shipment'  : (_value('date_shipment', with_header=True, as_date=True),),
                    'date_accepted'  : (_value('date_accepted', with_header=True, as_date=True),),
                    'date_payment_1' : (_value('date_payment_1', with_header=True, as_date=True),),
                    'date_payment_2' : (_value('date_payment_2', with_header=True, as_date=True),),
                    'date_payment_3' : (_value('date_payment_3', with_header=True, as_date=True),),
                    'author'         : (_value('author', with_header=True),),
                    'country'        : (_value('country', with_header=True),),
                    'warehouse'      : (_value('warehouse', with_header=True),),
                }
                #
                #   Платежи
                #
                values['payment'] = {
                    'payment1'     : (_value('payment1', with_header=True), _date_payment(),),
                    'payment2'     : (_value('payment2', with_header=True), _date_payment(),),
                }
                #
                #   Комментарии подразделений
                #
                values['comment'] = {
                    'comment1'     : (_value('comment1', with_header=True),),
                    'comment2'     : (_value('comment2', with_header=True),),
                    'comment3'     : (_value('comment3', with_header=True),),
                }
                #
                #   Расшифровка счета
                #
                values['item'] = {}

                saveback['line'] = saveback['n']

                return 1

        def _get_subline():
            line = saveback['line']

            try:
                purpose = _purpose()
                name = getString('%s%s' % (_article(), purpose and ' [%s]' % purpose or ''))
                price = _price()
                qty = _qty()
                units = _value('units')
                total = _get_total(price, qty)
                tax = _get_tax(total)
            except:
                return 0

            row = self.make_subitem('item', {'subline' : (name, qty, units, total, tax,)})

            if row:
                saveback['data'][line][self._default_order_size].append(row[0])

            return 0

        code = 0

        if items:
            items = [x.strip() for x in items]

            if self.columns:
                if not _value('article'):
                    pass
                elif items[0].isdigit():
                    code = _get_line()
                else:
                    code = _get_subline()

        return code and values or None

    def make_subitem(self, mode, values):
        items = []

        for key, x in values.items():
            name, value = '', None
            try:
                if mode == 'item':
                    name, qty, units, total, tax = x
                    if total:
                        items.append([0,0,0, self._default_login, name, qty, units, total, tax])
                elif mode == 'param':
                    name, value = x[0][0], x[0][1]
                    if value:
                        items.append([0,0,0,0, self._default_login, name, value])
                elif mode == 'payment':
                    name, value = x[0][0], getMoney(x[0][1])
                    if value:
                        date, tax, purpose = x[1], _get_tax(value), name
                        if date:
                            items.append([0,0,0,0, self._default_login, purpose, date, value, tax, 0])
                elif mode == 'comment':
                    name, value = x[0][0], x[0][1]
                    if value:
                        items.append([0,0,0,0, self._default_login, name, value])

            except:
                print_to(None, '>>> make_subitem error: %s [%s]' % (mode, value))
                if IsPrintExceptions:
                    print_exception()

        return items

    def upload(self):
        file = request.files.get('file')

        if file is None or not hasattr(file, 'stream'):
            return

        is_error = False

        data = []

        default_currency = 'RUB'
        default_rowspan = 0

        with file.stream as fi:
            self.size, saveback = 0, {'n' : 0}

            saveback['data'] = data

            for s in fi:
                line = re.sub(r'\"(.*);(.*)\"', r'\1\2', s.decode(default_encoding).strip())

                if not line:
                    continue

                if not line[0].isdigit():
                    if not data:
                        self.check_mode(line, file)
                        continue

                items = line.split(';')

                if len(items) < self.size:
                    continue

                values = self.get_values(items, saveback)

                if not values or not '#' in values:
                    continue

                row = [
                    0,
                    values.get('author'),
                    values.get('article'),
                    values.get('qty'),
                    values.get('purpose'),
                    values.get('price'),
                    values.get('currency') or default_currency,
                    values.get('total'),
                    values.get('tax'),
                    values.get('subdivision'),
                    values.get('equipment'),
                    values.get('seller'),
                    values.get('condition'),
                    values.get('account'),
                    '',
                    self.login,
                    0,
                    g.page.is_no_price,
                    default_rowspan,
                    ]

                for key in self._subqueries:
                    row.append(self.make_subitem(key, values.get(key)))

                data.append(row)

                saveback['n'] += 1

        if data:
            self.begin()

            sp = {}

            view = g.page.database_config('provision-register-order')
            sp['order'] = view['exec']+' '+view['args']

            for key in self._subqueries:
                view = g.page.database_config('provision-add-%s-order' % key)
                sp[key] = view['exec']+' '+view['args']

            for n, params in enumerate(data):
                order_id = 0

                row = self.run(sp['order'], tuple(params[0:self._default_order_size]))

                if self.engine_error:
                    break

                if not row or len(row[0]) < 2:
                    continue

                order_id = row[0][0]

                if not order_id:
                    continue

                for index, key in enumerate(self._subqueries):
                    values = params[self._default_order_size + index]

                    for p in values:
                        p[1] = order_id

                        row = self.run(sp[key], tuple(p))

                        if self.engine_error:
                            break

                    if self.engine_error:
                        break

            self.close()


class ApplicationService(Connection):

    def __init__(self, connection, kw=None):
        super().__init__(connection, g.requested_object)

        self._kw = kw

        self.lastrowid = None

    def _get_args(self):
        where, order, args, permissions = _make_page_default(self._kw, back_where=True)

        self.where = where
        self.order = order
        self.args = args

        if IsDebug:
            print('>>> ApplicationService, where: [%s]' % self.where)

    def _sql(self, sql):
        return sql.replace('{where}', self.where and 'WHERE %s' % self.where or '')

    def download(self):
        self._get_args()

        rows = []

        view = g.page.database_config(default_template)
        columns = view['export'] #[x for x in view['export'] if x in view['headers']]
        headers = [x in view['headers'] and view['headers'][x][0] or x for x in columns]
        encode_columns = _default_encode_columns + ('SellerTitle', 'SellerAddress', 'SellerURL', 'EquipmentName',)

        orders = g.page.runQuery(default_template, columns=columns, where=self.where, order=self.order, 
                                 as_dict=True, encode_columns=encode_columns)

        for data in orders:
            row = []
            for column in columns:
                if column not in data:
                    continue
                try:
                    v = data[column]
                    if v is None:
                        v = ''
                    elif column == 'RD':
                        v = getDate(v, UTC_FULL_TIMESTAMP, is_date=True)
                        v = getDate(v, LOCAL_EXCEL_TIMESTAMP)
                    elif column == 'Status':
                        v = g.page.get_status(v)[1]
                    elif column in ('Price', 'Tax', 'Total',):
                        v = getExcelMoney(v)
                    elif isinstance(v, str):
                        v = re.sub(r'\r?\n', ' ', v.strip())
                    row.append(v)
                except:
                    print_exception()

            rows.append(row)

        rows.insert(0, headers)
        return rows

    def run(self, mode):
        self._get_args()

        errors = []

        self.open(0)

        try:
            if mode == 'delete-orders':
                self.connect(self._sql(_SQL['Params']['delete']), None)
                self.connect(self._sql(_SQL['Items']['delete']), None, check_error=True)
                self.connect(self._sql(_SQL['Payments']['delete']), None, check_error=True)
                self.connect(self._sql(_SQL['Comments']['delete']), None, check_error=True)
                self.connect(self._sql(_SQL['Reviews']['delete']), None, check_error=True)
                self.connect(self._sql(_SQL['Reviewers']['delete']), None, check_error=True)
                self.connect(self._sql(_SQL['OrderDates']['delete']), None, check_error=True)
                self.connect(self._sql(_SQL['OrderChanges']['delete']), None, check_error=True)
                self.connect(self._sql(_SQL['OrderDocuments']['delete']), None, check_error=True)
                self.connect(self._sql(_SQL['Unreads']['delete']), None, check_error=True)

                if not self.is_error:
                    self.connect(self._sql(_SQL['Orders']['delete']), None)

            elif mode == 'clear-history':
                self.connect(self._sql(_SQL['Reviews']['delete']), None)

                if not self.is_error:
                    self.connect(self._sql(_SQL['Orders']['set-status']), (0,))
        except:
            if IsPrintExceptions:
                print_exception()

        self.close()

        if self.is_error:
            errors.append(gettext('Error: SQL broken. See transaction log.'))

        return errors


class Provision:

    def __init__(self, user):
        self.user = user
        self.login = user.login
        self.reviewer = user.full_name()

        self.action_id = None
        self.status = None

        self.today = getDateOnly(getToday(), DEFAULT_DATE_FORMAT[1])
        self.is_extra = has_request_item(EXTRA_)

        self.check_only = None

        self._author = ''
        self._executor = ''
        self._reviewer = None
        self._is_author = None
        self._is_executor = None

        self._errors = []

    @staticmethod
    def _exception(self, errors):
        errors.append(gettext('Error: Unexpected exception'))

    def _get_reference_id(self):
        return int(self.status.split(':')[2])

    def _get_reviewers(self, order_id):
        """
            Список текущих рецензентов по заказу.

            Аргументы:
                order_id        -- ID заказа
        """
        users = []

        # Assigned reviewers
        for x in _get_order_reviewers(order_id, as_dict=True):
            reviewer = _get_user(x.get('Login'))

            if reviewer is not None and reviewer not in users:
                users.append(reviewer)

        return users

    def _get_reviewer_managers(self, mode, order_id, author, **kw):
        """
            Рецензент и список руководителей заказчика.

            Аргументы:
                mode            -- режим опроса, 
                    0           -- все менеджеры, 
                    1           -- прямые руководители, 
                    2           -- вышестоящие руководители

                order_id        -- ID заказа
                author          -- логин рецензента

            Keyword arguments:
                is_review_headoffice -- Bool, включить руководство компании

                with_headoffice -- Bool, исполнительный директор
                with_assistant  -- Bool, заместитель ГД
                with_root       -- Bool, ГД

                check_only      -- Bool, check only flag

            Returns:
                reviewer        -- User, order author User or None
                managers        -- List, manager User list
        """
        reviewer = None

        is_review_headoffice = kw.get('is_review_headoffice') or False

        with_headoffice = kw.get('with_headoffice') or False
        with_assistant = kw.get('with_assistant') or False
        with_root = kw.get('with_root') or False

        order = kw.get('order') or g.requested_object.get('TID') == order_id and g.requested_object or _get_order(order_id)

        if author is None:
            author = order.get('Author')

        code = order.get('SubdivisionCode')

        reviewers = []

        try:
            if author:
                reviewer = _get_user(author)
        except:
            pass

        managers = []

        if code and mode in (0, 1):
            managers += User.get_managers(code, check_only=self.check_only)

        if reviewer is not None:
            if mode in (0, 1):
                managers += reviewer.managers(with_assistant=with_assistant, check_only=self.check_only)

            if mode in (0, 2) and is_review_headoffice:
                code = reviewer.subdivision_code == '0002' and '0001' or None
                with_headoffice = with_headoffice or not reviewer.has_subdivision_group(reviewer.subdivision_code)

                managers += reviewer.managers(id=reviewer.app_root('id', code=code), 
                    with_headoffice=with_headoffice, 
                    with_assistant=with_assistant, 
                    with_root=with_root,
                    check_only=self.check_only
                    )

            if mode in (0, 1) and code:
                managers += reviewer.managers(id=reviewer.app_root('id', code=code), check_only=self.check_only)

        if not self.check_only:
            if mode in (0, 1):
                managers += self._get_reviewers(order_id)

        return reviewer, list(set(managers))

    def _check_review_timedelta(self, order_id, status, note=None):
        """
            Проверить временной интервал для рецензии
        """
        now = getToday()

        errors = []

        if g.system_config.IsLimitedLengthExclude:
            return errors

        reviews = _get_reviews(order_id, login=self.login, cursor=True)

        for review in sorted(reviews, key=lambda k: k['StatusDate'], reverse=True):
            status_review = review['Status']
            status_date = review['StatusDate']

            if status == status_review and minutedelta(status_date, 15) > now and (
                not note or not is_unique_strings(note, review['Note'])):
                errors.append(gettext('Error: Confirmation review rules.'))
                break

        return errors

    def _mail(self, mode, html, reviewer, users, default_emails=None, decrees=None):
        """
            Отправить уведомление.

            Arguments:
                mode            -- String, email title
                html            -- String, template of email (HTML)
                reviewer        -- User, from user
                users           -- List, to User list

            Keyword arguments:
                default_emails  -- List, default to User list (unused)
                decrees         -- Tuple, list of decree ids

            Returns:
                code            -- Int, code of mail result 0|1.
        """
        errors = []
        done = 0

        emails = [user.email for user in users if user is not None and user.is_emailed]

        def _send(addr_to, addr_cc, root):
            if not (addr_to and addr_to.replace(reviewer.email, '')):
                return 0

            timestamp = getDate(getToday(), format=UTC_FULL_TIMESTAMP)
            done, canal, with_canal = 1, None, True
            link = decrees and g.page.get_decrees_link(root, ids=decrees, with_login=0, state='expand') or g.page.get_link(root)

            if not IsNoEmail and link:
                code = send_simple_mail(subject, 
                    html.replace('webperso', link[0]).replace('#args', link[1]), 
                    addr_to, 
                    addr_cc=addr_cc,
                    with_canal=with_canal
                    )

                if with_canal:
                    done, canal = code
                else:
                    done = code

            if IsTrace:
                print_to(None, '>>> mail sent %s, login:%s, to:%s, cc:%s, done:%s, canal:%s, link:%s, root:[%s]' % (
                    timestamp, self.login, addr_to, addr_cc, done, canal, link, root))

            return done

        if reviewer is not None and emails:
            subject = '%s %s' % (g.page.id.upper(), mode.upper())

            addrs = list(set(filter(None, emails)))

            # ---------------
            # Public web link
            # ---------------

            root = g.system_config.IsPublicEmailEnabled and DEFAULT_ROOT.get('public') or None

            public_emails = []

            if root:
                to = sorted(list(set([emails.pop(emails.index(x)) for x in g.page.system_config_emails_public if x in addrs])))
                cc = [x for x in g.page.system_config_emails_common if x not in to]

                addr_to = ';'.join(to)
                addr_cc = ';'.join(cc)

                done += _send(addr_to, addr_cc, root)

                if done:
                    public_emails = to + cc

            # --------------
            # Local web link
            # --------------

            root = DEFAULT_ROOT.get('local')

            if root:
                to = sorted([x for x in list(set(emails)) if x not in public_emails])
                cc = reviewer.email not in g.page.system_config_emails_public and (
                    not g.page.system_config_exclude_emails or reviewer.email not in g.page.system_config_exclude_emails) and reviewer.email or None

                addr_to = ';'.join(to)
                addr_cc = cc

                done += _send(addr_to, addr_cc, root)

        else:
            errors.append('Email recipient list is empty.')

        if done:
            print_to(None, '')

        return errors

    @staticmethod
    def combo_value(key, attrs, caller, template, default_key='Name', new_data=None):
        id = attrs.get(key) or None
        new = attrs.get('new_%s' % key) or ''

        value = new.strip()

        if not value and id and caller is not None:
            v = caller(id)
            if new_data and v is not None:
                v.update(new_data)
            value = v and template and (template % v) or v and v.get(default_key)

        return value

    def set_attrs(self, attrs):
        self._article = cleanHtml(getString(attrs.get('order_article')))
        self._subdivision_id = int(attrs.get('order_subdivision') or 0)
        self._subdivision_new = cleanHtml(getString(attrs.get('new_order_subdivision'), is_clean=True))
        self._category_id = int(attrs.get('order_category') or 0)
        self._category_new = cleanHtml(getString(attrs.get('new_order_category'), is_clean=True))
        self._qty = int(attrs.get('order_qty') or 1)
        self._price = getMoney(attrs.get('order_price') or 0)
        self._currency = attrs.get('order_currency')
        self._condition_id = int(attrs.get('order_condition') or 0)
        self._condition_new = cleanHtml(getString(attrs.get('new_order_condition'), is_clean=True))
        self._seller_id =  int(attrs.get('order_seller') or 0)
        self._seller_new = cleanHtml(getString(attrs.get('new_order_seller'), is_clean=True))
        self._seller_code = cleanHtml(getString(attrs.get('order_seller_code'), is_clean=True))
        self._seller_title = getString(attrs.get('order_seller_title'))
        self._seller_address = getString(attrs.get('order_seller_address'), save_links=True)
        self._seller_contact = getString(attrs.get('order_seller_contact'), is_clean=True)
        self._url = makeLink(getString(attrs.get('order_url'), save_links=True))
        self._duedate = attrs.get('order_duedate')
        self._author = attrs.get('order_author')
        self._sector_id = int(attrs.get('order_sector') or 0)
        self._sector_new = cleanHtml(getString(attrs.get('new_order_sector'), is_clean=True))

        g.page.get_attrs(self, attrs)

        if (not self._currency or self._currency == DEFAULT_UNDEFINED) and self._price:
            self._currency = 'RUB'

        self._subdivision = self.combo_value('order_subdivision', attrs, _get_subdivision, '')
        self._sector = self.combo_value('order_sector', attrs, _get_sector, '')
        self._category = self.combo_value('order_category', attrs, _get_category, '')
        self._condition = self.combo_value('order_condition', attrs, _get_condition, '')

        if self._seller_new:
            self._seller_id = None

        if self._seller_id:
            template = '%(Name)s||%(Title)s||%(Address)s||%(Code)s||%(Contact)s'
            new_data = {}
            if self._seller_title:
                new_data['Title'] = self._seller_title
            if self._seller_address:
                new_data['Address'] = self._seller_address
            if self._seller_code:
                new_data['Code'] = self._seller_code
            if self._seller_contact:
                new_data['Contact'] = self._seller_contact
            self._seller = self.combo_value('order_seller', attrs, _get_seller, template, new_data=new_data)
        elif not self._seller_new and self._seller_address:
            self._errors.append(gettext('Error: Seller URL address should be present together with a new company name!'))
        elif not self._seller_new and self._seller_title:
            self._errors.append(gettext('Error: Seller Title should be present together with a new company name!'))
        else:
            self._seller = '%s||%s||%s||%s||%s' % (
                self._seller_new, self._seller_title, self._seller_address, self._seller_code, self._seller_contact)

        if self._errors:
            return None

        return g.page.set_attrs(self, attrs)

    def _is_invalid_limited_length(self, value, size, back=None):
        if not g.system_config.IsCheckLimitedLength:
            return back and value or False
        if value:
            words = []
            ss = []
            for x in xsplit(re.sub(r'\n', '<br>', value), [' ', '"'], is_list=True):
                word = x.strip()
                if len(word) > 20:
                    w = list(set(word))
                    m = max([(len([x for x in word if x==s]), s) for s in w])
                    if not back and m[0] > 10 and not m[1].isalpha():
                        return True
                    else:
                        if not back and len([s for s in w if s not in ss]) == 0:
                            return True
                        ss += list(w)
                if word:
                    words.append(word)
            v = ''.join([w in '.,;:{}[]()!@#$%^&*-=_+/<>~`' and w or ' '+w for w in words]).strip()
            if back:
                return re.sub('<br>', r'\n', v)
            return words and len(v) < size
        return back and value or True

    def _make_vaild_name(self, value, with_point=None):
        v = self._is_invalid_limited_length(value, 10, back=True)
        return v and Capitalize('%s%s' % (v, with_point and v[-1] not in '.,?!' and '.' or ''), as_is=True) or ''

    @staticmethod
    def _name_message_info(name):
        return '<p>%s. %s "%s" %s:</p><ul class="name-message-info">%s</ul>' % (
            gettext("Please, supply more detailed information"), 
            gettext("In the item"), 
            gettext('%s declaration' % name), 
            gettext("should be present the next items"), 
            ''.join(['<li>%s</li>' % x for x in gettext('%s %s' % (name, 'items declaration')).split('-')]))

    def set_order(self, attrs, **kw):
        """
            Check & Make Provision Order
        """
        errors = []

        command = kw.get('command')
        is_check = kw.get('is_check')

        tag_params = self.set_attrs(attrs)

        if self._errors:
            return self._errors, None, None
        #
        # Check attrs are present
        #
        n = 0
        for index, value, title in sorted(tag_params.values(), key=itemgetter(0)):
            if index in g.page.order_tag_restrictions and (not value or value == DEFAULT_UNDEFINED or not str(value).replace('|', '')):
                #print_to(None, ':'.join([str(x) for x in (index, value, title)]))
                errors.append('%s %s' % (gettext('Warning: Parameter is empty:'), title))
                n += 1

        if errors:
            if n >= 5:
                errors = [gettext('Warning: Provision form is empty!')]
            if is_check:
                return errors
            return errors, None, None

        if len(self._equipment) < 10:
            errors.append(gettext('Error: Equipment should be present!'))
            return errors, None, None

        if g.page.check_tag_limits(self, errors, command=command):
            return errors, None, None

        if g.page.is_limited_length(attrs):
            if self._is_invalid_limited_length(self._article, 40):
                errors.append(self._name_message_info('Article'))
                return errors, None, None

            if self._is_invalid_limited_length(self._equipment, 80):
                errors.append(self._name_message_info('Equipment'))
                return errors, None, None

            if self._is_invalid_limited_length(self._purpose, 100):
                errors.append(self._name_message_info('Purpose'))
                return errors, None, None

        if not is_unique_strings(self._article, self._equipment):
            errors.append('%s: %s + %s.' % (gettext('Warning: Strings should be unique'), tag_params['Article'][2], tag_params['Equipment'][2]))
            return errors, None, None

        if not is_unique_strings(self._article, self._purpose):
            errors.append('%s: %s + %s.' % (gettext('Warning: Strings should be unique'), tag_params['Article'][2], tag_params['Purpose'][2]))
            return errors, None, None

        if len(getLink(self._seller)) > 0:
            errors.append('%s: %s.<br>%s.' % (gettext('Warning: Link is unavailable in this item'), tag_params['Seller'][2], gettext('Use special Order form field')))
            return errors, None, None

        if not is_unique_strings(self._purpose, self._equipment):
            errors.append('%s: %s + %s.' % (gettext('Warning: Strings should be unique'), tag_params['Purpose'][2], tag_params['Equipment'][2]))
            return errors, None, None

        if self._category == 'срочная' and not self._duedate:
            errors.append(gettext('Warning: Category is high. Set DueDate parameter value!'))
            return errors, None, None

        tag_params['Article'][1] = self._article = self._make_vaild_name(self._article)
        tag_params['Equipment'][1] = self._equipment = self._make_vaild_name(self._equipment, with_point=1)
        tag_params['Purpose'][1] = self._purpose = self._make_vaild_name(self._purpose, with_point=0)

        g.page.set_order(self, attrs, **kw)

        columns = sorted(list(tag_params.keys()))
        kw = dict(zip(map(lambda x: x.lower(), columns), [tag_params[x][1] for x in columns]))

        if not self._price:
            self._price = 0.0

        if not self._qty:
            self._qty = 1

        self._total = _get_total(self._price, self._qty)
        self._tax = _get_tax(self._total)

        if not self._subdivision:
            errors.append('%s %s' % (gettext('Error: Subdivision is underfined:'), self._subdivision))

        if not errors:
            kw['subdivision'] = self._subdivision
            kw['category'] = self._category or ''
            kw['seller'] = self._seller or ''
            kw['condition'] = self._condition or ''
            kw['total'] = self._total
            kw['tax'] = self._tax
            kw['duedate'] = self._duedate
            kw['status'] = 0
            kw['url'] = self._url
            kw['equipment'] = self._equipment
            kw['sector'] = self._sector or ''
            # XXX
            kw['account'] = getattr(self, '_account', None) or ''

            if kw['author']:
                kw.update({'login' : kw['author'], 'author' : self.login})
            else:
                kw['author'] = self.login

            kw['is_no_price'] = g.page.is_no_price
            kw['model'] = g.page.model

        if is_check:
            return errors

        return errors, tag_params, kw

    def set_decree(self, attrs, **kw):
        """
            Check & Make Provision Decree
        """
        errors = []

        review_id = attrs.get('review_id')
        decree_id = attrs.get('decree_id')
        report_id = attrs.get('report_id')
        is_check = attrs.get('is_check')

        tag_params = {}

        def _check_duedate():
            key = 'decree_duedate'
            value = None
            if key in attrs:
                if isIterable(attrs[key]) and len(attrs[key]) == 2:
                    new, save = attrs[key]
                    if not new:
                        self._errors.append(gettext('Error: Decree duedate should be present!'))
                    else:
                        if new < save:
                            self._errors.append(gettext('Error: Impossible to change date back!'))
                        if not review_id and getDate(new, LOCAL_EASY_DATESTAMP, is_date=True) < getDateOnly(getToday()):
                            self._errors.append(gettext('Error: Date is in past!'))
                    value = new
                else:
                    value = attrs[key]
            return value

        self._title = cleanHtml(getString(attrs.get('decree_title')), without_point=True)
        self._note = getString(attrs.get('decree_note'), save_links=True, with_html=True)
        self._duedate = _check_duedate()
        self._decree_status = int(attrs.get('decree_status') or '0')
        self._author = attrs.get('decree_author')
        self._executor = attrs.get('decree_executor')
        self._report = getString(attrs.get('decree_report'), save_links=True, with_html=True)

        if self._errors:
            return self._errors, None, None

        self._is_author = int(attrs.get('is_author') or '0')
        self._is_executor = int(attrs.get('is_executor') or '0')

        if not self._author:
            self._author = self.login

        if self._is_author:
            self._reviewer = User.get_by_login(self._author).full_name()

        if self._is_executor:
            self._author = self._executor

        if not errors:
            kw['review_id'] = review_id
            kw['decree_id'] = decree_id
            kw['report_id'] = report_id
            kw['title'] = self._title
            kw['note'] = self._note or ''
            kw['status'] = self._decree_status
            kw['duedate'] = self._duedate or ''
            kw['author'] = self._author or ''
            kw['executor'] = self._executor or ''
            kw['report'] = self._report or ''

        if is_check:
            return errors

        return errors, tag_params, kw

    def create_order(self, attrs):
        """
            Create a new Provision order
        """
        errors, tag_params, kw = self.set_order(attrs)

        if not errors:
            errors = self.run('register', kw)

        if self.action():
            tag_params['TID'] = self.action_id
            tag_params['Status'] = 0
            self.send_create_mail(tag_params)

        return errors

    def update_order(self, id, attrs):
        """
            Update given Provision order
        """
        errors, tag_params, kw = self.set_order(attrs)

        if id and not errors:
            kw['id'] = id
            errors = self.run('refresh', kw)

        return errors

    def delete_order(self, id):
        """
            Remove Provision order
        """
        errors, kw = [], {}

        if not (id and id == g.requested_object.get('TID')):
            errors.append(gettext('Error: Order ID is invalid!'))

        if g.page.is_disabled_delete():
            errors.append(gettext('Warning: Order cannot be removed!'))

        if not errors:
            kw['id'] = id
            kw['login'] = self.login
            errors = self.run('remove', kw)

            if not errors:
                seller_id = g.requested_object.get('SellerID')

                if seller_id:
                    kw['id'] = seller_id
                    self.run('del-seller', kw)

        if self.action():
            self.send_remove_mail(g.requested_object)

        return errors

    def clone_order(self, id, attrs):
        """
            Clone given Provision order
        """
        errors, tag_params, kw = self.set_order(attrs)

        if id and not errors:
            kw['id'] = None
            kw['account'] = ''
            kw['status'] = -1
            errors = self.run('register', kw)

        if self.action():
            tag_params['TID'] = self.action_id
            tag_params['Status'] = 0
            self.send_create_mail(tag_params)

        return errors

    def review_action(self, order_id, status, note, params=None, check_past=False, **kw):
        """
            Register Review Action.

            Arguments:
                params -- dict, review params

            Returns:
                Stored procedure response.
                If OK `ActionID`, `Status`
        """
        if not order_id:
            return

        mode = kw.get('mode')
        decree = kw.get('decree')

        self.action_id, self.status = 0, None
        command, review_id, decree_id, report_id, review_duedate, executor, with_mail, no_mail = '', 0, 0, 0, None, '', 0, 0

        if isinstance(params, dict):
            command = params.get('command', None) or ''
            review_id = int(params.get('review_id') or 0)
            decree_id = int(params.get('decree_id') or 0)
            report_id = int(params.get('report_id') or 0)
            review_duedate = params.get('review_duedate', None) or ''
            executor = params.get('executor', None) or ''
            with_mail = params.get('with_mail', None) or 0
            no_mail = params.get('no_mail', None) or 0

        if not checkDate(review_duedate, LOCAL_EASY_DATESTAMP):
            review_duedate = ''

        if check_past and review_duedate and getDate(review_duedate, LOCAL_EASY_DATESTAMP, is_date=True) < getDateOnly(getToday()):
            self._errors.append(gettext('Error: Date is in past!'))
            return

        action = kw.get('action')
        report = decree and decree.report

        cursor, error_msg = g.page.runProcedure(action or 'provision-register-review', 
            order_id=order_id,
            review_id=review_id,
            decree_id=decree_id,
            report_id=report_id,
            login=self._author or self.login, 
            reviewer=self._reviewer or self.reviewer, 
            status=status,
            note=note,
            review_duedate=review_duedate,
            executor=executor,
            report=report,
            edited_by=self.login,
            with_mail=with_mail,
            with_error=True,
            with_log=True,
        )

        if cursor:
            self.action_id = cursor[0][0]
            self.status = cursor[0][1]
        else:
            if IsTrace:
                print_to(None, '!!! review_action, no cursor: %s' % str(self.login))

        if error_msg and g.engine.engine_error:
            self._errors.append(error_msg)

        if self.action():
            if status == 9 and not no_mail:
                decree.refresh(self, action_id=self.action_id)
                self.send_decree_mail(decree, action=action)
            elif (status in (2,3,4,5,6,7,10,11,12) or with_mail) and not no_mail:
                self.send_review_mail(status, note, review_duedate=review_duedate, mode=mode)
        else:
            self._errors.append(gettext('Review Execution error'))

        if self._errors:
            if IsTrace or IsPrintExceptions:
                print_to(None, '!!! review_action, error: %s, action_id: %s, errors: %s' % (
                    self.status, self.action_id, repr(self._errors)))

    def set_unread(self, order_id, users, force=None):
        """
            Отметить как непрочтенное
        """
        if order_id and force:
            _set_total_selected(1, calc_euro(g.requested_object.get('Total'), g.requested_object.get('Currency')))

        logins = list(set([user.login for user in users if user is not None]))

        # Remove myself
        if not force and self.login in logins:
            logins.remove(self.login)

        if order_id == g.requested_object.get('TID'):
            logins = [x for x in logins if _is_read(x)]

        if not logins:
            return

        cursor, error_msg = g.page.runProcedure('provision-set-unread', 
                order_id=order_id,
                logins='|'.join(logins), 
                with_error=True,
            )

        if IsTrace:
            print_to(None, '>>> set_unread, login:%s, order:%d, users:%s' % (self.login, order_id, repr(logins)))

        if error_msg and g.engine.engine_error:
            print_to(None, '!!! set_unread, engine error: %s' % str(error_msg))
            self._errors.append(error_msg)

    def set_read(self, order_id, users, force=None):
        """
            Отметить как прочтенное
        """
        if force:
            rows, total = 0, 0.0
            if order_id:
                rows = -1
                total = calc_euro(g.requested_object.get('Total'), g.requested_object.get('Currency'))
            _set_total_selected(rows, total)

        logins = list(set([x.login for x in users if x is not None]))

        if order_id == g.requested_object.get('TID'):
            logins = [x for x in logins if _is_unread(x)]

        if not logins:
            return

        cursor, error_msg = g.page.runProcedure('provision-set-read', 
                order_id=order_id or 'null',
                logins='|'.join(logins), 
                with_error=True,
            )

        if IsTrace:
            print_to(None, '>>> set_read, login:%s, order:%s, users:%s' % (self.login, order_id, repr(logins)))

        if error_msg and g.engine.engine_error:
            print_to(None, '!!! set_read, engine error: %s' % str(error_msg))
            self._errors.append(error_msg)

    def notify(self, order_id, author, unreads=None):
        """
            Напомнить об изменениях в документе
        """
        reviewer = None

        try:
            if author:
                reviewer = _get_user(author)
        except:
            pass

        users = []

        if reviewer is not None:
            users.append(reviewer)
            users += reviewer.managers()

        if unreads:
            users += [User.get_by_email(x) for x in unreads]

        self.set_unread(order_id, users+[reviewer])

    def send_order_notifications(self, order_id, params=None, check_only=None, order=None):
        """
            Проверить статус заказа "Требуется обоснование" и отправить напоминание.

            Arguments:
                order_id    -- Int, order ID

            Keyword arguments:
                params      -- Dict, params of loader query
                check_only  -- Bool, check only flag, returns User list if True
                order       -- Dict, order item

            Returns:
                code        -- Int, code of mail result 0|1.
        """
        html = g.page.APPROVAL_ALARM_HTML

        with_mail = params and params.get('with_mail', None) or not params and 1 or 0

        if check_only:
            self.check_only = True

        if not order:
            order = _get_order(order_id)

        reviewer, chiefs = self._get_reviewer_managers(1, order_id, None, order=order)

        with_root = g.system_config.IsReviewRoot

        reviewer, managers = self._get_reviewer_managers(2, order_id, None, is_review_headoffice=True, 
            with_headoffice=True, with_assistant=True, with_root=with_root, order=order)

        if check_only:
            self.check_only = False

            return {
                'chiefs'    : chiefs, 
                'managers'  : managers,
            }
        elif not html:
            return

        manager_logins = [x.login for x in managers]

        reviews = _get_reviews(order_id, order='TID asc', cursor=True)

        def _check_review(mode, user):
            has_confirmation = 0
            has_confirm = 0
            confirmed_by = ''

            for row in reviews:
                login = row['Login']
                status = g.page.get_review_status(row['Status']).lower()

                if status == 'confirmation' and has_confirm:
                    if mode == 'confirmation':
                        if login == user.login:
                            has_confirmation = 1 # return True
                    else:
                        has_confirmation = 1

                if login in manager_logins:
                    if status == 'confirm':
                        has_confirm = 1
                        has_confirmation = 0
                        confirmed_by = login
                    elif status in ('accept', 'reject',):
                        if mode == 'confirm' and has_confirm and has_confirmation:
                            if login == user.login:
                                return True
                        if mode == 'confirmation':
                            has_confirm = 0

            if mode == 'confirmation':
                if confirmed_by == user.login:
                    return True
                return not (has_confirm and not has_confirmation) and True or False

            if mode == 'confirm':
                return not (has_confirm and has_confirmation and confirmed_by == user.login) and True or False

            return False

        make_unreads = []
        users = []

        default_reviewers = [User.get_by_email(x) for x in g.page.system_config_emails_approval]

        # ---------------------
        # Обоснование заказчика
        # ---------------------

        for user in filter(None, chiefs + [reviewer] + default_reviewers):
            # Обоснования нет
            if not _check_review('confirmation', user):
                make_unreads.append(user)
                users.append(user)

        # ----------------------
        # Резолюция руководителя
        # ----------------------

        for user in filter(None, managers):
            # Обоснование не просмотрено или решение не принято
            if not _check_review('confirm', user):
                make_unreads.append(user)
                users.append(user)

        self.set_unread(order_id, make_unreads)

        if IsTrace:
            print_to(None, '>>> send_order_notifications, login:%s, order:%d, users:%s, datetime:%s' % (self.login, order_id,
                repr([x.login for x in make_unreads]), getDate(getToday(), format=UTC_FULL_TIMESTAMP)))

        if not (with_mail and users):
            return

        # From
        user = _get_user(self.login)

        # To
        users += [User.get_by_email(x) for x in g.page.system_config_emails_common]

        props = {
            'id'          : order_id,
            'Seller'      : order.get('Seller'),
            'Article'     : order.get('Article'),
            'Date'        : getDate(getToday(), DEFAULT_DATETIME_INLINE_FORMAT),
            'Reviewer'    : 'Автор запроса: %s' % user.full_name(),
            'Message'     : g.page.confirmation_message,
        }

        html = _EMAIL_EOL.join(html.split('\n')) % props

        return self._mail('approval', html, user, users)

    def send_review_notifications(self, params=None):
        """
            Проверить статус заказов "На согласовании" и разослать напоминания
        """
        orders = _get_orders(where='Status in (1,4) and MD=%s' % g.page.model)

        for row in orders:
            order_id = row['TID']
            self.send_order_notifications(order_id, params=params)

    def send_create_mail(self, attrs):
        """
            Уведомление о создании заказа
        """
        html = g.page.CREATE_ALARM_HTML

        order_id = attrs.get('TID')

        if not order_id or not html:
            return None

        # From
        user = _get_user(self.login)

        # To
        login = attrs.get('Author')
        author = login and len(login) == 3 and login[1] != DEFAULT_UNDEFINED and login[1] or None

        reviewer = None

        try:
            if author:
                reviewer = _get_user(author)
        except:
            pass

        users = []

        if reviewer is not None:
            users.append(reviewer)
            users += reviewer.managers()

        users += [User.get_by_email(x) for x in g.page.system_config_emails_create]
        users += [User.get_by_email(x) for x in g.page.system_config_emails_common]

        self.set_unread(order_id, users+[reviewer])

        props = {
            'id'          : order_id,
            'Seller'      : '',
            'Article'     : attrs.get('Article')[1],
            'Date'        : getDate(getToday(), DEFAULT_DATETIME_INLINE_FORMAT),
            'Subdivision' : attrs.get('Subdivision')[1],
            'Reviewer'    : user.full_name(),
        }

        html = _EMAIL_EOL.join(html.split('\n')) % props

        return self._mail('new order', html, user, users)

    def send_remove_mail(self, attrs):
        """
            Уведомление об удалении заказа
        """
        html = g.page.REMOVE_ALARM_HTML

        order_id = attrs.get('TID')

        if not order_id or not html:
            return None

        # Remover
        user = _get_user(self.login)

        # To
        author = attrs.get('Author')
        reviewer = author and _get_user(author) or None

        users = []

        if reviewer is not None:
            users.append(reviewer)
            users += reviewer.managers()

        users += [User.get_by_email(x) for x in g.page.system_config_emails_remove]
        users += [User.get_by_email(x) for x in g.page.system_config_emails_common]

        props = {
            'id'          : order_id,
            'Seller'      : attrs.get('Seller'),
            'Article'     : attrs.get('Article'),
            'Date'        : getDate(getToday(), DEFAULT_DATETIME_INLINE_FORMAT),
            'Subdivision' : attrs.get('Subdivision'),
            'Reviewer'    : reviewer and reviewer.full_name() or '',
            'Remover'     : '%s (%s)' % (user and user.full_name() or '---', self.login),
        }

        html = _EMAIL_EOL.join(html.split('\n')) % props

        return self._mail('order removed', html, user, users)

    def send_approval_mail(self, attrs, no_status=None):
        """
            Запрос на согласование
        """
        html = g.page.APPROVAL_ALARM_HTML

        order_id = g.requested_object.get('TID')

        if not (order_id and html):
            return None

        status = g.requested_object.get('Status')

        if not no_status and not status < 5:
            return None

        # From
        user = _get_user(self.login)

        # To
        author = g.requested_object.get('Author')

        reviewer = None

        try:
            if author:
                reviewer = _get_user(author)
        except:
            pass

        users = []

        if reviewer is not None:
            users.append(reviewer)
            users += reviewer.managers(with_assistant=True)

            code = g.requested_object.get('SubdivisionCode')

            if code:
                users += reviewer.managers(id=reviewer.app_root('id', code=code), with_headoffice=True)

        users += self._get_reviewers(order_id)

        users += [User.get_by_email(x) for x in g.page.system_config_emails_approval]
        users += [User.get_by_email(x) for x in g.page.system_config_emails_common]

        self.set_unread(order_id, users+[reviewer])

        props = {
            'id'          : order_id,
            'Seller'      : g.requested_object.get('Seller') or '',
            'Article'     : g.requested_object.get('Article') or '',
            'Date'        : getDate(getToday(), DEFAULT_DATETIME_INLINE_FORMAT),
            'Reviewer'    : 'Автор запроса: %s' % user.full_name(),
            'Message'     : attrs and _html_note(attrs.get('note') or '', with_p=True),
        }

        html = _EMAIL_EOL.join(html.split('\n')) % props

        return self._mail('approval', html, user, users)

    def send_review_mail(self, status, note=None, **kw):
        """
            Уведомление о поступлении рецензии
        """
        html = g.page.REVIEW_ALARM_HTML

        order_id = g.requested_object.get('TID')
        order_status = g.requested_object.get('Status')

        if not order_id or not html or status < 2:
            return None

        is_review_headoffice, with_headoffice, with_assistant, with_root = \
            g.page.is_review_headoffice, \
            g.page.is_review_with_headoffice, \
            g.page.is_review_with_assistant, \
            g.page.is_review_with_root

        # Review Event
        if order_status in (1,2,3,4):
            with_root = g.system_config.IsReviewRoot

        # Paid Event
        if status == g.page.provision_review_statuses.get('paid'):
            is_review_headoffice, with_headoffice, with_root = 1, 1, g.system_config.IsReviewRoot

        # Delivered Event
        if status == g.page.provision_review_statuses.get('delivered'):
            is_review_headoffice, with_headoffice, with_root = 1, 1, 0

        # Decree Event
        if status == g.page.provision_review_statuses.get('decree'):
            is_review_headoffice, with_headoffice, with_root = 1, 1, g.system_config.IsReviewRoot

        is_audit = False

        # Audit Events
        if status in (g.page.provision_review_statuses.get('audit'), g.page.provision_review_statuses.get('failure'), g.page.provision_review_statuses.get('validated')):
            is_review_headoffice, with_headoffice, with_root = 0, 0, 0
            is_audit = True

        # From
        user = _get_user(self.login)

        # To
        author = g.requested_object.get('Author')

        reviewer, users = self._get_reviewer_managers(0, order_id, author, 
            is_review_headoffice=is_review_headoffice, 
            with_headoffice=with_headoffice, 
            with_assistant=with_assistant, 
            with_root=with_root
            )

        if is_audit:
            users += [User.get_by_email(x) for x in g.page.system_config_emails_audit]
        else:
            users += [User.get_by_email(x) for x in g.page.system_config_emails_review]
        users += [User.get_by_email(x) for x in g.page.system_config_emails_common]

        self.set_unread(order_id, users+[reviewer])
        self.set_read(order_id, [user])

        if reviewer is not None:
            if status > 2 and author != self.login:
                users.append(reviewer)

        review_duedate = kw.get('review_duedate', None) or ''

        reviewer = 'Автор рецензии: %s%s' % (user.full_name(), review_duedate and ( 
            '.<br>%s: %s' % (
                status == g.page.provision_review_statuses.get('delivered') and 'Дата исполнения' or 
                status == g.page.provision_review_statuses.get('paid') and 'Дата оплаты' or 
                status == g.page.provision_review_statuses.get('confirmation') and 'Срок обоснования' or 
                status == g.page.provision_review_statuses.get('failure') and 'Срок исполнения' or 
                '', 
                review_duedate
            )) or '')

        props = {
            'id'          : order_id,
            'Caption'     : g.page.get_review_alarm_caption(status, order_status), 
            'Seller'      : g.requested_object.get('Seller') or '',
            'Article'     : g.requested_object.get('Article') or '',
            'Date'        : getDate(getToday(), DEFAULT_DATETIME_INLINE_FORMAT),
            'Title'       : g.page.get_review_alarm_title(status, order_status), 
            'Reviewer'    : reviewer,
            'Message'     : _html_note(note or '', with_p=True),
            'Code'        : g.page.get_review_status(status, is_title=True),
            'code'        : g.page.get_review_status(status).lower() or '',
        }

        html = _EMAIL_EOL.join(html.split('\n')) % props

        return self._mail(kw.get('mode') or 'review', html, user, users)

    def send_decree_mail(self, decree, **kw):
        """
            Уведомление о поступлении поручения
        """
        html = g.page.DECREE_ALARM_HTML

        order_id = g.requested_object.get('TID')
        order_status = g.requested_object.get('Status')

        if not order_id or not html:
            return None

        # Decree Event
        is_review_headoffice, with_headoffice, with_assistant, with_root = \
            g.page.is_decree_headoffice, \
            g.page.is_decree_with_headoffice, \
            g.page.is_decree_with_assistant, \
            g.page.is_decree_with_root

        # From
        author = _get_user(self._author)

        # To
        executor = _get_user(self._executor)

        reviewer, users = self._get_reviewer_managers(0, order_id, self._executor, 
            is_review_headoffice=is_review_headoffice, 
            with_headoffice=with_headoffice, 
            with_assistant=with_assistant, 
            with_root=with_root
            )

        users += [User.get_by_email(x) for x in g.page.system_config_emails_decree + g.page.system_config_emails_common]

        self.set_unread(order_id, users+[reviewer])
        self.set_read(order_id, [author])

        if reviewer is not None:
            if self._author != self.login:
                users.append(reviewer)

        review_duedate = self._duedate or ''
        message = ''

        if self._is_executor:
            reviewer = 'Исполнитель: %s%s' % (executor.full_name(), review_duedate and ( 
                '.<br>%s: %s' % (
                    'Срок исполнения', 
                    review_duedate
                )) or '')

            title = self._title
            message = self._report

            user = executor
        else:
            reviewer = 'Автор поручения: %s%s' % (author.full_name(), review_duedate and ( 
                '.<br>%s: %s' % (
                    'Срок исполнения',
                    review_duedate
                )) or '')

            title = self._title
            message = self._note

            user = author

        props = {
            'id'          : order_id,
            'Caption'     : g.page.get_decree_alarm_caption(), 
            'Seller'      : g.requested_object.get('Seller') or '',
            'Article'     : g.requested_object.get('Article') or '',
            'Date'        : getDate(getToday(), DEFAULT_DATETIME_INLINE_FORMAT),
            'Title'       : g.page.get_decree_alarm_title(is_executor=self._is_executor), 
            'Reviewer'    : reviewer,
            'title'       : _html_note(title),
            'message'     : _html_note(message, with_p=True),
            'Code'        : g.page.get_decree_status(self._decree_status, is_title=True),
            'code'        : g.page.get_decree_status(self._decree_status)[0].lower() or '',
        }

        html = _EMAIL_EOL.join(html.split('\n')) % props

        return self._mail(kw.get('mode') or 'decree', html, user, users, decrees=(decree.decree_id,))

    def send_review_payments_mail(self, status, note=None, **kw):
        """
            Уведомление о поступлении рецензии о согласовании платежей
        """
        html = g.page.REVIEW_PAYMENTS_ALARM_HTML

        if status not in (2,3) or not html:
            return

        # From
        user = _get_user(self.login)

        reviewer = user

        # To
        users = []

        users += [User.get_by_email(x) for x in g.page.system_config_emails_payments]
        users += [User.get_by_email(x) for x in g.page.system_config_emails_common]

        caption = 'о согласовании платежей'
        reviewer = 'Автор рецензии: %s%s' % (user.full_name(), '')

        payment_status = g.page.get_payment_status(status)

        title = 'Информация о согласовании текущих платежей'

        props = {
            'Caption'     : caption,
            'company'     : kw['company'],
            'review_date' : kw['review_date'],
            'date'        : kw['date'],
            'Date'        : getDate(getToday(), DEFAULT_DATETIME_INLINE_FORMAT),
            'Title'       : title,
            'Reviewer'    : reviewer,
            'Message'     : _html_note(note or '', with_p=True),
            'Code'        : payment_status[1].upper(),
            'code'        : payment_status[0],
        }

        html = _EMAIL_EOL.join(html.split('\n')) % props

        return self._mail('payments review', html, user, users)

    def send_upload_attachment_mail(self, attrs):
        """
            Уведомление о загрузке файла вложения
        """
        html = g.page.UPLOAD_ATTACHMENT_ALARM_HTML

        order_id = g.requested_object.get('TID')

        if not order_id or not html:
            return None

        # From
        user = _get_user(self.login)

        # To
        login = attrs.get('Author')
        author = login and len(login) == 3 and login[1] != DEFAULT_UNDEFINED and login[1] or None

        reviewer = None

        try:
            if author:
                reviewer = _get_user(author)
        except:
            pass

        users = []

        if reviewer is not None:
            users.append(reviewer)
            #users += reviewer.managers()

        users += [User.get_by_email(x) for x in g.page.system_config_emails_upload]
        users += [User.get_by_email(x) for x in g.page.system_config_emails_common]

        self.set_unread(order_id, users+[reviewer])

        props = {
            'id'          : order_id,
            'Seller'      : g.requested_object.get('Seller') or '',
            'Article'     : g.requested_object.get('Article') or '',
            'Date'        : getDate(getToday(), DEFAULT_DATETIME_INLINE_FORMAT),
            'Subdivision' : g.requested_object.get('Subdivision'),
            'Attachment'  : attrs.get('Attachment')[1],
            'Message'     : _html_note(attrs.get('Message')[1] or '', with_p=True),
            'Reviewer'    : reviewer and reviewer.full_name() or '...',
            'uid'         : attrs.get('UID')[1],
        }

        html = _EMAIL_EOL.join(html.split('\n')) % props

        return self._mail('image upload', html, user, users)

    def accept(self, order_id, note):
        """
            Accept an order
        """
        errors = []

        status = g.page.provision_review_statuses.get('accept')

        if note:
            note = getString(note, save_links=True, with_html=True)

        if len(note) > MAX_CONFIRMATION_LEN:
            errors.append(gettext('Error: Confirmation Note is too long!'))

        errors += self._check_review_timedelta(order_id, status)

        if not errors:
            self.review_action(order_id, status, note)
            errors = self._errors

        if not errors:
            g.page.set_order_facsimile(order_id, self._author or self.login, with_error=True)

        return errors

    def reject(self, order_id, note):
        """
            Reject an order
        """
        errors = []

        status = g.page.provision_review_statuses.get('reject')

        if note:
            note = getString(note, save_links=True, with_html=True)

        if len(note) > MAX_CONFIRMATION_LEN:
            errors.append(gettext('Error: Confirmation Note is too long!'))

        errors += self._check_review_timedelta(order_id, status)

        if not errors:
            self.review_action(order_id, status, note)
            errors = self._errors

        return errors

    def confirm(self, order_id, note, params=None):
        """
            Confirm, request on information
        """
        errors = []

        status = g.page.provision_review_statuses.get('confirm')

        if note:
            note = getString(note, save_links=True, with_html=True)

        if len(note) > MAX_CONFIRMATION_LEN:
            errors.append(gettext('Error: Confirmation Note is too long!'))

        errors += self._check_review_timedelta(order_id, status)

        if not errors:
            self.review_action(order_id, status, note, params=params, check_past=True)
            errors = self._errors

        return errors

    def confirmation(self, order_id, note):
        """
            Make confirmation on order
        """
        errors = []

        status = g.page.provision_review_statuses.get('confirmation')

        if note:
            note = getString(note, save_links=True, with_html=True)

        if not note:
            errors.append(gettext('Error: Empty confirmation Note'))
        elif len(note) > MAX_CONFIRMATION_LEN:
            errors.append(gettext('Error: Confirmation Note is too long!'))

        errors += self._check_review_timedelta(order_id, status, note=note)

        if not errors:
            self.review_action(order_id, status, note)
            errors = self._errors

        return errors

    def paid(self, order_id, note, params=None):
        """
            Order paid event
        """
        errors = []

        status = g.page.provision_review_statuses.get('paid')

        if note:
            note = getString(note, save_links=True, with_html=True)

        if g.requested_object.get('Status') < 5:
            errors.append(gettext('Error: Order cannot be paid until accepted!'))
        elif len(note) > MAX_CONFIRMATION_LEN:
            errors.append(gettext('Error: Confirmation Note is too long!'))

        errors += self._check_review_timedelta(order_id, status)

        if not errors:
            self.review_action(order_id, status, note, params=params)
            errors = self._errors

        return errors

    def delivered(self, order_id, note, params=None):
        """
            Order delivered event
        """
        errors = []

        status = g.page.provision_review_statuses.get('delivered')

        if note:
            note = getString(note, save_links=True, with_html=True)

        if params and params.get('forced'):
            status = params.get('status', status)
        elif g.requested_object.get('Status') < 5:
            errors.append(gettext('Error: Order cannot be delivered until accepted!'))
        elif len(note) > MAX_CONFIRMATION_LEN:
            errors.append(gettext('Error: Confirmation Note is too long!'))

        if not params.get('review_duedate'):
            params['review_duedate'] = self.today

        def _set_note(s):
            return '%s (%s)%s' % (params['review_duedate'], gettext(s), note and '\n'+note or '')

        if params.get('delivered_in_part', None):
            note = _set_note('delivered in part')
            params['review_duedate'] = None
        else:
            note = _set_note('delivered in final')

        errors += self._check_review_timedelta(order_id, status)

        if not errors:
            self.review_action(order_id, status, note, params=params)
            errors = self._errors

        return errors

    def finish(self, order_id, note, params=None):
        """
            Order finished event
        """
        errors, title, status = [], 'set-status', g.page.statuses.get('finish')
        """
        kw.update({
            'order_id' : order_id,
            'status'   : status,
        })

        try:
            if not errors:
                kw['login'] = self.login
                errors = self.run(title, kw)
        except:
            if IsPrintExceptions:
                print_exception()

            self._exception(errors)
        """
        return errors

    def audit(self, order_id, note, params=None):
        """
            Order audit event
        """
        errors = []

        status = g.page.provision_review_statuses.get('audit')

        if note:
            note = getString(note, save_links=True, with_html=True)

        if params and params.get('forced'):
            status = params.get('status', status)

        if not errors:
            self.review_action(order_id, status, note, params=params)
            errors = self._errors

        return errors

    def failure(self, order_id, note, params=None):
        """
            Order failure event
        """
        errors = []

        status = g.page.provision_review_statuses.get('failure')

        if note:
            note = getString(note, save_links=True, with_html=True)

        if params and params.get('forced'):
            status = params.get('status', status)

        errors += self._check_review_timedelta(order_id, status)

        if not errors:
            self.review_action(order_id, status, note, params=params)
            errors = self._errors

        return errors

    def validated(self, order_id, note, params=None):
        """
            Order validated event
        """
        errors = []

        ob = g.requested_object
        order_status = ob.get('Status')

        status = g.page.provision_review_statuses.get('validated')

        if note:
            note = getString(note, save_links=True, with_html=True)

        if params and params.get('forced'):
            status = params.get('status', status)
        elif order_status < g.page.statuses.get('execute'):
            errors.append(gettext('Error: Order cannot be validated until accepted!'))
        elif order_status == g.page.statuses.get('finish'):
            errors.append(gettext('Error: Order has been already finished.'))
        elif len(note) > MAX_CONFIRMATION_LEN:
            errors.append(gettext('Error: Confirmation Note is too long!'))

        if not errors:
            self.review_action(order_id, status, note, params=params)
            errors = self._errors

        refreshOrder(order_id=order_id)

        if not errors:
            data, errors = self.set_status(order_id, {'command' : 'STATUS_FINISH'}, force=True)

        return errors

    def decree(self, order_id, note, params=None):
        """
            Decree an order
        """
        errors = []

        command = params.get('command')

        status = g.page.provision_review_statuses.get('decree')

        errors, tag_params, kw = self.set_decree(params)

        if errors or not kw:
            return errors

        review_id = int(kw.get('review_id') or 0) or None
        decree_id = int(kw.get('decree_id') or 0) or None
        report_id = int(kw.get('report_id') or 0) or None

        decree = _get_decree_instance(order_id=order_id, review_id=review_id, decree_id=decree_id, report_id=report_id)

        decree.refresh(self)

        action = ''
        is_accept_decree = 0

        if not command or command == 'SAVE_DECREE':
            if self._decree_status != g.page.provision_decree_statuses['work']:
                errors.append(gettext('Warning: Decree is already done!'))
            if not self._executor:
                errors.append(gettext('Error: Executor should be present!'))
            is_accept_decree = 1

        elif command == 'ACCEPT_DECREE':
            action = 'provision-accept-decree'
            is_accept_decree = 1

        elif command == 'FINISH_DECREE':
            if self._decree_status != g.page.provision_decree_statuses['work']:
                errors.append('%s %s!' % (
                    gettext('Warning: Decree is already'), 
                    g.page.get_decree_status(self._decree_status, is_title=True)
                    ))
            else:
                action = 'provision-finish-decree'

        elif command == 'REJECT_DECREE':
            if self._decree_status != g.page.provision_decree_statuses['work']:
                errors.append('%s %s!' % (
                    gettext('Warning: Decree is already'), 
                    g.page.get_decree_status(self._decree_status, is_title=True)
                    ))
            else:
                action = 'provision-reject-decree'

        elif command == 'REMOVE_DECREE':
            action = 'provision-remove-decree'

        if not errors:
            decree.make_note(note, **kw)
            decree.make_report(is_accept_decree=is_accept_decree, **kw)

        if len(note) > MAX_CONFIRMATION_LEN:
            errors.append(gettext('Error: Confirmation Note is too long!'))

        params.update({
            'review_duedate' : self._duedate,
            'executor'       : self._executor,
            'login'          : self._author,
            'with_mail'      : True,
        })

        errors += self._check_review_timedelta(order_id, status)

        check_past = not review_id and True or False

        if not errors:
            self.review_action(order_id, status, decree.note, params=params, check_past=check_past, 
                mode='decree', action=action, decree=decree)
            errors = self._errors

        return errors

    def params_action(self, order_id, attrs):
        """
            Actions with Order Params: ADD|DEL
        """
        command = attrs.get('command')
        id = int(attrs.get('id') or 0)
        param_id = int(attrs.get('param_id') or 0)
        new_param = getSQLString(attrs.get('new_param'))
        param_value_mode = int(attrs.get('param_value_mode'))
        value = getSQLString(attrs.get('value'))

        data, errors, kw, title = [], [], {}, ''

        if command in ('ADD_PARAM', 'SAVE_PARAM',):
            if not param_id and not new_param:
                errors.append(gettext('Error: Empty Param ID'))
            elif new_param:
                param_id = 0

            if not value:
                errors.append(gettext('Error: Empty Param value'))

            title = 'add-param'
            kw.update({
                'order_id'  : order_id,
                'param_id'  : param_id,
                'new_param' : new_param,
                'value'     : value,
                'id'        : id,
                'model'     : g.page.model,
            })

        if command == 'DEL_PARAM':
            if not id:
                errors.append(gettext('Error: Empty Param ID'))

            title = 'del-param'
            kw.update({
                'order_id'  : order_id,
                'param_id'  : param_id,
                'id'        : id,
            })
        
        try:
            if not errors:
                kw['login'] = self.login
                errors = self.run(title, kw)
        except:
            if IsPrintExceptions:
                print_exception()

            self._exception(errors)

        data = _get_order_params(order_id, order='Name')

        if self.status and not self.status.startswith('Invalid') and new_param:
            data['reference'] = ('param', self._get_reference_id(), new_param)

        return data, '', errors

    def items_action(self, order_id, attrs):
        """
            Actions with Order Items: ADD|DEL
        """
        command = attrs.get('command')
        id = int(attrs.get('id') or 0)
        item = getSQLString(attrs.get('name'))
        qty = int(attrs.get('qty') or 0) or 1
        units = getSQLString(attrs.get('units')) or 'шт.'
        total = getMoney(attrs.get('total'))
        currency = attrs.get('currency')
        account = getSQLString(attrs.get('account'))
        vendor_id = int(attrs.get('vendor') or 0)
        new_vendor = getSQLString(attrs.get('new_vendor'))
        no_tax = attrs.get('no_tax') and True or False

        data, errors, kw, title = [], [], {}, ''

        if command in ('ADD_ITEM', 'SAVE_ITEM',):
            if not item:
                errors.append(gettext('Error: Empty Item name'))

            if not currency or currency == DEFAULT_UNDEFINED:
                currency = 'RUB'

            if not total and not self.user.app_is_author:
                errors.append(gettext('Error: Empty Item total value'))

            title = 'add-item'
            kw.update({
                'order_id'  : order_id,
                'id'        : id,
                'vendor_id' : vendor_id,
                'item'      : item,
                'qty'       : qty,
                'units'     : units,
                'total'     : total,
                'tax'       : no_tax and _get_tax(total) or 0.0,
                'currency'  : currency,
                'account'   : account,
                'vendor'    : new_vendor,
            })

        if command == 'DEL_ITEM':
            if not id:
                errors.append(gettext('Error: Empty Item ID'))

            title = 'del-item'
            kw.update({
                'order_id'  : order_id,
                'id'        : id,
            })

        try:
            if not errors:
                kw['login'] = self.login
                errors = self.run(title, kw)
        except:
            if IsPrintExceptions:
                print_exception()

            self._exception(errors)

        data = _get_order_items(order_id, order='Name')

        if self.status and not self.status.startswith('Invalid') and new_vendor:
            data['reference'] = ('vendor', self._get_reference_id(), new_vendor)

        return data, '', errors

    def payments_action(self, order_id, attrs):
        """
            Actions with Order Payments: ADD|DEL
        """
        command = attrs.get('command')
        id = int(attrs.get('id') or 0)
        payment_id = int(attrs.get('payment_id') or 0)
        new_payment = getSQLString(attrs.get('new_payment'))
        date = attrs.get('date') or getDate(self.today, DEFAULT_DATE_FORMAT[1])
        total = getMoney(attrs.get('total'))
        currency = attrs.get('currency')
        status = int(attrs.get('status') or 0)
        comment = getSQLString(attrs.get('comment'))

        data, errors, kw, title, current_status = [], [], {}, '', 0

        order_total = g.requested_object.get('Total')
        order_currency = g.requested_object.get('Currency')
        order_status = g.requested_object.get('Status')

        try:
            payments = _get_payments(order_id, id=id) or None
            current_status = payments and payments.get('data')[0]['Status'] or 0
        except:
            pass

        if command in ('ADD_PAYMENT', 'SAVE_PAYMENT',):
            if not payment_id and not new_payment:
                errors.append(gettext('Error: Empty Payment ID'))
            elif new_payment:
                payment_id = 0

            if not date:
                pass

            if not total:
                errors.append(gettext('Error: Empty Payment total value'))

            if not currency or currency == DEFAULT_UNDEFINED:
                currency = 'RUB'

            if not self.is_extra:
                if status == 1 and order_status in (0,1,3,4):
                    errors.append(gettext("Error: Order is not accepted! Not allowed"))

                if status in (4,5) and order_status not in (5,6):
                    errors.append(gettext("Error: Order is not executed! Not allowed"))

                if status in (4,5) and current_status in (0,1):
                    errors.append(gettext("Error: Payment is not accepted! Not allowed"))

                if status in (4,5) and current_status == 3:
                    errors.append(gettext("Error: Payment is rejected! Not allowed"))

            selected_date = getDate(date, format=DEFAULT_DATE_FORMAT[1], is_date=True)

            if status in (4,5) and selected_date > self.today:
                errors.append(gettext("Error: Date of payment is in future! Not allowed"))

            rate = getMoney(attrs.get('rate')) or _get_exchange_rate('%s:RUB' % currency)
            exchange_rate = getMoney(attrs.get('exchange_rate'))

            if not exchange_rate:
                if order_currency == 'RUB' or not order_currency:
                    exchange_rate = 1.0
                elif currency != 'RUB':
                    exchange_rate = 1.0
                else:
                    exchange_rate = _get_exchange_rate('%s:RUB' % order_currency)

            if not self.is_extra and status == 1:
                x1, s1, x2, s2, x3, s3 = _calc_payments(_get_order_payments(order_id), order_total, order_currency, 
                    statuses=(1,2,4,5), exclude=(id,), is_cross=g.system_config.IsCross, 
                    exchange_rate=exchange_rate)
                total_rub = round(calc_rub(total, currency), 2)

                if currency == 'RUB':
                    if total_rub > s1:
                        errors.append(gettext("Error: Payment is over accepted limit! Not allowed"))

                        if IsTrace:
                            print_to(None, '!!! payments_action.limit %s %s %s [%s:%s] %s, rate:[%s]' % (
                                self.login, order_id, id, total_rub, s1, currency, 
                                _get_exchange_rate('%s:RUB' % currency)
                                ))

                else:
                    if total > s3 or total_rub > s1:
                        errors.append(gettext("Error: Payment is over accepted limit! Not allowed"))

                        if IsTrace:
                            print_to(None, '!!! payments_action.limit %s %s %s [%s:%s] %s, rate:[%s]' % (
                                self.login, order_id, id, total, s3, currency, 
                                _get_exchange_rate('%s:RUB' % currency)
                                ))

            title = 'add-payment'
            kw.update({
                'order_id'      : order_id,
                'payment_id'    : payment_id,
                'new_payment'   : new_payment,
                'date'          : date,
                'total'         : total,
                'tax'           : _get_tax(total * rate),
                'currency'      : currency,
                'rate'          : rate,
                'exchange_rate' : exchange_rate,
                'status'        : status,
                'comment'       : comment,
                'id'            : id,
            })

        if command == 'DEL_PAYMENT':
            if not id:
                errors.append(gettext('Error: Empty Payment ID'))

            title = 'del-payment'
            kw.update({
                'order_id'    : order_id,
                'payment_id'  : payment_id,
                'id'          : id,
            })

        try:
            if not errors:
                kw['login'] = self.login
                errors = self.run(title, kw)
        except:
            if IsPrintExceptions:
                print_exception()

            self._exception(errors)

        data = _get_order_payments(order_id)

        if self.status and not self.status.startswith('Invalid') and new_payment:
            data['reference'] = ('payment', self._get_reference_id(), new_payment)

        return data, '', errors

    def refers_action(self, order_id, attrs):
        """
            Actions with Order Refers: ADD|DEL
        """
        command = attrs.get('command')
        id = int(attrs.get('id') or 0)
        refer_id = int(attrs.get('refer_id') or 0)
        new_refer = getSQLString(attrs.get('new_refer'))
        value = getSQLString(attrs.get('value'))
        note = getSQLString(attrs.get('note'))

        data, errors, kw, title = [], [], {}, ''

        if command in ('ADD_REFER', 'SAVE_REFER',):
            if not refer_id and not new_refer:
                errors.append(gettext('Error: Empty Refer ID'))
            elif new_refer:
                refer_id = 0

            if not value or not value.isdigit():
                errors.append(gettext('Error: Empty or incorrect Refer value'))
            else:
                value = int(value)

            title = 'add-refer'
            kw.update({
                'order_id'  : order_id,
                'refer_id'  : refer_id,
                'new_refer' : new_refer,
                'value'     : value,
                'note'      : note,
                'id'        : id,
                'model'     : g.page.model,
            })

        if command == 'DEL_REFER':
            if not id:
                errors.append(gettext('Error: Empty Refer ID'))

            title = 'del-refer'
            kw.update({
                'order_id'  : order_id,
                'refer_id'  : refer_id,
                'id'        : id,
            })
        
        try:
            if not errors:
                kw['login'] = self.login
                errors = self.run(title, kw)
        except:
            if IsPrintExceptions:
                print_exception()

            self._exception(errors)

        data = _get_order_refers(order_id, order='Name')

        if self.status and not self.status.startswith('Invalid') and new_refer:
            data['reference'] = ('refer', self._get_reference_id(), new_refer)

        return data, '', errors

    def comments_action(self, order_id, attrs):
        """
            Actions with Order Comments: ADD|DEL
        """
        command = attrs.get('command')
        id = int(attrs.get('id') or 0)
        comment_id = int(attrs.get('comment_id') or 0)
        new_comment = getSQLString(attrs.get('new_comment'))
        note = getSQLString(attrs.get('note'))

        data, errors, kw, title = [], [], {}, ''

        if command == 'ADD_COMMENT':
            if not comment_id and not new_comment:
                errors.append(gettext('Error: Empty Comment ID'))
            elif new_comment:
                comment_id = 0

            if not note:
                errors.append(gettext('Error: Empty Comment value'))

            title = 'add-comment'
            kw.update({
                'order_id'    : order_id,
                'comment_id'  : comment_id,
                'new_comment' : new_comment,
                'note'        : note,
                'id'          : id,
            })

        try:
            if not errors:
                kw['login'] = self.login
                errors = self.run(title, kw)
        except:
            if IsPrintExceptions:
                print_exception()

            self._exception(errors)

        data = _get_order_comments(order_id, order='Author')

        if self.status and not self.status.startswith('Invalid') and new_comment:
            data['reference'] = ('comment', self._get_reference_id(), new_comment)

        return data, '', errors

    def documents_action(self, order_id, attrs):
        """
            Actions with Order Documents: ADD|DEL
        """
        command = attrs.get('command')
        id = int(attrs.get('id') or 0)
        filename = getSQLString(attrs.get('filename'))
        value = getSQLString(attrs.get('value'))
        for_audit = attrs.get('for_audit') and True or False

        data, errors, kw, title = [], [], {}, ''

        engine = g.storage

        if command in ('ADD_DOCUMENT',):
            command = None

        if command == 'DEL_DOCUMENT':
            if not id:
                errors.append(gettext('Error: Empty Document ID'))

            title = 'del-document'
            kw.update({
                'order_id'  : order_id,
                'id'        : id,
                'for_audit' : for_audit and 1 or 0,
            })

        try:
            if not errors and command:
                kw['login'] = self.login
                errors = self.run(title, kw, engine=engine)
        except:
            if IsPrintExceptions:
                print_exception()

            self._exception(errors)

        data = _get_order_documents(order_id, order='FileName', engine=engine)
        """
        if self.status and not self.status.startswith('Invalid'):
            data['reference'] = ('document', self._get_reference_id(), filename)
        """
        return data, '', errors

    def register_stocklist(self, order_id, state):
        """
            Change StockList State (ID) on the Order
        """
        if not order_id:
            return

        self.action_id, self.status = 0, None

        cursor, error_msg = g.page.runProcedure('provision-register-stocklist', 
                order_id=order_id,
                login=self.login, 
                id=int(state),
                with_error=True,
                with_log=True,
            )

        if cursor:
            self.action_id = cursor[0][0]
            self.status = cursor[0][1]
        else:
            if IsTrace:
                print_to(None, '!!! review_action, no cursor: %s' % str(self.login))

        if error_msg and g.engine.engine_error:
            self._errors.append(error_msg)

        errors = self._errors

        return errors

    def set_status(self, order_id, attrs, **kwargs):
        """
            Change status of Order
        """
        command = attrs.get('command')
        status = None

        is_extra = kwargs.get('is_extra') and True or False
        force = kwargs.get('force') and True or False

        data, errors, kw, title, review = [], [], {}, 'set-status', ''

        ob = g.requested_object
        unreads = None

        is_run = True

        if command.startswith('STATUS_'):
            key = command.split('_')[1].lower()

            errors = g.page.check_status_default(ob, key, is_extra=is_extra)

            if not errors:
                is_run, review, error = g.page.check_status(command, ob, order_id=order_id, key=key, force=force)
                if error:
                    errors.append(error)

            if review in ('audit', 'finish'):
                unreads = g.page.system_config_emails_audit

            if not is_run:
                status = ob['Status']
            elif not errors:
                status = g.page.statuses.get(key)
                unreads = status in (5,6) and g.page.system_config_emails_execute

            kw.update({
                'order_id' : order_id,
                'status'   : status,
            })

        try:
            if is_run and not errors:
                kw['login'] = self.login
                errors = self.run(title, kw)
        except:
            if IsPrintExceptions:
                print_exception()

            self._exception(errors)

        if not errors:
            errors = g.page.set_status(self, review, ob, **kw)

        if not errors:
            self.notify(order_id, ob.get('Author'), unreads=unreads or g.page.system_config_emails_review)

        refreshOrder(order_id=order_id)

        data = g.page.get_status(status), g.page.check_order_status()

        return data, errors

    def get_order_reviewers(self, order_id, by_list=None):
        """
            Get Order Checked Reviewers list
        """
        items = []

        reviewers = [x.login for x in self._get_reviewers(order_id)]

        author = g.requested_object.get('Author')

        is_review_headoffice = True

        with_headoffice = 1
        with_assistant = 1
        with_root = 1

        reviewer, users = self._get_reviewer_managers(0, order_id, author, is_review_headoffice=is_review_headoffice, 
            with_headoffice=with_headoffice, with_assistant=with_assistant, with_root=with_root)

        managers = [x.login for x in users]

        if reviewer:
            items.append(reviewer.login)

        items = list(set(filter(None, reviewers + managers)))

        if by_list:
            return items
        return DEFAULT_HTML_SPLITTER.join(items)

    def set_order_reviewers(self, order_id, data):
        """
            Set Order Checked Reviewers list
        """
        reviewers = self.get_order_reviewers(order_id, by_list=True)
        items = data.split(DEFAULT_HTML_SPLITTER)

        new = [x for x in items if x not in reviewers]

        errors, kw, title = [], {}, ''

        title = 'register-reviewers'

        if data:
            kw.update({
                'order_id'  : order_id,
                'value'     : DEFAULT_HTML_SPLITTER.join(items),
                'model'     : g.page.model,
            })
        else:
            errors.append(gettext('Error: Empty Reviewers list'))

        try:
            if not errors:
                kw['login'] = self.login
                errors = self.run(title, kw)
        except:
            if IsPrintExceptions:
                print_exception()

            self._exception(errors)

        if self.action():
            self.send_approval_mail({'note' : gettext('You were accepted as order reviwer.')}, no_status=True)

        return errors

    def action(self):
        return not g.engine.engine_error and self.status and not self.status.startswith('Invalid') and self.action_id or None

    def run(self, title, kw, engine=None):
        errors = []

        action = 'provision-%s-order' % title

        self.action_id, self.status = 0, None

        cursor = g.page.runProcedure(action, with_log=True, engine=engine, **kw)

        if cursor:
            self.action_id = cursor[0][0]
            self.status = cursor[0][1]
        else:
            if IsTrace:
                print_to(None, '!!! %s, no cursor: %s' % (action, str(self.login)))

            errors.append(gettext('Execution error'))

        if not self.action():
            errors.append('%s %s' % (
                gettext('Error: Provision order %s error:' % title), 
                self.status or gettext('Error: SQL broken. See transaction log.')))

        if errors:
            if IsTrace or IsPrintExceptions:
                print_to(None, '!!! %s, run error, status: %s, login: %s, kw: %s, errors: %s' % (
                    action, self.status, str(self.login), repr(kw), repr(errors)))

        g.page.reset()

        return errors


class OrderImageLoader(FileDecoder):

    _allowed_types = ('jpg', 'gif', 'png', 'pdf', 'xls', 'xlsx', 'doc', 'docx', 'txt',)
    _allowed_image_types = ('jpg', 'gif', 'png',)

    def __init__(self, **kw):
        if IsDeepDebug:
            print_to(None, 'OrderImageLoader.init')

        super(OrderImageLoader, self).__init__(**kw)

        self._source = ''
        self._uid = None
        self._size = 0
        self._content_type = ''
        self._lastrowid = None

        self.login = g.current_user.login

        self.errors = []

    def _init_state(self, **kw):
        if IsDeepDebug:
            print_to(None, 'OrderImageLoader.inistate')

        super(OrderImageLoader, self)._init_state(**kw)

        self._source = self.original

    def new_uid(self):
        self._uid = ('%s%s' % (self.request_id, getUID()))[:50].upper()

    @property
    def source(self):
        return self._source
    @property
    def size(self):
        return self._size
    @property
    def content_type(self):
        return self._content_type
    @property
    def lastrowid(self):
        return self._lastrowid
    @property
    def uid(self):
        return self._uid
    @property
    def is_error(self):
        return g.storage.is_error

    @staticmethod
    def get_data(cursor, index=0):
        rows = []
        for n, row in enumerate(cursor):
            rows.append(row)
        return rows and rows[index]

    @staticmethod
    def get_value(x):
        return x and len(x) > 0 and x[0][0] or None

    def image_type(self, filename):
        if filename and '.' in filename:
            x = filename.split('.')[1].lower()
            if x and x in self._allowed_image_types:
                return x
        return None

    def getImage(self, uid, with_log=None):
        where = "UID='%s'" % uid
        encode_columns = ('FileName',)

        row = None

        cursor = g.page.runQuery(_views['download'], where=where, encode_columns=encode_columns, with_log=with_log, engine=g.storage)
        if cursor:
            row = self.get_data(cursor)

        return row

    def setImage(self, order_id, note, for_audit, model):
        self._lastrowid = None

        image = self.file_getter(self.tmp_compressed)

        if not image:
            return

        self.new_uid()

        is_pyodbc = False

        try:
            is_pyodbc = g.storage.connection.get('driver') == 'pyodbc'
        except:
            pass

        sql = 'INSERT INTO [dbo].[OrderDocuments_tb](UID, OrderID, Login, FileName, FileSize, ContentType, ForAudit, Note, Image, MD) VALUES(%s)' % (
                is_pyodbc and '?,?,?,?,?,?,?,?,?' or '%s,%d,%s,%s,%d,%s,%d,%s,%s,%d'
            )

        args = ( 
            self.uid,
            order_id, 
            self.login,
            self.original,
            self.size,
            self.content_type,
            for_audit and 1 or 0,
            note or '',
            image,
            model,
        )

        rows, error_msg = g.storage.run(sql, args=args, no_cursor=True, with_error=True)

        if not self.is_error:
            self._lastrowid = g.page.getReferenceID(_views['order-documents'], 'UID', self.uid, engine=g.storage)

        if error_msg:
            self.errors.append('Engine error: %s' % error_msg)

        if not self.is_error:
            g.page.upload_attachment_notification(g.instance, self._lastrowid, 
                uid=self.uid,
                order_id=order_id,
                login=self.login,
                original=self.original,
                size=self.size,
                content_type=self.content_type,
                for_audit=for_audit,
                note=note,
                )

    def download(self, uid, with_commit=None):
        data = None

        row = self.getImage(uid)

        if row is not None and len(row) == 4:
            self._source = row[0]
            self._size = row[1]
            self._content_type = row[2]
            data = row[3]

        if data is None:
            self.errors.append(gettext('Error: No data downloaded!'))
            return None

        self._decompress(self.tmp_decompressed, data)

        if not self._content_type:
            self._content_type = '.' in self._source and self._source.split('.')[-1].lower() or ''

        return self.file_getter(self.tmp_decompressed)

    def zip(self, documents, order_id):
        from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
        from io import BytesIO

        archive = BytesIO()

        with ZipFile(archive, 'w', ZIP_DEFLATED) as output:
            for x in documents:
                uid = x['UID']
                filename = x['original-filename']
                rd = tuple(x['RD'].timetuple())

                info = ZipInfo('%s/%s' % (order_id, filename), date_time=rd)
                output.writestr(info, self.download(uid))

        self._content_type = 'zip'

        self.file_setter(self.tmp_decompressed, archive.getbuffer())

        archive.close()

        return self.file_getter(self.tmp_decompressed)

    def upload(self, order_id, stream, note, for_audit, model, with_commit=None):
        if not self.original or '.' not in self.original or self.original.split('.')[-1].lower() not in self._allowed_types:
            self.errors.append('%s:<br>%s' % (gettext('Error: Type of uploaded files are the next'), ', '.join(self._allowed_types)))
            return

        with stream as fi:
            self._size = self.file_setter(self.tmp_image, fi.read())

        if self._size > MAX_UPLOADED_IMAGE:
            self.errors.append('%s:<br>%s' % (gettext('Error: Size of uploaded data should be less then'), MAX_UPLOADED_IMAGE))
            return

        note = getString(note, save_links=True, with_html=True)
        
        if not note and for_audit:
            self.errors.append(gettext('Error: Image Note is obligatory field!'))
            return

        self._compress(self.tmp_compressed, self.tmp_image)

        self.setImage(order_id, note, for_audit, model)

## ==================================================== ##

def _ok_message(done):
    return g.page.order_created(done)

def _is_unread(x):
    return x in g.requested_object.get('UnreadByLogin') and True or False

def _is_read(x):
    return not _is_unread(x)

def _is_valid_author(login):
    return login and login not in ('autoload',) and True or False

def _is_valid_seller(seller):
    return seller and seller.get('Name') and not (seller['Name'].startswith('- ') and seller['Name'].endswith(' -'))

def _is_show_seller_info(login):
    x = g.system_config.SHOW_SELLER_INFO or ''
    return g.page.is_office_ceo or login in x or '*' in x

def _html_note(note, with_p=None):
    if with_p:
        note = ''.join(['<p>%s</p>' % x for x in note.split('\n\n')])
    return re.sub(r'\r?\n', '<br>', note.strip())

def _html_status(title, value, html=None):
    s = '<span class="status_stamp %s">%s</span>' % (g.page.review_statuses[value][0], title)
    return html and html % s or s

def _html_payment_status(title, value):
    return '<div class="payment_status_stamp %s">%s</div>' % (g.page.payment_statuses[value][0], title)

def _conv_date(value):
    if not value:
        return None
    v = value.split('.')
    if len(v) != 3:
        return None
    x = '%s-%s-%s' % (v[2], v[1], v[0])
    if not checkDate(x, DEFAULT_DATE_FORMAT[1]):
        return None
    return x

def _get_user(login):
    return login and _is_valid_author(login) and User.get_by_login(login) or None

def _get_top(per_page, page):
    if g.system_config.IsApplyOffset:
        top = per_page
    else:
        top = per_page * page
    offset = page > 1 and (page - 1) * per_page or 0
    return top, offset

def _get_max_page(per_page_options, total_lines):
    page, per_page = 1, max(per_page_options)
    for x in per_page_options:
        if x > total_lines:
            per_page = x
            page = 1
            break
    return page, per_page

def _get_title(value):
    return re.sub(r'""+', '"', re.sub(r'^\"(.*)\"$', r'\1', value.strip()))

def _get_total(price, qty):
    return price * qty

def _get_tax(total, is_clean=None):
    x = float(total)
    if is_clean:
        return x * 0.2
    return x - (x / 1.2)

def _get_exchange_rate(currency):
    return g.exchange_rate.get(currency) or 1.0

def _get_date(value, format=None):
    return getDate(value, format or DEFAULT_DATETIME_INLINE_SHORT_FORMAT)

def _get_columns(name):
    return ','.join(g.page.database_config(name).get('columns'))

def _get_view_columns(view):
    columns = []
    with_class = view.get('with_class') or {}
    for name in view.get('columns') or []:
        columns.append({
            'name'       : name,
            'header'     : view['headers'].get(name),
            'with_class' : with_class.get(name) and 1 or 0, #name in ('Avatar', 'StatusDate',) and 1 or 0,
        })
    return columns

#   ----------------
#   Class Instancies
#   ----------------

def _get_decree_instance(**kw):
    """
        Decree instance
    """
    ob = Decree(g.engine, **kw)
    ob._init_state(
        attrs={
            'locator'   : default_locator,
            'page'      : g.page,
            'view'      : _views['decrees'],
        }, 
        factory={
            'init_default'       : init_default,
            'refresh'            : refresh,
            'get_orders'         : _get_orders,
            'get_reviews'        : _get_reviews,
            'get_decrees'        : _get_decrees,
            'get_order'          : _get_order, 
            'get_order_link'     : _get_order_link, 
            'get_date'           : _get_date,
            'html_note'          : _html_note, 
            'info'               : _make_current_order_info, 
            'calc_rub'           : calc_rub, 
        }
    )
    return ob

def _get_profile_instance(login, **kw):
    """
        User Profile instance
    """
    ob = UserProfile(g.engine, login)
    ob._init_state(
        attrs={
            'locator'   : default_locator,
            'page'      : g.page,
        }, 
        factory={
            'get_seller'         : _get_seller, 
            'get_orders'         : _get_orders, 
            'get_decrees'        : _get_decrees,
            'get_order'          : _get_order, 
            'get_order_link'     : _get_order_link, 
            'get_date'           : _get_date,
            'html_note'          : _html_note, 
            'info'               : _make_current_order_info, 
        }
    )
    return ob

def _get_seller_instance(uid, **kw):
    """
        Seller instance
    """
    ob = Seller(g.engine, int(uid))
    ob._init_state(
        attrs={
            'locator'   : default_locator,
            'page'      : g.page,
            'stocklist' : kw.get('stocklist'),
            'stock'     : kw.get('stock'),
        }, 
        factory={
            'get_seller'         : _get_seller, 
            'get_orders'         : _get_orders, 
            'get_order'          : _get_order, 
            'get_order_link'     : _get_order_link, 
            'get_date'           : _get_date,
            'html_note'          : _html_note, 
            'info'               : _make_current_order_info, 
            'calc_rub'           : calc_rub, 
        }
    )
    return ob

def _get_payments_review_instance(date, **kw):
    """
        PaymentReview instance
    """
    ob = PaymentsReview(g.engine, date)
    ob._init_state(
        attrs={
            'locator'   : default_locator,
            'page'      : g.page,
        }, 
        factory={
            'get_order'          : _get_order,
            'get_orders'         : _get_orders,
            'get_order_dates'    : _get_order_dates,
            'get_seller_link'    : _get_seller_link,
            'get_order_link'     : _get_order_link,
            'get_date'           : _get_date,
            'get_exchange_rate'  : _get_exchange_rate,
            'html_note'          : _html_note,
            'info'               : _make_current_order_info,
            'calc_rub'           : calc_rub,
            'send_review_mail'   : g.instance.send_review_payments_mail,
        }
    )
    return ob

#   -------------------------
#   Database Objects Handlers
#   -------------------------

def _handler_money(config, row):
    for column in config.get('money', []):
        row[column] = getFloatMoney(row.get(column), driver=g.page.driver)
    return row

def _handler_changes(config, row):
    row['RD'] = getDate(row['RD'], DEFAULT_DATETIME_FORMAT)

def _handler_documents(config, row):
    row['image-type'] = g.page.image_loader.image_type(row['FileName'])
    if row.get('IsExist'):
        row['original-filename'] = row['FileName']
        row['FileName'] = '<a href="/storage/image/%s" target="_blank">%s</a>' % (row['UID'], row['FileName'])
    row['Note'] = getHtmlCaption(row['Note'])
    row['ForAudit'] = gettext(row['ForAudit'] and 'Yes' or 'No')

def _handler_items(config, row):
    if not row.get('Currency'):
        row['Currency'] = 'RUB'

    for column in config.get('money', []):
        row[column] = getCurrency(row[column], driver=g.page.driver) or '0.0'

    row['Name'] = getHtmlCaption(row['Name'])

def _handler_refers(config, row):
    if not row.get('Currency'):
        row['Currency'] = 'RUB'

    for column in config.get('money', []):
        row[column] = getCurrency(row[column], driver=g.page.driver) or '0.0'

    row['Name'] = '<a href="/provision?_id=%s" target="_blank">%s</a>' % (row['OrderReferID'], getHtmlCaption(row['Name']))
    row['Value'] = row['OrderReferID']

def _handler_payments(config, row):
    if not row.get('Currency'):
        row['Currency'] = 'RUB'

    row['Rate'] = not row.get('Rate') and '1.0' or str(float(row['Rate']))
    row['rate'] = float(row['Rate'])

    row['ExchangeRate'] = not row.get('ExchangeRate') and '1.0' or str(float(row['ExchangeRate']))
    row['exchange_rate'] = float(row['ExchangeRate'])

    for column in config.get('money', []):
        row[column.lower()] = getFloatMoney(row[column], driver=g.page.driver)
        row[column] = getCurrency(row[column], driver=g.page.driver)

    for column in ('PaymentDate', 'RD',):
        row[column] = getDate(row[column], LOCAL_EASY_DATESTAMP)

    status = row['Status']
    payment_status = g.page.get_payment_status(status)
    
    row['StatusID'] = status
    row['Status'] = _html_payment_status(payment_status[1], status)

def _get_order(order_id):
    #print(g.page.engine.connection.get('database'))
    config = g.page.database_config(default_template)
    columns = config['export']
    where = 'TID=%s' % order_id
    encode_columns = _default_encode_columns
    cursor = g.page.runQuery(default_template, columns=columns, top=1, where=where, as_dict=True, encode_columns=encode_columns)
    return cursor and _handler_money(config, cursor[0]) or {}

def _get_orders(**kw):
    template = kw.get('template') or default_template
    config = g.page.database_config(template)
    columns = kw.get('columns') or config['export']
    where = kw.get('where') or ''
    order = kw.get('order') or ''
    encode_columns = not kw.get('no_encode') and _default_encode_columns or None
    as_dict = 'as_dict' not in kw and True or kw['as_dict'] and True or False
    cursor = g.page.runQuery(template, columns=columns, where=where, order=order, as_dict=as_dict, encode_columns=encode_columns)
    return [_handler_money(config, row) for row in cursor]

def _get_reviews(order_id, **kw):
    reviews = []
    selected_id = kw.get('selected_id')

    view = _views['reviews']
    columns = g.page.database_config(view)['export']

    login = kw.get('login') or None
    review_id = kw.get('review_id') or None
    reviewer = kw.get('reviewer') or None

    where = 'OrderID=%d%s%s%s' % (
        int(order_id), 
        review_id and (" and TID=%d" % int(review_id)) or '',
        login and (" and Login='%s'" % login) or '',
        reviewer and (" and Reviewer='%s'" % reviewer) or '',
        )

    encode_columns = ('Article', 'Qty', 'Seller', 'Reviewer', 'Note',)

    order = kw.get('order') or 'TID'

    cursor = g.page.runQuery(view, columns=columns, where=where, order=order, as_dict=True, encode_columns=encode_columns)
    
    if kw.get('cursor'):
        return cursor

    today = getDateOnly(getToday())

    if cursor:
        IsSelected = False

        for n, row in enumerate(cursor):
            status = g.page.review_statuses.get(row['Status'])
            author = _get_user(row['Login'])

            html = ''
            if row['Status'] == 9:
                if row['DecreeStatus'] == g.page.provision_decree_statuses['work'] and row['DueDate'] and row['DueDate'] < today:
                    html = '<div class="overdue">%s</div>'
                elif row['DecreeStatus'] == g.page.provision_decree_statuses['done']:
                    html = '<div class="done">%s</div>'
                elif row['DecreeStatus'] == g.page.provision_decree_statuses['rejected']:
                    html = '<div class="rejected">%s</div>'

            row['Status'] = _html_status(g.page.get_review_status(row['Status'], is_title=True), row['Status'])
            row['StatusDate'] = _get_date(row['StatusDate'])
            row['Note'] = getHtmlCaption(row['Note'], html=html, truncate=10)

            if g.system_config.IsUseReviewerAvatar:
                avatar = author and author.get_small_avatar() or default_user_avatar(author)
                row['Reviewer'] = '%s <div class="reviewer" author="%s">%s</div>' % (avatar, author, row['Reviewer'])

            row['id'] = row['TID']

            if selected_id and row['id'] == selected_id:
                row['selected'] = 'selected'
                IsSelected = True
            else:
                row['selected'] = ''

            reviews.append(row)

        if not IsSelected:
            row = reviews[0]
            selected_id = row['id']
            row['selected'] = 'selected'

    return reviews, selected_id

def _get_decrees(**kw):
    template = kw.get('template') or _views['decrees']
    config = g.page.database_config(template)
    columns = kw.get('columns') or config['export']
    where = kw.get('where') or ''
    order = kw.get('order') or ''
    encode_columns = not kw.get('no_encode') and ('Reviewer', 'Note') or None
    cursor = g.page.runQuery(template, columns=columns, where=where, order=order, as_dict=True, encode_columns=encode_columns)
    return cursor

def _get_order_params(order_id, **kw):
    return g.page.get_order_params(select_items(order_id, 'order-params', ('Login', 'Name', 'Value',), **kw))

def _get_order_reviewers(order_id, **kw):
    columns = ('Login',)
    where = 'OrderID=%d' % order_id
    as_dict = kw.get('as_dict') or False
    x = g.page.runQuery(_views['order-reviewers'], columns=columns, where=where, as_dict=as_dict, distinct=True) + \
        g.page.runQuery(_views['order-changes'], columns=columns, where=where, as_dict=as_dict, distinct=True)
    return x

def _get_subdivisions(**kw):
    view = _views['subdivisions']
    columns = g.page.database_config(view)['export']
    encode_columns = ('Name', 'Manager', 'FullName',)

    where = '%s' % (
        kw.get('code') and "Code like '%s%%'" % kw.get('code') or ''
    )

    return g.page.runQuery(view, columns=columns, where=where, order='TID', as_dict=True, encode_columns=encode_columns)

def _get_sectors(**kw):
    view = _views['sectors']
    columns = g.page.database_config(view)['export']
    encode_columns = ('Name', 'Manager', 'FullName',)

    where = '%s' % (
        kw.get('code') and "Code like '%s%%'" % kw.get('code') or ''
    )

    return g.page.runQuery(view, columns=columns, where=where, order='TID', as_dict=True, encode_columns=encode_columns)

def _get_activities(**kw):
    view = _views['activities']
    columns = g.page.database_config(view)['export']
    encode_columns = ('Name',)
    return g.page.runQuery(view, columns=columns, order='TID', as_dict=True, encode_columns=encode_columns)

def _get_categories(**kw):
    view = _views['categories']
    columns = g.page.database_config(view)['export']
    encode_columns = ('Name',)
    return g.page.runQuery(view, columns=columns, order='TID', as_dict=True, encode_columns=encode_columns)

def _calc_total_status(data, **kw):
    if not data or not data.get('data'):
        return data
    rows = data['data']
    x = sum([getMoney(row.get('Total')) * (row.get('rate') or 1.0) for row in rows])
    data['status'] = x > 0 and ' (Σ: %s %s)' % (getCurrency(x), kw.get('is_rub') and 'RUB' or '') or ''
    return data

def _get_order_items(order_id, **kw):
    return _calc_total_status(
        select_items(order_id, 'order-items', ('Name', 'Units', 'Account', 'Vendor',), handler=_handler_items, **kw)
        )

def _get_order_payments(order_id, **kw):
    return _calc_total_status(
        select_items(order_id, 'order-payments', ('Purpose', 'Comment',), order='PaymentDate', handler=_handler_payments, **kw), 
        is_rub=True,
        )

def _get_payments(order_id, **kw):
    return select_items(order_id, 'order-payments', ('Purpose', 'Comment',), **kw)

def _calc_payments(data, total, currency, statuses=(5,), exclude=None, is_cross=None, exchange_rate=None, is_fact=None):
    """
        Calculate payments.

        Arguments:
            data     - dict, список платежей в словаре `data`
            total    - float, всего по заявке (лимит) в валюте заявки
            currency - str, валюта заявки

        Keyword arguments:
            statuses      - list, включить платежи по списку статусов
            exclude       - list of int, исключить список ID платежей
            is_cross      - bool, рублевый перерасчет по кросс-курсу
            exchange_rate - float, курс покупки валюты
            is_fact       - bool, значение по факту в рублях

        Returns:
            x1 - float, всего оплачено в рублях
            s1 - float, остаток неисполнено в рублях
            x2 - float, всего платежей в рублях (по курсу платежа на дату)
            s2 - float, остаток всего в рублях
            x3 - float, всего оплачено в валюте
            s3 - float, остаток неисполнено в валюте
    """
    def _currency(row):
        return row['Currency'] or 'RUB'

    def _is_rub(row):
        return _currency(row) == 'RUB'

    def _total(row):
        return row['total'] or 0

    def _exchange_rate(row):
        return _is_rub(row) and row.get('exchange_rate') or None

    def _rate(row):
        return not _is_rub(row) and row.get('rate') or None

    def _calc_rub_with_exchange_rate(row):
        if is_fact and _is_rub(row):
            return _total(row)
        exchange_rate = _exchange_rate(row)
        args = (_total(row), currency) if exchange_rate else (_total(row), _currency(row))
        return calc_rub(*args, exchange_rate=exchange_rate)

    def _calc_rub_with_rate(row):
        rate = _rate(row)
        exchange_rate = _exchange_rate(row)
        args = (_total(row), currency) if exchange_rate else (_total(row), _currency(row))
        return calc_rub(*args, rate=rate, exchange_rate=exchange_rate)

    def _zero(v):
        return v > 0 and v or 0

    rows = data['data']

    x1 = data and sum([
        _calc_rub_with_exchange_rate(row) 
            for row in rows if row['StatusID'] in statuses and (
                not exclude or row['TID'] not in exclude
                )]
        ) or 0
    #print('x1:', x1)

    total_rub = calc_rub(total, currency, is_cross=is_cross)
    if not x1 and exchange_rate:
        total_rub = total * exchange_rate
    #print('total_rub:', total_rub)
    
    s1 = round(total_rub - float(x1), 2) or 0.0
    #print('s1:', s1)

    x3 = data and sum([
        row['total'] 
            for row in rows if row['StatusID'] in statuses and (
                not exclude or row['TID'] not in exclude) and 
                row['Currency'] == currency
            ]) or 0
    s3 = total - x3
    #print('s3:', s3)

    x2 = data and sum([
        _calc_rub_with_rate(row)
            for row in rows
            ]) or 0
    s2 = _zero(s3 > 0 and round(total_rub - float(x2), 2) or 0.0)
    #print('s2:', s2)

    return x1, s1, x2, s2, x3, s3

def _get_order_refers(order_id, **kw):
    return _calc_total_status(
        select_items(order_id, 'order-refers', ('Login', 'OrderReferID', 'ReferType', 'Article', 'Qty', 'Currency', 'Total', 'Note',), handler=_handler_refers, **kw)
        )

def _get_order_comments(order_id, **kw):
    return select_items(order_id, 'order-comments', ('Author', 'Note',), **kw)

def _get_order_documents(order_id, engine=None, **kw):
    return select_items(order_id, 'order-documents', ('FileName', 'Note',), handler=_handler_documents, engine=engine or g.storage, model=g.page.model, **kw)

def _get_subdivision(id, key=None):
    if not id:
        return None

    view = _views['subdivisions']
    columns = g.page.database_config(view)['export']
    where = 'TID=%s' % id
    encode_columns = ('Name', 'Manager', 'FullName')
    cursor = g.page.runQuery(view, columns=columns, top=1, where=where, as_dict=True, encode_columns=encode_columns)
    return cursor and (key and cursor[0][key] or cursor[0]) or None

def _get_sector(id, key=None):
    if not id:
        return None

    view = _views['sectors']
    columns = g.page.database_config(view)['export']
    where = 'TID=%s' % id
    encode_columns = ('Name', 'Manager', 'FullName')
    cursor = g.page.runQuery(view, columns=columns, top=1, where=where, as_dict=True, encode_columns=encode_columns)
    return cursor and (key and cursor[0][key] or cursor[0]) or None

def _get_activity(id, key=None, **kw):
    cursor = None
    if kw and 'Activity' in kw:
        cursor = {
            'Name' : kw.get('Activity'),
            }
        return key and cursor[key] or cursor or None

    if not id:
        return None

    view = _views['activities']
    columns = g.page.database_config(view)['export']
    where = 'TID=%s' % id
    encode_columns = ('Name',)
    cursor = g.page.runQuery(view, columns=columns, top=1, where=where, as_dict=True, encode_columns=encode_columns)
    return cursor and (key and cursor[0][key] or cursor[0]) or None

def _get_category(id, key=None, **kw):
    cursor = None
    if kw and 'Category' in kw:
        cursor = {
            'Name' : kw.get('Category'),
            }
        return key and cursor[key] or cursor or None

    if not id:
        return None

    view = _views['categories']
    columns = g.page.database_config(view)['export']
    where = 'TID=%s' % id
    encode_columns = ('Name',)
    cursor = g.page.runQuery(view, columns=columns, top=1, where=where, as_dict=True, encode_columns=encode_columns)
    return cursor and (key and cursor[0][key] or cursor[0]) or None

def _get_condition(id, key=None, **kw):
    cursor = None
    if kw and 'Condition' in kw:
        cursor = {
            'Name'    : kw.get('Condition'),
            }
        return key and cursor[key] or cursor or None

    if not id:
        return None

    view = _views['conditions']
    columns = g.page.database_config(view)['export']
    where = 'TID=%s' % id
    encode_columns = ('Name',)
    cursor = g.page.runQuery(view, columns=columns, top=1, where=where, as_dict=True, encode_columns=encode_columns)
    return cursor and (key and cursor[0][key] or cursor[0]) or None

def _get_seller(id, key=None, **kw):
    row = None
    if kw and 'Seller' in kw:
        row = {
            'Name'    : kw.get('Seller'),
            'Title'   : kw.get('SellerTitle'), 
            'Address' : kw.get('SellerAddress'),
            'Code'    : kw.get('SellerCode'),
            'Type'    : kw.get('SellerType'),
            'Contact' : kw.get('SellerContact'),
            'URL'     : kw.get('SellerURL'),
            'Phone'   : kw.get('SellerPhone'),
            'Email'   : kw.get('SellerEmail'),
            }
    else:
        if not id:
            return None

        view = _views['sellers']
        columns = g.page.database_config(view)['export']
        where = 'TID=%s' % id
        encode_columns = ('Name', 'Title', 'Address', 'Contact', 'URL', 'Phone', 'Email')
        cursor = g.page.runQuery(view, columns=columns, top=1, where=where, as_dict=True, encode_columns=encode_columns)
        row = cursor and len(cursor) > 0 and cursor[0] or None

    if row:
        row['Name'] = getHtmlString(row['Name'])
        row['Code'] = row['Code'] and row['Code'].strip() or ''
        row['Contact'] = row['Contact'] and row['Contact'].strip() or ''
        row['rendered_link'] = getHtmlCaption(row['URL'])
        row['rendered_name'] = Seller.render_name(row['Name'], row['Type'])
    
    return row and (key and row[key] or row) or None

def _get_seller_link(row, **kw):
    return Seller.render_link(kw.get('locator') or default_locator, row['SellerID'], Seller.render_name(row['Seller'], row.get('SellerType')), blank=kw.get('blank'))

def _get_order_link(row, **kw):
    locator = kw.get('locator') or g.page.get_model_locator(row.get('MD'))
    blank = kw.get('blank') or 'blank'
    oid = row.get('TID')
    name = kw.get('name') or oid
    return '<a target="_%s" href="/%s?_id=%s&sidebar=0">%s</a>' % (blank, locator, oid, name)

def _get_stock(id, key=None, **kw):
    row = None
    if kw and 'Stock' in kw:
        row = {}
    else:
        if not id:
            return None

        stock = Stock(g.engine, row['TID'])
        stock._init_state()

        row = stock.attrs
    
    return row and (key and row[key] or row) or None

def _get_equipment(id, key=None, **kw):
    cursor = None
    if kw and 'Equipment' in kw:
        cursor = {
            'Name'    : kw.get('EquipmentName'),
            'Title'   : kw.get('Equipment'), 
            }
        return key and cursor[key] or cursor or None

    if not id:
        return None

    view = _views['equipments']
    columns = g.page.database_config(view)['export']
    where = 'TID=%s' % id
    encode_columns = ('Name', 'Title',)
    cursor = g.page.runQuery(view, columns=columns, top=1, where=where, as_dict=True, encode_columns=encode_columns)
    return cursor and (key and cursor[0][key] or cursor[0]) or None

def _get_order_dates(**kw):
    order_id = kw.get('order_id') or g.requested_object.get('TID')

    default_format = kw.get('format') or '%d.%m.%Y'

    def _date(value):
        return value and getDate(value, default_format) or ''

    dates = g.page.get_dates()

    if kw and 'Created' in kw:
        for key in dates.keys():
            dates[key][2] = _date(kw.get(key))

    else:
        view = _views['dates']
        where = order_id and 'OrderID=%s' % order_id or ''

        cursor = g.page.runQuery(view, top=1, where=where, as_dict=True)
        if cursor:
            for n, row in enumerate(cursor):
                for key in dates.keys():
                    dates[key][2] = _date(row.get(key))

    g.page.check_dates(dates)

    return [(x[0].lower(), x[1][1], x[1][2]) for x in sorted(dates.items(), key=itemgetter(1))]

#   --------------------
#   Common Page Handlers
#   --------------------

def _check_extra_tabs(row):
    return {}

def _valid_extra_action(action, row=None):
    tabs = _check_extra_tabs(row or g.requested_object)
    return (action not in _extra_action or action in list(tabs.values())) and action

def _serialize(value):
    return value is not None and str(value) or ''

def _get_total_selected(params):
    x = params.get('total_selected', '').split('|')
    if len(x) != 2:
        return
    g.total_selected = [int(x[0].strip() or 0), float((x[1].strip() or 0.0).replace(' ', ''))]

def _set_total_selected(inc, total):
    if inc == 0:
        g.total_selected = [0, 0.0]
    else:
        g.total_selected = [g.total_selected[0]+inc, g.total_selected[1]+(inc*total) or 0.0]

def _output_total_selected(value=None):
    x = value or g.total_selected
    #print(x[1])
    return x and len(x) == 2 and x[1] and '%s | %s' % (x[0], sMoney(x[1])) or '0 | 0.00'

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

def _calculate_tab_count(order_id, **kw):
    info = {}

    key = kw.get('key')
    reviews = kw.get('reviews')
    total = kw.get('total')
    currency = kw.get('currency')
    status = kw.get('status')
    is_cross = kw.get('is_cross', g.system_config.IsCross)

    def _size(value):
        return value and isIterable(value) and len(value) or 0

    if order_id:
        tabs = {}

        if not key or key == 'reviews':
            tabs['reviews'] = None
        if not key or key == 'params':
            tabs['params'] = _get_order_params(order_id, order='Name')
        if not key or key == 'items':
            tabs['items'] = _get_order_items(order_id, order='Name') or None
        if not key or key in ('reviews', 'payments'):
            tabs['payments'] = _get_order_payments(order_id) or None
        if not key or key == 'refers':
            tabs['refers'] = _get_order_refers(order_id)
        if not key or key == 'documents':
            tabs['documents'] = _get_order_documents(order_id)
        if not key or key == 'comments':
            tabs['comments'] = _get_order_comments(order_id)

        keys = list(tabs.keys())
        menu = dict(zip(keys, [tabs.get(x) and _size(tabs[x].get('data')) or 0 for x in keys]))

        menu['keys'] = keys

        if not key or key == 'reviews':
            menu['reviews'] = _size(reviews)

        info['tabs'] = tabs
        info['menu'] = menu

        if total and 'payments' in info['tabs']:
            data = info['tabs'].get('payments')
            t = isinstance(total, str) and getMoney(total) or total

            is_fact = 0

            x1, s1, x2, s2, x3, s3 = _calc_payments(data, t, currency, is_cross=is_cross, is_fact=is_fact)

            info['payment_total'] = str(s2)

            if (kw.get('status') or 0) > 1:
                info['paid_total'] = getCurrency(x1)
            if not is_fact:
                info['paid_total_title'] = 'Всего оплачено в рублях по текущему курсу'

            info['payment_total_value'] = s2
            info['paid_total_value'] = x1
            info['unpaid_total_value'] = s3 > 0 and s1 > 0 and s1 or 0.0

            if s1 > 0 and s3 > 0 and 'status' in data and data['status']:
                x = calc_from_rub(s1, currency, is_cross=False)
                data['status'] += ' = <span class="unpaid">%s: %s %s</span>' % (gettext('Unpaid'), getCurrency(x), currency)

        info['status'] = g.page.get_status()

    return info

def _get_payment_total(order_id, total, currency, is_cross=False):
    """
        Не оплачено (остаток)
    """
    return _calculate_tab_count(order_id, key='payments', total=total, currency=currency, is_cross=is_cross).get('unpaid_total_value') or 0.0

def _get_paid_total(order_id, total, currency):
    """
        Оплачено (затраты)
    """
    return _calculate_tab_count(order_id, key='payments', total=total, currency=currency).get('paid_total_value') or 0.0

def _get_created_after(value):
    return value and getDate(value, format=LOCAL_EASY_DATESTAMP, is_date=True) or g.system_config.DEFAULT_CREATED_AFTER

## ==================================================== ##

def getTabParams(order_id, review_id, param_name=None, format=None, **kw):
    """
        Параметры заявок -- список полей представления
    """
    order = order_id == g.requested_object.get('TID') and g.requested_object or None
    columns = g.page.is_no_price and g.page.database_config(default_template)['noprice'] or g.page.database_config(default_template)['columns']

    data, props, css = {}, {}, {}

    if order:
        for column in columns:
            value = order.get(column)

            if value is None:
                value = ''
            elif column in ('TID',):
                value = '%05d' % value
            elif column in ('Price',):
                value = str(value)
            elif column in ('Total', 'Tax',):
                value = getCurrency(value)
            elif column == 'Seller':
                value = _get_seller_link(order, locator=g.page.locator)
            elif column in ('RD',):
                value = _get_date(value)

            data[column] = value

        author = _get_user(order.get('Author'))
        data['AuthorName'] = author and author.short_name() or ''

        css['Article'] = [('urgently', g.page.is_urgently(order) and 'add' or 'remove')]

        if order.get('Currency'):
            currencies = [(x, 'remove') for x in g.page.default_currencies]
            currencies.append((order['Currency'].upper(), 'add'))
            css['Currency'] = currencies

        g.page.after(data)

        props = {
            'id'                 : review_id, 
            'disabled_edit'      : g.page.is_disabled_edit(), 
            'disabled_review'    : g.page.is_disabled_review(), 
            'disabled_accept'    : g.page.is_disabled_accept(), 
            'disabled_paid'      : g.page.is_disabled_paid(), 
            'disabled_validated' : g.page.is_disabled_validated(), 
            'disabled_delivered' : g.page.is_disabled_delivered(), 
            'disabled_statuses'  : g.page.disabled_statuses(), 
            'css'                : css,
        }

        if 'item_id' in kw:
            getTabBarcode(None, order_id, kw['item_id'], props=props, order=order)

    return data, columns, props

def getTabChanges(order_id, **kw):
    """
        История изменения заказа
    """
    view = 'order-changes'
    props = {'OrderID' : order_id}
    order = 'TID desc'

    data = select_items(order_id, view, ('Login', 'Name', 'Value',), handler=_handler_changes, order=order, no_selected=True)
    
    return data, props

def getTabStockList(order_id, review_id, params):
    """
        Товарный классификатор
    """
    data, columns, props = getTabParams(order_id, review_id)

    command, mode, query, items, id, state = _load_params(params)

    errors = g.instance.register_stocklist(order_id, state)

    return data, columns, props

def getTabGroupStockList(order_id, review_id, params):
    """
        Обновить Класс товара для группы заказов
    """
    data, columns, props = {}, {}, []

    login = g.current_user.login

    command = params.get('command')
    view = default_template

    kw = {'args' : params.get('query')}

    where, order, args, permissions = _make_page_default(kw, back_where=True)
    encode_columns = _default_encode_columns

    cursor = g.page.runQuery(view, where=where, order=order, encode_columns=encode_columns, as_dict=True) or []

    if IsTrace:
        print_to(errorlog, '--> provision:groupstocklist_%s %s, where:%s, cursor:%s' % (
            command, login, where, cursor and len(cursor) or 0
            ))

    for order in cursor:
        x = getTabStockList(order['TID'], review_id, params)

        if order['TID'] == order_id:
            data, columns, props = x

    return data, columns, props

def getTabCheckedReviewers(order_id, params):
    """
        Рецензенты по заявке
    """
    data, props, errors = {}, [], []

    login = g.current_user.login

    command = params.get('command')

    if command == 'GET_REVIEWERS':
        data = g.instance.get_order_reviewers(order_id)
    else:
        errors = g.instance.set_order_reviewers(order_id, params.get('data'))

    return data, props, errors

def getTabBarcode(command, order_id, item_id, order=None, props=None):
    if not props:
        props = {}

    props['barcode'] = g.page.barcode_action(command or 'generate', order_id, item_id, order=order)

    return props

## ==================================================== ##

def registerReview(order_id, status, note, params):
    errors = []
    if g.instance is None or not order_id:
        return errors, None

    if not status:
        return errors, None
    elif status == g.page.provision_review_statuses.get('accept'):
        errors = g.instance.accept(order_id, note)
    elif status == g.page.provision_review_statuses.get('reject'):
        errors = g.instance.reject(order_id, note)
    elif status == g.page.provision_review_statuses.get('confirm'):
        errors = g.instance.confirm(order_id, note, params=params)
    elif status == g.page.provision_review_statuses.get('confirmation'):
        errors = g.instance.confirmation(order_id, note)
    elif status == g.page.provision_review_statuses.get('paid'):
        errors = g.instance.paid(order_id, note, params=params)
    elif status == g.page.provision_review_statuses.get('failure'):
        errors = g.instance.failure(order_id, note, params=params)
    elif status == g.page.provision_review_statuses.get('validated'):
        errors = g.instance.validated(order_id, note, params=params)
    elif status == g.page.provision_review_statuses.get('delivered'):
        errors = g.instance.delivered(order_id, note, params=params)
    elif status == g.page.provision_review_statuses.get('decree'):
        errors = g.instance.decree(order_id, note, params=params)

    if IsDeepDebug:
        print('...errors:', errors)

    return errors, g.instance.action()

def refreshOrderItem(order_id, params):
    command = params and params.get('command')

    data, props, errors = {}, {}, []

    if command == 'seller':
        id = int(params.get('id') or '0')
        data = _get_seller(id)

    return data, props, errors

def createOrder():
    """
        Create a new Provision order
    """
    errors = None

    try:
        errors = g.instance.create_order(request.form)
    except:
        if IsPrintExceptions:
            print_exception()

    return errors

def updateOrder(order_id):
    """
        Update Provision order
    """
    errors = None

    try:
        errors = g.instance.update_order(order_id, request.form)
    except:
        if IsPrintExceptions:
            print_exception()

    return errors

def deleteOrder(order_id):
    """
        Delete Provision order
    """
    errors = None

    try:
        errors = g.instance.delete_order(order_id)
    except:
        if IsPrintExceptions:
            print_exception()

    return errors

def cloneOrder(order_id):
    """
        Clone Provision order
    """
    errors = None

    try:
        errors = g.instance.clone_order(order_id, request.form)
    except:
        if IsPrintExceptions:
            print_exception()

    return errors

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
        items['EditedBy'] = g.current_user.login

        if command == 'add':
            errors = ob.setNewNode(items)
            if not errors:
                id, errors = ob.addItem(items)

        elif command == 'update' and id is not None:
            errors = ob.updateItem(id, items)

        elif command == 'remove' and id is not None:
            errors = ob.removeItem(id)

        if query and isIterable(query):
            query.append((ob.direction, 'onplace'))
        else:
            items[ob.direction] = 'onplace'

    if command == 'link' and ob.has_links:
        data = ob.getLinks(query, attrs, id)

    else:
        data = ob.getItems(query, id, items=items, state=state)

        query = None

    props = {'id' : ob.id, 'value' : ob.value, 'mode' : mode, 'query' : query, 'table' : ob.table, 'title' : ob.title, 'errors' : errors}

    return data, props, ob.config, ob.editable_columns

def runDecreeActions(command, params=None):
    if IsTrace:
        print_to(None, '>>> decree actions:%s %s, params:%s' % (command, g.current_user.login, params))

    kw = {}

    page = params.get('page')
    is_submit = params.get('is_submit')

    ob = _get_decree_instance()

    base = '/decrees/%s' % page

    if is_submit:
        kw.update({
            'page'         : page,
            'vsc'          : vsc(force=g.system_config.IsForceRefresh),
            'width'        : 1280,
            'action'       : '',
            'loader'       : '/loader',
            'show_flash'   : True,
            'with_login'   : params.get('with_login') and 1 or 0,
            'app_role_ceo' : g.page.app_role_ceo and 1 or 0,
    })

    try:
        if command == 'sort':
            kw.update(ob.sort(params))
        elif command == 'print':
            kw.update(ob.print_orders(params))
        else:
            kw.update(ob.render(params))

    except Exception as ex:
        print_to(None, ['', 'decree:page %s Exception: %s' % (page, str(ex))])

        if IsPrintExceptions:
            print_exception()

    return kw

def runSellerActions(command, params=None):
    if IsTrace:
        print_to(None, '>>> seller actions:%s %s, params:%s' % (command, g.current_user.login, params))

    kw = {}

    uid = params.get('uid')
    is_submit = params.get('is_submit')
    stock = params.get('stock')

    reference = reference_factory.get('stocklist')
    stocklist = reference(g.engine)

    ob = _get_seller_instance(uid, stocklist=stocklist, stock=stock)

    if command == 'update':
        errors = ob.update()

        if is_submit:
            for error in errors:
                flash(error)
        else:
            kw['errors'] = errors and '<br>'.join(errors) or ''

        if not errors:
            kw['OK'] = gettext('Message: Seller was refreshed successfully.')

    base = '/%s/seller/%s' % (default_locator, uid)

    if is_submit:
        kw.update({
            'uid'        : uid,
            'vsc'        : vsc(force=g.system_config.IsForceRefresh),
            'width'      : 1280,
            'action'     : '',
            'loader'     : '/%s/loader' % default_locator,
            'show_flash' : True,
    })

    try:
        if command == 'sort':
            kw.update(ob.sort())
        elif command == 'print':
            kw.update(ob.print_orders(params))
        else:
            kw.update(ob.render())

    except Exception as ex:
        print_to(None, ['', 'seller:uid %s Exception: %s' % (uid, str(ex))])

        if IsPrintExceptions:
            print_exception()

    return kw

def runStockActions(command, params=None):
    if IsTrace:
        print_to(None, '>>> stock actions:%s %s, params:%s' % (command, g.current_user.login, params))

    kw = {}

    uid = params.get('uid')
    is_submit = params.get('is_submit')
    seller = params.get('seller')

    ob = Stock(g.engine, int(uid))
    ob._init_state(
        attrs={
            'locator' : default_locator,
            'page'    : g.page,
            'seller'  : seller,
        }, 
        factory={
            'get_orders'         : _get_orders, 
            'get_order'          : _get_order, 
            'get_order_link'     : _get_order_link, 
            'get_date'           : _get_date,
            'get_seller'         : _get_seller,
            'html_note'          : _html_note, 
            'info'               : _make_current_order_info, 
            'calc_rub'           : calc_rub, 
        }
    )

    if command == 'update':
        errors = ob.update()

        if is_submit:
            for error in errors:
                flash(error)
        else:
            kw['errors'] = errors and '<br>'.join(errors) or ''

        if not errors:
            kw['OK'] = gettext('Message: Stock was refreshed successfully.')

    base = '/%s/stock/%s' % (default_locator, uid)

    if is_submit:
        kw.update({
            'uid'        : uid,
            'vsc'        : vsc(force=g.system_config.IsForceRefresh),
            'width'      : 1280,
            'action'     : '',
            'loader'     : '/%s/loader' % default_locator,
            'show_flash' : True,
            'seller'     : seller,
    })

    try:
        if command == 'sort':
            kw.update(ob.sort())
        elif command == 'print':
            kw.update(ob.print_orders(params))
        else:
            kw.update(ob.render())

    except Exception as ex:
        print_to(None, ['', 'stock:uid %s Exception: %s' % (uid, str(ex))])

        if IsPrintExceptions:
            print_exception()

    return kw

def runPaymentActions(command, params=None):
    if IsTrace:
        print_to(None, '>>> payment actions:%s %s, params:%s' % (command, g.current_user.login, params))

    kw = {}

    date = params.get('date') or 'current'
    is_submit = params.get('is_submit')

    ob = _get_payments_review_instance(date)

    if command in ('accept', 'reject',):
        errors, data = ob.update(command, params=params)

        if is_submit:
            for error in errors:
                flash(error)
        else:
            kw['errors'] = errors and '<br>'.join(errors) or ''

        total = len(data)

        if not errors:
            kw['OK'] = '%s <div class="done">%s%s: %s</div>' % (
                gettext('Message: Action was done successfully.'),
                total and '%s<br>' % gettext('Message: Payments was successfully %s.' % (
                    command == 'accept' and 'accepted' or 
                    command == 'reject' and 'rejected' or 
                    'refreshed')) or '', 
                gettext('Total'),
                total
                )

        if not is_submit:
            kw['total'] = total
            kw['props'] = {'OK' : kw.get('OK') or ''}

    base = '/%s/payments/%s' % (default_locator, date)

    if is_submit:
        kw.update({
            'date'       : date,
            'forward'    : ob.forward,
            'back'       : ob.back,
            'vsc'        : vsc(force=g.system_config.IsForceRefresh),
            'width'      : 1280,
            'action'     : '',
            'loader'     : '/%s/loader' % default_locator,
            'show_flash' : True,
        })

    try:
        if command == 'changes':
            kw['data'] = ob.log(params)
        elif command == 'print':
            kw.update(ob.print_payments(params))
        elif command == 'sort':
            kw.update(ob.sort())
        elif is_submit:
            kw.update(ob.render())
        else:
            kw['data'] = ob.refresh()

    except Exception as ex:
        print_to(None, ['', 'payments:date %s Exception: %s' % (date, str(ex))])

        if IsPrintExceptions:
            print_exception()

    return kw

def runBarcodeActions(command, params=None):
    if IsTrace:
        print_to(None, '>>> barcode actions:%s %s, params:%s' % (command, g.current_user.login, params))

    kw = {}

    barcode = params.get('barcode')
    is_submit = params.get('is_submit')

    ob = BarcodeReader(g.engine)
    ob._init_state(
        attrs={
            'locator'   : default_locator,
            'page'      : g.page,
        }, 
        factory={
            'get_order'          : _get_order,
            'get_orders'         : _get_orders,
            'get_order_dates'    : _get_order_dates,
            'get_seller_link'    : _get_seller_link,
            'get_order_link'     : _get_order_link,
            'get_date'           : _get_date,
            'get_exchange_rate'  : _get_exchange_rate,
            'html_note'          : _html_note,
            'info'               : _make_current_order_info,
            'calc_rub'           : calc_rub,
        }
    )
    
    base = '/%s/barcode' % default_locator

    if is_submit:
        kw.update({
            'barcode'    : barcode,
            'vsc'        : vsc(force=g.system_config.IsForceRefresh),
            'width'      : 1280,
            'action'     : '',
            'loader'     : '/%s/loader' % default_locator,
            'show_flash' : True,
    })

    if command == 'render':
        ob.parse(barcode)

    kw['rendered_title'] = 'Склад.Сканер ШК'

    try:
        if command == 'print':
            kw.update(ob.print_orders(params))
        elif not is_submit:
            return ob.render()
        else:
            kw['data'] = ob.refresh()

    except Exception as ex:
        print_to(None, ['', 'barcode:[%s] Exception: %s' % (barcode, str(ex))])

        if IsPrintExceptions:
            print_exception()

    return kw

def runReviewerProfile(login, **kw):
    profile = _get_profile_instance(login, **kw)

    data = profile.render_reviewer()

    return data

def runSchedule(params):
    templates = g.page.get_schedule_template(without_separator=True)

    #_print_schedule_template()

    attrs = _make_page_default(None, back_where=True, uncheck_status=True)

    data, columns, props = {}, {}, {}

    documents = g.page.getTabDocumentsSchedule(params, attrs, templates['documents'])

    data['documents'] = documents[0]
    columns['documents'] = documents[1]

    decrees = g.page.getTabDecreesSchedule(params, attrs, templates['decrees'])

    data['decrees'] = decrees[0]
    columns['decrees'] = decrees[1]
    
    # XXX It's not ready yet! Check main menu settings and provision.default.$SidebarDialog [active]
    props['active'] = {
        'documents' : g.page.system_config_documents_schedule,
        'decrees'   : g.page.system_config_decrees_schedule,
    }

    return data, columns, props

## ==================================================== ##

def _make_export(kw):
    """
        Экспорт журнала заказов в Excel
    """
    view = g.page.database_config(default_template)
    columns = [x for x in view['columns'] if x in view['headers']]
    headers = [view['headers'][x][0] for x in columns]

    rows = []

    where, order, args, permissions = _make_page_default(kw, back_where=True, uncheck_status=True)

    encode_columns = _default_encode_columns

    cursor = g.page.runQuery(default_template, columns=columns, where=where, order=order, encode_columns=encode_columns, as_dict=True) or []

    for data in cursor:
        row = []
        for column in columns:
            if column not in data:
                continue
            try:
                v = data[column]
                if column == 'RD':
                    #v = re.sub(r'\s+', ' ', re.sub(r'<.*?>', ' ', str(v))).strip()
                    #v = getDate(v, UTC_FULL_TIMESTAMP, is_date=True)
                    v = getDate(v, UTC_EASY_TIMESTAMP)
                elif column == 'Status':
                    v = g.page.get_status(v)[1]
                elif column in ('Price', 'Tax', 'Total'):
                    v = getExcelMoney(v)
                elif column == 'Seller':
                    pass
                elif isinstance(v, str):
                    v = re.sub(r'\r?\n', ' ', v.strip())
                row.append(v)
            except:
                if IsPrintExceptions:
                    print_exception()

        rows.append(row)

    rows.insert(0, headers)
    return rows

def _make_response_name(name=None):
    return '%s-%s' % (getDate(getToday(), LOCAL_EXPORT_TIMESTAMP), name or 'perso')

def _make_xls_content(rows, title, name=None, encoding=None):
    output = makeCSVContent(rows, title, True, encoding=encoding)
    ext = 'csv'
    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=%s.%s" % (_make_response_name(name), ext)
    return response

def _make_refreshed_order(params, **kw):
    """
        Make Order data for update
    """
    columns = []
    props = {}
    data = {}

    command = params.get('command')

    config = g.page.database_config(_views['orders'])

    is_extra = kw.get('is_extra') and True or False

    is_update = command == 'updateorder'
    is_clone = command == 'cloneorder'

    ob = (is_update or is_clone) and g.requested_object or {}
    status = ob.get('Status')

    for x, key in (('order_id', 'TID'), ('author', 'Author'),):
        columns.append(x)
        props[x] = {'type' : 0, 'disabled' : False}
        data[x] = ob.get(key) or 0

    for key in config['updated']:
        column = key.lower()
        value = ob.get(key)

        props[column] = {'type' : 0}

        if key in ('Price', 'Total', 'Tax'):
            value = _serialize(not is_clone and value or None)
        elif key in ('Currency',):
            if value is None or is_clone:
                value = DEFAULT_UNDEFINED
        elif key.endswith('ID'):
            column = column[:-2].lower()
            props[column] = {'type' : 1}
            if value is None:
                value = 0

        data[column] = value
        columns.append(column)

    if is_clone:
        data['CategoryID'] = 0

    if props.get('equipment') and props['equipment']['type'] == 1:
        equipment = _get_equipment(ob.get('EquipmentID'))
        data['equipment'] = equipment and equipment.get('Title') or ''

    if props.get('seller') and props['seller']['type'] == 1:
        seller = _get_seller(ob.get('SellerID'))
        data['seller'] = ob.get('SellerID')

        seller_items = Seller.refreshed_items(seller)
        data.update(seller_items)

        for x in seller_items.keys():
            if x not in columns:
                columns.append(x)
            props[x] = {'type' : 0}

    for x in ('duedate',):
        columns.append(x)
        props[x] = {'type' : 0}
        data[x] = ''

    # ---------------------------
    # Check `disable` form's mode
    # ---------------------------

    users = [ob.get('Author'), ob.get('EditedBy')]

    disable = tuple(map(lambda x: x.lower(), config['disable']))

    is_disabled = not is_extra and g.current_user.login not in users
    is_frozen = not is_extra and not is_clone and g.page.is_disabled_edit(ob, force=True) and is_update

    def _disable(key, force=None):
        if key in g.system_config.ENABLED_ORDER_ITEMS:
            return False
        if g.page.is_page_manager and (key.startswith('seller') or key in ('category', 'sector', 'url')):
            return False
        return is_frozen or is_update and (key in disable or force) and is_disabled or False

    for key in columns:
        props[key]['disabled'] = _disable(key)

    is_author = g.page.is_order_author(ob)

    if not (g.page.is_page_manager or is_author) or (is_author and is_frozen):
        for key in disable:
            if key in props:
                props[key]['disabled'] = True

    # ----------------
    # Add DueDate item
    # ----------------
    
    order_id = data['order_id']

    if order_id:
        key = 'duedate'
        x = _get_order_params(order_id, code='DE')
        if x and x['data'] and len(x['data']) > 0:
            data[key] = x['data'][0].get('Value') or ''
            props[key]['disabled'] = _disable(key, force=True)
        columns.append(key)

    return data, columns, props

def _make_refreshed_decree(params, **kw):
    """
        Make Decree data for update
    """
    columns = []
    props = {}
    data = {}

    command = params.get('command')
    order_id = kw.get('order_id')
    review_id = int(params.get('review_id', 0)) or None
    decree_id = int(params.get('decree_id', 0)) or None
    report_id = int(params.get('report_id', 0)) or None

    decree = _get_decree_instance(order_id=order_id, review_id=review_id, decree_id=decree_id, report_id=report_id)

    decree.refresh()

    data, columns, props = decree.get_item(command, **kw)

    return data, columns, props

def _make_current_order_info(no_extra=None, no_seller=None, **kw):
    order_id = kw.get('order_id') or g.requested_object.get('TID')
    review_id = kw.get('review_id') or 0

    order = kw.get('order') or g.requested_object
    if 'id' in order:
        del order['id']

    def _get(key):
        return order.get(key) if order and key in order else g.requested_object.get(key)

    author = _get_user(_get('Author'))
    edited_by = _get_user(_get('EditedBy'))
    order_name = _get('Article')
    seller_id = _get('SellerID')
    seller = _get_seller(seller_id, **order)
    equipment_id = _get('EquipmentID')
    equipment = _get_equipment(equipment_id, **order)
    purpose = _get('Purpose')
    total = _get('Total')
    tax = _get('Tax')
    currency = _get('Currency')
    status = _get('Status')
    category_id = _get('CategoryID')
    category = _get_category(category_id, 'Name', **order)
    stocklist_id = _get('StockListID')
    stocklist_nodecode = _get('StockListNodeCode')
    sector = _get('Sector')

    num = '%05d' % int(order_id or 0)

    info = {
        'num'         : num,
        'order'       : order_id and '[%s]: %s' % (num, order_name),
        'author'      : author and author.full_name() or '',
        'edited_by'   : edited_by and 'Исп. %s%s' % (edited_by.full_name(), author and ' = Заказчик: %s' % author.full_name() or '') or '',
        'category'    : category_id and category_id < 5 and {
            'title' : category, 
            'class' : 'cc%s' % category_id,
            'code'  : category[0].upper(),
        },
        'purpose'     : getHtmlCaption(purpose, truncate=10),
        'status'      : g.page.check_order_status(order),
        'EUR'         : None,
        'url'         : getHtmlCaption(_get('URL'), truncate=20),
        'order_id'    : order_id,
        'documents'   : 0,
    }

    if not g.page.is_no_price:
        info.update({
            'EUR'       : getCurrency(calc_euro(total, currency), points=1) or '0.00',
            'RUB'       : getCurrency(calc_rub(total, currency), points=1) or '0.00',
            'cross'     : str(_get_exchange_rate(currency in ('RUB', None) and 'RUB:EUR' or 'RUB:%s' % currency)),
            'tax'       : getCurrency(calc_rub(tax, currency), points=1) or '0.00',
            'rate'      : str(_get_exchange_rate(currency in ('RUB', None) and 'EUR:RUB' or '%s:RUB' % currency)),
        })

    info['subdivision'] = _get('Subdivision')

    if equipment:
        title = equipment.get('Title')
        name = equipment.get('Name')

        info.update({
            'equipment_title' : title,
            'equipment_name'  : name and name != title and name,
        })

    info['sector'] = sector or ''

    if seller_id and not no_seller:
        info['seller_name'] = seller.get('rendered_name')
        s = Seller.render_link(g.page.locator or default_locator, seller_id, info['seller_name'], blank=kw.get('blank'))
        if _is_valid_seller(seller):
            if _is_show_seller_info(g.current_user.login):
                s = '%s <div class="seller_info">| %s</div>' % (s, _get_seller_instance(seller_id).getOrdersInfo())
        info['seller_link'] = s
        info.update(Seller.refreshed_items(seller, with_html=True))

    if not no_extra:
        info.update(_calculate_tab_count(order_id, reviews=kw.get('reviews'), total=total, currency=currency, status=status))

    info['dates'] = _get_order_dates(**order)

    if stocklist_id and stocklist_nodecode:
        stock = kw.get('stock')

        if stock is None:
            reference = reference_factory.get('stocklist')
            stock = reference(g.engine)

        name, parent_code = stock.getNodeClassName(stocklist_id, code=stocklist_nodecode)

        info['stocklist'] = {
            'id'          : stocklist_id, 
            'code'        : stocklist_nodecode,
            'name'        : name, 
            'parent_code' : parent_code,
            'level'       : stock.get_node_level(parent_code),
            'title'       : 'Класс товара',
        }

    if no_extra:
        info['condition'] = _get('Condition') or ''

    info['params'] = {
        'purpose'         : 'Обоснование',
        'equipment_title' : 'Описание',
        'equipment_name'  : 'Оборудование',
        'seller_name'     : 'Контрагент',
        'seller_title'    : 'Реквизиты',
        'seller_url'      : 'Ссылка на товар (URL)',
        'with_cross'      : 1,
    }

    info = g.page.make_current_order_info(order_id, info, order=order)

    g.page.point('order_info')

    return order_id, info, review_id

def _make_page_default(kw, back_where=None, uncheck_status=None):
    """
        Page Rendering
    """
    kw = g.page.render(kw or {}, back_where, uncheck_status)

    if back_where:
        return kw

    kw.update({
        'semaphore'         : initDefaultSemaphore(template='provision.semaphore'),
        'navigation'        : get_navigation(),
        'schedule_template' : g.page.get_schedule_template(),
        'schedule_params'   : g.page.schedule_params(),
    })

    return kw

def _make_page_menu(page_menu, kw, default_state=None):
    """
        Make page menu
    """
    state = get_request_item('state') or default_state or 'expand'

    page_menu.extend([ 
        (id, name, params, 
            id == state and 'warning' or 'primary') for name, id, params in (
                ('Свернуть', 'collapse', '&state=collapse'), 
                ('Развернуть', 'expand', '&state=expand'), 
        )
    ])

    content_state = state == 'collapse' and 1 or 0
    states = content_state and ('invisible', '') or ('', 'invisible')

    kw.update({
        'page_menu'     : page_menu,
        'content_state' : content_state,
        'states'        : states,
    })

## ==================================================== ##

def init_provision():
    g.page = PageProvision(
        'provision', 
        'WebPerso Provision Page', 
        'WebPerso Provision Orders View',
        'Provision order',
    )

def init_personal():
    g.page = PagePersonal(
        'personal', 
        'WebPerso Personal Page', 
        'WebPerso Personal Documents View',
        'Personal document',
    )

def init_diamond():
    g.page = PageDiamond(
        'diamond', 
        'WebPerso Diamond Page', 
        'WebPerso Diamond Products View',
        'Diamond product',
    )

def init_sale():
    g.page = PageSale(
        'sale', 
        'WebPerso Sale Page', 
        'WebPerso Sale Documents View',
        'Sale document',
    )

def init_purchase():
    g.page = PagePurchase(
        'purchase', 
        'WebPerso Purchase Page', 
        'WebPerso Purchase Documents View',
        'Purchase document',
    )

def init_workflow():
    g.page = PageWorkflow(
        'workflow', 
        'WebPerso Workflow Page', 
        'WebPerso Workflow Documents View',
        'Workflow document',
    )

def init_default(model=None):
    if model is None:
        g.page = PageDefault('default', '', '', '',)
    elif model == 30 or model in ('default', 'workflow'):
        init_workflow()
    elif model == 20 or model == 'sale':
        init_sale()
    elif model == 40 or model == 'purchase':
        init_purchase()
    elif model == 10 or model == 'diamond':
        init_diamond()
    elif model == 1 or model == 'personal':
        init_personal()
    else:
        init_provision()

#@provision.route('/', methods = ['GET'])
@provision.route('/service', methods = ['GET','POST'])
@login_required
def service(**kw):
    init_provision()

    refresh()

    args = get_request_items()

    if IsTrace:
        print_to(errorlog, '--> service.%s %s [%s:%s] args:%s engine:%s' % (
                 g.page.id, 
                 g.current_user.login, 
                 request.remote_addr, 
                 request.method, 
                 repr(args), 
                 repr(g.engine)
                 ), 
                 request=request)

    return jsonify({'message':'It works'})

@provision.route('/', methods = ['GET'])
@provision.route('/provision', methods=['GET', 'POST'])
@login_required
def start_provision():
    init_provision()
    return start()

@provision.route('/personal', methods=['GET', 'POST'])
@login_required
def start_personal():
    init_personal()
    return start()

@provision.route('/diamond', methods=['GET', 'POST'])
@login_required
def start_diamond():
    init_diamond()
    return start()

@provision.route('/sale', methods=['GET', 'POST'])
@login_required
def start_sale():
    init_sale()
    return start()

@provision.route('/purchase', methods=['GET', 'POST'])
@login_required
def start_purchase():
    init_purchase()
    return start()

@provision.route('/workflow', methods=['GET', 'POST'])
@login_required
def start_workflow():
    init_workflow()
    return start()

def start():
    try:
        return index()
    except:
        if IsPrintExceptions:
            print_exception()

        flash('Please, update the page by Ctrl-F5!')

def index():
    debug, kw = init_response(g.page.name)
    kw['product_version'] = product_version

    is_admin = g.current_user.is_administrator()
    is_operator = g.current_user.is_operator()

    command = get_request_item('command')

    order_id = int(get_request_item('order_id') or '0')
    review_id = int(get_request_item('review_id') or '0')

    if IsDebug:
        print('--> command:%s, order_id:%s, review_id:%s' % (
            command, 
            order_id, 
            review_id,
        ))

    reset = int(get_request_item('reset') or '0')
    if reset:
        kw['order_id'] = None
        kw['review_id'] = None

    refresh(order_id=order_id)

    done = ''

    IsMakePageDefault = True

    errors = []

    if command.startswith('admin'):
        command = command.split(DEFAULT_HTML_SPLITTER)[1]

        if get_request_item('OK') != 'run':
            command = ''

        elif command == 'deleteorder':
            errors = deleteOrder(order_id)

            if not errors:
                del kw['order_id']

            done = 'removed'

        elif not is_admin:
            flash('You have not permission to run this action!')
            command = ''

        elif command == 'upload':
            gen = ApplicationGenerator(CONNECTION['provision'])
            gen.upload()

        elif command == 'download':
            srv = ApplicationService(CONNECTION['provision'], kw)
            IsMakePageDefault = False

        elif command == 'delete-orders':
            srv = ApplicationService(CONNECTION['provision'], kw)
            errors = srv.run(command)

        elif command == 'clear-history':
            srv = ApplicationService(CONNECTION['provision'], kw)
            errors = srv.run(command)

    elif command == 'export':
        IsMakePageDefault = False

    kw['errors'] = errors and '<br>'.join(errors) or ''
    kw['OK'] = ''

    if IsMakePageDefault:
        _make_page_default(kw)

    if IsTrace:
        print_to(errorlog, '--> %s:%s %s [%s:%s] %s%s engine:%s' % (
                 g.page.id, 
                 command, 
                 g.current_user.login, 
                 request.remote_addr, 
                 kw.get('browser_info'), 
                 order_id, 
                 reset and ' reset:%s' % reset or '', 
                 repr(g.engine)
                 ), 
                 request=request)

    kw['vsc'] = vsc(force=g.system_config.IsForceRefresh)
    kw['avatar_width'] = g.system_config.IsUseReviewerAvatar and '80'

    if command:
        is_extra = has_request_item(EXTRA_)
        page_caption = gettext('%s registry' % g.page.caption)

        if not command.strip():
            pass

        elif done:
            if kw['errors']:
                flash('Provision Generator done with errors!')
            else:
                kw['OK'] = _ok_message(done)

        elif command == 'download':
            return _make_xls_content(srv.download(), page_caption, g.page.id)

        elif command == 'export':
            return _make_xls_content(_make_export(kw), page_caption, g.page.id, encoding=default_encoding)

    g.page.point('index')

    return make_response(render_template('%s.html' % g.page.id, debug=debug, **kw))

@provision.route('/changelog', methods = ['GET'])
def changelog():
    output = ''
    try:
        with open(os.path.join(basedir, 'changelog.txt'), 'rb') as fp:
            output = fp.readlines()
    except:
        if IsPrintExceptions:
            print_exception()

    response = make_response('\r\n'.join([x.decode(default_unicode).rstrip() for x in output]))
    response.headers["Content-Disposition"] = "attachment; filename=changelog.%s.txt" % product_version[0].replace(',', '')
    return response

@provision.after_request
def make_response_no_cached(response):
    try:
        g.instance, g.requested_object = None, None
        if g.engine is not None:
            if IsTrace:
                print_to(None, '>>> total queries count: %s' % g.engine.count)
            g.engine.close()
    except:
        pass
    # response.cache_control.no_store = True
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response

@provision.route('/workflow/blank/<order_id>', methods = ['GET'])
@login_required
def blank_workflow(order_id):
    debug, kw = init_response('WebPerso Workflow Blank Page')
    kw['product_version'] = product_version
    kw['module'] = 'workflow'

    init_workflow()

    is_admin = g.current_user.is_administrator()
    order_id = order_id and order_id.isdigit() and int(order_id) or 0

    command = get_request_item('command') or 'refresh'

    if IsDebug:
        print('--> command:%s, order_id:%s' % (
            command, 
            order_id, 
        ))

    if IsTrace:
        print_to(None, '>>> workflow blank:%s %s, command:%s' % (order_id, g.current_user.login, command))

    refresh(order_id=order_id)

    params = {
        'order_id'      : order_id, 
        'is_submit'     : 1, 
        'command'       : command, 
    }

    kw.update(g.page.make_blank(params=params))

    template = 'blank/%s.html' % kw.get('template') or 'a4'

    return make_response(render_template(template, debug=debug, **kw))

@before
def downloader(uid, action, order_id=None, model=None):
    if IsTrace:
        print_to(None, '>>> downloader:%s uid:%s order_id:%s' % (action, uid, order_id))

    loader, image, errors = None, None, None

    init_default(model)

    if model is not None:
        refresh()

    try:
        # Decode and download
        loader = OrderImageLoader()

        loader._init_state()
        if action == 'zip':
            documents = _get_order_documents(order_id)
            image = loader.zip(documents['data'], order_id)
        else:
            image = loader.download(uid, with_commit=False)

        errors = loader.errors

        status = (errors or loader.is_error) and 'fail' or 'success'

    except:
        if IsPrintExceptions:
            print_exception()

        if errors is None:
            errors = []

        errors.append(gettext('Error: Download failed'))

        status = 'exception'

    if image is None:
        image = 'No data'

    if IsTrace:
        print_to(None, '--> done:%s %s, uid:%s, size:%s [%s] %s' % (
            action, 
            g.current_user.login, 
            uid, 
            len(image), 
            status, 
            errors or ''
            ), encoding=default_encoding)

    loader.dispose()

    response = make_response(image)

    filename = uid

    if not loader.content_type:
        response.headers.set('Content-Type', 'text/html')
    elif loader.content_type in ('jpeg', 'jpg',):
        response.headers.set('Content-Type', 'image/jpeg')
    elif loader.content_type in ('png', 'gif',):
        response.headers.set('Content-Type', 'image/%s' % loader.content_type)
    elif loader.content_type == 'pdf':
        response.headers.set('Content-Type', 'application/pdf')
    elif loader.content_type.startswith('doc'):
        response.headers.set('Content-Type', 'application/msword')
    elif loader.content_type.startswith('xls'):
        response.headers.set('Content-Type', 'application/vnd.ms-excel')
    elif loader.content_type in ('zip', 'rar',):
        filename = 'documents_%s.zip' % order_id
        response.headers.set('Content-Type', loader.content_type)
        response.headers["Content-Disposition"] = "attachment; filename=%s" % filename
    else:
        filename = '%s.dump' % uid
        response.headers["Content-Disposition"] = "attachment; filename=%s" % filename

    #response.headers["x-filename"] = filename
    #response.headers["Access-Control-Expose-Headers"] = 'x-filename'

    del loader

    return response

@provision.route('/storage/image/<uid>', methods = ['GET'])
@login_required
def image(uid):
    return downloader(uid, 'image')

@provision.route('/provision/download_all/<order_id>', methods = ['GET'])
@login_required
def download_provision_all(order_id):
    return downloader(None, 'zip', order_id=order_id, model=0)

@provision.route('/workflow/download_all/<order_id>', methods = ['GET'])
@login_required
def download_workflow_all(order_id):
    return downloader(None, 'zip', order_id=order_id, model=30)

@provision.route('/storage/uploader', methods = ['POST'])
@login_required
def uploader():
    action = get_request_item('action') or 'upload'

    response = {}

    order_id = int(get_request_item('order_id') or '0')
    note = get_request_item('note') or ''
    for_audit = get_request_item('for_audit') == '1' and 1 or 0
    model = int(get_request_item('model') or '0')

    file = original = size = None

    errors = None

    try:
        # Uploaded document file
        file = request.files.get('file')

        if file is None or not hasattr(file, 'stream'):
            return None

        original, size = file.filename, file.content_length

    except:
        if IsPrintExceptions:
            print_exception()

    if IsTrace:
        print_to(None, '>>> uploader:%s %s [%s:%s] for_audit:%s, model:%s' % (
            action, 
            g.current_user.login, 
            order_id, 
            original,
            for_audit,
            model,
            ), encoding=default_encoding)

    init_default(model=model)

    refresh(order_id=order_id)

    try:
        # Decode and upload
        loader = OrderImageLoader()

        loader._init_state(original=original)
        loader.upload(order_id, file.stream, note, for_audit, model)

        errors = loader.errors

        status = (errors or loader.is_error) and 'fail' or 'success'

    except:
        if IsPrintExceptions:
            print_exception()

        if errors is None:
            errors = []

        errors.append(gettext('Error: Upload failed, uid:%s' % loader.uid))

        status = 'exception'

    if IsTrace:
        print_to(None, '--> done: [%s] uid:%s, size:%s, content_type:%s, lastrowid:%s [%s]' % (
            loader.source, 
            loader.uid,
            loader.size, 
            loader.content_type, 
            loader.lastrowid,
            status,
            ), encoding=default_encoding)

    loader.dispose()

    del loader

    response.update({
        'action'    : action,
        'status'    : status,
        'errors'    : errors,
    })

    return jsonify(response)

@provision.route('/provision/seller/<uid>', methods = ['GET', 'POST'])
@login_required
def seller_provision(uid):
    debug, kw = init_response('WebPerso Provision Seller Page')
    kw['product_version'] = product_version
    kw['module'] = 'seller'

    init_provision()

    is_admin = g.current_user.is_administrator()

    command = get_request_item('command') or 'refresh'

    if IsDebug:
        print('--> command:%s, uid:%s' % (
            command, 
            uid, 
        ))

    if IsTrace:
        print_to(None, '>>> seller:%s %s, command:%s' % (uid, g.current_user.login, command))

    refresh()

    _make_page_menu([], kw)

    params = {
        'uid'           : uid, 
        'is_submit'     : 1, 
        'command'       : command, 
        'stock'         : get_request_item('stock'), 
        'content_state' : kw['content_state']
    }

    kw.update(runSellerActions(command, params=params))

    return make_response(render_template('ext/seller.html', debug=debug, **kw))

@provision.route('/personal/seller/<uid>', methods = ['GET', 'POST'])
@login_required
def seller_personal(uid):
    debug, kw = init_response('WebPerso Personal Seller Page')
    kw['product_version'] = product_version
    kw['module'] = 'seller'

    init_personal()

    is_admin = g.current_user.is_administrator()

    command = get_request_item('command') or 'refresh'

    if IsDebug:
        print('--> command:%s, uid:%s' % (
            command, 
            uid, 
        ))

    if IsTrace:
        print_to(None, '>>> seller:%s %s, command:%s' % (uid, g.current_user.login, command))

    refresh()

    _make_page_menu([], kw)

    params = {
        'uid'           : uid, 
        'is_submit'     : 1, 
        'command'       : command, 
        'stock'         : get_request_item('stock'), 
        'content_state' : kw['content_state']
    }

    kw.update(runSellerActions(command, params=params))

    return make_response(render_template('ext/seller.html', debug=debug, **kw))

@provision.route('/diamond/seller/<uid>', methods = ['GET', 'POST'])
@login_required
def seller_diamond(uid):
    debug, kw = init_response('WebPerso Diamond Seller Page')
    kw['product_version'] = product_version
    kw['module'] = 'seller'

    init_diamond()

    is_admin = g.current_user.is_administrator()

    command = get_request_item('command') or 'refresh'

    if IsDebug:
        print('--> command:%s, uid:%s' % (
            command, 
            uid, 
        ))

    if IsTrace:
        print_to(None, '>>> seller:%s %s, command:%s' % (uid, g.current_user.login, command))

    refresh()

    _make_page_menu([], kw)

    params = {
        'uid'           : uid, 
        'is_submit'     : 1, 
        'command'       : command, 
        'stock'         : get_request_item('stock'), 
        'content_state' : kw['content_state']
    }

    kw.update(runSellerActions(command, params=params))

    return make_response(render_template('ext/seller.html', debug=debug, **kw))

@provision.route('/sale/seller/<uid>', methods = ['GET', 'POST'])
@login_required
def seller_sale(uid):
    debug, kw = init_response('WebPerso Sale Seller Page')
    kw['product_version'] = product_version
    kw['module'] = 'seller'

    init_sale()

    is_admin = g.current_user.is_administrator()

    command = get_request_item('command') or 'refresh'

    if IsDebug:
        print('--> command:%s, uid:%s' % (
            command, 
            uid, 
        ))

    if IsTrace:
        print_to(None, '>>> seller:%s %s, command:%s' % (uid, g.current_user.login, command))

    refresh()

    _make_page_menu([], kw)

    params = {
        'uid'           : uid, 
        'is_submit'     : 1, 
        'command'       : command, 
        'stock'         : get_request_item('stock'), 
        'content_state' : kw['content_state']
    }

    kw.update(runSellerActions(command, params=params))

    return make_response(render_template('ext/seller.html', debug=debug, **kw))

@provision.route('/purchase/seller/<uid>', methods = ['GET', 'POST'])
@login_required
def seller_purchase(uid):
    debug, kw = init_response('WebPerso Purchase Seller Page')
    kw['product_version'] = product_version
    kw['module'] = 'seller'

    init_purchase()

    is_admin = g.current_user.is_administrator()

    command = get_request_item('command') or 'refresh'

    if IsDebug:
        print('--> command:%s, uid:%s' % (
            command, 
            uid, 
        ))

    if IsTrace:
        print_to(None, '>>> seller:%s %s, command:%s' % (uid, g.current_user.login, command))

    refresh()

    _make_page_menu([], kw)

    params = {
        'uid'           : uid, 
        'is_submit'     : 1, 
        'command'       : command, 
        'stock'         : get_request_item('stock'), 
        'content_state' : kw['content_state']
    }

    kw.update(runSellerActions(command, params=params))

    return make_response(render_template('ext/seller.html', debug=debug, **kw))

@provision.route('/provision/stock/<uid>', methods = ['GET', 'POST'])
@login_required
def stock(uid):
    debug, kw = init_response('WebPerso Provision Stock Page')
    kw['product_version'] = product_version
    kw['module'] = 'stock'

    is_admin = g.current_user.is_administrator()

    command = get_request_item('command') or 'refresh'

    if IsDebug:
        print('--> command:%s, uid:%s' % (
            command, 
            uid, 
        ))

    if IsTrace:
        print_to(None, '>>> stock:%s %s, command:%s' % (uid, g.current_user.login, command))

    init_provision()

    refresh()

    _make_page_menu([], kw)

    params = {
        'uid'           : uid, 
        'is_submit'     : 1, 
        'command'       : command, 
        'seller'        : get_request_item('seller'), 
        'content_state' : kw['content_state']
    }

    kw.update(runStockActions(command, params=params))

    return make_response(render_template('ext/stock.html', debug=debug, **kw))

@provision.route('/provision/barcode', methods = ['GET', 'POST'])
@login_required
def barcode():
    debug, kw = init_response('WebPerso Provision Barcode Reader Page')
    kw['product_version'] = product_version
    kw['module'] = 'barcode'

    uid = None

    is_admin = g.current_user.is_administrator()

    command = get_request_item('command') or 'refresh'

    if IsDebug:
        print('--> command:%s, uid:%s' % (
            command, 
            uid, 
        ))

    if IsTrace:
        print_to(None, '>>> stock:%s %s, command:%s' % (uid, g.current_user.login, command))

    init_provision()

    refresh()

    _make_page_menu([], kw)

    params = {
        'uid'           : uid, 
        'is_submit'     : 1, 
        'command'       : command, 
        'content_state' : kw['content_state']
    }

    kw.update(runBarcodeActions(command, params=params))

    return make_response(render_template('ext/barcode.html', debug=debug, **kw))

@provision.route('/provision/calendar/<uid>', methods = ['GET', 'POST'])
@login_required
def calendar(uid):
    debug, kw = init_response('WebPerso Provision Calendar Page')
    kw['product_version'] = product_version
    kw['module'] = 'auth'

    action = 'calendar'

    is_admin = g.current_user.is_administrator()

    command = get_request_item('command') or 'refresh'

    if IsDebug:
        print('--> command:%s, uid:%s, debug:%s' % (
            command, 
            uid, 
            debug,
        ))

    period = get_request_item('period')
    interval = get_request_item('interval')
    created_after = get_request_item('created_after')

    state = get_request_item('state') or 'expand'

    if IsTrace:
        print_to(None, '>>> calendar:%s %s, command:%s, created_after:%s, period:%s, interval:%s, debug:%s' % (
            uid, g.current_user.login, command, created_after, period, interval, debug))

    if g.current_user.app_menu not in ('headoffice', 'default',):
        return redirect('abort') # render_template('404.html', **kw)

    init_provision()

    refresh()

    ob = AuditPlanCosts(g.engine, int(uid), period=period, interval=interval)
    ob._init_state(
        attrs={
            'created_after'     : _get_created_after(created_after),
            'locator'           : default_locator,
            'page'              : g.page,
            'debug'             : debug,
            'target'            : '_self',
        }, 
        factory={
            'calc_rub'          : calc_rub,
            'calc_euro'         : calc_euro,
            'get_orders'        : _get_orders,
            'get_order'         : _get_order,
            'get_params'        : _get_order_params,
            'get_payments'      : _get_order_payments,
            'get_payment_total' : _get_payment_total,
        }
    )

    base = '/%s/calendar/%s' % (default_locator, uid)

    page_menu = [ 
        (id, name, '%s?interval=%s%s' % (base, id, params), 
            (interval == id or id == 'week' and not interval) and 'warning' or 'primary' ) for name, id, params in (
                ('По дням', 'day', '&period=365'), 
                ('По неделям', 'week', '&period=53'), 
                ('По месяцам', 'month', '&period=12'),
        )
    ]

    page_menu.extend([ 
        (id, name, params, 
            id == state and 'warning' or 'primary') for name, id, params in (
                ('Свернуть', 'collapse', '&state=collapse'), 
                ('Развернуть', 'expand', '&state=expand'), 
        )
    ])

    content_state = state == 'collapse' and 1 or 0
    states = content_state and ('invisible', '') or ('', 'invisible')

    kw.update({
        'title'         : gettext('WebPerso Provision Calendar Page'),
        'module'        : 'finance',
        'uid'           : uid,
        'vsc'           : vsc(force=g.system_config.IsForceRefresh),
        'width'         : 1280,
        'action'        : action,
        'show_flash'    : True,
        'page_menu'     : page_menu,
        'content_state' : content_state,
        'states'        : states,
    })

    if debug != None:
        return ob.render_html()

    try:
        kw.update(ob.render(title=kw['title'], state=state, base=base))

    except Exception as ex:
        print_to(None, ['', '%s:uid %s Exception: %s' % (action, uid, str(ex))])

        if IsPrintExceptions:
            print_exception()

    return make_response(render_template('ext/audit.html', debug=debug, **kw))

@provision.route('/provision/statist/<uid>', methods = ['GET', 'POST'])
@login_required
def statist(uid):
    debug, kw = init_response('WebPerso Provision Statist Page')
    kw['product_version'] = product_version
    kw['module'] = 'auth'

    action = 'statist'

    is_admin = g.current_user.is_administrator()

    command = get_request_item('command') or 'refresh'

    if IsDebug:
        print('--> command:%s, uid:%s, debug:%s' % (
            command, 
            uid, 
            debug,
        ))

    created_after = get_request_item('created_after')

    state = get_request_item('state') or 'expand'

    if IsTrace:
        print_to(None, '>>> statist:%s %s, command:%s, created_after:%s, debug:%s' % (
            uid, g.current_user.login, command, created_after, debug))

    if g.current_user.app_menu not in ('headoffice', 'default',):
        return redirect('abort') # render_template('404.html', **kw)

    init_provision()

    refresh()

    ob = AuditFactCosts(g.engine, int(uid))
    ob._init_state(
        attrs={
            'created_after'     : _get_created_after(created_after),
            'locator'           : default_locator,
            'page'              : g.page,
            'debug'             : debug,
            'target'            : '_self',
        }, 
        factory={
            'calc_rub'          : calc_rub,
            'calc_euro'         : calc_euro,
            'get_orders'        : _get_orders,
            'get_order'         : _get_order,
            'get_paid_total'    : _get_paid_total,
        }
    )

    base = '/%s/statist/%s?sidebar=0&state=%s' % (default_locator, '%s', state)

    _make_page_menu([], kw)

    kw.update({
        'title'         : gettext('WebPerso Provision Statist Page'),
        'module'        : 'finance',
        'uid'           : uid,
        'vsc'           : vsc(force=g.system_config.IsForceRefresh),
        'width'         : 1280,
        'action'        : action,
        'show_flash'    : True,
    })

    if debug != None:
        return ob.render_html()

    try:
        kw.update(ob.render(title=kw['title'], state=state, base=base))

    except Exception as ex:
        print_to(None, ['', '%s:uid %s Exception: %s' % (action, uid, str(ex))])

        if IsPrintExceptions:
            print_exception()

    return make_response(render_template('ext/audit.html', debug=debug, **kw))

@provision.route('/provision/finance', methods=['GET', 'POST'])
@login_required
def finance():
    debug, kw = init_response('WebPerso Provision Finance Page')
    kw['product_version'] = product_version
    kw['module'] = 'auth'

    navigation = [
        {
            'link'  : '%s/provision/statist/0?state=collapse' % request.script_root, # ?debug=0
            'title' : gettext('Cost statistics'), 
            'class' : ''
        },
        {
            'link'  : '%s/provision/calendar/0?state=collapse' % request.script_root, # ?debug=0
            'title' : gettext('Finance calendar'), 
            'class' : ''
        },
        {
            'link'  : '%s/provision' % request.script_root,
            'title' : gettext('WebPerso Provision Page'), 
            'class' : ''
        },
    ]

    if IsTrace:
        print_to(None, '>>> finance:open %s' % g.current_user.login)

    init_provision()

    refresh()

    kw.update({
        'navigation' : get_navigation(),
        'width'      : 1280,
        'message'    : gettext('Finance menu').upper(),
        'vsc'        : vsc(force=g.system_config.IsForceRefresh),
        'navigation' : navigation,
    })

    return make_response(render_template('ext/finance.html', debug=debug, **kw))

@provision.route('/provision/payments/<date>', methods = ['GET', 'POST'])
@login_required
def payments(date):
    debug, kw = init_response('WebPerso Provision Payments Page')
    kw['product_version'] = product_version
    kw['module'] = 'payments'

    is_admin = g.current_user.is_administrator()

    command = get_request_item('command') or 'refresh'

    if IsDebug:
        print('--> command:%s, date:%s' % (
            command, 
            date, 
        ))

    if IsTrace:
        print_to(None, '>>> payments:%s %s, command:%s' % (date, g.current_user.login, command))

    init_provision()

    refresh()

    _make_page_menu([], kw)

    params = {
        'date'          : date, 
        'is_submit'     : 1, 
        'command'       : command, 
        'content_state' : kw['content_state']
    }

    kw.update(runPaymentActions(command, params=params))

    return make_response(render_template('ext/payments-review.html', debug=debug, **kw))

@provision.route('/decrees/<page>', methods = ['GET', 'POST'])
@login_required
def decrees(page):
    debug, kw = init_response('WebPerso Decrees Page')
    kw['product_version'] = product_version
    kw['module'] = 'decrees'

    is_admin = g.current_user.is_administrator()

    command = get_request_item('command') or 'refresh'

    ids = [x for x in (get_request_item('_ids') or '').split(':') if x]
    date_from = get_request_item('date_from') or ''
    login = get_request_item('login') or ''
    executor = get_request_item('executor') or ''
    status = get_request_item('status') or ''
    with_login = get_request_item('with_login', check_int=True) and 1 or 0

    if IsDebug:
        print('--> command:%s, page:%s' % (
            command, 
            page, 
        ))

    if IsTrace:
        print_to(None, '>>> decrees:%s %s, command:%s' % (page, g.current_user.login, command))

    init_default(page)

    refresh()

    _make_page_menu([], kw, default_state='collapse')

    if g.page.app_role_ceo or ids:
        with_login = 0
    if not with_login and not (g.page.app_role_ceo or g.page.is_office_ceo):
        with_login = 1

    params = {
        'page'          : page, 
        'is_submit'     : 1, 
        'command'       : command, 
        'content_state' : kw['content_state'], 
        'ids'           : ids, 
        'date_from'     : date_from,
        'login'         : login,
        'executor'      : executor,
        'status'        : status,
        'with_login'    : with_login,
    }

    kw.update(runDecreeActions(command, params=params))

    return make_response(render_template('ext/decrees.html', debug=debug, **kw))

@provision.route('/provision/loader', methods = ['GET', 'POST'])
def loader_provision():
    init_provision()
    return loader()

@provision.route('/personal/loader', methods = ['GET', 'POST'])
def loader_personal():
    init_personal()
    return loader()

@provision.route('/diamond/loader', methods = ['GET', 'POST'])
def loader_diamond():
    init_diamond()
    return loader()

@provision.route('/sale/loader', methods = ['GET', 'POST'])
def loader_sale():
    init_sale()
    return loader()

@provision.route('/purchase/loader', methods = ['GET', 'POST'])
def loader_purchase():
    init_purchase()
    return loader()

@provision.route('/workflow/loader', methods = ['GET', 'POST'])
def loader_workflow():
    init_workflow()
    return loader()

@login_required
def loader():
    exchange_error = ''
    exchange_message = ''

    is_extra = has_request_item(EXTRA_)

    action = get_request_item('action') or default_action
    selected_menu_action = get_request_item('selected_menu_action') or action != default_action and action or default_log_action

    response = {}

    order_id = int(get_request_item('order_id') or '0')
    review_id = int(get_request_item('review_id') or '0')
    note = get_request_item('note') or ''

    item_id = int(get_request_item('item_id') or '0')

    refresh(order_id=order_id)

    attrs = sortedDict({})

    params = get_request_item('params') or ''

    if IsDebug:
        print('--> action:%s order_id:%s review_id:%s' % (action, order_id, review_id))

    if IsTrace:
        print_to(None, '--> %s.loader:%s %s [%s:%s] %s%s%s engine:%s' % (
            g.page.id,
            action, 
            g.current_user.login, 
            order_id, 
            review_id, 
            selected_menu_action,
            params and (' params:%s' % reprSortedDict(params, is_sort=True)) or '',
            note and ' note:[%s]' % note or '',
            repr(g.engine)
            ), 
            encoding=default_encoding)

    currentfile = None
    reviews = []
    config = None

    data = ''
    number = ''
    columns = []
    total = 0
    status = ''

    review = None
    props = None
    errors = None

    tabs = _check_extra_tabs(g.requested_object)

    g.page.set_params(params)

    try:
        if action in (default_action, default_log_action, default_print_action): # and not review_id
            """
                Default Action (LINE|SUBLINE)
            """
            reviews, review_id = _get_reviews(order_id)
            currentfile = _make_current_order_info(review_id=review_id, reviews=reviews)
            config = _get_view_columns(g.page.database_config(_views['reviews']))
            action = _valid_extra_action(selected_menu_action) or default_log_action

        review_actions = (None, None, '832', '833', '834', '835', '846', '854', None, '857', None, '858', '859',)

        if action in review_actions:
            """
                Review actions
            """
            errors, review_id = registerReview(order_id, review_actions.index(action), note, params)
            reviews = _get_reviews(order_id, selected_id=review_id)[0]
            refreshOrder(order_id=order_id)
            currentfile = _make_current_order_info(order_id=order_id, review_id=review_id, reviews=reviews)
            config = _get_view_columns(g.page.database_config(_views['reviews']))
            action = default_log_action

        if not action:
            pass

        elif action == default_log_action:
            data, columns, props = getTabParams(order_id, review_id, item_id=item_id)

        elif action == '836':
            """
                Actions with Order Params
            """
            data, status, errors = g.instance.params_action(order_id, params)
            currentfile = [order_id, _calculate_tab_count(order_id, key='params'), review_id]

        elif action == '837':
            """
                Actions with Order Items
            """
            data, status, errors = g.instance.items_action(order_id, params)
            currentfile = [order_id, _calculate_tab_count(order_id, key='items'), review_id]

            item_id = data.get('selected_id')

            props = getTabBarcode(None, order_id, item_id, order=g.requested_object)

        elif action == '838':
            """
                Actions with Order Payments
            """
            data, status, errors = g.instance.payments_action(order_id, params)
            currentfile = [order_id, _calculate_tab_count(
                order_id, 
                key='payments', 
                total=g.requested_object.get('Total'), 
                currency=g.requested_object.get('Currency'),
                status=g.requested_object.get('Status'),
                ), 
                review_id]

        elif action == '839':
            """
                Actions with Order Comments
            """
            data, status, errors = g.instance.comments_action(order_id, params)
            currentfile = [order_id, _calculate_tab_count(order_id, key='comments'), review_id]

        elif action == '840':
            """
                Update status of order in LINE area (review status)
            """
            view = g.page.database_config(default_template)
            columns = view['columns']
            props = [columns.index(x) for x in g.page.status_columns]
            status = g.requested_object.get('Status')
            data = g.page.check_order_status()
            reviews = _get_reviews(order_id)[0]
            currentfile = [order_id, _calculate_tab_count(
                order_id, 
                key='reviews', 
                total=g.requested_object.get('Total'), 
                reviews=reviews, 
                status=status
                ), 
                review_id]

        elif action == '841':
            """
                Refresh content for Edit action
            """
            command = params.get('command').lower()
            if 'param' in command:
                data = _get_order_params(order_id, **params)
            elif 'item' in command:
                data = _get_order_items(order_id, **params)
            elif 'payment' in command:
                data = _get_order_payments(order_id, **params)
            elif 'refer' in command:
                data = _get_order_refers(order_id, **params)
            elif 'document' in command:
                data = _get_order_documents(order_id, **params)
            elif 'comment' in command:
                data = _get_order_comments(order_id, **params)

        elif action == '842':
            """
                Change status of Order
            """
            data, errors = g.instance.set_status(order_id, params, is_extra=is_extra)

        elif action == '843':
            """
                Refresh content for Create/Update/Clone an Order or Decree
            """
            command = params.get('command').lower()

            if not command:
                pass
            elif 'order' in command:
                data, columns, props = _make_refreshed_order(params, is_extra=is_extra)
            elif 'decree' in command:
                data, columns, props = _make_refreshed_decree(params, is_extra=is_extra, order_id=order_id)

        elif action == '844':
            """
                Send request for approval
            """
            errors = g.instance.send_approval_mail(params)

        elif action == '845':
            """
                Validate and Create/Update/Clone an Order or Decree if not errors
            """
            command = params.get('command').lower()
            submit = params.get('submit')

            if submit:
                message = 'order'
                done = ''

                if not command:
                    pass
                elif command == 'createorder':
                    errors = g.instance.create_order(params)
                    done = 'created'
                elif command == 'updateorder':
                    errors = g.instance.update_order(order_id, params)
                    done = 'updated'
                elif command == 'cloneorder':
                    errors = g.instance.clone_order(order_id, params)
                    done = 'created'

                if errors:
                    done = ''

                data = {
                    'action_id' : g.instance.action_id,
                    'message'   : _ok_message(done),
                }
            else:
                errors = g.instance.set_order(params, is_check=True)

        elif action == '847':
            """
                Actions with Order Documents
            """
            data, status, errors = g.instance.documents_action(order_id, params)
            info = [order_id, _calculate_tab_count(order_id, key='documents'), review_id]

            currentfile = g.page.documents_action(order_id, info)

        elif action == '848':
            """
                Set unread
            """
            if params:
                force = params.get('force') and 1 or 0
                if params.get('mode') == 'all':
                    order_id = None
            else:
                force = 0
            _get_total_selected(params)
            errors = g.instance.set_unread(order_id, [g.current_user], force=force)
            data = {'total_selected' : _output_total_selected()}

        elif action == '849':
            """
                Set read
            """
            if params:
                force = params.get('force') and 1 or 0
                if params.get('mode') == 'all':
                    order_id = None
            else:
                force = 0
            _get_total_selected(params)
            errors = g.instance.set_read(order_id, [g.current_user], force=force)
            data = {'total_selected' : _output_total_selected()}

        elif action == '851':
            """
                Send review notifications
            """
            errors = g.instance.send_review_notifications()

        elif action == '852':
            """
                Send the Order's review notifications
            """
            errors = g.instance.send_order_notifications(order_id, params=params)

        elif action == '853':
            """
                Order Changes History data
            """
            data, props = getTabChanges(order_id, params=params)

        elif action == '855':
            """
                Refresh Order items in the edit form
            """
            data, props, errors = refreshOrderItem(order_id, params)

        elif action == '856':
            """
                Actions with Order Refers
            """
            for x in params.get('value').split(','):
                params['value'] = x
                data, status, errors = g.instance.refers_action(order_id, params)
                if errors:
                    break
            info = g.page.make_current_order_info(order_id, _calculate_tab_count(order_id, key='refers'), order=g.requested_object)

            currentfile = [order_id, info, review_id]

        elif action == '860':
            """
                Reviewer actions
            """
            data = runReviewerProfile(params.get('login'))

        elif action == '861':
            """
                Reference service maintainance
            """
            data, props, config, columns = runReference(attrs, params)

        elif action == '862':
            """
                Update StockList link in the Order and return main view Tab
            """
            data, columns, props = getTabStockList(order_id, review_id, params)

            refreshOrder(order_id=order_id)

            currentfile = _make_current_order_info(review_id=review_id)
            config = _get_view_columns(g.page.database_config(_views['reviews']))

        elif action == '863':
            """
                Update Schedule list
            """
            data, columns, props = runSchedule(params)

        elif action == '864':
            """
                Delete an Order (instead of Index:Delete)
            """
            command = params.get('command').lower()
            submit = params.get('submit')

            if submit:
                done = ''

                if command == 'deleteorder':
                    errors = deleteOrder(order_id)
                    done = 'removed'

                if errors:
                    done = ''

                data = {
                    'action_id' : order_id,
                    'message'   : _ok_message(done),
                }

        elif action == '865':
            """
                Update StockList link in the group of Order and return main view Tab
            """
            data, columns, props = getTabGroupStockList(order_id, review_id, params)

            refreshOrder(order_id=order_id)

            currentfile = _make_current_order_info(review_id=review_id)
            config = _get_view_columns(g.page.database_config(_views['reviews']))

        elif action == '866':
            """
                Activate Checked Reviewers dialog
            """
            data, props, errors = getTabCheckedReviewers(order_id, params)

        elif action == '867':
            """
                Update param combo values
            """
            param_id = int(params.get('param_id') or 0)
            data = g.page.get_param_combo_values(param_id)
            order_params = _get_order_params(order_id, params=['ParamID=%s' % param_id])
            current_value = order_params['data'] and order_params['data'][0].get('Value') or None
            props = [current_value]

        elif action == '868':
            """
                Handle provision barcode
            """
            command = params.get('command').lower()
            item_id = int(params.get('item_id') or 0)

            props = getTabBarcode(command, order_id, item_id, order=g.requested_object)

        elif action == '869':
            """
                Render provision barcode
            """
            command = params.get('command').lower()
            data = runBarcodeActions(command, params=params)

        elif action in ('871', '872', '873', '874'):
            """
                Actions with Seller/Stock/Payments Review
            """
            module = None
            command = ''

            try:
                x = params.get('command').split('_')
                module = x[0]
                command = x[-1].lower()
            except:
                pass

            if not module:
                kw = {}
            elif module == 'SELLER':
                kw = runSellerActions(command, params=params)
            elif module == 'STOCK':
                kw = runStockActions(command, params=params)
            else:
                kw = runPaymentActions(command, params=params)

            data = kw.get('data')
            total = kw.get('total')
            errors = kw.get('errors')
            props = kw.get('props')

        elif action == '875':
            """
                Actions with Decrees
            """
            errors, review_id = registerReview(order_id, g.page.provision_review_statuses.get('decree'), note, params)
            data, columns, props = _make_refreshed_decree(params, is_extra=is_extra, order_id=order_id)

    except:
        if IsPrintExceptions:
            print_exception()

    if not total:
        total = data and isIterable(data) and len(data) or 0

    if IsTrace and IsDeepDebug:
        print_to(None, '--> loader:%s %s data total:%s' % (action, g.current_user.login, total), encoding=default_encoding)

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
        'order_id'         : order_id,
        'review_id'        : review_id,
        # ----------------------------------------------
        # Default Lines List (sublines equal as reviews)
        # ----------------------------------------------
        'currentfile'      : currentfile,
        'sublines'         : reviews,
        'config'           : config,
        'tabs'             : list(tabs.keys()),
        # --------------------------
        # Results (Log page content)
        # --------------------------
        'total'            : total,
        'data'             : data,
        'status'           : status,
        'props'            : props,
        'columns'          : columns,
        'errors'           : errors,
    })

    g.page.point('loader')

    return jsonify(response)

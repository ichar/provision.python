# -*- coding: utf-8 -*-

import re

from config import DATE_STAMP

from ..settings import *
from ..barcodes import genBarcode
from ..utils import (
     getToday, getDate, getDateOnly, sMoney, getMoney, getCurrency, getFloatMoney, getString, getSQLString,
     checkPaginationRange, Capitalize, unCapitalize, cleanHtml
     )

from .page_default import PageDefault

##  ===================
##  PageProvision Model
##  ===================

default_page = 'provision'
default_locator = 'provision'
default_template = 'provision-orders'

_PAGE_LINK = ('%sprovision', '?sidebar=0',)

valid_status = 7
valid_payment_status = 5

#
# Warning!!! ValueError: unsupported format character ';' (0x3b) at index 981 -> use `100%%` double semicolon!
#

_APPROVAL_ALARM_HTML = '''
<html>
<head>
  <style type="text/css">
    h1 { font-size:18px; padding:0; margin:0 0 10px 0; }
    div.box { font:normal 12px Verdana, Arial; }
    div.box * { display:block; }
    dd { font-size:16px; font-weight:bold; line-height:24px; padding:0; color:#468; margin-left:10px; white-space:nowrap; }
    span { color:#000; padding-top:3px; font-size:12px; white-space:nowrap; }
    a { cursor:pointer; }
    .seller {}
    .order * { display:inline-block !important; }
    .caption { padding-top:10px; padding-bottom:10px; }
    .info { margin:10px 0 10px 0; }
    div.title { margin-top:10px; font-weight:bold; color:rgba(120, 100, 80, 0.6); }
    div.message { margin-top:10px; font-size:12px; }
    div.line { border-top:1px dotted #888; width:100%%; height:1px; margin:10px 0 10px 0; }
    div.line hr { display:none; }
  </style>
</head>
<body>
  <div class="box">
  <h1 class="center">Запрос на согласование</h1>
  <table>
  <tr><td class="info">Просим в течение 2-х рабочих дней согласовать исполнение заказа.</td></tr>
  <tr><td class="caption">Заявка снабжения:</td></tr>
  <tr><td><dd class="order"><a target="_blank" href="webperso#args&_id=%(id)s">[%(id)05d]</a>&nbsp;%(Article)s</dd></td></tr>
  <tr><td><span class="info">%(Date)s</span></td></tr>
  <tr><td>
    <div class="title">Запрос на согласование заявки снабжения. %(Reviewer)s</div>
    <div class="message">%(Message)s</div>
  </td></tr>
  <tr><td><div class="line"><hr></div></td></tr>
  </table>
  </div>
</body>
</html>
'''

_CREATE_ALARM_HTML = '''
<html>
<head>
  <style type="text/css">
    h1 { font-size:18px; padding:0; margin:0 0 10px 0; }
    div.box { font:normal 12px Verdana, Arial; }
    div.box * { display:block; }
    dd { font-size:16px; font-weight:bold; line-height:24px; padding:0; color:#468; margin-left:10px; white-space:nowrap; }
    span { color:#000; padding-top:3px; font-size:12px; white-space:nowrap; }
    a { cursor:pointer; }
    .seller {}
    .order * { display:inline-block !important; }
    .caption { padding-top:10px; padding-bottom:10px; }
    .info { margin:10px 0 10px 0; }
    div.title { margin-top:10px; font-weight:bold; color:rgba(120, 100, 80, 0.6); }
    div.message { margin-top:10px; font-size:12px; }
    div.line { border-top:1px dotted #888; width:100%%; height:1px; margin:10px 0 10px 0; }
    div.line hr { display:none; }
  </style>
</head>
<body>
  <div class="box">
  <h1 class="center">Заявка снабжения</h1>
  <table>
  <tr><td class="info">Создана новая заявка на закупку/поставку товарной номенклатуры.</td></tr>
  <tr><td class="caption">Заказ:</td></tr>
  <tr><td><dd class="order"><a target="_blank" href="webperso#args&_id=%(id)s">[%(id)05d]</a>&nbsp;%(Article)s</dd></td></tr>
  <tr><td><span class="info">%(Date)s</span></td></tr>
  <tr><td>
    <div class="title">Заказчик: %(Subdivision)s. ФИО: %(Reviewer)s</div>
    <div class="message"></div>
  </td></tr>
  <tr><td><div class="line"><hr></div></td></tr>
  </table>
  </div>
</body>
</html>
'''

_REMOVE_ALARM_HTML = '''
<html>
<head>
  <style type="text/css">
    h1 { font-size:18px; padding:0; margin:0 0 10px 0; }
    div.box { font:normal 12px Verdana, Arial; }
    div.box * { display:block; }
    dd { font-size:16px; font-weight:bold; line-height:24px; padding:0; color:#468; margin-left:10px; white-space:nowrap; }
    span { color:#000; padding-top:3px; font-size:12px; white-space:nowrap; }
    a { cursor:pointer; }
    .seller {}
    .order * { display:inline-block !important; }
    .caption { padding-top:10px; padding-bottom:10px; }
    .info { margin:10px 0 10px 0; }
    div.title { margin-top:10px; font-weight:bold; color:rgba(120, 100, 80, 0.6); }
    div.remover { margin-top:10px; font-size:12px; font-weight:bold; color:#c72424; }
    div.line { border-top:1px dotted #888; width:100%%; height:1px; margin:10px 0 10px 0; }
    div.line hr { display:none; }
  </style>
</head>
<body>
  <div class="box">
  <h1 class="center">Заявка снабжения</h1>
  <table>
  <tr><td class="info">Заявка снабжения удалена.</td></tr>
  <tr><td class="caption">Заказ:</td></tr>
  <tr><td><dd class="order"><a target="_blank" href="webperso#args&_id=%(id)s">[%(id)05d]</a>&nbsp;%(Article)s</dd></td></tr>
  <tr><td><span class="info">%(Date)s</span></td></tr>
  <tr><td>
    <div class="title">Заказчик: %(Subdivision)s. ФИО: %(Reviewer)s</div>
    <div class="remover">Удалено: %(Remover)s</div>
  </td></tr>
  <tr><td><div class="line"><hr></div></td></tr>
  </table>
  </div>
</body>
</html>
'''

_REVIEW_ALARM_HTML = '''
<html>
<head>
  <style type="text/css">
    h1 { font-size:18px; padding:0; margin:0 0 10px 0; }
    div.box { font:normal 12px Verdana, Arial; }
    div.box * { display:block; }
    dd { font-size:16px; font-weight:bold; line-height:24px; padding:0; color:#468; margin-left:10px; white-space:nowrap; }
    span { color:#000; padding-top:3px; font-size:12px; white-space:nowrap; }
    a { cursor:pointer; }
    .seller {}
    .order * { display:inline-block !important; }
    .caption { padding-top:10px; padding-bottom:10px; }
    .info { padding-top:10px; display:inline-block; }
    .code { background-color:#333333; padding:5px 20px 5px 20px; border:1px solid #806080; text-align:center; color:white; width:fit-content; max-width:250px; width:max-content; display:inline-block; }
    .work { background-color:#888888; }
    .review { background-color:#886666; }
    .accept { background-color:#84C284; }
    .reject { background-color:#E4606A; }
    .confirm { background-color:#4B55CC; }
    .confirmation { background-color:#48BCD8; }
    .execute { background-color:#CC80CC; }
    .paid { background-color:#DEA248; }
    .delivered { background-color:#488DA0; }
    .decree { background-color:#b654a8; }
    .audit { background-color:#A28E2C; }
    .failure { background-color:#C24620; }
    .validated { background-color:#64A048; }
    .finish { background-color:#488DA0; }
    div.title { margin-top:10px; font-weight:bold; color:rgba(120, 100, 80, 0.6); }
    div.message { margin-top:10px; font-size:12px; }
    div.line { border-top:1px dotted #888; width:100%%; height:1px; margin:10px 0 10px 0; }
    div.line hr { display:none; }
  </style>
</head>
<body>
  <div class="box">
  <h1 class="center">Уведомление %(Caption)s</h1>
  <table>
  <tr><td><dd class="code %(code)s">%(Code)s</dd></td></tr>
  <tr><td class="caption">Заявка снабжения:</td></tr>
  <tr><td><dd class="seller">%(Seller)s</dd></td></tr>
  <tr><td><dd class="order"><a target="_blank" href="webperso#args&_id=%(id)s">[%(id)05d]</a>&nbsp;%(Article)s</dd></td></tr>
  <tr><td><span class="info">%(Date)s</span></td></tr>
  <tr><td>
    <div class="title">%(Title)s. %(Reviewer)s</div>
    <div class="message">%(Message)s</div>
  </td></tr>
  <tr><td><div class="line"><hr></div></td></tr>
  </table>
  </div>
</body>
</html>
'''

_REVIEW_PAYMENTS_ALARM_HTML = '''
<html>
<head>
  <style type="text/css">
    h1 { font-size:18px; padding:0; margin:0 0 10px 0; }
    div.box { font:normal 12px Verdana, Arial; }
    div.box * { display:block; }
    dd { font-size:16px; font-weight:bold; line-height:24px; padding:0; color:#468; margin-left:10px; white-space:nowrap; }
    span { color:#000; padding-top:3px; font-size:12px; white-space:nowrap; }
    a { cursor:pointer; }
    .company {}
    .order * { display:inline-block !important; }
    .caption { padding-top:10px; padding-bottom:10px; }
    .info { padding-top:10px; display:inline-block; }
    .code { background-color:#333333; padding:5px 20px 5px 20px; border:1px solid #806080; text-align:center; color:white; width:fit-content; max-width:250px; width:max-content; display:inline-block; }
    .work { background-color:#888888; }
    .review { background-color:#886666; }
    .accept { background-color:#84C284; }
    .reject { background-color:#E4606A; }
    .confirm { background-color:#4B55CC; }
    .confirmation { background-color:#48BCD8; }
    .execute { background-color:#CC80CC; }
    .paid { background-color:#DEA248; }
    .delivered { background-color:#488DA0; }
    .finish { background-color:#488DA0; }
    div.title { margin-top:10px; font-weight:bold; color:rgba(120, 100, 80, 0.6); }
    div.message { margin-top:10px; font-size:12px; }
    div.line { border-top:1px dotted #888; width:100%%; height:1px; margin:10px 0 10px 0; }
    div.line hr { display:none; }
  </style>
</head>
<body>
  <div class="box">
  <h1 class="center">Уведомление %(Caption)s</h1>
  <table>
  <tr><td><dd class="code %(code)s">%(Code)s</dd></td></tr>
  <tr><td class="caption">Компания:</td></tr>
  <tr><td><dd class="company">%(company)s</dd></td></tr>
  <tr><td><dd class="order"><a target="_blank" href="webperso/payments/%(review_date)s">на дату [%(date)s]</a></dd></td></tr>
  <tr><td><span class="info">%(Date)s</span></td></tr>
  <tr><td>
    <div class="title">%(Title)s. %(Reviewer)s</div>
    <div class="message">%(Message)s</div>
  </td></tr>
  <tr><td><div class="line"><hr></div></td></tr>
  </table>
  </div>
</body>
</html>
'''

_UPLOAD_ATTACHMENT_ALARM_HTML = '''
<html>
<head>
  <style type="text/css">
    h1 { font-size:18px; padding:0; margin:0 0 10px 0; }
    div.box { font:normal 12px Verdana, Arial; }
    div.box * { display:block; }
    dd { font-size:16px; font-weight:bold; line-height:24px; padding:0; color:#468; margin-left:10px; white-space:nowrap; }
    span { color:#000; padding-top:3px; font-size:12px; white-space:nowrap; }
    a { cursor:pointer; }
    .seller {}
    .order * { display:inline-block !important; }
    .caption { padding-top:10px; padding-bottom:10px; }
    .info { margin:10px 0 10px 0; }
    .code { background-color:#78A048; padding:5px 20px 5px 20px; border:1px solid #806080; text-align:center; color:white; width:fit-content; max-width:250px; width:max-content; display:inline-block; }
    div.title { margin-top:10px; font-weight:bold; color:rgba(120, 100, 80, 0.6); }
    div.attachment { margin-top:10px; font-size:12px; font-weight:bold; color:rgba(100, 30, 60, 0.8); }
    div.message { margin-top:10px; font-size:12px; }
    div.uid { margin-top:10px; font-size:12px; color:#c00; }
    div.line { border-top:1px dotted #888; width:100%%; height:1px; margin:10px 0 10px 0; }
    div.line hr { display:none; }
  </style>
</head>
<body>
  <div class="box">
  <h1 class="center">Информация по заявке снабжения</h1>
  <table>
  <tr><td><dd class="code">ВЛОЖЕНИЕ</dd></td></tr>
  <tr><td class="info">Загружен документ финансовой отчетности.</td></tr>
  <tr><td class="caption">Заказ:</td></tr>
  <tr><td><dd class="order"><a target="_blank" href="webperso#args&_id=%(id)s">[%(id)05d]</a>&nbsp;%(Article)s</dd></td></tr>
  <tr><td><span class="info">%(Date)s</span></td></tr>
  <tr><td>
    <div class="attachment">Файл: %(Attachment)s<br>Автор документа: %(Reviewer)s</div>
    <div class="message">%(Message)s</div>
    <div class="uid">UID: %(uid)s</div>
  </td></tr>
  <tr><td><div class="line"><hr></div></td></tr>
  </table>
  </div>
</body>
</html>
'''

## ==================================================== ##

_config = {
    'provision-orders' : { 
        'columns' : ['TID', 'Article', 'Qty', 'Subdivision', 'Price', 'Currency', 'Total', 'Condition', 'Seller', 'Status', 'RD',],
        'noprice' : ['TID', 'Article', 'Qty', 'Subdivision', 'AuthorName', 'Seller', 'Status', 'RD',],
        'disable' : ['Seller',], # 'Author', 'Article', 'Qty', 'Subdivision'
        'view'    : '[dbo].[WEB_Orders_vw]',
        'headers' : { 
            'TID'          : ('ID заявки',              'npp',          '', ''),
            'Article'      : ('НАИМЕНОВАНИЕ ТОВАРА',    'article',      '', ''),
            'Author'       : ('Автор заявки',           '',             '', ''),
            'AuthorName'   : ('Заказчик',               'author',       '', ''),
            'Qty'          : ('Кол-во, шт.',            'qty',          '', ''),
            'Category'     : ('Категория',              '',             '', ''),
            'Purpose'      : ('ОБОСНОВАНИЕ',            '',             '', ''),
            'Price'        : ('Цена за единицу',        'money price',  'nowrap', ''),
            'Currency'     : ('Валюта',                 'currency',     '', ''),
            'Total'        : ('СУММА',                  'money _total', '', ''),
            'Tax'          : ('НДС',                    'money tax',    '', ''),
            'Subdivision'  : ('ПОТРЕБИТЕЛЬ',            'office',       '', ''),
            'Condition'    : ('Условия оплаты',         'condition',    '', ''),
            'Equipment'    : ('Описание',               '',             '', ''),
            'Account'      : ('Номер счета',            '',             '', ''),
            'URL'          : ('Ссылка на товар',        '',             '', ''),
            'Seller'       : ('ПОСТАВЩИК',              'seller',       '', ''),
            'Status'       : ('',                       'status',       's1 nowrap', 'Статус заявки'),
            'ReviewStatus' : ('Статус заявки',          '',             '', ''),
            'RD'           : ('Дата',                   'rd',           '', ''),
            # Extra application headers
            'num'          : ('Заявка снабжения',       '',             '', ''),
            'StockName'    : ('Класс товара',           '',             '', ''),
            'OrderDate'    : ('Дата заявки',            '',             '', ''),
            'Sector'       : ('Участок производства',   '',             '', ''),
            'OrderPrice'   : ('Цена в рублях',          '',             '', ''),
            'PaymentName'  : ('Инициатор платежа',      '',             '', ''),
            'PriceType'    : ('Цена за единицу',        '',             '', ''),
            'CurrencyType' : ('Валюта платежа',         '',             '', ''),
            'FinishDueDate': ('Срок исполнения',        '',             '', ''),
            'AuditDate'    : ('Дата аудита',            '',             '', ''),
            'Validated'    : ('Акцептовано к закрытию', '',             '', ''),
        },
        'export'  : (
            'TID', 'Author', 'Article', 'Qty', 'Purpose', 'Price', 'Currency', 'Total', 'Tax', 'Company', 'Subdivision', 'Sector', 'Equipment', 'EquipmentName', 'Condition', 'Seller', 'SellerCode', 'SellerType', 'SellerTitle', 'SellerAddress', 'SellerContact', 'SellerURL', 'Category', 'Account', 'URL', 'Status', 'ReviewStatus', 'ReviewStatuses', 'SubdivisionCode', 'SubdivisionID', 'SectorID', 'EquipmentID', 'SellerID', 'ConditionID', 'CategoryID', 'StockListID', 'StockListNodeCode', 'UnreadByLogin', 'EditedBy', 'RowSpan', 'Created', 'Approved', 'ReviewDueDate', 'Paid', 'Delivered', 'FinishDueDate', 'AuditDate', 'Validated', 'Facsimile', 'MD', 'RD',
            ),
        'status'  : ('Qty', 'Price',),
        'updated' : ('Author', 'Article', 'Qty', 'Purpose', 'Price', 'Currency', 'URL', 'EditedBy', 'SubdivisionID', 'SectorID', 'ConditionID', 'EquipmentID', 'SellerID', 'CategoryID',),
        'sorted'  : ('TID', 'Subdivision', 'Article', 'Qty', 'Price', 'Total', 'Seller', 'Status', 'RD',),
        'money'   : ('Total', 'Tax',),
    },
    'provision-order-items' : { 
        'columns' : ('TID', 'Login', 'Name', 'Vendor', 'Qty', 'Units', 'Total', 'Currency', 'Account'),
        'view'    : '[dbo].[WEB_OrderItems_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'Login'        : 'Автор',
            'Name'         : 'Наименование',
            'Qty'          : 'Кол-во',
            'Units'        : 'Ед/изм.',
            'Total'        : 'Сумма',
            'Currency'     : 'Валюта',
            'Vendor'       : 'Производитель товара',
            'Account'      : 'Номер в 1С',
            'Tax'          : 'НДС',
        },
        'export'  : ('TID', 'Login', 'Name', 'Qty', 'Units', 'Total', 'Tax', 'Currency', 'Account', 'Vendor', 'VendorID', 'RD',),
        'money'   : ('Total', 'Tax',),
    },
    'provision-order-payments' : { 
        'columns' : ('TID', 'Login', 'Purpose', 'PaymentDate', 'Total', 'Currency', 'Rate', 'ExchangeRate', 'Tax', 'Status',),
        'view'    : '[dbo].[WEB_OrderPayments_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'PaymentID'    : 'ID параметра',
            'Login'        : 'Автор',
            'Purpose'      : 'Назначение платежа',
            'PaymentDate'  : 'Дата платежа',
            'Total'        : 'Сумма',
            'Currency'     : 'Валюта',
            'Rate'         : 'Курс ЦБ',
            'ExchangeRate' : 'Курс покупки валюты',
            'Tax'          : 'НДС (руб.)',
            'Status'       : 'Статус',
            'Comment'      : 'Примечание',
        },
        'with_class' : {
            'Status' : True,
        },
        'export'  : ('TID', 'PaymentID', 'Login', 'Purpose', 'PaymentDate', 'Total', 'Tax', 'Status', 'RD', 'Currency', 'Rate', 'ExchangeRate', 'Comment',),
        'money'   : ('Total', 'Tax',),
    },
}

## ==================================================== ##

##  -------------------
##  Page HTML arguments
##  -------------------

def _get_page_args(query=None):
    args = {}

    if has_request_item(EXTRA_):
        args[EXTRA_] = (EXTRA_, None)

    def _get_item(name, check_int=None):
        return get_request_item(name, check_int=check_int, args=query)

    try:
        args.update({
            'stock'       : ['StockListID', int(_get_item('stock') or '0')],
            'company'     : ['Company', _get_item('company') or ''],
            'subdivision' : ['SubdivisionID', int(_get_item('subdivision') or '0')],
            'sector'      : ['SectorID', int(_get_item('sector') or '0')],
            'author'      : ['Author', _get_item('author') or ''],
            'seller'      : ['SellerID', int(_get_item('seller') or '0')],
            'vendor'      : ['Vendor', int(_get_item('vendor') or '0')],
            'category'    : ['CategoryID', int(_get_item('category') or '0')],
            'currency'    : ['Currency', _get_item('currency') or ''],
            'condition'   : ['ConditionID', int(_get_item('condition') or '0')],
            'date_from'   : ['RD', _get_item('date_from') or ''],
            'date_to'     : ['RD', _get_item('date_to') or ''],
            'status'      : ['Status', _get_item('status', check_int=True)],
            'reviewer'    : ['Reviewer', _get_item('reviewer') or ''],
            'confirmed'   : ['ReviewStatuses', _get_item('confirmed') or ''],
            'paid'        : ['ReviewStatuses', _get_item('paid') or ''],
            'delivered'   : ['ReviewStatuses', _get_item('delivered') or ''],
            'finish'      : ['ReviewStatuses', _get_item('finish') or ''],
            'autoclosed'  : ['ReviewStatuses', _get_item('autoclosed') or ''],
            'audit'       : ['AuditDate', _get_item('audit') or ''],
            'id'          : ['TID', _get_item('_id', check_int=True)],
            'ids'         : ['TID', get_request_item('_ids')],
        })
    except:
        args.update({
            'stock'       : ['StockListID', 0],
            'company'     : ['Company', ''],
            'subdivision' : ['SubdivisionID', 0],
            'sector'      : ['SectorID', 0],
            'author'      : ['Author', ''],
            'seller'      : ['SellerID', 0],
            'vendor'      : ['Vendor', 0],
            'category'    : ['CategoryID', 0],
            'currency'    : ['Currency', ''],
            'condition'   : ['ConditionID', 0],
            'date_from'   : ['RD', ''],
            'date_to'     : ['RD', ''],
            'status'      : ['Status', None],
            'reviewer'    : ['Reviewer', ''],
            'confirmed'   : ['ReviewStatus', ''],
            'paid'        : ['ReviewStatus', ''],
            'delivered'   : ['ReviewStatus', ''],
            'finish'      : ['ReviewStatus', ''],
            'autoclosed'  : ['ReviewStatus', ''],
            'audit'       : ['AuditDate', ''],
            'id'          : ['TID', None],
            'ids'         : ['TID', None],
        })
        flash('Please, update the page by Ctrl-F5!')

    return args


## ==================================================== ##


class PageProvision(PageDefault):
    
    def __init__(self, id, name, title, caption, **kw):
        if IsDeepDebug:
            print('PageProvision init')

        super().__init__(id, name, title, caption, **kw)

        self._model = 0
        self._distinct = True

    def _init_state(self, engine, attrs=None, factory=None, *args, **kwargs):
        if IsDeepDebug:
            print('PageProvision initstate')

        super()._init_state(engine, attrs, factory, valid_status=valid_status, valid_payment_status=valid_payment_status)

        self._permissions()

        self._is_no_price = not (
            self.is_provision_manager or 
            self.is_office_direction or 
            self.is_office_execution or 
            #self.is_ceo or 
            #self.is_headoffice or 
            #self.is_cao or 
            self.is_assistant or 
            self.is_auditor or 
            self.is_cto or 
            self.is_chief or 
            self.is_consultant
            ) and 1 or 0

        if IsDeepDebug:
            print('--> is_no_price:%s' % self.is_no_price)

    #   ----------------------------
    #   EMAIL HTML MESSAGE TEMPLATES
    #   ----------------------------

    @property
    def APPROVAL_ALARM_HTML(self):
        return _APPROVAL_ALARM_HTML
    @property
    def CREATE_ALARM_HTML(self):
        return _CREATE_ALARM_HTML
    @property
    def REMOVE_ALARM_HTML(self):
        return _REMOVE_ALARM_HTML
    @property
    def REVIEW_ALARM_HTML(self):
        return _REVIEW_ALARM_HTML
    @property
    def REVIEW_PAYMENTS_ALARM_HTML(self):
        return _REVIEW_PAYMENTS_ALARM_HTML
    @property
    def UPLOAD_ATTACHMENT_ALARM_HTML(self):
        return _UPLOAD_ATTACHMENT_ALARM_HTML
    @property
    def confirmation_message(self):
        return 'Пожалуйста, ознакомьтесь с информацией о согласовании заявки снабжения'

    #   -----------
    #   PERMISSIONS
    #   -----------

    def _permissions(self):
        super()._permissions()

    def is_disabled_accept(self, ob=None):
        if ob is None:
            ob = g.requested_object
        status = ob.get('Status') or 0
        return (status > 4 or status > 0 and not self.is_vip) and True or False

    #   -----------

    @property
    def model(self):
        return self._model
    @property
    def distinct(self):
        return self._distinct
    @property
    def is_no_price(self):
        return self._is_no_price
    @property
    def status_columns(self):
        return self._is_no_price and ('Status',) or ('Status',)
    @property
    def is_page_manager(self):
        return self.is_owner or self.is_provision_manager
    @property
    def page_config(self):
        return _config
    @property
    def page_link(self):
        return _PAGE_LINK
    @property
    def order_tag_restrictions(self):
        return (0,1,2,3,4,13,14)
    @property
    def barcode_date_format(self):
        return DATE_STAMP

    #   --------
    #   HANDLERS
    #   --------

    def after(self, order):
        order['Status'] = ''

    def order_created(self, done):
        return done and gettext('Message: Order was %s successfully.' % done) or ''

    def disabled_statuses(self):
        statuses = []

        ob = g.requested_object

        # ----------------------------
        # Полномочия на смену статусов
        # ----------------------------

        order_id = ob['TID']
        params = self.order_params(order_id, ["Code='EX'"])
        executor = params and params[0]['Value']

        login = g.current_user.login
        is_author = (self.is_author or self.is_manager) and ob['Author'] == login or executor == login
        is_provision_manager = self.is_provision_manager or self.is_admin

        statuses.append(not (is_author or self.is_provision_manager) and 1 or 0)
        statuses.append(not (is_provision_manager) and 1 or 0)
        statuses.append(not (is_author or is_provision_manager) and 1 or 0)
        statuses.append(not (is_author or is_provision_manager) and 1 or 0)
        statuses.append(not (is_author or is_provision_manager) and 1 or 0)

        return statuses

    @staticmethod
    def get_review_alarm_caption(status, order_status):
        return status == 7 and order_status > 5 and 'о поставке товара на склад' or order_status > 4 and 'об исполнении' or 'о согласовании'

    def get_review_alarm_title(self, status, order_status):
        if status == self.provision_review_statuses['audit']:
            return 'Запрос на аудиторскую проверку'
        if status == self.provision_review_statuses['failure']:
            return 'Замечание аудитора'
        if status == self.provision_review_statuses['validated']:
            return 'Акцептовано к закрытию'
        if status == self.provision_review_statuses['confirmation']:
            return 'Обоснование по заявке снабжения'
        return 'Информация %s заявки снабжения' % (
               status == self.provision_review_statuses['delivered'] and 'об исполнении' or 
               status == self.provision_review_statuses['paid'] and 'об оплате' or 
               status == self.provision_review_statuses['decree'] and 'к исполнению' or 
               'о согласовании'
               )

    #   -----------------------
    #   OVERIDDEN SYSTEM CONFIG
    #   -----------------------

    @property
    def system_config_emails_approval(self):
        return g.system_config.DEFAULT_EMAILS_PROVISION_APPROVAL or []
    @property
    def system_config_emails_create(self):
        return g.system_config.DEFAULT_EMAILS_PROVISION_CREATE or []
    @property
    def system_config_emails_remove(self):
        return g.system_config.DEFAULT_EMAILS_PROVISION_REMOVE or []
    @property
    def system_config_emails_review(self):
        return g.system_config.DEFAULT_EMAILS_PROVISION_REVIEW or []
    @property
    def system_config_emails_execute(self):
        return g.system_config.DEFAULT_EMAILS_PROVISION_EXECUTE or []
    @property
    def system_config_emails_payments(self):
        return g.system_config.DEFAULT_EMAILS_PROVISION_PAYMENTS or []
    @property
    def system_config_emails_audit(self):
        return g.system_config.DEFAULT_EMAILS_PROVISION_AUDIT or []
    @property
    def system_config_emails_decree(self):
        return g.system_config.DEFAULT_EMAILS_PROVISION_DECREE or []
    @property
    def system_config_emails_upload(self):
        return g.system_config.DEFAULT_EMAILS_PROVISION_UPLOAD or []
    @property
    def system_config_documents_schedule(self):
        return g.system_config.get('IsApplyDocumentsSchedule', 1)
    @property
    def system_config_decrees_schedule(self):
        return g.system_config.get('IsApplyDecreesSchedule', 1)

    #   --------
    #   SETTINGS
    #   --------

    @property
    def is_review_headoffice(self):
        return g.system_config.IsReviewHeadOffice
    @property
    def is_review_with_headoffice(self):
        return 0
    @property
    def is_review_with_assistant(self):
        return 1
    @property
    def is_review_with_root(self):
        return 1
    @property
    def is_decree_headoffice(self):
        return 1
    @property
    def is_decree_with_headoffice(self):
        return 1
    @property
    def is_decree_with_assistant(self):
        return 0
    @property
    def is_decree_with_root(self):
        return 0

    @staticmethod
    def is_valid_1C(v):
        p = g.system_config.PROVISION_CHECK_1C
        if not p:
            return True
        elif not v:
            return False
        else:
            for x in [_.strip() for _ in v.split(' ')]:
                if not (x and x.isdigit()) or len(x) < p:
                    return False
        return True

    @staticmethod
    def is_valid_stock_route(code, reviewers):
        routes = g.system_config.PROVISION_STOCK_ROUTES
        if not routes:
            return (True, None)
        elif not code:
            return (False, None)
        else:
            for route in routes:
                c, login = route.split(':')
                if (code.startswith(c) or c == '*') and not login in reviewers:
                    return (False, route)
        return (True, None)

    #   -----------

    def get_header(self, name, config='provision-orders'):
        view = self.page_config.get(config) or super().page_config.get(config)
        x = view.get('headers').get(name)
        return x and x[0] or ''

    def database_config(self, name):
        if name in _config:
            return _config[name]

        return super().database_config(name)

    def get_dates(self):
        return { 
            'Created'       : [1, 'Дата создания', ''],
            'ReviewDueDate' : [2, 'Дата обоснования', ''],
            'Approved'      : [3, 'Дата согласования', ''],
            'Paid'          : [4, 'Дата оплаты', ''],
            'Delivered'     : [5, 'Дата поставки на склад', ''],
            'AuditDate'     : [6, 'Дата аудита', ''],
            'Validated'     : [7, 'Дата исполнения', ''],
        }

    def check_dates(self, dates):
        ob = g.requested_object
        if ob and ob.get('Status') != self.statuses.get('finish') and ob['Created'] > getDate('2021-07-01', format=LOCAL_EASY_DATESTAMP, is_date=True):
            dates['Validated'][2] = ''

    def set_attrs(self, ob, attrs):
        return {
            'Login'         : (0, ob.login, 'Автор заявки',),
            'Subdivision'   : (1, ob._subdivision, 'ПОТРЕБИТЕЛЬ',),
            'Article'       : [2, ob._article, 'Наименование товара',], 
            'Qty'           : (3, ob._qty, 'Количество (шт)',),
            'Purpose'       : [4, ob._purpose, 'Обоснование',],
            'Price'         : (5, ob._price, 'Цена за единицу',),
            'Currency'      : (6, ob._currency, 'Валюта',),
            'Condition'     : (7, ob._condition, 'Условия оплаты'),
            'Seller'        : (8, ob._seller, 'ПОСТАВЩИК',),
            'SellerTitle'   : (9, ob._seller_title, 'Реквизиты компании поставщика',),
            'SellerAddress' : (10, ob._seller_address, 'Адрес организации',),
            'SellerCode'    : (11, ob._seller_code, 'Код 1C',),
            'SellerContact' : (12, ob._seller_contact, 'Контактные лица',),
            'Equipment'     : [13, ob._equipment, 'Описание оборудования или технологического процесса',], 
            'DueDate'       : (14, ob._duedate, 'Срок исполнения',), 
            'Author'        : (15, ob._author, 'Заказчик',), 
            'Category'      : (16, ob._category, 'Категория',),
            'URL'           : (17, ob._url, 'Ссылка на товар на сайте поставщика (URL)',),
            'Sector'        : (18, ob._sector, 'Участок производства',),
            }

    def order_paid(self, ob):
        return self._get_paid_total(ob.get('TID'), ob.get('Total'), ob.get('Currency')) or 0

    def order_no_paid(self, ob):
        order_id = ob['TID']
        total = ob.get('Total') or 0
        paid = self.order_paid(ob)
        fixed = 0
        params = self.order_params(order_id, ["Code='SF'"])
        try:
            fixed = getMoney(params[0]['Value'])
        except:
            pass
        no_paid = (fixed or total) - paid
        return no_paid > 0 and no_paid or 0

    def order_params(self, order_id, params):
        data = self._get_order_params(order_id, params=params)
        return data and data.get('data') or []

    def check_is_serve(self, stock_id):
        if not stock_id:
            return False
        params = tuple(filter(None, self.stocklist.getNodeClassParams(stock_id).split(':')))
        return 'PD' in params or 'FD' in params

    def qualified_documents(self, with_permissions=None):
        x = '(MD=%s or MD is null)' % self.model

        if with_permissions:
            if self.is_office_ceo:
                qd = ''
            elif not (self.is_personal_manager or self.is_provision_manager or self.is_payments_manager):
                qd = x
            elif self.is_payments_manager:
                qd = ''
            elif self.is_personal_manager:
                qd = 'MD=1'
            elif self.is_provision_manager:
                qd = x
            else:
                qd = ''
        else:
            qd = x

        return qd

    def upload_attachment_notification(self, callback, rowid, **kw):
        order_id = kw.get('order_id')

        if not order_id or not callback:
            return

        # -----------------------------------------------
        # Уведомление о загрузке документа (вложение ДБО)
        # -----------------------------------------------

        if not kw.get('for_audit'):
            return

        attrs = {
            'Author'        : (0, kw.get('login'), 'Автор вложения',), 
            'Attachment'    : (1, kw.get('original'), 'Файл вложения',), 
            'Message'       : (2, kw.get('note'), 'Содержание',), 
            'UID'           : (3, '%s:%s' % (rowid, kw.get('uid')), 'UID',), 
        }

        callback.send_upload_attachment_mail(attrs)

    def set_query_for_vendors(self, vendor_id, items):
        cursor = self.runQuery(self._views['order-vendors'], columns=('OrderID', ), where="TID=%s" % vendor_id, distinct=True)
        item = cursor and ','.join([str(x[0]) for x in cursor])
        if item:
            items.append('TID in (%s)' % item)

    def check_tag_limits(self, ob, errors, **kw):
        d0 = g.requested_object.get('FinishDueDate')
        d1 = getDate(ob._duedate, LOCAL_EASY_DATESTAMP, is_date=True)
        if d0 != d1 and d1 < getDateOnly(getToday()):
            errors.append(gettext('Error: FinishDueDate is in past!'))

        return super().check_tag_limits(ob, errors)

    def barcode_action(self, command, order_id, item_id, **kw):
        order = kw.get('order')
        
        stock_id = order and order.get('StockListID')
        is_serve = self.check_is_serve(stock_id)

        if command != 'generate' or not item_id or is_serve:
            return ''

        options = {
            'quiet_zone'    : 0, #6.5,
            'font_size'     : 7, 
            'module_width'  : 0.1196, #0.1160,
            'module_height' : 4.0,
            'text_distance' : 1,
            'write_text'    : True,
            'center_text'   : False, 
        }

        size = None # (270, None)

        value = '{0:>05}:{1:}:{2:}'.format(order_id, item_id, getDate(getToday(), self.barcode_date_format))
        barcode = genBarcode(value, text='') #, size=size, options=options

        if size:
            return barcode['output']
        return "data:image/png;base64,%s" % barcode['output']

    #   --------
    #   STATUSES
    #   --------

    def check_status_default(self, ob, key, **kw):
        is_extra = kw.get('is_extra') and True or False

        statuses = self.statuses
        status = ob.get('Status')

        errors = []

        if is_extra:
            pass
        elif key in ('review', 'execute',) and not ob.get('Price'):
            errors.append(gettext('Error: Price is not defined'))
        elif key == 'review' and status > statuses['review'] and status < statuses['execute']:
            errors.append(gettext('Error: Status of order cannot be changed.'))
        elif key == 'execute' and status not in (statuses['accepted'], statuses['finish'],):
            errors.append(gettext('Error: Status of order cannot be changed.'))
        elif key == 'finish' and status != statuses['execute']:
            errors.append(gettext('Error: Status of order cannot be changed.'))

        return errors

    def check_status(self, command, ob, **kw):
        is_run, error = True, ''

        order_id = kw.get('order_id')
        review = kw.get('key')
        force = kw.get('force')

        stock_id = ob.get('StockListID')
        stock_code = ob.get('StockListNodeCode')

        def _get_codes(codes):
            return ','.join(["'%s'" % x for x in codes])

        def _params_error(codes, force=None):
            error = ''
            params = self.order_params(order_id, not force and ["Code in (%s)" % _get_codes(codes)] or None)
            # No Order Params
            if not params:
                is_run = False
                error = gettext('Error: Order Params should be present before change status.')
            else:
                for p in params:
                    c = p['Code']
                    v = p['Value']
                    if c in codes:
                        if c == '1C' and not self.is_valid_1C(v):
                            continue
                        codes.remove(c)
                if codes:
                    is_run = False
                    error = '%s\n%s:<div class="notification-errors">%s</div>%s' % (
                        gettext('Error: Status of order cannot be changed.'),
                        gettext('Order Params are not exist'),
                        '\n'.join(['- '+gettext('ParamCode:%s' % x) for x in codes]),
                        gettext('Please, change the lacks!'),
                        )
                    #error = re.sub(r'\n', '<br>', re.sub(r'\t', '&nbsp', error))
            return error

        # -------------------------
        # Контроль: НА СОГЛАСОВАНИЕ
        # -------------------------

        if command == 'STATUS_REVIEW':
            if not error:
                # Параметры
                error = _params_error(['DE','EX','CO'], force=True)
            if not error and not stock_id:
                # Класс товара
                error = gettext('Error: No NodeClassTag! Status of order cannot be changed.')
            if not error and g.system_config.PROVISION_STOCKS_DEPTH and len(stock_code.split('.')) < g.system_config.PROVISION_STOCKS_DEPTH:
                # Минимальная глубина классификации
                error = gettext('Error: Low NodeClass Depth! Status of order cannot be changed.')
            if not error and stock_code:
                # Маршруты согласования
                accepted = self.get_order_reviewers(ob, 'accept')
                is_valid, route = self.is_valid_stock_route(stock_code, accepted)
                if not is_valid:
                    error = '%s\n%s' % (
                        gettext('Error: Not valid stock route! Status of order cannot be changed.'),
                        route or ''
                        )
            if not error:
                items = self._get_order_items(order_id)
                # Счет
                if not items['total']:
                    is_run = False
                    error = gettext('Error: Order Items should be present before change status.')

        # -----------------------
        # Контроль: НА ИСПОЛНЕНИЕ
        # -----------------------

        if command == 'STATUS_EXECUTE':
            pass

        # -------------------
        # Контроль: ИСПОЛНЕНО
        # -------------------

        if command == 'STATUS_FINISH':
            provision_review_statuses = ob.get('ReviewStatuses')
            stock_id = ob.get('StockListID')

            is_serve = self.check_is_serve(stock_id)

            paid = ':%s:' % self.provision_review_statuses['paid']
            delivered = ':%s:' % self.provision_review_statuses['delivered']
            audit = ':%s:' % self.provision_review_statuses['audit']
            validated = ':%s:' % self.provision_review_statuses['validated']

            delivered_date = ob.get('Delivered')

            condition = self._get_condition(ob.get('ConditionID'), key='Code')
            is_post = condition and 'POST' in condition

            if not force:
                if not error:
                    # Параметры
                    error = _params_error(['AC','DP','DE','EX','CO','SF','1C'], force=True)
                if not error:
                    items = self._get_order_items(order_id)
                    # Счет
                    if not items['total']:
                        error = gettext('Error: Order Items should be present before change status.')
                if not error and not (is_post or paid in provision_review_statuses):
                    # Платежи
                    error = gettext('Error: No Paid! Status of order cannot be changed.')
                if not error and not (is_serve or delivered in provision_review_statuses):
                    # Поставка на склад
                    error = gettext('Error: No Delivered! Status of order cannot be changed.')
            if not error:
                no_paid = self.order_no_paid(ob)
                params = self.order_params(order_id, ["Code like '%%AU%%'"])
                is_many = params and params[0]['Value'].lower().startswith('много')
                is_should_be_closed = not (no_paid or is_many) and validated in provision_review_statuses and (is_serve or delivered_date)
                if force:
                    # Акцептовано к закрытию (validated)
                    if is_should_be_closed:
                        review = 'finish'
                    else:
                        is_run = False
                elif is_should_be_closed:
                    review = 'finish'
                else:
                    is_run = False
                    # Исполнено
                    if provision_review_statuses.endswith(audit):
                        error = gettext('Error: Order is in audit already.')
                    else:
                        review = 'audit'

        error = re.sub(r'\n', '<br>', re.sub(r'\t', '&nbsp', error))

        return is_run, review, error

    def set_status(self, callback, review, ob, **kw):
        order_id = kw.get('order_id')

        if not order_id or not callback:
            return

        errors = []

        is_autoclose = False
        is_audit = False
        is_finish = False

        if review == 'autoclose':
            provision_review_statuses = ob.get('ReviewStatuses')
            stock_id = ob.get('StockListID')

            # ------------
            # Автозакрытие
            # ------------

            params = tuple(filter(None, self.stocklist.getNodeClassParams(stock_id).split(':')))

            paid = ':%s:' % self.provision_review_statuses['paid']
            autoclose = ':%s:' % self.provision_review_statuses['autoclose']

            if not params:
                return
            # Paid + Delivered
            if 'PD' in params and paid in provision_review_statuses:
                is_autoclose = True
            # Forced + Delivered
            elif 'FD' in params and not provision_review_statuses.endswith(autoclose):
                is_autoclose = True

        elif review == 'audit':

            # -----
            # Аудит
            # -----

            is_audit = True

        elif review == 'finish':

            # ---------
            # Исполнено
            # ---------

            is_finish = True

        if is_autoclose:
            errors = callback.delivered(order_id, '', params={'forced' : True})
        if is_audit:
            errors = callback.audit(order_id, '', params={'forced' : True})
        if is_finish:
            errors = callback.finish(order_id, '', params={'forced' : True})

        return errors

    def set_order_facsimile(self, order_id, author, with_error=None):
        return None

    #   ----------------
    #   RENDER DOCUMENTS
    #   ----------------

    def is_urgently(self, order):
        category = order.get('CategoryID')
        status = order.get('Status')
        return category == 2 and status in (1,2,4,5,6) and True or False

    def is_limited_length(self, attrs):
        return attrs.get('is_limited_length') and not g.system_config.IsLimitedLengthExclude and True or False

    def make_current_order_info(self, order_id, info, **kw):
        """
            Совокупная стоимость закупки с учетом обеспечения
        """
        order = kw.get('order')

        if not order or order['TID'] != order_id:
            return info

        currency = order.get('Currency')
        total = order.get('Total')

        where = "OrderID=%s and MD=%s" % (order_id, g.page.model)

        cursor = self.runQuery(self._views['order-documents'], where=where, as_dict=True, engine=g.storage)
        if cursor:
            info['documents'] = 1;

        if self._is_no_price:
            return info

        where = "OrderID=%s" % order_id

        cursor = self.runQuery(self._views['order-refers'], where=where, as_dict=True)
        if cursor:
            total = self._calc_rub(total, currency)
            s = [total]

            for row in cursor:
                x = getFloatMoney(row['Total'], driver=self.driver)
                euro = self._calc_rub(x, row['Currency'])
                total += euro
                s.append(euro)

            total = self._calc_from_rub(total, currency)

            value = self.is_check_refers and (' [%s]' % (' ; '.join([getCurrency(x) for x in s]))) or ''

            info['refers_info'] = {
                'title' : 'Совокупная цена закупки:', 
                'value' : '%s%s %s' % (getCurrency(total), value, currency)
            }

        return info

    def access_query(self, args):
        """
            Полномочия пользователя
        """
        aq = ''

        if self.is_owner: # or not self.is_apply_union:
            pass

        elif self.is_office_direction:
            if not self.is_args and self.is_ceo and not self.is_uncheck_status and not self.no_union:
                aq = 'Status in (1)' #,2,3,4

        elif self.is_assistant:
            aq = "SubdivisionCode like '%s%%'" % self.subdivision_code[:3]

        elif self.is_cto:
            aq = "(SubdivisionCode > '003%%' or SubdivisionCode='0012')"

        elif self.is_cao:
            pass

        elif self.is_office_execution:
            if not self.is_args:
                aq = 'Status in (2,3,5,6)'

        elif self.is_stock_manager:
            if not self.is_args:
                aq = "(Status in (5,6) or SubdivisionCode like '%s%%')" % self.subdivision_code[:3]

        elif args and args.get('id')[1]:
            self.is_search_order = True

        elif not self.is_provision_manager:
            aq = self.subdivision_documents()

        # -------------------
        # Полномочия "автора"
        # -------------------

        if aq and 'Author' not in aq:
            aq = '(%s)' % ' or '.join(list(filter(None, [aq, "Author='%s'" % self.login])))

        # -----------------------
        # Полномочия "рецензента"
        # -----------------------

        if aq and self.is_with_reviewers_template:
            aq = '(%s)' % ' or '.join(list(filter(None, [aq, "[dbo].CHECK_IsInReviewers_fn(TID, '%s')=1" % self.login])))

        return aq

    def render(self, kw, back_where=None, uncheck_status=None):
        """
            Render Provision data by the given ID
        """
        self.point('provision.render-start')

        order_id = int(kw.get('order_id') or 0)
        review_id = int(kw.get('review_id') or 0)

        # -----------------------
        # Полномочия пользователя
        # -----------------------

        root = '%s/' % request.script_root

        is_mobile = kw.get('is_mobile')

        self.no_union = get_request_item('no_union') == '1' and True or not self.is_apply_union and True or False

        if IsDeepDebug:
            print('--> current_user:[%s] %s%s%s%s%s%s%s%s%s%s vip:%s' % (
                self.login, 
                self.is_admin and 1 or 0, 
                self.is_provision_manager and 1 or 0, 
                self.is_payments_manager and 1 or 0, 
                self.is_stock_manager and 1 or 0, 
                self.is_office_direction and 1 or 0, 
                self.is_office_execution and 1 or 0, 
                self.is_auditor and 1 or 0, 
                self.is_ceo and 1 or 0, 
                self.is_cao and 1 or 0, 
                self.is_cto and 1 or 0, 
                self.is_vip and 1 or 0, 
                ))

        # ------------------------
        # Параметры запроса (args)
        # ------------------------

        args = _get_page_args(kw.get('args'))

        # -------------------------------
        # Представление БД (default_view)
        # -------------------------------

        self.default_view = self.database_config(default_template)

        # --------------------------------------------
        # Позиционирование строки в журнале (position)
        # --------------------------------------------

        position = get_request_item('position').split(':')
        line = len(position) > 3 and int(position[3]) or 1

        # -----------------------------------
        # Параметры страницы (page, per_page)
        # -----------------------------------

        page, per_page = get_page_params(default_page)
        top, offset = self._get_top(per_page, page)

        per_page_options = (5, 10, 20, 30, 40, 50, 100,)
        if self.is_admin or self.is_provision_manager or self.is_office_direction:
            per_page_options += (250, 500, 1000)

        self.is_uncheck_status = uncheck_status

        # ---------------------------
        # Поисковый контекст (search)
        # ---------------------------

        search, items, TID = self.make_search(kw)

        # -----------------------------------
        # Команда панели управления (сommand)
        # -----------------------------------

        command = get_request_item('command')

        # -------------
        # Фильтр (args)
        # -------------

        StockListID = args['stock'][1]
        SubdivisionID = args['subdivision'][1]
        SectorID = args['sector'][1]
        SellerID = args['seller'][1]
        ConditionID = args['condition'][1]
        CategoryID = args['category'][1]

        reviewer = args['reviewer'][1]
        
        default_date_format = DEFAULT_DATE_FORMAT[1]

        # ----------------
        # SQL Query filter
        # ----------------

        qf = self.args_parser(args, items)

        self.is_args = len(items) > 0 or not self.is_apply_union

        # ----------------------
        # Скрыть архив + корзину
        # ----------------------

        if not args.get('id')[1] and (not args.get('status')[1] or (isinstance(args['status'][1], int) and args['status'][1] < valid_status)) and \
                not TID and not self.is_uncheck_status:
            items.append('Status < %d' % valid_status)

        # ----------------------------
        # Параметры URL (Query string)
        # ----------------------------

        qs = ''

        if items:
            qs += ' and '.join(items)

        # ---------------------------------------------
        # Область видимости по умолчанию (Access Query)
        # ---------------------------------------------

        aq = self.access_query(args)

        # -------------------
        # Qualified Documents
        # -------------------

        qd = self.qualified_documents()

        # =========
        # SQL WHERE
        # =========
        
        where = ' and '.join(list(filter(None, [aq, qs, qd])))

        # -----------
        # НЕ ПРОЧТЕНО
        # -----------
        
        if self.is_apply_union and not self.is_search_order and not self.no_union:
            sql = "'%s' in (select Login from [dbo].Unreads_tb u where u.OrderID=TID)" % self.login
            union = ((None, None, ' and '.join(filter(None, [sql, qd]))), (offset, top, where,))
        else:
            union = where

        # ---------------------------------
        # Сортировка журнала (current_sort)
        # ---------------------------------

        current_sort = int(get_request_item('sort') or '0')
        if current_sort == 7:
            order = 'Status, ReviewStatus'
        elif current_sort > 0:
            order = '%s' % self.default_view['sorted'][current_sort]
        else:
            order = 'TID'

        if current_sort in (0,3,4,5,8):
            order += " desc"

        if current_sort != 0:
            order += '%s%s' % (order and ',' or '', 'TID desc')

        if IsDeepDebug:
            print('--> where:%s\n... order:%s\n... args: %s' % (where, order, args))

        if back_where:
            return where, order, args, {
                'is_admin' : self.is_admin,
                'is_provision_manager' : self.is_provision_manager,
                'is_stock_manager' : self.is_stock_manager,
                'is_office_direction' : self.is_office_direction,
                'is_office_execution' : self.is_office_execution,
                'is_assistant' : self.is_assistant,
                'is_auditor' : self.is_auditor, 
                'is_ceo' : self.is_ceo,
                'is_cao' : self.is_cao,
                'is_cto' : self.is_cto,
                }

        pages = 0
        total_orders = 0
        total_sum = 0
        total_selected = [0, 0.0]

        orders = []
        reviews = []

        selected_row = {}

        # ======================
        # Выборка данных журнала
        # ======================

        self.point('provision.render-1')

        if IsTrace:
            print_to(None, '--> page_%s.render, login:%s, where:%s' % (self.id, self.login, where))

        if self.engine != None:

            # --------------------------------------------------
            # Кол-во записей по запросу в журнале (total_orders)
            # --------------------------------------------------

            cursor = self.runQuery(default_template, columns=('count(*)', 'sum(Qty)',), where=where)
            if cursor:
                total_orders, total_cards = cursor[0]

            if command == 'export':
                top = 10000

            self.point('provision.render-1.0')

            # --------------------------------------
            # Установить максимальный размер журнала
            # --------------------------------------

            if self.is_max_per_page and not get_request_item('per_page'):
                page, per_page = self._get_max_page(per_page_options, total_orders)
                top, offset = self._get_top(per_page, page)

            self.point('provision.render-1.1')

            # ===============
            # Заявки (orders)
            # ===============

            cursor = self.runQuery(default_template, columns=self.default_view['export'], top=top, offset=offset, where=union, order=order, 
                                   distinct=self.distinct, as_dict=True, encode_columns=self._encode_columns)

            self.point('provision.render-1.2')

            if cursor:
                IsSelected = False
                login = '%s:' % self.login

                unreads = 0
                ids = []

                for n, row in enumerate(cursor):
                    #if not self._is_apply_inion and offset and n < offset:
                    #    continue
                    if not self.distinct and self._check_id(row['TID'], ids):
                        continue

                    row['RowSpan'] = 1

                    status = row['Status']

                    if order_id and order_id == row['TID']:
                        row['selected'] = 'selected'
                        selected_row = row

                        IsSelected = True

                    total = getFloatMoney(row['Total'], driver=self.driver)

                    euro = self._calc_euro(total, row['Currency'])

                    if not self._is_no_price:
                        total_sum += euro

                    row['Total'] = getCurrency(total)
                    row['Tax'] = getCurrency(row.get('Tax'), driver=self.driver)

                    for x in row:
                        if not row[x] or str(row[x]).lower() == 'none':
                            row[x] = ''

                    row['classes'] = {}
                    row['title'] = {}
                    row['rowspan'] = {}
                    row['none'] = []

                    _status = None

                    for column in self.default_view['columns']:
                        classes = [self.default_view['headers'][column][1]]

                        if self.is_valid_status(status) and column in self.status_columns:
                            _status, _title = self.check_order_status(row)
                            if _status:
                                classes.append(_status)
                                classes.append('noselected')

                                row['title'][column] = _title
                            else:
                                if status > 1:
                                    classes.append(self.statuses.get(status))
                                    classes.append('noselected')
                                elif status == 1: # and not self.is_ceo:
                                    classes.append('review')
                                    classes.append('noselected')

                                row['title'][column] = self.get_status(status)[1]

                        if column == 'Article':
                            if self.is_urgently(row):
                                classes.append('urgently')

                        if column == 'Currency':
                            classes.append(row[column])

                        row['classes'][column] = ' '.join([x for x in classes if x])

                    row['title']['TID'] = self.get_status(status)[1]

                    row['status'] = _status or self.statuses.get(status) or ''
                    row['unread'] = not self.no_union and row['UnreadByLogin'] and login in row['UnreadByLogin'] and 'unread' or ''

                    row['AuthorName'] = self.user_short_name(row['Author']) or ''
                    #if self._is_no_price:
                    #    row['AuthorName'] = self.user_short_name(row['Author']) or ''
                    row['classes']['AuthorName'] = self.default_view['headers']['AuthorName'][1]

                    row['id'] = row['TID']
                    row['TID'] = '%05d' % row['id']
                    row['RD'] = self._get_date(row['RD'])

                    if row['SellerID']:
                        row['Seller'] = self._get_seller_link(row)
                        row['classes']['Seller'] += ' link'

                    g.page.after(row)

                    if row['unread'] and not self.is_search_order and not self.no_union:
                        row['title']['Article'] = gettext('Contains unread information')
                        orders.insert(unreads, row)
                        unreads += 1
                    else:
                        orders.append(row)

                    if row['unread']:
                        total_selected[0] += 1
                        total_selected[1] += euro

                if line > len(orders):
                    line = 1

                if not IsSelected and len(orders) >= line:
                    row = orders[line-1]
                    order_id = row['id']
                    row['selected'] = 'selected'
                    selected_row = row

                selected_row['order_id'] = order_id

                if unreads:
                    for row in orders:
                        if not row['unread']:
                            row['union'] = unreads
                            break

            if len(orders) == 0:
                order_id = 0
                review_id = 0

            if total_orders:
                pages = int(total_orders / per_page)
                if pages * per_page < total_orders:
                    pages += 1

            self.point('provision.render-1.3')

            # ======================
            # Согласования (reviews)
            # ======================

            if order_id:
                reviews, review_id = self._get_reviews(order_id, review_id=review_id, reviewer=reviewer)

            self.point('provision.render-1.4')

        # -----------------------------------------------------------
        # Справочники фильтра запросов (sellers, reviewers, statuses)
        # -----------------------------------------------------------
        
        stocks = self.ref_stocks()
        companies = self.ref_companies()
        subdivisions = self.ref_subdivisions()
        sectors = self.ref_sectors()
        categories = self.ref_categories()
        sellers = self.ref_sellers()
        vendors = self.ref_vendors()
        currencies = self.ref_currencies()
        conditions = self.ref_conditions()
        statuses = self.ref_statuses()
        payment_statuses = self.ref_payment_statuses()
        params = self.ref_params()
        payments = self.ref_payments()
        refers = self.ref_refers()
        comments = self.ref_comments()

        # ---------------------
        # Орг.штатная структура
        # ---------------------

        authors = self.ref_authors()
        users = self.ref_users()
        reviewers = self.ref_reviewers()

        self.engine.dispose()

        self.point('provision.render-2')

        paids = [(0, DEFAULT_UNDEFINED,), ('U', 'не обработано',), ('N', 'не оплачено',), ('Y', 'оплачено',)]
        audits = [(0, DEFAULT_UNDEFINED,), ('Y', 'передано на проверку',), ('F', 'замечания',), ('V', 'акцептовано к закрытию',), ('N', 'вне аудита',)]

        # --------------------------------------
        # Нумерация страниц журнала (pagination)
        # --------------------------------------

        iter_pages = []
        for n in range(1, pages+1):
            if checkPaginationRange(n, page, pages):
                iter_pages.append(n)
            elif iter_pages[-1] != -1:
                iter_pages.append(-1)

        query_string = 'per_page=%s' % per_page
        base = '%s?%s' % (self.id, query_string)

        is_extra = has_request_item(EXTRA_)

        modes = [(n, self.default_view['headers'][x][0] or self.default_view['headers'][x][3]) for n, x in enumerate(self.default_view['sorted'])]
        sorted_by = self.default_view['headers'][self.default_view['sorted'][current_sort]]

        pagination = {
            'total'             : '%s / %s' % (total_orders, getCurrency(total_sum) or '0.00'), # EUR[€]
            'title'             : gettext('Total orders / Price on page'),
            'per_page'          : per_page,
            'pages'             : pages,
            'current_page'      : page,
            'iter_pages'        : tuple(iter_pages),
            'has_next'          : page < pages,
            'has_prev'          : page > 1,
            'per_page_options'  : per_page_options,
            'link'              : '%s%s%s%s%s' % (base, qf,
                                                 (search and "&search=%s" % search) or '',
                                                 (current_sort and "&sort=%s" % current_sort) or '',
                                                 (self.no_union and "&no_union=1") or '',
                                                 ),
            'sort'              : {
                'modes'         : modes,
                'sorted_by'     : sorted_by,
                'current_sort'  : current_sort,
            },
            'position'          : '%d:%d:%d:%d' % (page, pages, per_page, line),
        }

        loader = '/%s/loader' % default_locator

        is_full_container = 0
        short = get_request_item('short')
        if short:
            is_full_container = short != '0' and 1 or 0
        elif is_mobile:
            is_full_container = 0

        if is_extra:
            pagination['extra'] = 1
            loader += '?%s' % EXTRA_

        kw.update({
            'base'              : base,
            'page'              : g.page,
            'page_title'        : gettext(self.title),
            'form_caption'      : 'order:%s,decree:%s' % (gettext('of %s' % self.caption), gettext('of decree')),
            'header_subclass'   : 'left-header',
            'show_flash'        : True,
            'hide_menu'         : True,
            'manual'            : True,
            'is_hidden'         : self.is_office_direction and 1 or 0,
            'is_full_container' : is_full_container,
            'is_no_line_open'   : 0, 
            'is_no_price'       : self._is_no_price,
            'is_show_menu'      : 1,
            'is_show_documents' : 1,
            'is_with_blink'     : 0,
            'model'             : g.page.model,
            'loader'            : loader,
            'args'              : args,
            'current_order'     : None, 
            'tabs'              : {},
            'config'            : self.default_view,
            'columns'           : self._is_no_price and 'noprice' or 'columns',
            'pagination'        : pagination,
            'orders'            : orders,
            'reviews'           : reviews,
            'stocks'            : stocks,
            'companies'         : companies,
            'subdivisions'      : subdivisions,
            'sectors'           : sectors,
            'authors'           : authors,
            'sellers'           : sellers,
            'vendors'           : vendors,
            'currencies'        : currencies,
            'conditions'        : conditions,
            'statuses'          : statuses,
            'params'            : params,
            'payments'          : payments,
            'refers'            : refers,
            'comments'          : comments,
            'categories'        : categories,
            'payment_statuses'  : payment_statuses,
            'reviewers'         : reviewers,
            'users'             : users,
            'paids'             : paids,
            'audits'            : audits,
            'search'            : search or '',
            'order_statuses'    : ':'.join(self.order_statuses),
            'links_pages'       : self.links_pages,
            'total_selected'    : self._output_total_selected(total_selected),
        })

        if g.system_config.IsActiveScroller and kw.get('is_active_scroller'):
            kw['is_active_scroller'] = 0 if len(orders) > g.system_config.IsActiveScroller else 1

        self.point('provision.render-finish')

        return kw

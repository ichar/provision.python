# -*- coding: utf-8 -*-

from ..settings import *
from ..utils import (
     getToday, getDate, getDateOnly, getMoney, getCurrency, getFloatMoney, getString, getSQLString,
     checkPaginationRange, Capitalize, unCapitalize, cleanHtml
     )

from .page_default import PageDefault

##  ===============
##  PageSale Model
##  ===============

default_page = 'provision'
default_locator = 'sale'
default_template = 'provision-orders'

_PAGE_LINK = ('%ssale', '?sidebar=0',)

valid_status = 7
valid_payment_status = 5

_schedule_keys = ('documents', 'decrees')

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
  <tr><td class="info">Просим в течение 2-х рабочих дней согласовать ввод в действие документа.</td></tr>
  <tr><td class="caption">%(Caption)s:</td></tr>
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
  <h1 class="center">Контракт на поставку продукции</h1>
  <table>
  <tr><td class="info">Создан новый документ.</td></tr>
  <tr><td class="caption">Документ:</td></tr>
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
  <h1 class="center">Контракт на поставку продукции</h1>
  <table>
  <tr><td class="info">Документ удален.</td></tr>
  <tr><td class="caption">Документ:</td></tr>
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
  <tr><td class="caption">%(Caption)s:</td></tr>
  <tr><td><dd class="seller">%(Seller)s</dd></td></tr>
  <tr><td><dd class="order"><a target="_blank" href="webperso#args&_id=%(id)s">[%(id)05d]</a>&nbsp;%(Article)s</dd></td></tr>
  <tr><td><span class="info">%(Date)s</span></td></tr>
  <tr><td>
    <div class="title">Запрос на согласование контракта на поставку продукции. %(Reviewer)s</div>
    <div class="message">%(Message)s</div>
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
        'columns' : ['TID', 'Article', 'Account', 'Subdivision', 'Category', 'Seller', 'Status', 'RD',], #, 'Currency', 'Total', 'Condition'
        'noprice' : None,
        'disable' : ['Author', 'Article', 'Subdivision', 'Seller',],
        'view'    : '[dbo].[WEB_Orders_vw]',
        'headers' : { 
            'TID'          : ('ID документа',           'npp',          '', ''),
            'Article'      : ('НАИМЕНОВАНИЕ ДОКУМЕНТА', 'article',      '', ''),
            'Author'       : ('Автор документа',        '',             '', ''),
            'AuthorName'   : ('Заказчик',               '',             '', ''),
            'Category'     : ('Категория',              'category',     '', ''),
            'Purpose'      : ('ОБОСНОВАНИЕ',            '',             '', ''),
            'Price'        : ('Цена за единицу',        'money price',  '', ''),
            'Currency'     : ('Валюта',                 'currency',     '', ''),
            'Total'        : ('ЛИМИТ',                  'money _total', '', ''),
            'Tax'          : ('НДС',                    'money tax',    '', ''),
            'Subdivision'  : ('ПОДРАЗДЕЛЕНИЕ',          'office',       '', ''),
            'Condition'    : ('Условия оплаты',         'condition',    '', ''),
            'Equipment'    : ('Описание',               '',             '', ''),
            'Account'      : ('Регистрационный номер',  'account',      'nowrap', ''),
            'URL'          : ('Ссылка на товар',        '',             '', ''),
            'Seller'       : ('КОНТРАГЕНТ',             'seller',       '', ''),
            'Status'       : ('',                       'status',       's1 nowrap', 'Статус документа'),
            'ReviewStatus' : ('Статус документа',       '',             '', ''),
            'RD'           : ('Дата',                   'rd',           '', ''),
            # Extra application headers
            'num'          : ('Номер документа',        '',             '', ''),
            'StockName'    : ('Класс продукции',        '',             '', ''),
            'OrderDate'    : ('Дата документа',         '',             '', ''),
            'Sector'       : ('Участок производства',   '',             '', ''),
            'OrderPrice'   : ('Лимит',                  '',             '', ''),
            'PaymentName'  : ('Инициатор документа',    '',             '', ''),
            'PriceType'    : ('Стоимость контракта',    '',             '', ''),
            'CurrencyType' : ('Валюта расчетов',        '',             '', ''),
            'FinishDueDate': ('Срок действия',          '',             '', ''),
        },
        'export'  : (
            'TID', 'Author', 'Article', 'Qty', 'Purpose', 'Price', 'Currency', 'Total', 'Tax', 'Subdivision', 'Equipment', 'EquipmentName', 'Condition', 'Seller', 'SellerCode', 'SellerType', 'SellerTitle', 'SellerAddress', 'SellerContact', 'SellerURL', 'Category', 'Account', 'URL', 'Status', 'ReviewStatus', 'ReviewStatuses', 'SubdivisionCode', 'SubdivisionID', 'EquipmentID', 'SellerID', 'ConditionID', 'CategoryID', 'StockListID', 'StockListNodeCode', 'UnreadByLogin', 'EditedBy', 'RowSpan', 'Created', 'Approved', 'ReviewDueDate', 'Paid', 'Delivered', 'FinishDueDate', 'MD', 'RD',
            ),
        'status'  : ('Qty', 'Price',),
        'updated' : ('Author', 'Article', 'Account', 'Qty', 'Purpose', 'Price', 'Currency', 'URL', 'EditedBy', 'SubdivisionID', 'ConditionID', 'EquipmentID', 'SellerID', 'CategoryID',),
        'sorted'  : ('TID', 'Subdivision', 'Article', 'Price', 'Total', 'Seller', 'Status', 'RD',),
        'money'   : ('Total', 'Tax',),
    },
    'provision-order-items' : { 
        'columns' : ('TID', 'Login', 'Name', 'Qty', 'Units', 'Total', 'Currency', 'Account'),
        'view'    : '[dbo].[WEB_OrderItems_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'Login'        : 'Автор',
            'Name'         : 'Наименование',
            'Qty'          : 'Кол-во',
            'Units'        : 'Ед/изм.',
            'Total'        : 'Сумма',
            'Currency'     : 'Валюта',
            'Account'      : 'Номер в 1С (расход)',
            'Tax'          : 'НДС',
        },
        'export'  : ('TID', 'Login', 'Name', 'Qty', 'Units', 'Total', 'Tax', 'Currency', 'Account', 'RD',),
        'money'   : ('Total', 'Tax',),
    },
    'provision-order-payments' : { 
        'columns' : ('TID', 'Login', 'Purpose', 'PaymentDate', 'Total', 'Currency', 'Rate', 'Status',),
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
            'Tax'          : 'НДС (руб.)',
            'Status'       : 'Статус',
            'Comment'      : 'Примечание',
        },
        'with_class' : {
            'Status' : True,
        },
        'export'  : ('TID', 'PaymentID', 'Login', 'Purpose', 'PaymentDate', 'Total', 'Tax', 'Status', 'RD', 'Currency', 'Rate', 'Comment',),
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
            'subdivision' : ['SubdivisionID', int(_get_item('subdivision') or '0')],
            'author'      : ['Author', _get_item('author') or ''],
            'seller'      : ['SellerID', int(_get_item('seller') or '0')],
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
            'id'          : ['TID', _get_item('_id', check_int=True)],
            'ids'         : ['TID', get_request_item('_ids')],
        })
    except:
        args.update({
            'stock'       : ['StockListID', 0],
            'subdivision' : ['SubdivisionID', 0],
            'author'      : ['Author', ''],
            'seller'      : ['SellerID', 0],
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
            'id'          : ['TID', None],
            'ids'         : ['TID', None],
        })
        flash('Please, update the page by Ctrl-F5!')

    return args


## ==================================================== ##


class PageSale(PageDefault):

    def __init__(self, id, name, title, caption, **kw):
        if IsDeepDebug:
            print('PageSale init')

        super().__init__(id, name, title, caption, **kw)

        self._model = 20
        self._distinct = True

    def _init_state(self, engine, attrs=None, factory=None, *args, **kwargs):
        if IsDeepDebug:
            print('PageSale initstate')

        super()._init_state(engine, attrs, factory, valid_status=valid_status, valid_payment_status=valid_payment_status)

        self._permissions()

        self._is_no_price = 0

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
    def confirmation_message(self):
        return 'Пожалуйста, ознакомьтесь с информацией о согласовании организационно-распорядительного документа'

    #   -----------
    #   PERMISSIONS
    #   -----------

    def _permissions(self):
        super()._permissions()

    def is_disabled_accept(self, ob=None):
        if ob is None:
            ob = g.requested_object
        status = ob.get('Status') or 0
        return status > 0 and True or False

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
    def locator(self):
        return default_locator
    @property
    def status_columns(self):
        return ('Status',)
    @property
    def is_page_manager(self):
        return (self.is_owner or self.is_sale_manager) and True or False
    @property
    def page_link(self):
        return _PAGE_LINK
    @property
    def order_tag_restrictions(self):
        return (0,1,2,4,8,13)
    @property
    def page_config(self):
        return _config
    @property
    def object_types(self):
        return ('документ', 'документы', 'документов')

    #   --------------

    @staticmethod
    def get_review_alarm_caption(status, order_status):
        return order_status > 4 and 'об исполнении' or 'о согласовании'
    @staticmethod
    def get_review_alarm_title(status, order_status):
        return status == 5 and 'Обоснование по договору продажи' or 'Информация %s договора продажи' % (
               status == 7 and 'об исполнении' or 
               status == 6 and 'об оплате' or 
               status == 9 and 'к исполнению' or 
               'о согласовании'
               )

    #   -----------------------
    #   OVERIDDEN SYSTEM CONFIG
    #   -----------------------

    @property
    def system_config_emails_approval(self):
        return g.system_config.DEFAULT_EMAILS_SALE_APPROVAL or []
    @property
    def system_config_emails_create(self):
        return g.system_config.DEFAULT_EMAILS_SALE_CREATE or []
    @property
    def system_config_emails_remove(self):
        return g.system_config.DEFAULT_EMAILS_SALE_REMOVE or []
    @property
    def system_config_emails_review(self):
        return g.system_config.DEFAULT_EMAILS_SALE_REVIEW or []
    @property
    def system_config_emails_execute(self):
        return g.system_config.DEFAULT_EMAILS_SALE_EXECUTE or []
    @property
    def system_config_emails_payments(self):
        return g.system_config.DEFAULT_EMAILS_SALE_PAYMENTS or []
    @property
    def system_config_emails_audit(self):
        return g.system_config.DEFAULT_EMAILS_SALE_AUDIT or []
    @property
    def system_config_emails_decree(self):
        return g.system_config.DEFAULT_EMAILS_SALE_DECREE or []
    @property
    def system_config_emails_upload(self):
        return g.system_config.DEFAULT_EMAILS_SALE_UPLOAD or []

    #   --------
    #   SETTINGS
    #   --------

    @property
    def is_review_headoffice(self):
        return g.system_config.IsReviewHeadOffice
    @property
    def is_review_with_headoffice(self):
        return 1
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
        return 1
    @property
    def is_decree_with_root(self):
        return 1

    #   -----------

    def get_header(self, name, config='provision-orders'):
        view = self.page_config.get(config) or super().page_config.get(config)
        x = view.get('headers').get(name)
        return x and x[0] or ''

    def database_config(self, name):
        if name in _config:
            return _config[name]

        return super().database_config(name)

    def set_attrs(self, ob, attrs):
        setattr(ob, '_account', getSQLString(attrs.get('order_account')))
        return {
            'Login'         : (0, ob.login, 'Автор заявки',),
            'Subdivision'   : (1, ob._subdivision, 'ПОДРАЗДЕЛЕНИЕ',),
            'Article'       : [2, ob._article, 'Наименование документа',], 
            'Qty'           : (3, ob._qty, 'Количество (шт)',),
            'Purpose'       : [4, ob._purpose, 'Обоснование',],
            'Price'         : (5, ob._price, 'Лимит',),
            'Currency'      : (6, ob._currency, 'Валюта',),
            'Condition'     : (7, ob._condition, 'Условия оплаты'),
            'Seller'        : (8, ob._seller, 'КОНТРАГЕНТ',),
            'SellerTitle'   : (9, ob._seller_title, 'Реквизиты компании',),
            'SellerAddress' : (10, ob._seller_address, 'Адрес',),
            'SellerCode'    : (11, ob._seller_code, 'Код 1C',),
            'SellerContact' : (12, ob._seller_contact, 'Контакты',),
            'Equipment'     : [13, ob._equipment, 'Описание',], 
            'DueDate'       : (14, ob._duedate, 'Срок исполнения',), 
            'Author'        : (15, ob._author, 'Заказчик',), 
            'Category'      : (16, ob._category, 'Категория',),
            'URL'           : (17, ob._url, 'Ссылка на сайте Компании (URL)',),
            'Account'       : [18, ob._account, 'Регистрационный номер',], 
            }

    #   --------
    #   HANDLERS
    #   --------

    def after(self, order):
        order['Status'] = ''

    #   ----------
    #   REFERENCES
    #   ----------

    def ref_reviewers(self):
        reviewers = [(x, self.model_users[x]['full_name']) 
            for x, v in sorted(list(self.model_users.items()), key=lambda k: k[1]['full_name'])]
        return reviewers

    #   --------
    #   STATUSES
    #   --------

    def set_order_facsimile(self, order_id, author, with_error=None):
        return super().set_order_facsimile(order_id, author, with_error=with_error)

    #   ----------------
    #   RENDER DOCUMENTS
    #   ----------------

    def make_current_order_info(self, order_id, info, **kw):
        if info and info.get('stocklist'):
            info['stocklist']['title'] = 'Класс продукции'
        return info

    def access_query(self, args):
        """
            Полномочия пользователя
        """
        aq = ''

        if self.is_owner or not self.is_apply_union:
            pass

        elif self.is_office_direction:
            if not self.is_args and self.is_ceo and not self.is_uncheck_status and not self.no_union:
                aq = ''

        elif self.app_role_ceo:
            pass

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
        self.point('sale.render-start')

        order_id = int(kw.get('order_id') or 0)
        review_id = int(kw.get('review_id') or 0)

        # -----------------------
        # Полномочия пользователя
        # -----------------------

        root = '%s/' % request.script_root

        is_mobile = kw.get('is_mobile')

        self.no_union = get_request_item('no_union') == '1' and True or False

        if IsDeepDebug:
            print('--> current_user:[%s] %s%s%s%s%s%s%s%s%s vip:%s' % (
                self.login, 
                self.is_admin and 1 or 0, 
                self.is_provision_manager and 1 or 0, 
                self.is_payments_manager and 1 or 0, 
                self.is_stock_manager and 1 or 0, 
                self.is_office_direction and 1 or 0, 
                self.is_office_execution and 1 or 0, 
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
        SellerID = args['seller'][1]
        ConditionID = args['condition'][1]
        CategoryID = args['category'][1]

        reviewer = args['reviewer'][1]
        
        default_date_format = DEFAULT_DATE_FORMAT[1]

        self.is_apply_union = self.is_apply_union

        # ----------------
        # SQL Query filter
        # ----------------

        qf = self.args_parser(args, items)

        self.is_args = len(items) > 0

        # ----------------------
        # Скрыть архив + корзину
        # ----------------------

        if not args.get('id')[1] and (not args.get('status')[1] or args['status'][1] < valid_status) and not TID and not self.is_uncheck_status:
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
                'is_auditor' : 0, 
                'is_ceo' : self.is_ceo,
                'is_cao' : self.is_cao,
                'is_cto' : self.is_cto,
                }

        pages = 0
        total_orders = 0
        total_sum = 0

        orders = []
        reviews = []

        selected_row = {}

        # ======================
        # Выборка данных журнала
        # ======================

        self.point('sale.render-1')

        if IsTrace:
            print_to(None, '--> page_%s.render, login:%s, where:%s' % (self.id, self.login, where))

        if self.engine != None:

            # --------------------------------------------------
            # Кол-во записей по запросу в журнале (total_orders)
            # --------------------------------------------------

            cursor = self.runQuery(default_template, columns=('count(*)', 'sum(Qty)',), where=where, distinct=True)
            if cursor:
                total_orders, total_cards = cursor[0]

            if command == 'export':
                top = 10000

            # --------------------------------------
            # Установить максимальный размер журнала
            # --------------------------------------

            if self.is_max_per_page and not get_request_item('per_page'):
                page, per_page = self._get_max_page(per_page_options, total_orders)
                top, offset = self._get_top(per_page, page)

            self.point('sale.render-1.1')

            # ===============
            # Заявки (orders)
            # ===============

            cursor = self.runQuery(default_template, columns=self.default_view['export'], top=top, offset=offset, where=union, order=order, 
                                   distinct=self.distinct, as_dict=True, encode_columns=self._encode_columns)

            self.point('sale.render-1.2')

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

                    if not self._is_no_price:
                        total_sum += self._calc_euro(row.get('Total'), row.get('Currency'))

                    row['Total'] = getCurrency(row.get('Total'), driver=self.driver)
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
                                elif status == 1 and not self.is_ceo:
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
                    row['unread'] = row['UnreadByLogin'] and login in row['UnreadByLogin'] and 'unread' or ''

                    row['AuthorName'] = self._is_no_price and self.user_short_name(row['Author']) or ''
                    row['id'] = row['TID']
                    row['TID'] = '%05d' % row['id']
                    row['RD'] = self._get_date(row['RD'])

                    if row['SellerID']:
                        row['Seller'] = self._get_seller_link(row, locator=default_locator)
                        row['classes']['Seller'] += ' link'

                    g.page.after(row)

                    if row['unread'] and not self.is_search_order:
                        row['title']['Article'] = gettext('Contains unread information')
                        orders.insert(unreads, row)
                        unreads += 1
                    else:
                        orders.append(row)

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

            self.point('sale.render-1.3')

            # ======================
            # Согласования (reviews)
            # ======================

            if order_id:
                reviews, review_id = self._get_reviews(order_id, review_id=review_id, reviewer=reviewer)

            self.point('sale.render-1.4')

        # -----------------------------------------------------------
        # Справочники фильтра запросов (sellers, reviewers, statuses)
        # -----------------------------------------------------------
        
        stocks = self.ref_stocks()
        subdivisions = self.ref_subdivisions()
        categories = self.ref_categories()
        sellers = self.ref_sellers()
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

        self.point('sale.render-2')

        paids = [(0, DEFAULT_UNDEFINED,), ('U', 'не обработано',), ('N', 'не оплачено',), ('Y', 'оплачено',)]

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

        modes = [(n, self.default_view['headers'][x][0]) for n, x in enumerate(self.default_view['sorted'])]
        sorted_by = self.default_view['headers'][self.default_view['sorted'][current_sort]]

        pagination = {
            'total'             : '%s / %s' % (total_orders, getCurrency(total_sum, driver=self.driver) or '0.00'), # EUR[€]
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
            'columns'           : 'columns',
            'pagination'        : pagination,
            'orders'            : orders,
            'reviews'           : reviews,
            'stocks'            : stocks,
            'subdivisions'      : subdivisions,
            'authors'           : authors,
            'sellers'           : sellers,
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
            'search'            : search or '',
            'order_statuses'    : ':'.join(self.order_statuses),
            'total_selected'    : '0 | 0.00',
        })

        if g.system_config.IsActiveScroller and kw.get('is_active_scroller'):
            kw['is_active_scroller'] = 0 if len(orders) > g.system_config.IsActiveScroller else 1

        self.point('sale.render-finish')

        return kw

    #   ---------
    #   SCHEDULES
    #   ---------

    def schedule_params(self):
        """
            Schedule items count: rows, columns
        """
        return {'documents' : (7, 4), 'decrees' : (6, 5)}

    def make_schedule_document_status(self, key):
        #
        # Schedule statuses: [[<id>, <title>, <classes>], ... ]
        #
        status = (
            key == 'work' and [
                ['on-work', 'Проекты документов', ''], 
                ['on-archive', 'В архиве', ''], 
                ['on-removed', 'Корзина', ''], 
                ['total-orders', 'Всего документов', ''],
                ] or 
            key == 'review' and [
                ['on-review', 'На согласовании', ''], 
                ['on-review-done', 'Согласование проведено', 'reviewed done'], 
                ['on-review-wait', 'Ожидают согласования', 'review-wait wait'],
                ] or 
            key == 'accepted' and [
                ['on-accepted', 'Согласовано', ''], 
                ['on-finish-done', 'Согласовано, Оплачено и Исполнено', 'executed done'],
                ['on-finish-wait', 'Ожидают исполнения', 'executed-wait wait'],
                ['on-finish-out', 'Обратите внимание! Документы вне исполнения (согласованы, но перенесены в архив или удалены)', 'autoclosed'],
                ] or 
            key == 'rejected' and [
                ['on-rejected', 'Отказано', ''], 
                None, 
                None,
                ] or 
            key == 'confirm' and [
                ['on-confirm', 'Документы, по которым требуется дополнительное обоснование', ''], 
                ['on-confirmed-done', 'Обоснование представлено', 'confirmed done'], 
                ['on-confirmed-wait', 'Ожидают обоснования (информация не представлена)', 'confirm-wait wait'],
                ] or 
            key == 'paid' and [
                ['on-execute', 'На исполнении', ''], 
                ['on-paid-done', 'Оплачено', 'paid done'], 
                ['on-paid-wait', 'Ожидают оплаты', 'paid-wait wait'],
                ] or 
            key == 'finish' and [
                ['on-finish', 'Действующие документы', ''], 
                ] or 
            None
            )

        return status

    def getTabDocumentsSchedule(self, params, attrs, templates):
        """
            Регламент согласования (документы)
        """
        data = {}

        self.point('schedule.documents-start')

        login = g.current_user.login

        command = params.get('command')
        per_page = params.get('per_page') or 10
        view = self._views['schedule']
        columns = self.database_config(view)['export']

        kw = {}

        where, order, args, permissions = attrs

        is_private = not (permissions['is_ceo'] or permissions['is_auditor'] or permissions['is_admin'])

        for column in [('TID', 'OrderID'), ('Status', 'OrderStatus'),]:
            where = where.replace(column[0], column[1])

        order = 'OrderID, ReviewID'
    
        cursor = self.runQuery(view, columns=columns, where=where, order=order, as_dict=True) or []

        if IsTrace:
            print_to(errorlog, '-->  schedule documents:%s %s, where:%s, cursor:%s' % (
                command, login, where, cursor and len(cursor) or 0
                ))

        data['total-orders'] = 0

        order_users = None

        def _is_login():
            return order_users and (login in order_users.get('chiefs') or login in order_users.get('managers')) and True or False

        ids, orders, reviews, done_action_list = [], [], [], []
        #
        # Schedule values: 
        #   <ids>   -- status ids, [<id>, ... ]
        #   <data>  -- schedule values, {<id> : 0}
        #   <id>    -- schedule id, 'on-<status>{-<done|wait|out>}'
        #
        for template in templates:
            for item in template[2]:
                id = item[0][0]
                ids.append(id)
                data[id] = 0
        
                if id.endswith('done'):
                    done_action_list.append(id)
        #
        # Schedule current user permissions menu:
        #   <done_action_list>  -- status done id list, [<id>] - list of <id>
        #   <done_action>       -- status done flags, {<id> : -1|0|1
        #
        def _make_done_action(order_status):
            done_action = {}
            current_status = self.default_statuses.get(order_status)

            for id in done_action_list:
                # Согласование
                if id == 'on-review-done':
                    if is_private:
                        if not (_is_login() and current_status == 'work'):
                            continue
                    elif current_status != 'review':
                        continue
                # Обоснование
                elif id == 'on-confirmed-done':
                    if current_status != 'confirm':
                        continue
                    """
                    elif not order_users:
                        pass
                    elif login in order_users['chiefs']:
                        pass
                    elif login in order_users['managers']:
                        pass
                    else:
                        continue
                    """
                # Исполнение
                elif id == 'on-execute-done':
                    if current_status != 'execute':
                        continue
                # Оплата
                elif id == 'on-paid-done':
                    if current_status != 'execute':
                        continue
                # Поставка на склад
                elif id == 'on-delivered-done':
                    if current_status != 'finish':
                        continue
                # На контроле исполнения
                elif id == 'on-finish-done':
                    pass
                # Автозакрытие
                elif id == 'on-autoclosed-done':
                    if current_status != 'finish':
                        continue
                else:
                    continue

                done_action[id] = -1

            return done_action

        key, id, order_status, review_status, order_id = '', '', 0, 0, 0
        #
        # Order statuses: {<id> : <order_status>}
        #
        statuses = {}
        #
        # Review statuses: {<review_status> : (<key>, <order_status>, <id>}, <review_status>=<x.y>, x - order status, y - review status
        #
        provision_review_statuses = self.sub_statuses

        order, done_action, on_autoclosed, schedules, audit = None, {}, -1, {}, []

        is_approved = is_rejected = is_paid = is_delivered = False

        def _add(key, id):
            if key not in schedules:
                schedules[key] = []
            schedules[key].append(str(id))
            data[key] += 1

        today = getToday()

        # ---------------------------
        # Конвертация данных (Mazars) 
        # ---------------------------

        cdate_20210601 = getDate('2021-07-01', format=LOCAL_EASY_DATESTAMP, is_date=1)

        def _check_wait(review):
            #
            # Set Wait key
            #
            if order_id and (not review or order_id != review['OrderID']): # and review_status is not None
                for action in done_action:
                    if action == 'on-autoclosed-done':
                        continue
                    key = '-'.join(action.split('-')[:-1])
                    wait_key, out_key = '%s-wait' % key, '%s-out' % key
                    if done_action[action] != 1:
                        if on_autoclosed:
                            pass
                        elif action == 'on-finish-done':
                            if is_approved and not is_rejected:
                                if order_status in (7,9):
                                    _add(out_key, order_id)
                                elif order_status not in (2,3,4) and not (is_paid and is_delivered):
                                    _add(wait_key, order_id)
                        elif wait_key in data:
                            if is_private and order_status == 0 and key == 'on-review':
                                if _is_login():
                                    _add(wait_key, order_id)
                            else:
                                data[wait_key] += 1

                if is_audit:
                    if not audit:
                        pass
                    elif audit[-1] == self.provision_review_statuses['validated']:
                        _add('on-validated', order_id)
                    elif audit[-1] == self.provision_review_statuses['failure']:
                        _add('on-failure', order_id)
                    else:
                        _add('on-audit-out', order_id)

        for review in cursor:
            _check_wait(review)
            #
            # Check new order item started
            #
            if review['OrderID'] not in orders:
                order = review
                order_id = order['OrderID']
                order_status = order['OrderStatus']
                on_autoclosed = 0

                is_approved = order['Approved'] and True or False
                is_rejected = False
                is_paid = order['Paid'] and True or False
                is_delivered = order['Delivered'] and True or False
                is_audit = order['AuditDate'] and True or False

                s = self.default_statuses.get(order_status)

                order_users = None

                if s in ('review', 'confirm',):
                    pass

                elif is_private and s == 'work':
                    order_users = g.instance.send_order_notifications(order_id, check_only=True, order=order)

                    if IsDeepDebug:
                        print('-> getTabSchedule.order_users:', order_id, len(cursor), order_users)

                done_action = _make_done_action(order_status)

                data['total-orders'] += 1
    
                key = self.default_statuses[order_status]

                id = self.provision_statuses[key][1]

                if id not in statuses:
                    statuses[id] = order_status

                if order['CategoryID'] in (4,) and order_status in (2,5,):
                    _add('on-autopaid', order_id)

                if order_status == 0 and order['FinishDueDate'] and today > order['FinishDueDate']:
                    _add('on-review-out', order_id)

                audit = []

                if is_audit:
                    data['on-audit'] += 1

                data[id] += 1

                orders.append(order_id)

            review_status = review['ReviewStatus']
            #
            # Decree items
            #
            if review_status == self.provision_review_statuses['decree']:
                pass
            #
            # Set Done key
            #
            elif review_status is not None:
                if order['Approved'] and order['Created'] < cdate_20210601 and order_status == _provision_statuses['finish'] and review_status == self.provision_review_statuses['paid']:
                    order_status, review_status = _provision_statuses['finish'], self.provision_review_statuses['validated']

                s = '%s.%s' % (order_status, review_status)

                if review['Reviewer'] == CEO_LOGIN:
                    if self.is_review_status(review_status, 'accept'):
                        is_rejected = False
                    elif self.is_review_status(review_status, 'reject'):
                        is_rejected = True

                if s in provision_review_statuses:
                    status = provision_review_statuses[s][2]
                    done_key = '%s-done' % status
                    if done_key in done_action:
                        if done_action[done_key] != 1:
                            done = True
                            if not status:
                                continue
                            elif status == 'on-confirmed' and done_action[done_key] == 0:
                                pass
                            elif status == 'on-paid':
                                pass
                            elif status == 'on-finish' and is_approved and is_delivered:
                                pass
                            elif status == 'on-delivered':
                                pass
                            elif status == 'on-autoclosed':
                                on_autoclosed = 1
                            else:
                                done = False

                            if done:
                                done_action[done_key] = 1
                                data[done_key] += 1

                    elif status in ('on-accepted', 'on-rejected'):
                        pass
                    elif status == 'on-confirm':
                        done_action['on-confirmed-done'] = 0
                    elif status == 'on-work':
                        pass

                    if is_audit:
                        if review_status in (
                            self.provision_review_statuses['audit'],
                            self.provision_review_statuses['failure'],
                            self.provision_review_statuses['validated']):
                            audit.append(review_status)

                if is_private:
                    if order_status == 0 and login == review['Reviewer'] and _is_login():
                        done_key = 'on-review-done'
                        if review_status < 5 and done_action[done_key] != 1:
                            done_action[done_key] = 1
                            _add(done_key, order_id)

        _check_wait(None)

        args = {
            'per_page' : '?per_page=%s' % per_page,
            'no_union' : '&no_union=1',
            'page'     : self.id,
        }

        for id in ids:
            args.update({
                'status'     : '',
                'review'     : '',
                'confirmed'  : '',
                'paid'       : '',
                'delivered'  : '',
                'audit'      : '',
                'failure'    : '',
                'validated'  : '',
                'audit-out'  : '',
                'finish'     : '',
                'autopaid'   : '',
                'autoclosed' : '',
                'data'       : data[id],
            })

            if id == 'total-orders':
                args['status'] = '&status=10'
            elif is_private and id in ('on-review-done', 'on-review-wait') and id in schedules:
                args['review'] = '&_ids=%s' % ':'.join(schedules[id])
            elif id in statuses:
                args['status'] = '&status=%s' % statuses[id]
            elif id == 'on-confirmed-done':
                args['confirmed'] = '&confirmed=Y'
            elif id == 'on-confirmed-wait':
                args['confirmed'] = '&confirmed=N'
            elif id == 'on-paid-done':
                args['paid'] = '&paid=Y'
            elif id == 'on-paid-wait':
                args['paid'] = '&paid=N'
            elif id == 'on-delivered-done':
                args['delivered'] = '&delivered=Y'
            elif id == 'on-delivered-wait':
                args['delivered'] = '&delivered=N'
            elif id == 'on-audit':
                args['audit'] = '&audit=Y'
            elif id == 'on-validated' and id in schedules:
                args['validated'] = '&_ids=%s' % ':'.join(schedules[id])
            elif id == 'on-failure' and id in schedules:
                args['failure'] = '&_ids=%s' % ':'.join(schedules[id])
            elif id == 'on-audit-out' and id in schedules:
                args['audit-out'] = '&_ids=%s' % ':'.join(schedules[id])
            elif id == 'on-finish-done':
                args['finish'] = '&finish=Y'
            elif id in ('on-finish-wait', 'on-finish-out', 'on-review-out') and id in schedules:
                args['finish'] = '&_ids=%s' % ':'.join(schedules[id])
            elif id == 'on-autopaid' and id in schedules:
                args['autopaid'] = '&_ids=%s' % ':'.join(schedules[id])
            elif id == 'on-autoclosed-done':
                args['autoclosed'] = '&autoclosed=Y'
            else:
                data[id] = '<div class="no-value">%(data)s</div>' % args
                continue

            data[id] = '<a target="_blank" href="/%(page)s%(per_page)s%(no_union)s%(status)s%(review)s%(confirmed)s%(paid)s%(delivered)s%(audit)s%(validated)s%(failure)s%(audit-out)s%(finish)s%(autopaid)s%(autoclosed)s">%(data)s</a>' % args

        self.point('schedule.documents-finish')

        return data, ids


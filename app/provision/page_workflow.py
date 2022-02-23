# -*- coding: utf-8 -*-

from ..settings import *
from ..models import User
from ..utils import (
     normpath, getToday, getDate, getDateOnly, checkDate, spent_time, makeSearchQuery, getString, getSQLString, getHtmlString,
     checkPaginationRange, Capitalize, unCapitalize, cleanHtml
     )

from .page_default import PageDefault

##  ==================
##  PageWorkflow Model
##  ==================

default_page = 'provision'
default_locator = 'workflow'
default_template = 'provision-orders'

_PAGE_LINK = ('%sworkflow', '?sidebar=0',)

##  ==========================
##  PageDefault Class Statuses
##  ==========================

_default_statuses = dict(zip([0,1,2,3,4,7,9], ['work', 'review', 'accepted', 'rejected', 'confirm', 'archive', 'removed']))

_PROVISION_STATUSES = {
    'work'       : (0, 'on-work', 'в работе', '', 'в работе (проект документа)'),
    'review'     : (1, 'on-review', 'на подписи', '', 'на подписи'),
    'accepted'   : (2, 'on-accepted', 'утверждено', '2.2', 'документ утвержден (действует)'),
    'rejected'   : (3, 'on-rejected', 'отказано', '3.3', 'на подписи = отказано'),
    'confirm'    : (4, 'on-confirm', 'требуется обоснование', '4.4', 'на подписи = требуется обоснование'),
    'confirmed'  : (4, 'on-confirmed', 'обоснование представлено', '4.5', 'на подписи = обоснование представлено'),
    'finish'     : (6, 'on-finish', 'отменено', '6.6', 'действие отменено'),
    'archive'    : (7, 'on-archive', 'в архиве', '', 'в архиве'),
    'x1'         : (8, None, '', '', ''),
    'removed'    : (9, 'on-removed', 'корзина', '', 'корзина'),
}

_provision_statuses = dict([(x[1], x[0]) for x in _default_statuses.items()])

_PROVISION_SUB_STATUSES = dict([(x[1][3], (x[0], x[1][0], x[1][1],)) for x in _PROVISION_STATUSES.items() if x[1][3]])

_PROVISION_REVIEW_STATUSES = {
     1 : ('', '...'),
     2 : ('accept', 'подписано'),
     3 : ('reject', 'отказано'),
     4 : ('confirm', 'требуется обоснование'),
     5 : ('confirmation', 'информация'),
     6 : ('finish', 'отменено'),
     9 : ('decree', 'поручение'),
}

_provision_review_statuses = dict([(x[1][0], x[0]) for x in _PROVISION_REVIEW_STATUSES.items()])

valid_status = 7
valid_payment_status = 5

_schedule_keys = ('documents', 'decrees')

_ACCOUNT_SPLITTER = '/'

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
  <h1 class="center">Организационно-распорядительный документ</h1>
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
  <h1 class="center">Организационно-распорядительный документ</h1>
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
    <div class="title">Запрос на согласование организационно-распорядительного документа. %(Reviewer)s</div>
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
        'columns' : ['TID', 'Article', 'Account', 'Subdivision', 'Category', 'Status', 'RD',],
        'noprice' : None,
        'disable' : ['Account', 'Author', 'Article', 'Qty', 'Subdivision'],
        'view'    : '[dbo].[WEB_Orders_vw]',
        'headers' : { 
            'TID'          : ('ID документа',           'npp',          '', ''),
            'Article'      : ('НАИМЕНОВАНИЕ ДОКУМЕНТА', 'article',      '', ''),
            'Activity'     : ('Вид деятельности',       '',             '', ''),
            'Author'       : ('Автор документа',        '',             '', ''),
            'Category'     : ('Категория',              'category',     '', ''),
            'Purpose'      : ('СОДЕРЖАНИЕ',             '',             '', ''),
            'Report'       : ('Отчет о выполнении поручения', '',       '', ''),
            'Subdivision'  : ('ПОДРАЗДЕЛЕНИЕ',          'office',       '', ''),
            'Equipment'    : ('ФИО руководителя',       '',             '', ''),
            'Account'      : ('Регистрационный номер',  'account',      'nowrap', ''),
            'Status'       : ('',                       'status',       's1 nowrap', 'Статус документа'),
            'ReviewStatus' : ('Статус документа',       '',             '', ''),
            'RD'           : ('Дата',                   'rd',           '', ''),
            # Extra application headers
            'num'          : ('Номер документа',        '',             '', ''),
            'StockName'    : ('Класс документа',        '',             '', ''),
            'OrderDate'    : ('Дата',                   '',             '', ''),
            'FinishDueDate': ('Срок ввода в действие',  '',             '', ''),
        },
        'export'  : (
            'TID', 'ActivityID', 'SubdivisionID', 'EquipmentID', 'CategoryID', 'StockListID', 'Author', 'Account', 'Article', 'Purpose', 'Activity', 'Subdivision', 'SubdivisionCode', 'Equipment', 'Category', 'Status', 'ReviewStatus', 'ReviewStatuses', 'SubdivisionCode', 'StockListNodeCode', 'UnreadByLogin', 'EditedBy', 'Created', 'Approved', 'ReviewDueDate', 'FinishDueDate', 'Facsimile', 'MD', 'RD',
            ),
        'status'  : (),
        'updated' : ('ActivityID', 'SubdivisionID', 'CategoryID', 'Author', 'Article', 'Account', 'Equipment', 'Purpose', 'EditedBy'),
        'sorted'  : ('TID', 'Subdivision', 'Article', 'Account', 'Activity', 'Category', 'Status', 'RD',),
        'money'   : (),
    },
    'provision-activities' : { 
        'columns' : ('TID', 'Name',),
        'view'    : '[dbo].[WEB_Activities_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'Name'         : 'Вид деятельности',
        },
        'export'  : ('TID', 'Name', 'Code',),
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
    'provision-register-order' : { 
        'params'  : "0,'%(login)s','%(article)s','%(purpose)s','%(activity)s','%(subdivision)s','%(category)s','%(equipment)s','%(account)s','%(duedate)s','%(author)s',%(status)s,%(model)s,null",
        'args'    : "%d,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',%d,%d,null",
        'exec'    : '[dbo].[REGISTER_Order_sp]',
    },
    'provision-refresh-order' : { 
        'params'  : "0,%(id)d,'%(login)s','%(article)s','%(purpose)s','%(activity)s','%(subdivision)s','%(category)s','%(equipment)s','%(account)s','%(duedate)s','%(author)s',%(model)s,null",
        'exec'    : '[dbo].[UPDATE_Order_sp]',
    },
    'provision-schedule' : { 
        'columns' : (),
        'view'    : '[dbo].[WEB_Schedule_vw]',
        'export'  : (
            'OrderID', 'ReviewID', 'SubdivisionID', 'CategoryID', 
            'Author', 'Reviewer', 'SubdivisionCode', 
            'OrderStatus', 'ReviewStatus', 
            'Created', 'Approved', 'ReviewDueDate', 'StatusDate', 'RegistryDate',
            ),
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
            'activity'    : ['ActivityID', int(_get_item('activity') or '0')],
            'category'    : ['CategoryID', int(_get_item('category') or '0')],
            'date_from'   : ['RD', _get_item('date_from') or ''],
            'date_to'     : ['RD', _get_item('date_to') or ''],
            'status'      : ['Status', _get_item('status', check_int=True)],
            'reviewer'    : ['Reviewer', _get_item('reviewer') or ''],
            'confirmed'   : ['ReviewStatuses', _get_item('confirmed') or ''],
            'id'          : ['TID', _get_item('_id', check_int=True)],
            'ids'         : ['TID', get_request_item('_ids')],
        })
    except:
        args.update({
            'stock'       : ['StockListID', 0],
            'subdivision' : ['SubdivisionID', 0],
            'author'      : ['Author', ''],
            'activity'    : ['ActivityID', 0],
            'category'    : ['CategoryID', 0],
            'date_from'   : ['RD', ''],
            'date_to'     : ['RD', ''],
            'status'      : ['Status', None],
            'reviewer'    : ['Reviewer', ''],
            'confirmed'   : ['ReviewStatus', ''],
            'id'          : ['TID', None],
            'ids'         : ['TID', None],
        })
        flash('Please, update the page by Ctrl-F5!')

    return args


## ==================================================== ##


class PageWorkflow(PageDefault):

    def __init__(self, id, name, title, caption, **kw):
        if IsDeepDebug:
            print('PageWorkflow init')

        super().__init__(id, name, title, caption, **kw)

        self._model = 30
        self._distinct = True

    def _init_state(self, engine, attrs=None, factory=None, *args, **kwargs):
        if IsDeepDebug:
            print('PageWorkflow initstate')

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
    @property
    def object_types(self):
        return ('документ', 'документы', 'документов')

    @staticmethod
    def get_review_alarm_caption(status, order_status):
        return order_status > 4 and 'об исполнении' or 'о согласовании'
    @staticmethod
    def get_review_alarm_title(status, order_status):
        return status == 5 and 'Обоснование по организационно-распорядительному документу' or 'Информация %s организационно-распорядительного документа' % (
               status == 7 and 'об исполнении' or 
               status == 6 and 'об оплате' or 
               status == 9 and 'к исполнению' or 
               'о согласовании'
               )

    #   -----------
    #   PERMISSIONS
    #   -----------

    def _permissions(self):
        super()._permissions()

    def is_disabled_accept(self, ob=None):
        if ob is None:
            ob = g.requested_object
        status = ob.get('Status') or 0
        category = ob.get('CategoryID') or 0
        if status not in (self.statuses['review'], self.statuses['confirm']):
            return True
        elif category == 1 and not self.is_order_author(ob):
            return True
        elif not (g.current_user.app_is_consultant or g.current_user.app_is_office_manager):
            return True
        return False

    #   -----------

    @property
    def locator(self):
        return default_locator
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
        return ('Status',)
    @property
    def is_page_manager(self):
        return (self.is_owner or self.is_workflow_manager) and True or False
    @property
    def page_config(self):
        return _config
    @property
    def page_link(self):
        return _PAGE_LINK
    @property
    def order_tag_restrictions(self):
        return (0,1,2,4,13,14,16,19)

    #   -----------------------
    #   OVERIDDEN SYSTEM CONFIG
    #   -----------------------

    @property
    def system_config_emails_approval(self):
        return g.system_config.DEFAULT_EMAILS_WORKFLOW_APPROVAL or []
    @property
    def system_config_emails_create(self):
        return g.system_config.DEFAULT_EMAILS_WORKFLOW_CREATE or []
    @property
    def system_config_emails_remove(self):
        return g.system_config.DEFAULT_EMAILS_WORKFLOW_REMOVE or []
    @property
    def system_config_emails_review(self):
        return g.system_config.DEFAULT_EMAILS_WORKFLOW_REVIEW or []
    @property
    def system_config_emails_execute(self):
        return g.system_config.DEFAULT_EMAILS_WORKFLOW_EXECUTE or []
    @property
    def system_config_emails_payments(self):
        return g.system_config.DEFAULT_EMAILS_WORKFLOW_PAYMENTS or []
    @property
    def system_config_emails_audit(self):
        return g.system_config.DEFAULT_EMAILS_WORKFLOW_AUDIT or []
    @property
    def system_config_emails_decree(self):
        return g.system_config.DEFAULT_EMAILS_WORKFLOW_DECREE or []
    @property
    def system_config_emails_upload(self):
        return g.system_config.DEFAULT_EMAILS_WORKFLOW_UPLOAD or []

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

    #   -----------

    def get_header(self, name, config='provision-orders'):
        view = self.page_config.get(config) or super().page_config.get(config)
        x = view.get('headers').get(name)
        return x and x[0] or ''

    def database_config(self, name):
        if name in _config:
            return _config[name]

        return super().database_config(name)

    def get_attrs(self, ob, attrs):
        #print('get_attrs:workflow')

        ob._equipment = getString(attrs.get('order_equipment'), with_html=False)
        ob._purpose = getString(attrs.get('order_purpose'), save_links=True, with_html=False)

        activity_new = cleanHtml(getString(attrs.get('new_order_activity'), is_clean=True))
        activity = ob.combo_value('order_activity', attrs, self._get_activity, '')

        #print('activity:', '[%s]' % activity, attrs)

        ob._activity = activity

    def set_attrs(self, ob, attrs):
        ob._account = getSQLString(attrs.get('order_account'))
        return {
            'Login'         : (0, ob.login, 'Автор документа',),
            'Subdivision'   : (1, ob._subdivision, 'ПОДРАЗДЕЛЕНИЕ',),
            'Article'       : [2, ob._article, 'Наименование документа',], 
            'Qty'           : (3, ob._qty, 'Количество (шт)',),
            'Purpose'       : [4, ob._purpose, 'СОДЕРЖАНИЕ',],
            'Price'         : (5, ob._price, 'Лимит',),
            'Currency'      : (6, ob._currency, 'Валюта',),
            'Condition'     : (7, ob._condition, 'Условия оплаты'),
            'Seller'        : (8, ob._seller, 'КОНТРАГЕНТ',),
            'SellerTitle'   : (9, ob._seller_title, 'Реквизиты компании',),
            'SellerAddress' : (10, ob._seller_address, 'Адрес',),
            'SellerCode'    : (11, ob._seller_code, 'Код 1C',),
            'SellerContact' : (12, ob._seller_contact, 'Контакты',),
            'Equipment'     : [13, ob._equipment, 'ФИО руководителя',], 
            'DueDate'       : (14, ob._duedate, 'Срок ввода в действие',), 
            'Author'        : (15, ob._author, 'Заказчик',), 
            'Category'      : (16, ob._category, 'Категория документа',),
            'URL'           : (17, ob._url, 'Ссылка на сайте Компании (URL)',),
            'Account'       : [18, ob._account, 'Регистрационный номер',], 
            'Activity'      : [19, ob._activity, 'Вид деятельности',], 
            }

    def set_order(self, ob, attrs, **kw):
        if ob._account:
            return

        account = ''

        columns = ['max(Account)']
        where = "CategoryID=%s" % ob._category_id

        num = '0'

        def _get_number(value):
            x = value
            m = re.match(r'(\w-)?(\d+)(/\w*)?', value)
            if m and len(m.groups()) > 1:
                x = m.group(2)
            return (x.isdigit() and int(x) or 0) + 1

        def _get_code(activity):
            return ''.join([x[0].upper() for x in activity.split(' ')])

        cursor = self._get_orders(columns=columns, where=where, as_dict=False)
        if cursor:
            x = cursor[0][0]
            if x:
                num = (_ACCOUNT_SPLITTER in x and x.split(_ACCOUNT_SPLITTER) or x.split(' '))[0]
        else:
            pass

        rdate = getDate(getToday(), format=DEFAULT_DATETIME_TODAY_FORMAT)

        if ob._category_id == 1:
            account = 'П-%02d/%s от %s г. Краснознаменск' % (_get_number(num), _get_code(ob._activity),  rdate)
        elif ob._category_id == 2:
            account = 'Р-%03d/%s от %s г. Краснознаменск' % (_get_number(num), _get_code(ob._activity),  rdate)
        else:
            account = '%05d/%s от %s' % (_get_number(num), _get_code(ob._activity), rdate)

        #print(account)

        ob._account = account

    def get_dates(self):
        return { 
            'Created'       : [1, 'Дата создания', ''],
            'ReviewDueDate' : [2, 'Дата согласования', ''],
            'Approved'      : [3, 'Дата ввода в действие', ''],
            'Finish'        : [4, 'Дата отмены', ''],
        }

    #   --------
    #   STATUSES
    #   --------

    @property
    def default_statuses(self):
        return _default_statuses
    @property
    def statuses(self):
        # ID by Key
        return _provision_statuses
    @property
    def provision_statuses(self):
        # By Key
        return _PROVISION_STATUSES
    @property
    def sub_statuses(self):
        # By complex id: <status ID>:<review_status ID>
        return _PROVISION_SUB_STATUSES
    @property
    def review_statuses(self):
        # By ID
        return _PROVISION_REVIEW_STATUSES
    @property
    def provision_review_statuses(self):
        # By Key
        return _provision_review_statuses
    @property
    def order_statuses(self):
        return tuple(sorted(set(list(self.provision_statuses.keys()) + list(self.provision_review_statuses.keys()))))

    def get_review_status(self, value, is_title=None):
        ob = g.requested_object
        category_id = ob.get('CategoryID') or 0
        if is_title and value == self.provision_review_statuses['accept']:
            return (category_id == 1 or self.is_order_author(ob)) and 'ПОДПИСАНО' or 'СОГЛАСОВАНО'
        return value in self.review_statuses and self.review_statuses[value][is_title and 1 or 0].upper() or ''

    def set_order_facsimile(self, order_id, author, with_error=None):
        return super().set_order_facsimile(order_id, author, with_error=with_error)

    #   --------
    #   HANDLERS
    #   --------

    def after(self, order):
        order['Status'] = ''

    def is_disabled_review(self, ob=None):
        if ob is None:
            ob = g.requested_object
        category_id = ob.get('CategoryID') or 0
        return category_id == 1

    #   ----------
    #   REFERENCES
    #   ----------

    def ref_activities(self):
        activities = [(0, DEFAULT_UNDEFINED,)]
        cursor = self.runQuery(self._views['activities'], order='Name', distinct=True, encode_columns=(1,))
        activities += [(x[0], x[1]) for x in cursor if x[1]]
        return activities

    def ref_reviewers(self):
        reviewers = [(x, self.model_users[x]['full_name']) 
            for x, v in sorted(list(self.model_users.items()), key=lambda k: k[1]['full_name'])]
        return reviewers

    #   ----------------
    #   RENDER DOCUMENTS
    #   ----------------

    def make_current_order_info(self, order_id, info, **kw):
        info['params'] = {
            'purpose'         : 'СОДЕРЖАНИЕ',
            'equipment_title' : 'Руководитель',
            'with_cross'      : 0,
        }
        if info and info.get('stocklist'):
            info['stocklist']['title'] = ''

        order = kw.get('order')

        if not order or order['TID'] != order_id:
            return info

        info['activity'] = order.get('Activity')
        info['edited_by'] = info['edited_by'].replace('Заказчик', 'Автор документа')

        where = "OrderID=%s and MD=%s" % (order_id, g.page.model)

        cursor = self.runQuery(self._views['order-documents'], where=where, as_dict=True, engine=g.storage)
        if cursor:
            info['documents'] = 1;

        if order.get('CategoryID', 999):
            info['blank'] = 1;

        return info

    def make_blank(self, ob=None, params=None):
        if ob is None:
            ob = g.requested_object

        order_id = ob['TID']

        status = ob.get('Status') or 0
        author = ob.get('Author') or ''
        category_id = ob.get('CategoryID') or 0
        category = ob.get('Category') or ''
        account = ob.get('Account') or ''
        article = ob.get('Article') or ''
        purpose = ob.get('Purpose') or ''
        equipment = ob.get('Equipment') or ''
        approved = ob.get('Approved') or None

        date = location = number = title = preface = post = person = ''

        # П-04/Д от 22.10.2021 г. Краснознаменск
        # Об организации делопроизводства в АО «РОЗАН ФАЙНЭНС»
        # Генеральный директор АО «РОЗАН ФАЙНЭНС» О.У. Айбазов.
        # В целях роста корпоративной делопроизводственной культуры, обеспечения сохранности производственной документации, повышения исполнительской дисциплины внедрить в повседневную жизнедеятельность Компании автоматизированные технологии ведения делопроизводства.
        # Обязанности по организации работ возложить на Управляющего директора Яковицкого В.В.

        category = category.upper()

        x = account.split(' ')
        if len(x) > 2:
            date = x[2]
            location = len(x) > 4 and '%s %s' % (x[3], x[4]) or 'г. Краснознаменск'
            number = x[0]

        title = article

        preface, content, other, part = [], [], [], 1

        _is_body = 0
        _is_other = 0
        _is_signer = 0

        lines = purpose.split('\n')
        signer = re.sub(r'\n', ' ', equipment).split(' ')

        for line in lines:
            if not line:
                continue
            if line.startswith('-----'):
                part += 1
                continue
            if category_id in (1,2):
                if not preface:
                    preface.append(getHtmlString(line, save_links=True))
                    continue
                elif not _is_body:
                    if 'ПРИКАЗЫВАЮ' in line.upper():
                        _is_body = 1
                        continue
                    elif category_id > 1:
                        _is_body = 1
            else:
                if part == 1:
                    preface.append(getHtmlString(line, save_links=True))
                    continue
                elif part == 2:
                    _is_body = 1
                    _is_other = 0
                elif part == 3:
                    _is_body = 0
                    _is_other = 1

            if _is_body or _is_other:
                if not _is_signer:
                    words = line.split(' ')
                    for i, s in enumerate(signer):
                        if s in words and i == words.index(s):
                            if i > 3:
                                _is_signer = 1
                                if category_id in (1,2):
                                    _is_other = 1 
                                break
                        elif i == 0:
                            break
                    if _is_signer:
                        continue

                if _is_other:
                    other.append('<pre>%s</pre>' % getHtmlString(line, save_links=True))
                else:
                    content.append('<p>%s</p>' % line.strip())

        user = User.get_by_login(author)
        if user is not None:
            post = re.sub(r'\"(.*)\"', r'«\1»', user.post)
            person = user.short_name(is_back=True)

        facsimile = ob.get('Facsimile')

        template = 'a4-c%s' % category_id

        info = {
            'category'  : category,
            'date'      : date,
            'location'  : location,
            'number'    : number,
            'title'     : article,
            'preface'   : '<br>'.join(preface),
            'content'   : '\n'.join(content),
            'other'     : '\n'.join(other),
            'post'      : post,
            'facsimile' : facsimile,
            'signing'   : facsimile and 'with_signing' or '',
            'person'    : person,
            'template'  : template,
        }

        return info

    def access_query(self, args):
        """
            Полномочия пользователя
        """
        aq = ''

        if self.is_owner or not self.is_apply_union:
            pass

        elif self.is_office_direction:
            pass

        elif self.is_workflow_manager:
            pass

        elif args and args.get('id')[1]:
            self.is_search_order = True

        #elif not self.is_provision_manager:
        #    aq = self.subdivision_documents()

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
        self.point('workflow.render-start')

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
        SellerID = None
        ConditionID = None
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

        self.point('workflow.render-1')

        if IsTrace:
            print_to(None, '--> page_%s.render, login:%s, where:%s' % (self.id, self.login, where))

        if self.engine != None:

            # --------------------------------------------------
            # Кол-во записей по запросу в журнале (total_orders)
            # --------------------------------------------------

            cursor = self.runQuery(default_template, columns=('count(*)',), where=where, distinct=True)
            if cursor:
                total_orders = cursor[0][0]
                total_cards = 0

            if command == 'export':
                top = 10000

            # --------------------------------------
            # Установить максимальный размер журнала
            # --------------------------------------

            if self.is_max_per_page and not get_request_item('per_page'):
                page, per_page = self._get_max_page(per_page_options, total_orders)
                top, offset = self._get_top(per_page, page)

            self.point('workflow.render-1.1')

            # ==================
            # Документы (orders)
            # ==================

            cursor = self.runQuery(default_template, columns=self.default_view['export'], top=top, offset=offset, where=union, order=order, 
                                   distinct=self.distinct, as_dict=True, encode_columns=self._encode_columns)

            self.point('workflow.render-1.2')

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

                        row['classes'][column] = ' '.join([x for x in classes if x])

                    row['title']['TID'] = self.get_status(status)[1]

                    row['status'] = _status or self.statuses.get(status) or ''
                    row['unread'] = row['UnreadByLogin'] and login in row['UnreadByLogin'] and 'unread' or ''

                    row['AuthorName'] = self._is_no_price and self.user_short_name(row['Author']) or ''
                    row['id'] = row['TID']
                    row['TID'] = '%05d' % row['id']
                    row['RD'] = self._get_date(row['RD'])

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

            self.point('workflow.render-1.3')

            # ======================
            # Согласования (reviews)
            # ======================

            if order_id:
                reviews, review_id = self._get_reviews(order_id, review_id=review_id, reviewer=reviewer)

            self.point('workflow.render-1.4')

        # -----------------------------------------------------------
        # Справочники фильтра запросов (sellers, reviewers, statuses)
        # -----------------------------------------------------------
        
        stocks = self.ref_stocks()
        activities = self.ref_activities()
        subdivisions = self.ref_subdivisions()
        categories = self.ref_categories()
        statuses = self.ref_statuses()
        params = self.ref_params()
        comments = self.ref_comments()

        # ---------------------
        # Орг.штатная структура
        # ---------------------

        authors = self.ref_authors()
        managers = self.ref_managers()
        users = self.ref_users()
        reviewers = self.ref_reviewers()

        self.engine.dispose()

        self.point('workflow.render-2')

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
            'total'             : '%s' % total_orders,
            'title'             : gettext('Total documents in current selection'),
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
            'activities'        : activities,
            'subdivisions'      : subdivisions,
            'authors'           : authors,
            'statuses'          : statuses,
            'params'            : params,
            'comments'          : comments,
            'categories'        : categories,
            'reviewers'         : reviewers,
            'managers'          : managers,
            'users'             : users,
            'search'            : search or '',
            'order_statuses'    : ':'.join(self.order_statuses),
            'links_pages'       : self.links_pages,
            'total_selected'    : '0 | 0.00',
        })

        if g.system_config.IsActiveScroller and kw.get('is_active_scroller'):
            kw['is_active_scroller'] = 0 if len(orders) > g.system_config.IsActiveScroller else 1

        self.point('workflow.render-finish')

        return kw

    #   ---------
    #   SCHEDULES
    #   ---------

    def schedule_params(self):
        """
            Schedule items count: rows, columns
        """
        return {'documents' : (5, 4), 'decrees' : (6, 5)}

    def make_schedule_document_status(self, key):
        #
        # Schedule statuses: [[<id>, <title>, <classes>], ... ]
        #
        status = (
            key == 'work' and [
                ['on-work', 'Проекты документов', ''], 
                ['on-archive', 'В архиве (отменено)', ''], 
                ['on-removed', 'Корзина', ''], 
                ['total-orders', 'Всего документов', ''],
                ] or 
            key == 'review' and [
                ['on-review', 'На подписи', ''], 
                ['on-review-wait', 'Ожидают подписи', 'review-wait wait'],
                ['on-review-out', 'Обратите внимание! Срок ввода в действие документа просрочен', 'review-out out'],
                ] or 
            key == 'accepted' and [
                ['on-accepted', 'Документ действует', ''], 
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
    
        is_private = not (permissions['is_ceo'] or permissions['is_admin'])

        for column in [('TID', 'OrderID'), ('Status', 'OrderStatus'),]:
            where = where.replace(column[0], column[1])

        order = 'OrderID, ReviewID'

        cursor = self.runQuery(view, columns=columns, where=where, order=order, as_dict=True) or []

        if IsTrace:
            print_to(errorlog, '--> schedule documents:%s %s, where:%s, cursor:%s' % (
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
                # Утверждение
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

        order, done_action, schedules, audit = None, {}, {}, []

        is_approved = is_rejected = is_confirm = False

        def _add(key, id):
            if key not in schedules:
                schedules[key] = []
            schedules[key].append(str(id))
            data[key] += 1

        today = getToday()

        def _check_wait(review):
            #
            # Set Wait key
            #
            if order_id and (not review or order_id != review['OrderID']): # and review_status is not None
                for action in done_action:
                    key = '-'.join(action.split('-')[:-1])
                    wait_key, out_key = '%s-wait' % key, '%s-out' % key
                    if done_action[action] != 1:
                        if wait_key in data:
                            if is_private and order_status == 0 and key == 'on-review':
                                if _is_login():
                                    _add(wait_key, order_id)
                            else:
                                data[wait_key] += 1

        for review in cursor:
            _check_wait(review)
            #
            # Check new order item started
            #
            if review['OrderID'] not in orders:
                order = review
                order_id = order['OrderID']
                order_status = order['OrderStatus']

                is_approved = order['Approved'] and True or False
                is_rejected = False
                is_confirm = False

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

                if order_status == 0 and order.get('FinishDueDate') and today > order.get('FinishDueDate'):
                    _add('on-review-out', order_id)
    
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
                s = '%s.%s' % (order_status, review_status)

                if review['Reviewer'] == CEO_LOGIN:
                    if self.is_review_status(review_status, 'accept'):
                        is_rejected = False
                    elif self.is_review_status(review_status, 'reject'):
                        is_rejected = True
                    elif self.is_review_status(review_status, 'confirm'):
                        done_action['on-confirmed-done'] = 0
                        data['on-confirmed-done'] = 0
                        is_confirm = True

                if s in provision_review_statuses:
                    status = provision_review_statuses[s][2]
                    done_key = '%s-done' % status
                    if done_key in done_action:
                        if done_action[done_key] != 1:
                            done = True
                            if not status:
                                continue
                            elif status == 'on-confirmed' and done_action[done_key] == 0 and is_confirm:
                                pass
                            else:
                                done = False

                            if done:
                                done_action[done_key] = 1
                                data[done_key] += 1

                    elif status in ('on-accepted', 'on-rejected'):
                        pass
                    #elif status == 'on-confirm':
                    #    done_action['on-confirmed-done'] = 0
                    elif status == 'on-work':
                        pass

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
            else:
                data[id] = '<div class="no-value">%(data)s</div>' % args
                continue

            data[id] = '<a target="_blank" href="/%(page)s%(per_page)s%(no_union)s%(status)s%(review)s%(confirmed)s">%(data)s</a>' % args

        self.point('schedule.documents-finish')

        return data, ids


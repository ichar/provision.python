# -*- coding: utf-8 -*-

from operator import itemgetter

from config import IsTrace

from ..settings import *
from ..models import get_users, get_users_dict
from ..utils import (
     normpath, getToday, getDate, getDateOnly, checkDate, spent_time, makeSearchQuery, getString, getSQLString,
     Capitalize, unCapitalize, sortedDict
     )

from .sellers import Seller

##  ==========================
##  PageDefault Class Statuses
##  ==========================

_MODELS = {
    'purchase'  : 40,
    'workflow'  : 30,
    'sale'      : 20,
    'provision' : 0,
}

_pages = {
    'purchase'  : 'Закупки',
    'workflow'  : 'Секретариат', 
    'sale'      : 'Продажи',
    'provision' : 'Снабжение', 
}

_default_statuses = dict(zip([0,1,2,3,4,5,6,7,9], ['work', 'review', 'accepted', 'rejected', 'confirm', 'execute', 'finish', 'archive', 'removed']))

_PROVISION_STATUSES = {
    'work'       : (0, 'on-work', 'в работе', '', 'в работе'),
    'review'     : (1, 'on-review', 'на согласовании', '', 'на согласовании'),
    'accepted'   : (2, 'on-accepted', 'согласовано', '2.2', 'на согласовании = согласовано'),
    'rejected'   : (3, 'on-rejected', 'отказано', '3.3', 'на согласовании = отказано'),
    'confirm'    : (4, 'on-confirm', 'требуется обоснование', '4.4', 'на согласовании = требуется обоснование'),
    'confirmed'  : (4, 'on-confirmed', 'обоснование представлено', '4.5', 'на согласовании = обоснование представлено'),
    'execute'    : (5, 'on-execute', 'на исполнении', '5.2', 'на исполнении = согласовано'),
    'paid'       : (5, 'on-paid', 'на исполнении', '5.6', 'на исполнении = оплачено'),
    'delivered'  : (5, 'on-delivered', 'на исполнении', '5.7', 'на исполнении = поставлено на склад'),
    'audit'      : (5, 'on-audit', 'на исполнении', '5.10', 'на исполнении = аудит'),
    'failure'    : (5, 'on-failure', 'на исполнении', '5.11', 'на исполнении = замечания аудита'),
    'validated'  : (5, 'on-validated', 'на исполнении', '5.12', 'на исполнении = акцептовано к закрытию'),
    'U1'         : (6, 'on-delivered', 'исполнено', '6.2', 'исполнено = согласовано'),
    'U2'         : (6, 'on-delivered', 'исполнено', '6.5', 'исполнено = информация'),
    'U3'         : (6, 'on-delivered', 'исполнено', '6.6', 'исполнено = оплачено'),
    'U4'         : (6, 'on-delivered', 'исполнено', '6.7', 'исполнено = поставлено на склад'),
    'autoclosed' : (6, 'on-autoclosed', 'исполнено', '6.8', 'исполнено = автозакрытие'),
    'finish'     : (6, 'on-finish', 'исполнено', '6.12', 'исполнено'),
    'archive'    : (7, 'on-archive', 'в архиве', '', 'в архиве'),
    'x1'         : (8, None, '', '', ''),
    'removed'    : (9, 'on-removed', 'корзина', '', 'корзина'),
}

_provision_statuses = dict([(x[1], x[0]) for x in _default_statuses.items()])

_PROVISION_SUB_STATUSES = dict([(x[1][3], (x[0], x[1][0], x[1][1],)) for x in _PROVISION_STATUSES.items() if x[1][3]])

_PROVISION_REVIEW_STATUSES = {
     1 : ('', '...'),
     2 : ('accept', 'согласовано'),
     3 : ('reject', 'отказано'),
     4 : ('confirm', 'требуется обоснование'),
     5 : ('confirmation', 'информация'),
     6 : ('paid', 'оплачено'),
     7 : ('delivered', 'товар на складе'),
     8 : ('autoclosed', 'автозакрытие'),
     9 : ('decree', 'поручение'),
    10 : ('audit', 'аудит'),
    11 : ('failure', 'замечание'),
    12 : ('validated', 'акцептовано'),
}

_provision_review_statuses = dict([(x[1][0], x[0]) for x in _PROVISION_REVIEW_STATUSES.items()])

_PROVISION_PAYMENT_STATUSES = {
     0 : ('work', 'в работе', 1),
     1 : ('review', 'на согласовании', 1),
     2 : ('accept', 'согласовано', 0),
     3 : ('reject', 'отказано', 0),
     4 : ('execute', 'на исполнении', 1),
     5 : ('paid', 'исполнено', 1),
}

_provision_payment_statuses = dict([(x[1][0], x[0]) for x in _PROVISION_PAYMENT_STATUSES.items()])

_PROVISION_DECREE_STATUSES = {
     0 : ('work', 'на исполнении'),
     1 : ('done', 'исполнено'),
     2 : ('overdue', 'просрочено'),
     3 : ('rejected', 'отменено'),
     4 : ('accepted', 'принято к исполнению'),
     5 : ('changed', 'изменено'),
     6 : ('reported', 'отчет подготовлен'),
     7 : ('discard', 'вне исполнения'),
     8 : ('oversight', 'вне контроля'),
}

_provision_decree_statuses = dict([(x[1][0], x[0]) for x in _PROVISION_DECREE_STATUSES.items()])

_valid_status = 7
_valid_payment_status = 5
_valid_decree_status = 3

_schedule_keys = ('documents', 'decrees')

_decrees_link_type = 1

_DECREE_ALARM_HTML = '''
<html>
<head>
  <style type="text/css">
    h1 { font-size:18px; padding:0; margin:0 0 10px 0; }
    div.box { font:normal 12px Verdana, Arial; }
    div.box * { display:block; }
    dd { font-size:16px; font-weight:bold; line-height:24px; padding:0; color:#468; margin-left:10px; white-space:nowrap; }
    span { color:#000; padding-top:3px; font-size:12px; white-space:nowrap; }
    a { cursor:pointer; }
    .bold { font-weight:bold; }
    .seller {}
    .order * { display:inline-block !important; }
    .caption { padding-top:10px; padding-bottom:10px; }
    .info { padding-top:10px; display:inline-block; }
    .code { background-color:#B654A8; padding:5px 20px 5px 20px; border:1px solid #806080; text-align:center; color:white; width:fit-content; max-width:250px; width:max-content; display:inline-block; }
    .work { border:0px solid #CC80CC; color:#C8C; }
    .done { border:0px solid #488DA0; color:#080; }
    .overdue { background-color:#C24620; color:white; }
    .rejected { border:0px solid #64606A; color:#777; }
    div.title { margin-top:10px; font-weight:bold; color:rgba(120, 100, 80, 0.6); }
    div.message { margin-top:10px; font-size:12px; }
    div.status { margin-top:10px; margin-left:0px; font-size:12px; font-weight:bold; color:#333; }
    div.status * { display:inline-block; }
    span.status { padding:5px; width:max-content; }
    div.note { margin-top:5px; }
    div.line { border-top:1px dotted #888; width:100%%; height:1px; margin:10px 0 10px 0; }
    div.line hr { display:none; }
  </style>
</head>
<body>
  <div class="box">
  <h1 class="center">Уведомление %(Caption)s</h1>
  <table>
  <tr><td><dd class="code">ПОРУЧЕНИЕ</dd></td></tr>
  <tr><td class="caption">Документ:</td></tr>
  <tr><td><dd class="order"><a target="_blank" href="webperso#args">[%(id)05d]</a>&nbsp;%(Article)s</dd></td></tr>
    <tr><td><span class="info">%(Date)s</span></td></tr>
  <tr><td>
    <div class="title">%(Title)s. %(Reviewer)s</div>
    <div class="message"><div class="note bold">%(title)s</div><div class="note">%(message)s</div></div>
    <div class="status bold">Статус: <span class="status %(code)s">%(Code)s</span></div>
  </td></tr>
  <tr><td><div class="line"><hr></div></td></tr>
  </table>
  </div>
</body>
</html>
'''

## ==================================================== ##

_config = {
    'provision-companies' : { 
        'columns' : ('Name',),
        'view'    : '[dbo].[WEB_Companies_vw]',
    },
    'provision-order-dates' : { 
        'columns' : ('TID', 'Created', 'Approved', 'Paid', 'Delivered', 'ReviewDueDate', 'FinishDueDate', 'WithMail', 'Facsimile',),
        'view'    : '[dbo].[OrderDates_tb]',
    },
    'provision-order-unreads' : { 
        'columns' : ('Login',),
        'view'    : '[dbo].[OrderUnreads_tb]',
    },
    'provision-order-reviewers' : { 
        'columns' : ('ID', 'OrderID', 'Login',),
        'view'    : '[dbo].[Reviewers_tb]',
    },
    'provision-order-authors' : { 
        'columns' : ('Author',),
        'view'    : '[dbo].[WEB_Authors_vw]',
    },
    'provision-order-changes' : { 
        'columns' : ('TID', 'Login', 'Name', 'Value', 'RD',),
        'view'    : '[dbo].[WEB_OrderChanges_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'Login'        : 'Автор',
            'Name'         : 'Наименование реквизита',
            'Value'        : 'Значение',
            'RD'           : 'Дата изменения',
        },
        'export'  : ('TID', 'Login', 'Name', 'Value', 'RD',),
    },
    'provision-reviews' : { 
        'columns' : ('TID', 'StatusDate', 'Reviewer', 'Status', 'Note',),
        'view'    : '[dbo].[WEB_Reviews_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'OrderID'      : '№ заявки',
            'RegistryDate' : 'Дата заявки',
            'Reviewer'     : 'ФИО должностного лица',
            'Status'       : 'Статус',
            'Note'         : 'Рецензия',
            'StatusDate'   : 'Дата',
        },
        'export'  : ('TID', 'OrderID', 'Login', 'Reviewer', 'Status', 'DecreeStatus', 'Note', 'DueDate', 'MD', 'RegistryDate', 'StatusDate',),
    },
    'provision-decrees' : { 
        'columns' : ('TID', 'OrderID', 'Registry', 'Reviewer', 'Executor', 'Note', 'DueDate',),
        'view'    : '[dbo].[WEB_Decrees_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'OrderID'      : '№ документа',
            'RegistryDate' : 'Дата распоряжения',
            'Reviewer'     : 'ФИО автора',
            'Executor'     : 'Исполнитель',
            'Note'         : 'Содержание',
            # Extra application headers
            'num'          : ('Номер поручения', '', '', ''),
            'id'           : ('ID поручения', '', '', ''),
            'ReviewID'     : ('ID рецензии', '', '', ''),
            'Author'       : ('Автор документа', '', '', ''),
            'AuthorName'   : ('Автор поручения', '', '', ''),
            'ExecutorName' : ('Исполнитель', '', '', ''),
            'Article'      : ('Заголовок поручения', '', '', ''),
            'Purpose'      : ('ПОРУЧЕНИЕ', '', '', ''),
            'Report'       : ('Отчет о выполнении поручения', '', '', ''),
            'Status'       : ('Статус исполнения', '', '', ''),
            'DueDate'      : ('Срок исполнения', '', '', ''),
            'Page'         : ('Раздел АИС', '', '', ''),
            'ReviewDate'   : ('Дата выдачи поручения', '', '', ''),
            'Accepted'     : ('Принято к исполнению', '', '', ''),
            'RD'           : ('Дата регистрации', '', '', ''),
        },
        'export'  : ('TID', 'OrderID', 'ReviewID', 'ReportID', 'Executor', 'DecreeStatus', 'DueDate', 'Author', 'Reviewer', 'Note', 'ReviewStatus', 'ReviewDate', 'Accepted', 'Reported', 'EditedBy', 'RD'),
    },
    'provision-subdivisions' : { 
        'columns' : ('TID', 'Name',),
        'view'    : '[dbo].[WEB_Subdivisions_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'Name'         : 'Отдел',
            'Code'         : 'Код',
            'Manager'      : 'Руководитель',
            'FullName'     : 'Полное наименование подразделения',
        },
        'export'  : ('TID', 'Name', 'Code', 'Manager', 'FullName',),
    },
    'provision-sectors' : { 
        'columns' : ('TID', 'Name',),
        'view'    : '[dbo].[WEB_Sectors_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'Name'         : 'Участок производства',
            'Code'         : 'Код',
            'Manager'      : 'Руководитель',
            'FullName'     : 'Полное наименование подразделения',
        },
        'export'  : ('TID', 'Name', 'Code', 'Manager', 'FullName',),
    },
    'provision-categories' : { 
        'columns' : ('TID', 'Name', 'MD',),
        'view'    : '[dbo].[WEB_Categories_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'Name'         : 'Категория',
        },
        'export'  : ('TID', 'Name', 'MD',),
    },
    'provision-sellers' : { 
        'columns' : ('TID', 'Name', 'MD',),
        'view'    : '[dbo].[WEB_Sellers_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'Name'         : 'Наименование компании',
            'Title'        : 'Реквизиты',
            'Address'      : 'Адрес местонахождения организации',
            'Code'         : 'Код 1C',
            'Type'         : 'Орг-правовая форма',
            'Contact'      : 'Контакты',
            'URL'          : 'Адрес сайта (URL)',
            'Phone'        : 'Телефон',
            'Email'        : 'Email',
        },
        'export'  : ('TID', 'Name', 'Title', 'Address', 'Code', 'Type', 'Contact', 'URL', 'Phone', 'Email', 'EditedBy', 'MD', 'RD',),
    },
    'provision-vendors' : { 
        'columns' : ('TID', 'Name',),
        'view'    : '[dbo].[WEB_Vendors_vw]',
    },
    'provision-conditions' : { 
        'columns' : ('TID', 'Name',),
        'view'    : '[dbo].[WEB_Conditions_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'Name'         : 'Условие оплаты',
        },
        'export'  : ('TID', 'Name', 'Code',),
    },
    'provision-equipments' : { 
        'columns' : ('TID', 'Name',),
        'view'    : '[dbo].[WEB_Equipments_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'Title'        : 'Категория',
            'Name'         : 'Наименование',
        },
        'export'  : ('TID', 'Title', 'Name',),
    },
    'provision-params' : { 
        'columns' : ('TID', 'Name', 'MD',),
        'view'    : '[dbo].[WEB_Params_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'Name'         : 'Наименование',
        },
        'export'  : ('TID', 'Name', 'MD',),
    },
    'provision-param-values' : { 
        'columns' : ('ParamID', 'Value',),
        'view'    : '[dbo].[WEB_ParamValues_vw]',
    },
    'provision-payments' : { 
        'columns' : ('TID', 'Name',),
        'view'    : '[dbo].[WEB_Payments_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'Name'         : 'Наименование',
        },
        'export' : ('TID', 'Name',),
    },
    'provision-refers' : { 
        'columns' : ('TID', 'Name', 'MD',),
        'view'    : '[dbo].[WEB_Refers_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'Name'         : 'Наименование',
        },
        'export' : ('TID', 'Name', 'MD',),
    },
    'provision-comments' : { 
        'columns' : ('TID', 'Name',),
        'view'    : '[dbo].[WEB_Comments_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'Name'         : 'Наименование',
        },
        'export' : ('TID', 'Name',),
    },
    'provision-order-params' : { 
        'columns' : ('TID', 'Login', 'Name', 'Value',),
        'view'    : '[dbo].[WEB_OrderParams_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'ParamID'      : 'ID параметра',
            'Login'        : 'Автор',
            'Name'         : 'Параметр',
            'Value'        : 'Значение',
        },
        'export'  : ('TID', 'ParamID', 'Login', 'Name', 'Code', 'Value', 'RD',),
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
        'export'  : ('TID', 'Login', 'Name', 'Qty', 'Units', 'Total', 'Tax', 'Currency', 'Account', 'Vendor', 'VendorID', 'RD',),
        'money'   : ('Total', 'Tax',),
    },
    'provision-order-payments' : { 
        'columns' : ('TID', 'Login', 'Purpose', 'PaymentDate', 'Total', 'Currency', 'Rate', 'Tax', 'Status',),
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
    'provision-order-refers' : { 
        'columns' : ('TID', 'Login', 'OrderReferID', 'ReferType', 'Name', 'Qty', 'Currency', 'Total', 'Note'),
        'view'    : '[dbo].[WEB_OrderRefers_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'Login'        : 'Автор',
            'OrderReferID' : 'Номер заявки',
            'ReferType'    : 'Тип обеспечения',
            'Name'         : 'Наименование заявки',
            'Qty'          : 'Кол-во',
            'Total'        : 'Сумма',
            'Currency'     : 'Валюта',
            'Note'         : 'Примечание',
        },
        'export'  : ('TID', 'Login', 'ReferType', 'Name', 'Qty', 'Currency', 'Total', 'Note', 'OrderReferID', 'ReferID', 'RegistryDate', 'ReferDate',),
        'money'   : ('Total',),
    },
    'provision-order-documents' : { 
        'columns' : ('TID', 'Login', 'FileName', 'Note', 'FileSize', 'ForAudit', 'RD',),
        'view'    : '[dbo].[WEB_OrderDocuments_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'OrderID'      : '№ заявки',
            'Login'        : 'Автор',
            'FileName'     : 'Документ',
            'FileSize'     : 'Размер файла',
            'ContentType'  : 'Тип',
            'Note'         : 'Содержание',
            'ForAudit'     : 'ДБО',
            'UID'          : 'UID',
            'RD'           : 'Дата',
        },
        'export'  : ('TID', 'OrderID', 'Login', 'FileName', 'FileSize', 'ContentType', 'Note', 'IsExist', 'UID', 'ForAudit', 'RD',),
    },
    'provision-order-comments' : { 
        'columns' : ('TID', 'Login', 'Author', 'Note',),
        'view'    : '[dbo].[WEB_OrderComments_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'CommentID'    : 'ID параметра',
            'Login'        : 'Автор',
            'Author'       : 'Автор комментария',
            'Note'         : 'Комментарий',
        },
        'export'  : ('TID', 'CommentID', 'Login', 'Author', 'Note', 'RD',),
    },
    'provision-order-vendors' : { 
        'columns' : ('TID', 'OrderID', 'Name',),
        'view'    : '[dbo].[WEB_OrderVendors_vw]',
    },
    'provision-review-payments' : { 
        'columns' : ('TID', 'OrderID', 'Seller', 'Article', 'Subdivision', 'Currency', 'Total', 'Comment', 'PaymentDate', 'Login', 'Purpose', 'Rate', 'Tax', 'Status',),
        'view'    : '[dbo].[WEB_ReviewPayments_vw]',
        'headers' : { 
            'TID'          : 'ID',
            'PaymentID'    : 'ID платежа',
            'Login'        : 'Автор',
            'Purpose'      : 'Назначение платежа',
            'PaymentDate'  : 'Дата платежа',
            'Total'        : 'Сумма',
            'Currency'     : 'Валюта',
            'Rate'         : 'Курс ЦБ',
            'ExchangeRate' : 'Курс покупки валюты',
            'Tax'          : 'НДС (руб.)',
            'Status'       : 'Статус',
            'Seller'       : 'Поставщик',
            'Article'      : 'Наименование товара',
            'Subdivision'  : 'Подразделение',
            'Comment'      : 'Примечание',
        },
        'export'  : ('TID', 'OrderID', 'Author', 'Subdivision', 'Article', 'OrderCurrency', 'OrderTotal', 'PaymentID', 'Login', 'Purpose', 'PaymentDate', 'Total', 'Tax', 'Status', 'Currency', 'Rate', 'ExchangeRate', 'Comment', 'RD',),
        'money'   : ('Total', 'Tax', 'TotalRub',),
    },
    'provision-review-payment-changes' : { 
        'columns' : ('TID', 'PaymentID', 'OrderID', 'Login', 'Status', 'RD',),
        'view'    : '[dbo].[PaymentChanges_tb]',
        'headers' : { 
            'TID'          : 'ID',
            'PaymentID'    : 'ID платежа',
            'OrderID'      : 'ID заявки',
            'Status'       : 'Статус',
            'RD'           : 'Дата изменения',
        },
        'export'  : ('TID', 'PaymentID', 'OrderID', 'Login', 'Status', 'RD',),
    },
    'provision-schedule' : { 
        'columns' : (),
        'view'    : '[dbo].[WEB_Schedule_vw]',
        'export'  : (
            'OrderID', 'Author', 'OrderStatus', 'RegistryDate',
            'ReviewID', 'Reviewer', 'ReviewStatus',
            'Created', 'Approved', 'Paid', 'Delivered', 'ReviewDueDate', 'FinishDueDate', 'AuditDate', 'Validated',
            'CategoryID', 'SubdivisionID', 'SubdivisionCode', 'StatusDate', 'StockListID',
            ),
    },
    'provision-cost-orders' : { 
        'columns' : (),
        'view'    : '[dbo].[WEB_CostOrders_vw]',
        'export'  : (
            'TID', 'Author', 'Article', 'Qty', 'Price', 'Currency', 'Total', 'Tax', 'Subdivision', 'Seller', 'Account', 'Status', 
            'SubdivisionID', 'EquipmentID', 'SellerID', 'ConditionID', 'CategoryID', 'StockListID', 
            'StockListNodeCode', 'ConditionCode', 
            'EditedBy', 'Created', 'Approved', 'Paid', 'Delivered', 'MD', 'RD'
            ),
        'money'   : ('Total', 'Tax',),
    },
    'provision-stocks' : {
        'columns' : ('TID', 'Name', 'ShortName', 'NodeLevel', 'Children', 'Orders',),
        'view'    : '[dbo].[WEB_Stocks_vw]',
        'headers' : {
            'TID'          : 'ID',
            'Name'         : 'Наименование',
            'Title'        : 'Заголовок',
            'NodeLevel'    : 'Уровень',
            'NodeCode'     : 'Код',
            'RefCode1C'    : 'Код номенклатуры 1C',
            'Params'       : 'Параметры',
            'ShortName'    : 'Вид',
            'Comment'      : 'Примечание',
            'EditedBy'     : 'Автор',
            'Children'     : 'Кол-во подклассов',
            'Orders'       : 'Всего заказов',
            'RD'           : 'Дата',
        },
        'export'  : ('TID', 'Name', 'Title', 'ShortName', 'NodeLevel', 'NodeCode', 'Children', 'RefCode1C', 'Params', 'Comment', 'EditedBy', 'Children', 'Orders', 'RD',),
    },
    'provision-stocks-children' : {
        'columns' : ('TID', 'Name', 'ShortName', 'NodeLevel', 'Children', 'Orders',),
        'view'    : '[dbo].[WEB_StocksChildren_vw]',
        'headers' : {
            'TID'          : 'ID',
            'Name'         : 'Наименование',
            'Title'        : 'Заголовок',
            'NodeLevel'    : 'Уровень',
            'NodeCode'     : 'Код',
            'RefCode1C'    : 'Код номенклатуры 1C',
            'ShortName'    : 'Вид',
            'Comment'      : 'Примечание',
            'EditedBy'     : 'Автор',
            'Children'     : 'Кол-во подклассов',
            'Orders'       : 'Всего заказов',
            'RD'           : 'Дата',
        },
        'export' : ('TID', 'Name', 'Title', 'ShortName', 'NodeLevel', 'NodeCode', 'Children', 'RefCode1C', 'Comment', 'EditedBy', 'Children', 'Orders', 'RD',),
    },
    'provision-stocks-children-tree' : {
        'columns' : ('TID', 'Name', 'ShortName', 'NodeLevel', 'NodeCode', 'Children', 'Orders',),
        'exec'    : '[dbo].[GET_StocksChildren_sp]',
    },
    'provision-register-order' : { 
        'params'  : "0,'%(login)s','%(article)s',%(qty)s,'%(purpose)s',%(price).5f,'%(currency)s',%(total).2f,%(tax).2f,'%(subdivision)s','%(sector)s','%(category)s','%(equipment)s','%(seller)s','%(condition)s','%(account)s','%(url)s','%(duedate)s','%(author)s',%(status)s,%(is_no_price)s,%(model)s,0,null",
        'args'    : "%d,'%s','%s',%d,'%s',%.2f,'%s',%.2f,%.2f,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',%s,%d,%d,%d,null",
        'exec'    : '[dbo].[REGISTER_Order_sp]',
    },
    'provision-refresh-order' : { 
        'params'  : "0,%(id)d,'%(login)s','%(article)s',%(qty)s,'%(purpose)s',%(price).5f,'%(currency)s',%(total).2f,%(tax).2f,'%(subdivision)s','%(sector)s','%(category)s','%(equipment)s','%(seller)s','%(condition)s','%(account)s','%(url)s','%(duedate)s','%(author)s',%(is_no_price)s,%(model)s,null",
        'exec'    : '[dbo].[UPDATE_Order_sp]',
    },
    'provision-remove-order' : { 
        'params'  : "0,%(id)d,'%(login)s',null",
        'exec'    : '[dbo].[DELETE_Order_sp]',
    },
    'provision-accept-decree' : { 
        'params'  : "0,%(decree_id)d,'%(login)s','%(reviewer)s','%(report)s',null",
        'exec'    : '[dbo].[ACCEPT_Decree_sp]',
    },
    'provision-finish-decree' : { 
        'params'  : "0,%(decree_id)d,'%(login)s',null",
        'exec'    : '[dbo].[FINISH_Decree_sp]',
    },
    'provision-reject-decree' : { 
        'params'  : "0,%(decree_id)d,'%(login)s',null",
        'exec'    : '[dbo].[REJECT_Decree_sp]',
    },
    'provision-remove-decree' : { 
        'params'  : "0,%(decree_id)d,'%(login)s',null",
        'exec'    : '[dbo].[REMOVE_Decree_sp]',
    },
    'provision-register-review' : { 
        'params'  : "0,%(order_id)d,%(review_id)d,%(decree_id)d,%(report_id)d,'%(login)s','%(reviewer)s',%(status)d,'%(note)s','%(review_duedate)s',%(with_mail)d,'%(executor)s','%(report)s','%(edited_by)s',null",
        'args'    : '0,%d,%d,%d,%d,%s,%s,%d,%s,%s,%d,%s,%s,%s,null',
        'exec'    : '[dbo].[REGISTER_Review_sp]',
    },
    'provision-register-stocklist' : { 
        'params'  : "0,%(order_id)d,'%(login)s',%(id)d,null",
        'args'    : '0,%d,%s,%d,null',
        'exec'    : '[dbo].[REGISTER_OrderStockList_sp]',
    },
    'provision-register-payment-status' : { 
        'params'  : "0,%(id)d,'%(login)s',%(status)d,null",
        'args'    : '0,%d,%s,%d,null',
        'exec'    : '[dbo].[REGISTER_PaymentStatus_sp]',
    },
    'provision-register-reviewers-order' : { 
        'params'  : "0,%(order_id)d,'%(login)s','%(value)s',%(model)d,null",
        'args'    : "%d,%d,'%s','%s',%d,null",
        'exec'    : '[dbo].[REGISTER_Reviewers_sp]',
    },
    'provision-set-unread' : { 
        'params'  : "0,%(order_id)d,'%(logins)s',null",
        'args'    : '0,%d,%s,null',
        'exec'    : '[dbo].[SET_Unread_sp]',
    },
    'provision-set-read' : { 
        'params'  : "0,%(order_id)s,'%(logins)s',null",
        'args'    : '0,%d,%s,null',
        'exec'    : '[dbo].[SET_Read_sp]',
    },
    'provision-add-comment-order' : { 
        'params'  : "0,%(order_id)d,%(id)d,%(comment_id)d,'%(login)s','%(new_comment)s','%(note)s',null",
        'args'    : "%d,%d,%d,%d,%s,%s,%s,null",
        'exec'    : '[dbo].[ADD_Comment_sp]',
    },
    'provision-add-document-order' : { 
        'params'  : "0,'%(uid)s',%(order_id)d,'%(login)s','%(filename)s',%(filesize)s,%(content_type)s,%(foraudit)s,'%(note)s','%(image)s',null",
        'args'    : "%d,%s,%d,%s,%s,%d,%s,%d,%s,%s,null",
        'exec'    : '[dbo].[ADD_Document_sp]',
    },
    'provision-add-item-order' : { 
        'params'  : "0,%(order_id)d,%(id)d,%(vendor_id)d,'%(login)s','%(item)s',%(qty)d,'%(units)s',%(total).2f,%(tax).2f,'%(currency)s','%(account)s','%(vendor)s',null",
        'args'    : "%d,%d,%d,%d,'%s','%s',%d,'%s',%.2f,%.2f,'%s','%s','%s',null",
        'exec'    : '[dbo].[ADD_Item_sp]',
    },
    'provision-add-param-order' : { 
        'params'  : "0,%(order_id)d,%(id)d,%(param_id)d,'%(login)s','%(new_param)s','%(value)s',%(model)d,null",
        'args'    : "%d,%d,%d,%d,'%s','%s','%s',%d,null",
        'exec'    : '[dbo].[ADD_Param_sp]',
    },
    'provision-add-payment-order' : { 
        'params'  : "0,%(order_id)d,%(id)d,%(payment_id)d,'%(login)s','%(new_payment)s','%(date)s',%(total).2f,%(tax).2f,'%(currency)s',%(rate).4f,%(exchange_rate).4f,%(status)s,'%(comment)s',null",
        'args'    : "%d,%d,%d,%d,'%s','%s','%s',%.2f,%.2f,'%s',%.4f,%.4f,%d,null",
        'exec'    : '[dbo].[ADD_Payment_sp]',
    },
    'provision-add-refer-order' : { 
        'params'  : "0,%(order_id)d,%(id)d,%(refer_id)d,'%(login)s','%(new_refer)s',%(value)d,'%(note)s',%(model)d,null",
        'args'    : "%d,%d,%d,%d,'%s','%s',%d,'%s',%d,null",
        'exec'    : '[dbo].[ADD_Refer_sp]',
    },
    'provision-del-comment-order' : { 
        'params'  : "0,%(order_id)d,%(id)d,%(comment_id)d,'%(login)s',null",
        'args'    : "%d,%d,%d,%d,'%s',null",
        'exec'    : '[dbo].[DEL_Comment_sp]',
    },
    'provision-del-document-order' : { 
        'params'  : "0,%(order_id)d,%(id)d,'%(login)s',null",
        'args'    : "%d,%d,%d,'%s',null",
        'exec'    : '[dbo].[DEL_Document_sp]',
    },
    'provision-del-item-order' : { 
        'params'  : "0,%(order_id)d,%(id)d,'%(login)s',null",
        'args'    : "%d,%d,%d,'%s',null",
        'exec'    : '[dbo].[DEL_Item_sp]',
    },
    'provision-del-param-order' : { 
        'params'  : "0,%(order_id)d,%(id)d,%(param_id)d,'%(login)s',null",
        'args'    : "%d,%d,%d,%d,'%s',null",
        'exec'    : '[dbo].[DEL_Param_sp]',
    },
    'provision-del-payment-order' : { 
        'params'  : "0,%(order_id)d,%(id)d,%(payment_id)d,'%(login)s',null",
        'args'    : "%d,%d,%d,%d,'%s',null",
        'exec'    : '[dbo].[DEL_Payment_sp]',
    },
    'provision-del-refer-order' : { 
        'params'  : "0,%(order_id)d,%(id)d,%(refer_id)d,'%(login)s',null",
        'args'    : "%d,%d,%d,%d,'%s',null",
        'exec'    : '[dbo].[DEL_Refer_sp]',
    },
    'provision-del-seller-order' : { 
        'params'  : "0,%(id)d,'%(login)s',null",
        'args'    : "%d,%d,'%s',null",
        'exec'    : '[dbo].[DEL_Seller_sp]',
    },
    'provision-set-status-order' : { 
        'params'  : "0,%(order_id)d,'%(login)s',%(status)s,null",
        'exec'    : '[dbo].[SET_Status_sp]',
    },
    'provision-set-order-facsimile' : { 
        'params'  : "0,%(order_id)d,'%(login)s','%(facsimile)s',null",
        'exec'    : '[dbo].[SET_OrderFacsimile_sp]',
    },
    'provision-update-seller' : { 
        'params'  : "0,%(id)d,'%(login)s','%(cname)s','%(title)s','%(address)s','%(code)s',%(ctype)d,'%(contact)s','%(url)s','%(phone)s','%(email)s',null",
        'exec'    : '[dbo].[UPDATE_Seller_sp]',
    },
    'provision-update-stock' : { 
        'params'  : "0,%(id)d,'%(login)s','%(cname)s','%(title)s','%(shortname)s','%(refcode1c)s','%(comment)s',null",
        'exec'    : '[dbo].[UPDATE_Stock_sp]',
    },
    'provision-download-image' : { 
        'columns' : ('FileName', 'FileSize', 'ContentType', 'Image',),
        'view'    : '[storage].[dbo].[OrderDocuments_tb]',
    },
}

## ==================================================== ##

def _is_status_in_review(ob, statuses):
    review_statuses = ob.get('ReviewStatuses') or ''
    for s in statuses:
        if '%s:' % s in review_statuses:
            return True
    return False

def _is_last_status_in_review(ob, status, exclude_statuses):
    review_statuses = [int(x) for x in (ob.get('ReviewStatuses') or '').split(':') if x]
    for s in reversed(review_statuses):
        if s == status:
            return True
        elif s in exclude_statuses:
            return False
    return False


class Base:

    def __init__(self, *args, **kwargs):
        self._started = getToday()

        if IsDeepDebug:
            print('Base init')

        super().__init__(*args, **kwargs)

        self.engine = None
        self.last_engine = None
        self.login = g.current_user.login
        self.subdivision_code = g.current_user.subdivision_code

        self.system_config = None
        self.is_with_points = 0
        self.is_cross = 0
        self.is_check_refers = 0

    def _init_state(self, engine, attrs, factory, *args, **kwargs):
        if IsDeepDebug:
            print('Base initstate')

        self.engine = engine

        self.is_args = False
        self.is_uncheck_status = False
        self.no_union = False

    @property
    def is_error(self):
        return self.last_engine.is_error
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

    def database_config(self, name):
        pass

    def getReferenceID(self, name, key, value, engine=None, **kw):
        config = self.database_config(name)

        self.last_engine = engine or self.engine

        try:
            return self.last_engine.getReferenceID(name, key, value, config=config, **kw)
        finally:
            pass

    def runProcedure(self, name, engine=None, **kw):
        config = self.database_config(name)

        self.last_engine = engine or self.engine

        try:
            return self.last_engine.runProcedure(name, config=config, **kw)
        finally:
            self.point('base.runProcedure: %s' % name)

    def runQuery(self, name, engine=None, **kw):
        config = self.database_config(name)

        self.last_engine = engine or self.engine

        try:
            return self.last_engine.runQuery(name, config=config, **kw)
        finally:
            self.point('base.runQuery: %s' % name)

    def reset(self):
        if self.last_engine is not None:
            self.last_engine.engine_error = False

    def point(self, name):
        if not self.is_with_points:
            return

        self._finished = getToday()

        if IsTrace:
            print_to(None, '>>> %s: %s sec' % (name, spent_time(self._started, self._finished)))


class PageDefault(Base):

    # Использовать UNION в SQL запросах
    is_apply_union = 0
    # Выборка данных для назначенных рецензентов
    is_with_reviewers_template = 0
    # Включить орг-штатную структуру в запросах
    is_use_company_subdivisions = 0
    # Выборка данных без ограничений размера страницы
    is_max_per_page = 0

    def __init__(self, id, name, title, caption, **kw):
        if IsDeepDebug:
            print('PageDefault init')

        super().__init__()

        self._errors = []

        self._id = id
        self._model = 0
        self._distinct = False
        self._name = name
        self._title = title
        self._caption = caption
        self._is_no_price = 0

        self._locator = None
        self._params = None

        self._attrs = {}

    def _init_state(self, engine, attrs=None, factory=None, **kw):
        if IsDeepDebug:
            print('PageDefault initstate')

        super()._init_state(engine, attrs, factory)

        if attrs:
            self._locator = attrs.get('locator')
            self._views = attrs.get('views')
            self._encode_columns = attrs.get('encode_columns')
            self._statuses = attrs.get('statuses')
            self._review_statuses = attrs.get('provision_review_statuses')
            self._payment_statuses = attrs.get('payment_statuses')
            #
            # system_config.attrs
            #
            self.system_config = attrs.get('system_config')
            self.stocklist = attrs.get('stocklist')
            self.image_loader = attrs.get('image_loader')

        if self.system_config:
            self.is_apply_union = self.system_config.IsApplyUnion
            self.is_with_reviewers_template = self.system_config.IsWithReviewersTemplate
            self.is_use_company_subdivisions = self.system_config.IsUseCompanySubdivisions
            self.is_max_per_page = self.system_config.IsMaxPerPage
            self.is_with_points = self.system_config.IsWithPoints
            self.is_cross = self.system_config.IsCross
            self.is_check_refers = self.system_config.IsCheckRefers

            self.stocks_view_type = 'default'
            try:
                self.stocks_view_type = self.system_config.STOCKS_VIEW_TYPE
            except:
                pass

        if factory:
            for key in factory.keys():
                setattr(self, '_%s' % key, self.set_factory(key, factory))

        self._models = dict(zip(_MODELS.keys(), _MODELS.values()))

        self.model_users = get_users_dict(as_dict=True)

        self.today = getDateOnly(getToday())

    #   ----------------------------
    #   EMAIL HTML MESSAGE TEMPLATES
    #   ----------------------------

    @property
    def APPROVAL_ALARM_HTML(self):
        return None
    @property
    def CREATE_ALARM_HTML(self):
        return None
    @property
    def REMOVE_ALARM_HTML(self):
        return None
    @property
    def REVIEW_ALARM_HTML(self):
        return None
    @property
    def DECREE_ALARM_HTML(self):
        return _DECREE_ALARM_HTML
    @property
    def REVIEW_PAYMENTS_ALARM_HTML(self):
        return None
    @property
    def UPLOAD_ATTACHMENT_ALARM_HTML(self):
        return None
    @property
    def confirmation_message(self):
        return ''

    @staticmethod
    def get_decree_alarm_caption():
        return 'об исполнении'

    def get_decree_alarm_title(self, is_executor):
        return '%s поручения' % (
               is_executor and 'Отчет об исполнении' or 'Содержание'
               )

    #   -----------
    #   PERMISSIONS
    #   -----------

    def _permissions(self):
        self.is_owner = g.current_user.is_owner()
        self.is_admin = g.current_user.is_administrator()
        self.is_office_ceo = g.current_user.app_is_office_ceo
        self.is_office_direction = g.current_user.app_is_office_direction
        self.is_office_execution = g.current_user.app_is_office_execution
        self.is_assistant = g.current_user.app_role_assistant
        self.is_headoffice = g.current_user.app_role_headoffice
        self.is_ceo = g.current_user.app_role_ceo
        self.is_cao = g.current_user.app_role_cao
        self.is_cto = g.current_user.app_role_cto
        self.is_chief = g.current_user.app_role_chief

        self.is_provision_manager = g.current_user.app_is_provision_manager
        self.is_personal_manager = g.current_user.app_is_personal_manager
        self.is_payments_manager = g.current_user.app_is_payments_manager
        self.is_diamond_manager = g.current_user.app_is_diamond_manager
        self.is_purchase_manager = g.current_user.app_is_purchase_manager
        self.is_sale_manager = g.current_user.app_is_sale_manager
        self.is_workflow_manager = g.current_user.app_is_workflow_manager
        self.is_stock_manager = g.current_user.app_is_stock_manager
        self.is_auditor = g.current_user.app_is_auditor

        self.is_manager = g.current_user.app_is_manager
        self.is_consultant = g.current_user.app_is_consultant
        self.is_author = g.current_user.app_is_author

        self.is_vip = self.is_ceo or self.is_cao or self.is_cto or self.is_office_direction or self.is_page_manager

    @property
    def app_role_ceo(self):
        """
            Делопроизводство. Делегирование полномочий ГД
        """
        if not g.current_user:
            return False
        login = g.current_user.login
        """
        subdivision_code = g.current_user.subdivision_code
        app_is_workflow_manager = g.current_user.app_is_workflow_manager
        role = subdivision_code == '0013' and app_is_workflow_manager
        """
        role = g.current_user.subdivision_code == '0013' and g.current_user.app_is_workflow_manager
        return role

    def is_order_author(self, ob=None):
        if ob is None:
            ob = g.requested_object
        return not ob and True or ob.get('Author') == self.login and True or False

    def is_disabled_accept(self, ob=None):
        return False

    def is_disabled_edit(self, ob=None, force=None):
        if ob is None:
            ob = g.requested_object
        status = ob.get('Status') or 0
        if not force:
            if self.is_page_manager or self.is_order_author(ob):
                return False
        return (force or not (force or self.is_page_manager)) and status > 0 and status not in (self.statuses['rejected'], self.statuses['confirm']) and True or False

    def is_disabled_delete(self, ob=None):
        if ob is None:
            ob = g.requested_object
        status = ob.get('Status') or 0
        if self.is_order_author(ob) and status == self.statuses['work']:
            return False
        return not self.is_page_manager and True or status > self.statuses['confirm'] and status < self.statuses['removed'] and True or False

    def is_disabled_review(self, ob=None):
        if ob is None:
            ob = g.requested_object
        status = ob.get('Status') or 0
        return status > 4 or status == 2 and not g.current_user.app_role_ceo or False

    def is_disabled_paid(self, ob=None):
        if ob is None:
            ob = g.requested_object
        status = ob.get('Status') or 0
        if status == self.statuses.get('execute') and not _is_status_in_review(ob, (
            #self.provision_review_statuses.get('audit'), 
            self.provision_review_statuses.get('autoclosed'), 
            )):
            return False
        return True

    def is_disabled_validated(self, ob=None):
        if ob is None:
            ob = g.requested_object
        status = ob.get('Status') or 0
        if status == self.statuses.get('execute') and _is_last_status_in_review(ob, 
                self.provision_review_statuses.get('audit'), (
                self.provision_review_statuses.get('validated'), self.provision_review_statuses.get('failure')
            )):
            return False
        return True
    
    def is_disabled_delivered(self, ob=None):
        if ob is None:
            ob = g.requested_object
        status = ob.get('Status') or 0
        if status == self.statuses.get('execute') and not ob.get('Delivered') and not _is_status_in_review(ob, (
            self.provision_review_statuses.get('autoclosed'), 
            )):
            return False
        return True

    #   -----------

    @property
    def models(self):
        return sortedDict(_MODELS)
    @property
    def default_page(self):
        return 'workflow'
    @property
    def locator(self):
        return self._locator
    @property
    def id(self):
        return self._id
    @property
    def model(self):
        return self._model
    @property
    def name(self):
        return self._name
    @property
    def title(self):
        return self._title
    @property
    def caption(self):
        return self._caption
    @property
    def distinct(self):
        return self._distinct
    @property
    def is_no_price(self):
        return self._is_no_price
    @property
    def is_page_manager(self):
        return False
    @property
    def params(self):
        return self._params
    @property
    def default_currencies(self):
        return ('RUB', 'USD', 'EUR', 'CHF', 'GBP')
    @property
    def page_config(self):
        return _config
    @property
    def page_link(self):
        return None
    @property
    def order_tag_restrictions(self):
        pass
    @property
    def barcode_date_format(self):
        pass
    @property
    def object_types(self):
        return ('заявка', 'заявки', 'заявок')
    @property
    def links_pages(self):
        return [('', DEFAULT_UNDEFINED,)] + sorted(list(_pages.items()))

    #   -------------
    #   SYSTEM CONFIG
    #   -------------

    @property
    def system_config_emails_common(self):
        return g.system_config.DEFAULT_EMAILS_COMMON or []
    @property
    def system_config_emails_public(self):
        return g.system_config.DEFAULT_EMAILS_PUBLIC or []
    @property
    def system_config_exclude_emails(self):
        return g.system_config.EXCLUDE_EMAILS or []

    #   -----------------------
    #   OVERIDDEN SYSTEM CONFIG
    #   -----------------------

    @property
    def system_config_emails_approval(self):
        pass
    @property
    def system_config_emails_create(self):
        pass
    @property
    def system_config_emails_remove(self):
        pass
    @property
    def system_config_emails_review(self):
        pass
    @property
    def system_config_emails_execute(self):
        pass
    @property
    def system_config_emails_payments(self):
        pass
    @property
    def system_config_emails_audit(self):
        pass
    @property
    def system_config_emails_decree(self):
        pass
    @property
    def system_config_emails_upload(self):
        pass
    @property
    def system_config_documents_schedule(self):
        return 1
    @property
    def system_config_decrees_schedule(self):
        return 1

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

    #   --------
    #   HANDLERS
    #   --------

    def after(self):
        pass

    def check_dates(self, dates):
        pass

    def disabled_statuses(self):
        return None

    #   --------
    #   STATUSES
    #   --------

    @property
    def default_statuses(self):
        # By ID
        return _default_statuses
    @property
    def statuses(self):
        # ID by Key
        return _provision_statuses
    @property
    def provision_statuses(self):
        # By Key (tuple)
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
    @property
    def payment_statuses(self):
        # By ID
        return _PROVISION_PAYMENT_STATUSES
    @property
    def provision_payment_statuses(self):
        # By Key
        return _provision_payment_statuses
    @property
    def decree_statuses(self):
        # By ID
        return _PROVISION_DECREE_STATUSES
    @property
    def provision_decree_statuses(self):
        # By Key
        return _provision_decree_statuses
    @property
    def valid_status(self):
        return _valid_status
    @property
    def valid_payment_status(self):
        return _valid_payment_status
    @property
    def valid_decree_status(self):
        return _valid_decree_status

    def is_review_status(self, value, key):
        return self.review_statuses[value][0] == key

    def is_valid_status(self, status):
        return True

    def is_finished(self, ob=None):
        if ob is None:
            ob = g.requested_object
        return ob.get('Status') == self.statuses['finish']

    def get_status(self, value=None, **kw):
        """
            Returns Order's Status CSS (on-), title by value
        """
        key = None
        if value is None or value not in range(0, 10):
            key, title = self.check_order_status()
        else:
            key = self.default_statuses[value]
        if not key:
            return (None, '',)
        return self.provision_statuses[key][1], self.provision_statuses[key][2].upper()

    @staticmethod
    def get_order_status(ob=None):
        if ob is None:
            ob = g.requested_object
        return '%s.%s' % (ob.get('Status') or 0, ob.get('ReviewStatus') or 0)

    @staticmethod
    def get_order_statuses(ob=None):
        if ob is None:
            ob = g.requested_object
        return ob.get('ReviewStatuses', '').split(':')

    def get_order_reviewers(self, ob, status):
        reviewers = []
        if not ob or not status:
            return reviewers
        order_id = ob['TID']
        reviews = self._get_reviews(order_id, cursor=True)
        if reviews:
            for review in reviews:
                login = review['Login']
                if review['Status'] == self.provision_review_statuses[status]:
                    reviewers.append(login)
        return reviewers

    def check_confirmation(self, ob, order_status):
        if not (ob and order_status):
            return True
        if order_status == self.provision_statuses['confirmed'][3]:
            for review in self._get_reviews(ob['TID'], order='TID desc', cursor=True):
                if review['Status'] == self.provision_review_statuses['confirm']:
                    return False
                if review['Status'] == self.provision_review_statuses['confirmation'] and review['Login'] != CEO_LOGIN:
                    return True
            return False
        return True

    def check_order_status(self, ob=None):
        """
            Returns complex Order's Status key and complex title by value as 'X.Y'
        """
        order_status = self.get_order_status(ob)
        s = int(order_status.split('.')[0])
        key = x = None
        if s < 2 or s > 5:
            key = x = self.default_statuses[s]
        else:
            is_exists = False
            for rs in self.get_order_statuses(ob)[::-1]:
                order_status = '%s.%s' % (s, rs)
                if order_status in self.sub_statuses:
                    if self.check_confirmation(ob, order_status):
                        is_exists = True
                        break
            if is_exists:
                x, status, css = self.sub_statuses[order_status]
                key = x.startswith('U') and css.split('-')[1] or x
            else:
                key = x = self.default_statuses[s]
        return key, self.provision_statuses[x][4].upper()

    def get_review_status(self, value, is_title=None):
        return value in self.review_statuses and self.review_statuses[value][is_title and 1 or 0].upper() or ''

    def get_payment_status(self, value):
        return value in range(0, self.valid_payment_status+1) and self.payment_statuses.get(value) or None

    def get_decree_status(self, value, is_title=None):
        v = value in range(0, self.valid_decree_status+1) and self.decree_statuses.get(value) or None
        if is_title:
            if v:
                if v[0] == self.provision_decree_statuses['overdue']:
                    return gettext('Note! Decree duedate is overdue')
                return v[1].upper()
            else:
                return ''
        return v

    def order_created(self, done):
        return done and gettext('Message: Document was %s successfully.' % done) or ''

    def check_status_default(self, ob, key, **kw):
        pass

    def check_confirmation(self, ob, order_status):
        return True

    def check_status(self, command, ob, **kw):
        return True, '', ''

    def set_status(self, callback, review, ob, **kw):
        return []

    def set_order_facsimile(self, order_id, author, with_error=None):
        self._refreshOrder(order_id=order_id)

        if g.requested_object['Status'] != self.statuses['accepted']:
            return None

        import os
        p = normpath(os.path.join(basedir, 'app/static/facsimile'))
        visa = sorted([x for x in os.listdir(p) if re.search(r'^%s-\d+\.png$' % author, x)])
        facsimile = visa and random.choice(visa) or '%s.png' % author

        cursor, error_msg = self.runProcedure('provision-set-order-facsimile', 
            order_id=order_id,
            login=self.login,
            facsimile=facsimile,
            with_error=with_error,
        )

        if IsTrace:
            print_to(None, '>>> set_order_facsimile, login:%s, order:%d, facsimile:%s' % (self.login, order_id, facsimile))

        if error_msg and self.is_error:
            print_to(None, '!!! set_order_facsimile, engine error: %s' % str(error_msg))

        return self.is_error

    #   --------

    @staticmethod
    def _check_id(id, ids):
        if id in ids:
            return 1
        ids.append(id)
        return 0

    def get_page_name(self, name):
        return _pages.get(name) or '...'

    def get_header(self, name, config=None):
        view = self.page_config.get(config or 'provision-orders')
        return view.get('headers').get(name)[0]

    def get_link(self, root):
        link = self.page_link
        return link and (link[0] % root, link[1])

    def get_decrees_link(self, root, ids=None, with_login=None, state=None):
        return '%sdecrees/%s?with_login=%s%s&state=%s' % (
            root, 
            self.id, 
            with_login is None and 1 or with_login, 
            ids and '&_ids=%s' % ':'.join([str(x) for x in ids]) or '', 
            state is None and 'collapse' or state
            ), ''

    def get_dates(self):
        return { 
            'Created'       : [1, 'Дата создания', ''],
            'ReviewDueDate' : [2, 'Дата обоснования', ''],
            'Approved'      : [3, 'Дата согласования', ''],
        }

    def get_model_locator(self, model):
        return self._models.get(model) or self.locator

    def database_config(self, name):
        return _config.get(name)

    def user_short_name(self, login):
        ob = self.model_users.get(login)
        return ob and ob.get('short_name') or login

    def user_full_name(self, login):
        ob = self.model_users.get(login)
        return ob and ob.get('full_name') or login

    def user_post(self, login):
        ob = self.model_users.get(login)
        return ob and ob.get('post') or ''

    def set_params(self, params):
        self._params = params

    def get_attrs(self, ob, attrs):
        setattr(ob, '_equipment', getString(attrs.get('order_equipment')))
        setattr(ob, '_purpose', getString(attrs.get('order_purpose'), save_links=True, with_html=True))

    def set_attrs(self, ob, attrs):
        pass

    def set_order(self, ob, attrs, **kw):
        pass

    def get_order_params(self, data):
        return data

    def get_param_combo_values(self, param_id):
        values = []
        where = 'ParamID=%s' % param_id
        order = 'Value%s' % (param_id == 45 and ' DESC' or '') # borisov
        cursor = self.runQuery(self._views['param_values'], where=where, order=order, distinct=True, encode_columns=(1,))
        values += [x[1] for x in cursor]
        return values

    def set_query_for_vendors(self, vendor_id, items):
        pass

    def check_tag_limits(self, ob, errors, **kw):
        for tag, value, size in (('Article', ob._article, 500), ('Equipment', ob._equipment, 1000), ('Purpose', ob._purpose, 2000),):
            if len(value) > size:
                errors.append(gettext('Error: Field %s is too long' % tag) + ' (max %s)!' % size)
        return errors and True or False

    def documents_action(self, order_id, info):
        return info

    def barcode_action(self, command, order_id, item_id, **kw):
        pass

    def upload_attachment_notification(self, callback, rowid, **kw):
        pass

    #   ----------
    #   REFERENCES
    #   ----------

    def ref_stocks(self):
        stocks = []
        if self.stocks_view_type.startswith('tree'):
            s = (self.stocks_view_type.split('>')[1] or '&nbsp;')*3
            view = 'provision-stocks-children-tree'
            cursor = self.runQuery(view, params='%s' % self.model, encode_columns=('Name', 'ShortName',), as_dict=True)
            stocks += [(x['TID'], '%s%s' % (s*(x['NodeLevel']-1), x['Name'])) for x in cursor if x['Orders'] > 0]
        else:
            view = self.stocks_view_type == 'view' and self._views['stocks-children'] or self._views['stocks']
            cursor = self.runQuery(view, order='NodeCode', encode_columns=('Name', 'ShortName',), as_dict=True)
            stocks += [(x['TID'], x['ShortName'] or x['Name']) for x in cursor if x['Orders'] > 0]
            stocks = sorted(stocks, key=itemgetter(1))
        stocks.insert(0, (0, DEFAULT_UNDEFINED,))
        stocks.insert(1, (-1, EMPTY_REFERENCE_VALUE,))
        return stocks

    def ref_companies(self):
        companies = [DEFAULT_UNDEFINED]
        cursor = self.runQuery(self._views['companies'], order='Name', distinct=True, encode_columns=(0,))
        companies += [x[0] for x in cursor]
        return companies

    def ref_subdivisions(self):
        subdivisions = [(0, DEFAULT_UNDEFINED,)]
        where = ''

        if self.is_use_company_subdivisions:
            if g.current_user.subdivision_id:
                if not (self.is_office_direction or self.is_page_manager) and self.subdivision_code > '002':
                    where = "Code like '%s%%'" % self.subdivision_code[:3]

        cursor = self.runQuery(self._views['subdivisions'], where=where, order='Name', distinct=True, encode_columns=(1,))
        subdivisions += [(x[0], x[1]) for x in cursor]
        return subdivisions

    def ref_sectors(self):
        sectors = [(0, DEFAULT_UNDEFINED,)]
        where = ''
        cursor = self.runQuery(self._views['sectors'], where=where, order='Name', distinct=True, encode_columns=(1,))
        sectors += [(x[0], x[1]) for x in cursor]
        return sectors

    def ref_categories(self):
        categories = [(0, DEFAULT_UNDEFINED,)]
        cursor = self.runQuery(self._views['categories'], order='Name', distinct=True, encode_columns=(1,))
        categories += [(x[0], x[1]) for x in cursor if x[2] in (None, self.model)]
        return categories

    def ref_sellers(self):
        sellers = [(0, DEFAULT_UNDEFINED,)]
        columns = ('TID', 'Name', 'Type', 'MD')
        cursor = self.runQuery(self._views['sellers'], columns=columns, order='Name', distinct=True, encode_columns=('Name',), as_dict=True)
        sellers += [(x['TID'], Seller.render_name(x['Name'], x['Type'])) for x in cursor if x['MD'] in (None, self.model)]
        return sellers

    def ref_currencies(self):
        currencies = [DEFAULT_UNDEFINED]
        #cursor = self.runQuery(self._views['orders'], columns=('Currency',), order='Currency', distinct=True, encode_columns=(0,))
        #currencies += [x[0] for x in cursor if x[0] and x[0].strip()]
        currencies += sorted(self.default_currencies)
        return currencies

    def ref_conditions(self):
        conditions = [(0, DEFAULT_UNDEFINED,)]
        cursor = self.runQuery(self._views['conditions'], order='Name', distinct=True, encode_columns=(1,))
        conditions += [(x[0], x[1]) for x in cursor if x[1]]
        return conditions

    def ref_statuses(self):
        statuses = [('', DEFAULT_UNDEFINED,)]
        statuses += [(x, self.get_status(x)[1].lower()) for x in range(0, self.valid_status + 1) if x in self.default_statuses]

        if self.is_office_direction or self.is_page_manager:
            statuses.insert(1, (10, gettext('all'),))

        if self.is_page_manager:
            statuses.append((9, self.get_status(9)[1].lower(),))
        return statuses

    def ref_payment_statuses(self):
        payment_statuses = [(x, self.get_payment_status(x)[1].lower()) for x in range(0, self.valid_payment_status + 1) 
            if self.payment_statuses[x][2]]
        return payment_statuses

    def ref_params(self):
        params = [(0, DEFAULT_UNDEFINED,)]
        cursor = self.runQuery(self._views['params'], order='Name', distinct=True, encode_columns=(1,))
        params += [(x[0], x[1]) for x in cursor if x[2] in (None, self.model)]
        return params

    def ref_payments(self):
        payments = [(0, DEFAULT_UNDEFINED,)]
        cursor = self.runQuery(self._views['payments'], order='Name', distinct=True, encode_columns=(1,))
        payments += [(x[0], x[1]) for x in cursor]
        return payments

    def ref_refers(self):
        refers = [(0, DEFAULT_UNDEFINED,)]
        cursor = self.runQuery(self._views['refers'], order='Name', distinct=True, encode_columns=(1,))
        refers += [(x[0], x[1]) for x in cursor if x[2] in (None, self.model)]
        return refers

    def ref_comments(self):
        comments = [(0, DEFAULT_UNDEFINED,)]
        cursor = self.runQuery(self._views['comments'], order='Name', distinct=True, encode_columns=(1,))
        comments += [(x[0], x[1]) for x in cursor]
        return comments

    def ref_vendors(self):
        vendors = [(0, DEFAULT_UNDEFINED,)]
        cursor = self.runQuery(self._views['vendors'], order='Name', distinct=True, encode_columns=(1,))
        vendors += [(x[0], x[1]) for x in cursor]
        return vendors

    def ref_authors(self):
        authors = [('', DEFAULT_UNDEFINED,)]
        cursor = self.runQuery(self._views['authors'], order='Author', distinct=True)
        authors += sorted([(x[0], self.model_users[x[0]]['full_name']) for x in cursor if x[0] in self.model_users], key=itemgetter(1))
        return authors

    def ref_reviewers(self):
        reviewers = []
        cursor = self.runQuery(self._views['authors'], order='Author', distinct=True) + [[x] for x in g.system_config.WORKFLOW_OFFICE_GROUP]
        reviewers += sorted([(x[0], self.model_users[x[0]]['full_name']) for x in cursor if x[0] in self.model_users and self.model_users[x[0]]['enabled']], key=itemgetter(1))
        return reviewers

    def ref_users(self):
        users = [(x, '%s %s [%s]' % (self.model_users[x]['subdivision_code'], self.model_users[x]['full_name'], 
            self.model_users[x]['subdivision_name'])) 
                for x, v in sorted(list(self.model_users.items()), key=lambda k: k[1]['full_name'])]
        users.insert(0, ('', DEFAULT_UNDEFINED,))
        return users

    def ref_short_users(self):
        users = [(x, self.model_users[x]['short_name']) 
            for x, v in sorted(list(self.model_users.items()), key=lambda k: k[1]['short_name'])]
        users.insert(0, ('', DEFAULT_UNDEFINED,))
        return users

    def ref_persons(self):
        persons = [(x, self.model_users[x]['full_name']) 
            for x, v in sorted(list(self.model_users.items()), key=lambda k: k[1]['full_name'])]
        persons.insert(0, ('', DEFAULT_UNDEFINED,))
        return persons

    def ref_managers(self):
        persons = [(ob.login, ob.full_name()) for ob in get_users(is_ob=True) if ob.app_is_office_manager]
        persons.insert(0, ('', DEFAULT_UNDEFINED,))
        return persons

    def ref_decree_statuses(self):
        statuses = [(x, v[1]) 
            for x, v in sorted(list(self.decree_statuses.items()))]
        statuses.insert(0, ('', DEFAULT_UNDEFINED,))
        return statuses

    #   ----------------
    #   RENDER DOCUMENTS
    #   ----------------

    def is_urgently(self, order):
        return False

    def is_limited_length(self, attrs):
        return False

    def make_current_order_info(self, order_id, info, **kw):
        if info and info.get('stocklist'):
            info['stocklist']['title'] = 'Класс товара'
        return info

    def qualified_documents(self, with_permissions=None):
        qd = 'MD=%s' % self.model
        """
        if _QUALIFIED_DOCUMENTS and not (self.is_payments_manager or self.is_ceo or self.is_owner):
            qd = "(StockListNodeCode is null or StockListNodeCode not like '%s')" % _QUALIFIED_DOCUMENTS
        """
        return qd

    def make_search(self, kw):
        """
            Поиск контекста
        """
        search = get_request_item('search', args=kw.get('args'))
        self.is_search_order = False
        items = []

        TID = None

        # ----------------------------------------------
        # Поиск ID файла, номера ТЗ (search is a number)
        # ----------------------------------------------

        if search:
            self.is_search_order = True

            try:
                TID = int(search)
                items.append('(TID=%s)' % TID)
            except:
                #   Поиск по контексту:
                #   -------------------
                #     #4:преламинат || антенна || антена
                #     >краска && (золот || серебр || перлам)
                masks = {
                    '#1' : "(Article like '%(v)s')%(k)s",
                    '#2' : "(Article like '%(v)s' or Equipment like '%(v)s')%(k)s",
                    '#3' : "(Article like '%(v)s' or Purpose like '%(v)s')%(k)s",
                    '#4' : "(Article like '%(v)s' or Equipment like '%(v)s' or Purpose like '%(v)s')%(k)s",
                    '#5' : "(EditedBy like '%(v)s')%(k)s",
                    '#6' : "(Author like '%(v)s')%(k)s",
                    '#7' : "(Author like '%(v)s' or EditedBy like '%(v)s')%(k)s",
                    'default'  : "(Article like '%(v)s' or Account like '%(v)s')%(k)s",
                    'params'   : "(Name like '%(v)s' or Value like '%(v)s')%(k)s",
                    'items'    : "(Name like '%(v)s')%(k)s",
                    'payments' : "(Purpose like '%(v)s' or Comment like '%(v)s')%(k)s",
                }
                c, o = makeSearchQuery(search, masks)
                s = list(filter(None, c))

                if s:
                    if o in ('params', 'items', 'payments',):
                        view = 'provision-order-%s' % o
                        where = ''.join(s)
                        cursor = self.runQuery(view, columns=('OrderID',), where=where, distinct=True)
                        if cursor:
                            items.append('TID in (%s)' % ','.join([str(x[0]) for x in cursor]))
                        else:
                            items.append('TID in (-1)')
                    else:
                        items.append('(%s)' % ''.join(s))

        return search, items, TID

    def args_parser(self, args, items):
        """
            Формирование параметров SQL-запроса
        """
        qf = ''

        # -----------------
        # Параметры фильтра
        # -----------------

        for key in args:
            if key == EXTRA_ or key in DATE_KEYWORDS:
                continue
            name, value = args[key]
            if value == DEFAULT_UNDEFINED:
                continue
            elif key in ('status',) and value == 0:
                items.append("%s=%s" % (name, value))
                qf += "&%s=%s" % (key, value)
            elif value:
                if key in ('author', 'reviewer', 'company'):
                    items.append("%s='%s'" % (name, value))
                elif key == 'status' and value == 10:
                    self.is_apply_union = 0
                elif key == 'date_from':
                    if checkDate(value, DEFAULT_DATE_FORMAT[1]):
                        items.append("%s >= '%s 00:00'" % (name, value))
                    else:
                        args['date_from'][1] = ''
                        continue
                elif key == 'date_to':
                    if checkDate(value, DEFAULT_DATE_FORMAT[1]):
                        items.append("%s <= '%s 23:59'" % (name, value))
                    else:
                        args['date_to'][1] = ''
                        continue
                elif key == 'id':
                    items.append("%s=%s" % (name, value))
                    self.is_search_order = True
                elif key == 'ids':
                    items.append("%s in (%s)" % (name, ','.join([x for x in value.split(':')])))
                    self.is_apply_union = 0
                    self.is_uncheck_status = True
                elif key == 'stock':
                    if value == -1:
                        items.append("%s is null" % name)
                    else:
                        items.append("StockList%s like '%s%%'" % (self.stocklist.node_code, self.stocklist.getNodeClassCode(value)))
                elif key in ('subdivision', 'sector', 'category', 'seller', 'condition', 'status',):
                    if isinstance(value, str) and ':' in value:
                        items.append("%s in (%s)" % (name, ','.join([x for x in value.split(':')])))
                    elif value == -1:
                        items.append("%s is null" % name)
                    else:
                        items.append("%s=%s" % (name, value))
                    self.is_apply_union = 0
                elif key == 'confirmed':
                    subsql = "[dbo].CHECK_IsConfirmed_fn(%s, '5',':4')" % name
                    if value == '0' or not value:
                        continue
                    elif value in 'yY':
                        items.append("(Status=4 and %s=1)" % subsql)
                    elif value in 'nN':
                        items.append("(Status=4 and %s=0)" % subsql)
                elif key == 'paid':
                    if value == '0' or not value:
                        continue
                    elif value in 'yY':
                        subsql = "[dbo].CHECK_IsInReviews_fn(%s, '6')" % name
                        items.append("(Status=5 and %s=1)" % subsql)
                    elif value in 'nN':
                        subsql = "[dbo].CHECK_IsInReviews_fn(%s, '6')" % name
                        items.append("(Status=5 and %s=0)" % subsql)
                    elif value in 'uU':
                        items.append("(Price=0 or (Status >= 0 and %s is null))" % name)
                    elif value in 'aA':
                        subsql = "[dbo].CHECK_IsInReviews_fn(%s, '1')" % name
                        items.append("(Status in (5,6) and %s=1)" % subsql)
                elif key == 'delivered':
                    subsql = "[dbo].CHECK_IsInReviews_fn(%s, '7')" % name
                    if value == '0' or not value:
                        continue
                    elif value in 'yY':
                        items.append("(Status=6 and %s=1)" % subsql)
                    elif value in 'nN':
                        items.append("(Status=6 and %s=0)" % subsql)
                    self.is_uncheck_status = True
                elif key == 'finish':
                    if value == '0' or not value:
                        continue
                    elif value in 'yY':
                        items.append("(Status=6 and Approved is not null and Paid is not null)")
                    elif value in 'nN':
                        items.append("(Status in (5,6) and Approved is not null and (Paid is null or Delivered is null))")
                    self.is_uncheck_status = True
                elif key == 'autoclosed':
                    subsql = "[dbo].CHECK_IsInReviews_fn(%s, '8')" % name
                    if value == '0' or not value:
                        continue
                    elif value in 'yY':
                        items.append("(Status=6 and %s=1)" % subsql)
                    elif value in 'nN':
                        items.append("(Status=6 and %s=0)" % subsql)
                elif key == 'audit':
                    if value == '0' or not value:
                        continue
                    elif value in 'yY':
                        items.append("%s is not null" % name)
                    elif value in 'nN':
                        items.append("%s is null" % name)
                    elif value in 'fF':
                        items.append("[dbo].CHECK_IsInReviews_fn(ReviewStatuses, '11')=1")
                    elif value in 'vV':
                        items.append("Validated is not null")
                elif key == 'vendor':
                    g.page.set_query_for_vendors(value, items)
                else:
                    items.append("%s='%s'" % (name, value,))

                qf += "&%s%s=%s" % (key in ('id', 'ids') and '_' or '', key, value)

            elif value == 0:
                if key in ('status',):
                    items.append("%s=%s" % (name, value))
                    qf += "&%s=%s" % (key, value)

        return qf

    def subdivision_documents(self):
        items = []

        authors = []

        if self.is_manager and g.current_user.subdivision_id > 2:
            subdivision_id = None
            subdivision_name = g.current_user.subdivision_name
            manager, code = '', ''

            view = self._views['subdivisions']
            columns = self.database_config(view)['export']

            cursor = self.runQuery(view, columns=columns, where="Name='%s'" % subdivision_name, as_dict=True)
            ob = cursor[0] if cursor else None
            if ob:
                manager = ob['Manager']
                code = ob['Code']
                subdivision_id = ob['TID']

            if subdivision_id:
                pass
            else:
                name = g.current_user.subdivision_fullname
                if name:
                    subdivision_id = self.getReferenceID(view, 'Name', name)

            ids = None

            if not code:
                code = self.subdivision_code

            if subdivision_id or code:
                try:
                    if code and code[:3] > '001':
                        ids = [str(row['TID']) for row in self._get_subdivisions(code=code[:3])]
                    if ids:
                        items.append('SubdivisionID in (%s)' % ','.join(ids))
                except:
                    if IsPrintExceptions:
                        print_exception()

            if not ids:
                items.append('SubdivisionID=%d' % (subdivision_id or 0))

            if manager:
                authors.append(manager)

        if self.is_author:
            authors.append(self.login)

        if authors:
            items.append("Author in (%s)" % ','.join(["'%s'" % x for x in authors]))

        aq = ''

        if items:
            aq = ' or '.join(items)
            if len(items) > 1:
                aq = '(%s)' % aq

        return aq

    #   ---------
    #   SCHEDULES
    #   ---------

    def is_decree_work(self, decree):
        return decree['DecreeStatus'] == self.provision_decree_statuses['work']

    def is_decree_done(self, decree):
        return decree['DecreeStatus'] == self.provision_decree_statuses['done']

    def is_decree_rejected(self, decree):
        return decree['DecreeStatus'] == self.provision_decree_statuses['rejected']

    def is_decree_overdue(self, decree):
        return self.is_decree_work(decree) and decree.get('DueDate') and self.today > decree['DueDate']

    def is_decree_accepted(self, decree):
        return self.is_decree_work(decree) and decree.get('Accepted')

    def is_decree_changed(self, decree):
        return self.is_decree_work(decree) and decree.get('ReviewDate') and decree['ReviewDate'] >= decree['RD']

    def is_decree_reported(self, decree):
        return self.is_decree_work(decree) and decree.get('Reported')

    def is_decree_discard(self, decree):
        return self.is_decree_overdue(decree) and not decree.get('ReportID')

    def is_decree_oversight(self, decree):
        return self.is_decree_overdue(decree) and self.is_decree_reported(decree) and decree['Author'] == self.login

    @property
    def provision_decree_keys(self):
        return (
            ('incoming', 'Получено'), 
            ('incoming-executor', 'На исполнении'), 
            ('separator', ''), 
            ('outgoing', 'Выдано'), 
            ('outgoing-executor', 'На исполнении'), 
            ('outgoing-author', 'Вне контроля'),
            )

    def schedule_params(self):
        """
            Schedule items count: rows, columns
        """
        return {'documents' : (8, 4), 'decrees' : (6, 5)}

    def make_schedule_document_status(self, key):
        #
        # Schedule statuses: [[<id>, <title>, <classes>], ... ]
        #
        status = (
            key == 'work' and [
                ['on-work', 'Заявки в работе', ''], 
                ['on-archive', 'В архиве', ''], 
                ['on-removed', 'Корзина', ''], 
                ['total-orders', 'Всего заявок', ''],
                ] or 
            key == 'review' and [
                ['on-review', 'На согласовании', ''], 
                ['on-review-done', 'Согласование проведено', 'reviewed done'], 
                ['on-review-wait', 'Ожидают согласования', 'review-wait wait'],
                ['on-review-out', 'Обратите внимание! Срок исполнения заявки просрочен', 'review-out out'],
                ] or 
            key == 'accepted' and [
                ['on-accepted', 'Согласовано', ''], 
                ['on-finish-done', 'Согласовано, Оплачено и Исполнено', 'executed done'],
                ['on-finish-wait', 'Ожидают исполнения', 'executed-wait wait'],
                ['on-finish-out', 'Обратите внимание! Заявки вне исполнения (согласованы, но перенесены в архив или удалены)', 'autoclosed'],
                ] or 
            key == 'rejected' and [
                ['on-rejected', 'Отказано', ''], 
                None, 
                None,
                ] or 
            key == 'confirm' and [
                ['on-confirm', 'Заявки, по которым требуется дополнительное обоснование', ''], 
                ['on-confirmed-done', 'Обоснование представлено', 'confirmed done'], 
                ['on-confirmed-wait', 'Ожидают обоснования (информация не представлена)', 'confirm-wait wait'],
                ] or 
            key == 'paid' and [
                ['on-execute', 'На исполнении', ''], 
                ['on-paid-done', 'Оплачено', 'paid done'], 
                ['on-paid-wait', 'Ожидают оплаты', 'paid-wait wait'],
                ['on-autopaid', 'Это периодические ежемесячные платежи', 'autoclosed'],
                ] or 
            key == 'audit' and [
                ['on-audit', 'Аудит::Передано в систему финансового аудита', ''], 
                ['on-validated', 'Акцептовано к закрытию', 'validated done'], 
                ['on-failure', 'Замечания', 'failure wait'],
                ['on-audit-out', 'В ходе проверки', 'audit out'], 
                None
                ] or 
            key == 'finish' and [
                ['on-finish', 'Исполнено', ''], 
                ['on-delivered-done', 'Товар на складе', 'delivered done'], 
                ['on-delivered-wait', 'Ожидают поставки', 'delivered-wait wait'],
                ['on-autoclosed-done', 'Автозакрытие', 'autoclosed'],
                ] or 
            None
            )

        return status

    def make_schedule_decree_status(self, key):
        #
        # Schedule statuses: [[<id>, <title>, <classes>], ... ]
        #
        status = (
            key == 'incoming' and [
                ['', 'Всего полученных поручений', ''], 
                ['work', 'На исполнении', 'work'], 
                ['done', 'Исполнено', 'done'],
                ['overdue', 'Просрочено', 'overdue wait'],
                ['rejected', 'Отменено', 'rejected'],
                ] or 
            key == 'incoming-executor' and [
                ['accepted', 'Принято к исполнению', ''], 
                ['changed', 'Изменено', 'changed'], 
                ['reported', 'Отчет подготовлен', 'reported'],
                ['discard', 'Вне исполнения', 'out'],
                ] or 
            key == 'outgoing' and [
                ['', 'Всего выданных поручений', ''], 
                ['work', 'На исполнении', 'work'], 
                ['done', 'Исполнено', 'done'],
                ['overdue', 'Просрочено', 'overdue wait'],
                ['rejected', 'Отменено', 'rejected'],
                ] or 
            key == 'outgoing-executor' and [
                ['accepted', 'Принято к исполнению', ''], 
                ['changed', 'Изменено', 'changed'], 
                ['reported', 'Отчет подготовлен', 'reported'],
                ['discard', 'Вне исполнения', 'out'],
                ] or 
            key == 'outgoing-author' and [
                ['oversight', 'Обратите внимание! Поручения требуют контроля исполнения', ''], 
                ] or 
            None
            )

        return status

    def get_schedule_template(self, without_separator=None):
        template = dict(zip(_schedule_keys, ([], [])))

        delimeter = '::'

        def _comp(k):
            return '%s:%03d' % (k[1][0], k[1][3] and int(k[1][3].split('.')[1]) or 0)

        for n, (key, value) in enumerate([x for x in sorted(self.provision_statuses.items(), key=lambda k: _comp(k)) if x[1][1]]):
            status = self.make_schedule_document_status(key)
            if not status:
                continue
            #
            # Schedule item value: [<status>, <Name>, [(<id>, 0), ...], 
            #   <status> - order status key
            #   <id> - schedule item id
            #
            title = value[2]
            if delimeter in status[0][1]:
                title, name = status[0][1].split(delimeter)
                status[0][1] = name
            item = [key, Capitalize(title), ([(x, 0) for x in status if x])]
            template['documents'].append(item)

        def _item(key, x):
            return (('%s%s' % (key, x[0] and '-%s'% x[0] or ''), x[1], x[2]), 0)

        for key, title in self.provision_decree_keys:
            if key == 'separator':
                if not without_separator:
                    template['decrees'].append([key, '', self.schedule_params()['decrees'][1]+1])
                continue
            status = self.make_schedule_decree_status(key)
            item = [key, title, ([_item(key, x) for x in status if x])]
            template['decrees'].append(item)

        return template

    def print_schedule_template(self):
        templates = self.get_schedule_template()
        for key in _schedule_keys:
            for x in templates[key]:
                print(x[0:2])
                for s in x[2]:
                    print('-->', s)

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

        is_private = not (permissions['is_ceo'] or permissions['is_auditor'] or permissions['is_admin']) # or g.page.is_page_manager

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

        is_approved = is_rejected = is_paid = is_delivered = is_serve = False

        def _add(key, id):
            if key not in schedules:
                schedules[key] = []
            schedules[key].append(str(id))
            data[key] += 1

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
                                elif order_status not in (2,3,4) and not (is_paid and (is_delivered or is_serve)):
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

                stock_id = order.get('StockListID')
                is_serve = self.check_is_serve(stock_id)

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

                if order_status == 0 and order['FinishDueDate'] and self.today > order['FinishDueDate']:
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

    def getTabDecreesSchedule(self, params, attrs, templates):
        """
            Регламент согласования (поручения)
        """
        data = {}

        self.point('schedule.decrees-start')

        login = g.current_user.login

        command = params.get('command')
        per_page = params.get('per_page') or 10
        view = self._views['decrees']
        columns = self.database_config(view)['export']

        kw = {}
    
        where, order, args, permissions = attrs

        is_private = not (permissions['is_ceo'] or permissions['is_auditor'] or permissions['is_admin'])

        order = 'OrderID, TID'

        cursor = self.runQuery(view, columns=columns, order=order, as_dict=True) or []

        if IsTrace:
            print_to(errorlog, '--> schedule decrees:%s %s, where:%s, cursor:%s' % (
                command, login, where, cursor and len(cursor) or 0
                ))

        data['total-decrees'] = 0

        #print('... templates:', templates)

        ids, decrees, columns = [], [], []
        #
        # Schedule values: 
        #   <ids>   -- status ids, [<id>, ... ]
        #   <data>  -- schedule values, {<id> : 0}
        #   <id>    -- schedule id, 'on-<status>{-<done|wait|out>}'
        #
        for template in templates:
            id = template[0]
            ids.append(id)
            for item in template[2]:
                key = item[0][0]
                columns.append(key)
                data[key] = 0
            data[id] = 0

        #print('... ids:', ids)

        key, id, decree_status, order_id, decree_id, report_id = '', '', 0, 0, 0, 0
        #
        # Decree statuses: {<id> : <decree_status>}
        #
        statuses = {}
        #
        # Decree statuses: {<review_status> : (<key>, <order_status>, <id>}, <review_status>=<x.y>, x - order status, y - review status
        #
        decree, schedules, status = None, {}, 0

        is_incoming = is_outgoing = False

        def _add(key, id):
            if key not in schedules:
                schedules[key] = []
            if id not in schedules[key]:
                schedules[key].append(id)
            data[key] += 1

        def _set_id():
            return _decrees_link_type == 1 and decree_id or order_id

        for decree in cursor:
            is_outgoing, is_incoming, status_key = False, False, ''
    
            if decree['Author'] == login:
                is_outgoing = True
                status_key = 'outgoing'
            elif decree['Executor'] == login:
                is_incoming = True
                status_key = 'incoming'
            else:
                continue

            data['total-decrees'] += 1
    
            decree_status = decree['DecreeStatus']
            decree_duedate = decree['DueDate']
            decree_id = decree['TID']
            order_id = decree['OrderID']
            review_id = decree['ReviewID']
            report_id = decree['ReportID']

            for status in self.provision_decree_statuses:
                key = '%s-%s' % (status_key, status)
    
                if status == 'overdue' and self.is_decree_overdue(decree):
                    _add(key, _set_id())
                if decree_status == self.provision_decree_statuses[status]:
                    _add(key, _set_id())

                key = '%s-executor-%s' % (status_key, status)

                if status == 'accepted' and self.is_decree_accepted(decree):
                    _add(key, _set_id())
                if status == 'changed' and self.is_decree_changed(decree):
                    _add(key, _set_id())
                if status == 'reported' and self.is_decree_reported(decree):
                    _add(key, _set_id())
                if status == 'discard' and self.is_decree_discard(decree):
                    _add(key, _set_id())
                if status == 'oversight' and self.is_decree_oversight(decree):
                    key = '%s-author-%s' % (status_key, status)
                    _add(key, _set_id())

            if decree_id in decrees:
                continue
            else:
                decrees.append(decree_id)

            _add(status_key, _set_id())

        #print('... data 0:', data)

        def _link(**kw):
            args = {
                'per_page' : '?per_page=%s' % per_page,
                'no_union' : '&no_union=1',
                'page'     : self.id,
            }
            args.update(**kw)
            if _decrees_link_type == 1:
                return '<a target="_blank" href="/decrees/%(page)s%(per_page)s%(status)s">%(data)s</a>' % args
            else:
                return '<a target="_blank" href="/%(page)s%(per_page)s%(no_union)s%(status)s">%(data)s</a>' % args

        def _ids(key):
            return ':'.join([str(x) for x in schedules[key]])
    
        for id, title in self.provision_decree_keys:
            if data.get(id):
                data[id] = _link(status='&_ids=%s' % _ids(id), data=data[id])
            else:
                data[id] = '<div class="no-value">0</div>'

            args = {}
            for status in self.provision_decree_statuses:
                key = '%s-%s' % (id, status)

                try:
                    value = data[key]
                except:
                    continue

                args['data'] = value

                if not value:
                    data[key] = '<div class="no-value">%(data)s</div>' % args
                    continue
                elif status == 'overdue':
                    if key in schedules:
                        args['status'] = '&_ids=%s' % _ids(key)
                    else:
                        continue
                else:
                    args['status'] = '&_ids=%s' % _ids(key) #'&%s=%s' % (id, self.provision_decree_statuses[status])

                data[key] = _link(**args)

        #print('... data:', data)
        #print('... columns:', columns)

        self.point('schedule.decrees-finish')

        return data, columns

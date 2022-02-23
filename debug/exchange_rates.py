import os
import sys
import requests, json
from operator import itemgetter

sys.path.append(r'/storage/www/apps/perso/app')

from sqlalchemy import create_engine
from app.database import DatabaseEngine
from app.utils import getDate, getDateOnly

default_encoding = 'cp1251'
basedir = os.path.abspath(os.path.dirname(__file__))

DEFAULT_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S' # %H:%M:%S

passwd = '!iSbx_21/' # 'abcd'

#connection = { 'server':'172.19.9.69', 'user':'debug', 'password':passwd, 'database':'ProvisionDB', 'timeout':15 }
connection = { 'server':'172.19.9.62', 'user':'debug', 'password':passwd, 'database':'ProvisionDB', 'timeout':15 }
engine = create_engine('mssql+pymssql://%(user)s:%(password)s@%(server)s' % connection)
sql = 'SELECT * FROM [ProvisionDB].[dbo].[Payments_tb] order by TID desc'
cursor = engine.execute(sql)
mask = None

page = DatabaseEngine(name='provision', user=None, connection=connection)

config = {
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
}

rows = []

def get_data(name, **kw):
    return page.runQuery(name, config=config[name], **kw)

def printData(cursor, limit=None, mask=None):
    for n, row in enumerate(cursor):
        rows.append(row)
        if limit and n > limit:
            continue
        #print('--> %05d: %s' % (n, row))
        print('--> %05d: %s' % (n, (mask or '%s') % row))

rates = {}

def load_rates(currency, source, encoding=default_encoding):
    p = os.path.join(basedir, source)
    print(p)
    with open(p, 'r', encoding=encoding) as fin:
        for line in fin:
            if not line:
                continue
            s = line.split(';')
            date = getDate(s[0], format='%d.%m.%Y', is_date=True)
            rate = float(s[1].replace('"', '').replace(',', '.'))
            if date not in rates:
                rates[date] = {}
            rates[date][currency] = rate
        

name = 'provision-review-payments' # 'provision-order-payments'
columns = ('TID', 'PaymentDate', 'Total', 'OrderCurrency', 'Currency', 'Status', 'ExchangeRate',) #
where = "Currency='RUB' and OrderCurrency in ('EUR','USD') and ExchangeRate in (1.0, null) and PaymentDate<'2021-12-16'"
order = 'PaymentDate desc'
encode_columns = None
cursor = get_data(name, columns=columns, where=where, order=order, as_dict=1)
mask='%(TID)s %(PaymentDate)s %(OrderCurrency)s:%(Currency)s %(Total)s %(ExchangeRate)s'

printData(cursor, limit=10, mask=mask)
print('total payments: %s' % len(rows))

load_rates('EUR', 'rates/EURRUB.csv')
load_rates('USD', 'rates/USDRUB.csv')

print('rates:%s' % len(rates))
#print(rates)
#date = getDate('2021-12-15 00:00:00', format=DEFAULT_DATETIME_FORMAT, is_date=True)
#print('%s : %s' % (date, rates.get(date)))

sql = 'update [ProvisionDB].[dbo].[Payments_tb] set ExchangeRate=%d where TID=%d'

n = 0
for row in rows:
    tid = row['TID']
    payment_date = row['PaymentDate']
    currency = row['OrderCurrency']
    #print('TID: %s PaymentDate: %s Currency: %s' % (tid, payment_date, currency))
    if payment_date not in rates:
        continue
    exchange_rate = rates[payment_date][currency]
    args = (exchange_rate, tid)
    #print(sql, args)
    n += 1
    page.conn.execute(sql, args)

print('>>> %s' % n)
page.close()

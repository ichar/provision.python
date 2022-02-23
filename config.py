# -*- coding: cp1251 -*-

import os
import sys
import codecs
import datetime
import traceback
import imp

from collections import Iterable

basedir = os.path.abspath(os.path.dirname(__file__))
errorlog = os.path.join(basedir, 'traceback.log')

app_release = 2

# ----------------------------
# Global application constants
# ----------------------------

IsDebug                = 0  # Debug[stdout]: prints general info (1 - forbidden with apache!)
IsDeepDebug            = 0  # Debug[stdout]: prints detailed info (1 - forbidden with apache!)
IsTrace                = 1  # Trace[errorlog]: output execution trace for http-requests
IsSemaphoreTrace       = 0  # Trace[errorlog]: output trace for semaphore actions
IsLogTrace             = 1  # Trace[errorlog]: output detailed trace for Log-actions
IsTmpClean             = 1  # Flag: clean temp-folder
IsUseDecodeCyrillic    = 1  # Flag: sets decode cyrillic mode
IsUseDBLog             = 1  # Flag: sets DB OrderLog enabled to get log-messages
IsPrintExceptions      = 1  # Flag: sets printing of exceptions
IsForceRefresh         = 0  # Flag: sets http forced refresh for static files (css/js)
IsDecoderTrace         = 0  # Flag: sets decoder output
IsDisableOutput        = 0  # Flag: disabled stdout
IsShowLoader           = 0  # Flag: sets page loader show enabled
IsNoEmail              = 0  # Flag: don't send email
IsBankperso            = 0  # Flag: Bankperso application
IsProvision            = 1  # Flag: Provision application
IsPublic               = 1  # Flag: Public application
IsFuture               = 0  # Flag: opens inactive future menu items
IsDemo                 = 0  # Flag: sets demo-mode (inactive)
IsPageClosed           = 0  # Flag: page is closed or moved to another address (page_redirect)

PUBLIC_URL = 'http://192.168.0.88:5000/'

page_redirect = {
    'items'    : ('*',),
    'base_url' : '/auth/onservice',
    'logins'   : ('admin',),
    'message'  : 'Waiting 30 sec',
}

LocalDebug = {
    'bankperso'    : 0,
    'calculator'   : 0,
    'cards'        : 0,
    'catalog'      : 0,
    'configurator' : 0,
    'database'     : 0,
    'diamond'      : 0,
    'legal'        : 0,
    'mails'        : 0,
    'models'       : 0,
    'orderstate'   : 0,
    'persostation' : 0,
    'provision'    : 0,
    'purchase'     : 0,
    'sale'         : 0,
    'reporter'     : 0,
    'semaphore'    : 0,
    'settings'     : 0,
    'worker'       : 0,
    'workflow'     : 0,
}

LOCAL_FULL_TIMESTAMP   = '%d-%m-%Y %H:%M:%S'
LOCAL_EXCEL_TIMESTAMP  = '%d.%m.%Y %H:%M:%S'
LOCAL_EASY_TIMESTAMP   = '%d-%m-%Y %H:%M'
LOCAL_EASY_DATESTAMP   = '%Y-%m-%d'
LOCAL_EXPORT_TIMESTAMP = '%Y%m%d%H%M%S'
UTC_FULL_TIMESTAMP     = '%Y-%m-%d %H:%M:%S'
UTC_EASY_TIMESTAMP     = '%Y-%m-%d %H:%M'
DATE_TIMESTAMP         = '%d/%m'
DATE_STAMP             = '%Y%m%d'

default_print_encoding = 'cp866'
default_unicode        = 'utf-8'
default_encoding       = 'cp1251'
default_iso            = 'ISO-8859-1'

# ---------------------------- #

pwd1 = 'abcd'
pwd2 = '****'

CONNECTION = {}

SEMAPHORE_TEMPLATE = 'provision.semaphore'

if IsBankperso:
    CONNECTION.update({
        'semaphore'    : { 'server':'172.19.12.84:10999', 'user':'sa', 'password':'******', 'database':'BankDB',   'timeout':15, 'with_check':0 },
        'bankperso'    : { 'server':'172.19.12.84:10999', 'user':'sa', 'password':'******', 'database':'BankDB',   'timeout':15, 'with_check':0 },
        'cards'        : { 'server':'172.19.12.84:10999', 'user':'sa', 'password':'******', 'database':'Cards',    'timeout':15, 'with_check':0 },
        'configurator' : { 'server':'172.19.12.84:10999', 'user':'sa', 'password':'******', 'database':'BankDB',   'timeout':15, 'with_check':0 },
        'orderlog'     : { 'server':'172.19.12.84:10999', 'user':'sa', 'password':'******', 'database':'OrderLog', 'timeout':15, 'with_check':0, 'encoding':default_iso },
    })
    SEMAPHORE_TEMPLATE = 'bankperso.semaphore'

if IsProvision:
    CONNECTION.update({
        'semaphore'    : { 'server':'172.19.9.69', 'user':'debug', 'password':pwd1, 'database':'ProvisionDB', 'timeout':15, 'with_check':0 },
        #'diamond'      : { 'server':'172.19.9.69', 'user':'debug', 'password':pwd1, 'database':'DiamondDB',   'timeout':15 },
        #'legal'        : { 'server':'172.19.9.69', 'user':'debug', 'password':pwd1, 'database':'LegalDB',     'timeout':15 },
        #'personal'     : { 'server':'172.19.9.69', 'user':'debug', 'password':pwd1, 'database':'PersonalDB',  'timeout':15 },
        'provision'    : { 'server':'172.19.9.69', 'user':'debug', 'password':pwd1, 'database':'ProvisionDB', 'timeout':15 },
        'purchase'     : { 'server':'172.19.9.69', 'user':'debug', 'password':pwd1, 'database':'PurchaseDB',  'timeout':15 },
        'sale'         : { 'server':'172.19.9.69', 'user':'debug', 'password':pwd1, 'database':'SaleDB',      'timeout':15 },
        'workflow'     : { 'server':'172.19.9.69', 'user':'debug', 'password':pwd1, 'database':'WorkflowDB',  'timeout':15 },
        'storage'      : { 'server':'172.19.9.69', 'user':'debug', 'password':pwd1, 'database':'storage',     'timeout':15 },
    })


smtphost1 = {
    'host'         : '127.0.0.1', 
    'port'         : 25,
    'connect'      : None,
    'tls'          : 0,
    'method'       : 1,
    'from'         : 'mailrobot@rosan.ru',
}

smtphost2 = {
    'host'         : 'smtp-mail.outlook.com', 
    'port'         : 587,
    'connect'      : {'login' : "support@expresscard.ru", 'password' : "***"},
    'tls'          : 1,
    'method'       : 2,
    'from'         : 'support@expresscard.ru',
}

smtphosts = (smtphost1, smtphost2)

email_address_list = {
    'adminbd'      : '911@rosan.ru',     
    'support'      : 'support@expresscard.ru',
    'warehouse'    : 'dhperso@rosan.ru;dbadmin@rosan.ru;akts@it.rosan.ru;support@expresscard.ru',
    'mailrobot'    : 'mailrobot@rosan.ru',
}

image_encoding = {
}

BP_ROOT = { 
}

INFOEXCHANGE_ROOT = {
}

SDC_ROOT = {
}

EXCHANGE_ROOT = {
}

INDIGO_IMAGE_PATH = {
}

DEFAULT_ROOT = {
    'local'  : 'http://localhost:5000/',
    'public' : 'https://express.rosan.ru/',
}
POSTONLINE_DATA_PATH = ''

# ---------------------------- #

ansi = not sys.platform.startswith("win")

n_a = 'n/a'
cr = '\n'

def isIterable(v):
    return not isinstance(v, str) and isinstance(v, Iterable)

#######################################################################

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SSL_DISABLE = False

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    WTF_CSRF_ENABLED = False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'storage', 'app.db.debug')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'storage', 'app.db.new')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


config = { \
    'production' : ProductionConfig,
    'default'    : DevelopmentConfig,
}

##  --------------------------------------- ##

def setup_console(sys_enc=default_unicode):
    """
    Set sys.defaultencoding to `sys_enc` and update stdout/stderr writers to corresponding encoding
    .. note:: For Win32 the OEM console encoding will be used istead of `sys_enc`
    http://habrahabr.ru/post/117236/
    http://www.py-my.ru/post/4bfb3c6a1d41c846bc00009b
    """
    global ansi
    reload(sys)
    
    try:
        if sys.platform.startswith("win"):
            import ctypes
            enc = "cp%d" % ctypes.windll.kernel32.GetOEMCP()
        else:
            enc = (sys.stdout.encoding if sys.stdout.isatty() else
                        sys.stderr.encoding if sys.stderr.isatty() else
                            sys.getfilesystemencoding() or sys_enc)

        sys.setdefaultencoding(sys_enc)

        if sys.stdout.isatty() and sys.stdout.encoding != enc:
            sys.stdout = codecs.getwriter(enc)(sys.stdout, 'replace')

        if sys.stderr.isatty() and sys.stderr.encoding != enc:
            sys.stderr = codecs.getwriter(enc)(sys.stderr, 'replace')
    except:
        pass

def print_to(f, v, mode='ab', request=None, encoding=default_encoding):
    if IsDisableOutput:
        return
    items = not isIterable(v) and [v] or v
    if not f:
        f = getErrorlog()
    fo = open(f, mode=mode)
    def _out(s):
        if not isinstance(s, bytes):
            fo.write(s.encode(encoding, 'ignore'))
        else:
            fo.write(s)
        fo.write(cr.encode())
    for text in items:
        try:
            if IsDeepDebug or IsTrace:
                print(text)
            if request is not None:
                _out('%s>>> %s [%s]' % (cr, datetime.datetime.now().strftime(UTC_FULL_TIMESTAMP), request.url))
            _out(text)
        except Exception as e:
            pass
    fo.close()

def print_exception(stack=None):
    print_to(errorlog, '%s>>> %s:%s' % (cr, datetime.datetime.now().strftime(LOCAL_FULL_TIMESTAMP), cr))
    traceback.print_exc(file=open(errorlog, 'a'))
    if stack is not None:
        print_to(errorlog, '%s>>> Traceback stack:%s' % (cr, cr))
        traceback.print_stack(file=open(errorlog, 'a'))

def getErrorlog():
    return errorlog

def getCurrentDate():
    return datetime.datetime.now().strftime(LOCAL_EASY_DATESTAMP)

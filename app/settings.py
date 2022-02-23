# -*- coding: utf-8 -*-

import re
import random
import json
from datetime import datetime

# https://pypi.org/project/user-agents/
from user_agents import parse as user_agent_parse

from flask import Response, render_template, url_for, redirect, request, make_response, jsonify, flash, stream_with_context, g
from flask_login import login_required, current_user
from flask_babel import gettext

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsShowLoader, IsForceRefresh, IsPrintExceptions, 
     IsBankperso, IsProvision, IsPublic, IsFuture, 
     basedir, errorlog, print_to, print_exception, 
     LOCAL_EASY_TIMESTAMP, LOCAL_EASY_DATESTAMP, PUBLIC_URL, getCurrentDate, isIterable
)

from .patches import is_limited, is_forbidden

#
#   DON'T IMPORT utils HERE !!!
#

product_version = ('5.10', 'Final, 2022-02-10')

#########################################################################################

#   -------------
#   Default types
#   -------------

DEFAULT_LANGUAGE = 'ru'
DEFAULT_LOG_MODE = 1
DEFAULT_PER_PAGE = 10
DEFAULT_OPER_PER_PAGE = 50
DEFAULT_MANAGER_PER_PAGE = 20
DEFAULT_ADMIN_PER_PAGE = 10
DEFAULT_PAGE = 1
DEFAULT_UNDEFINED = '---'
DEFAULT_DATE_FORMAT = ('%d/%m/%Y', '%Y-%m-%d',)
DEFAULT_DATETIME_FORMAT = '<nobr>%Y-%m-%d</nobr><br><nobr>%H:%M:%S</nobr>'
DEFAULT_DATETIME_INLINE_FORMAT = '<nobr>%Y-%m-%d</nobr> <nobr>%H:%M:%S</nobr>' #'<nobr>%Y-%m-%d&nbsp;%H:%M:%S</nobr>'
DEFAULT_DATETIME_INLINE_SHORT_FORMAT = '<nobr>%Y-%m-%d</nobr><br><nobr>%H:%M</nobr>'
DEFAULT_DATETIME_PERSOLOG_FORMAT = ('%Y%m%d', '%Y-%m-%d %H:%M:%S',)
DEFAULT_DATETIME_SDCLOG_FORMAT = ('%d.%m.%Y', '%d.%m.%Y %H:%M:%S,%f',)
DEFAULT_DATETIME_EXCHANGELOG_FORMAT = ('%d.%m.%Y', '%Y-%m-%d %H:%M:%S.%f',)
DEFAULT_DATETIME_READY_FORMAT = '%b %d %Y %I:%M%p'
DEFAULT_DATETIME_TODAY_FORMAT = '%d.%m.%Y'
DEFAULT_HTML_SPLITTER = ':'
DEFAULT_USER_AVATAR = ('<img class="avatar" src="%s" title="%s" alt="%s">', '/static/img/person-default.jpg', '', 'jpg', (40, None))

USE_FULL_MENU = True

MAX_TITLE_WORD_LEN = 50
MAX_XML_BODY_LEN = round(1024*1024*2)
MAX_XML_TREE_NODES = 100
MAX_LOGS_LEN = 99999
MAX_CARDHOLDER_ITEMS = 4999
MAX_INDIGO_ITEMS = 999
MAX_LINK_LENGTH = 100
MAX_CONFIRMATION_LEN = 8000
MAX_UPLOADED_IMAGE = 10**8
EMPTY_VALUE = '...'
EMPTY_REFERENCE_VALUE = ' - не задано - '

# action types
VALID_ACTION_TYPES = ('101', '301',)

BATCH_TYPE_PERSO = 7

COMPLETE_STATUSES = (62, 64, 98, 197, 198, 199, 201, 202, 203, 255,)

SETTINGS_PARSE_XML = True

FILEDATA        = 'FileData'
FILEINFO        = 'FileInfo'
FILEBODY_RECORD = 'FileBody_Record'
FILERECNO       = 'FileRecNo'
PROCESSINFO     = 'ProcessInfo'

default_locale = 'rus'

_citi_tags = (
    'CompanyName:ClientName:',
    'AddressLine1:AddressLine2:AddressLine3:AddressLine4:AddressLine5:AddressLine6:AddressLine7:',
    'PLASTIC:CARD_TYPE:Urgency:PROCESS_ERR_MSG:Envelope:Insert1:Insert2:',
    'PROCESS_ERR_MSG',
    'Client:CDT_NAME:PlasticWH_ContainerList:DELIV_INC:AREP_NAME:Sort:CheckInfo:'
    'Insert3:Insert4:Insert5:Insert6:Insert7:Insert8:Insert9:Insert10:Insert11'
)

_bin_bank_tags = (
    'CityDOS:StreetDOS:Addressee:AddresseeDOS',
    'BADDR:City:Street',
)

IMAGE_TAGS_DECODE_CYRILLIC = {
    'CITI_BANK' : (
        ('CITIEMV',), (
            ('wintodos', {
                'default' : {'.' : _citi_tags[0] + _citi_tags[1] + _citi_tags[2]},
                'record'  : {'.' : _citi_tags[0] + _citi_tags[1] + _citi_tags[2]},
                'image'   : {},
                'errors'  : {'.' : _citi_tags[3]},
            }),
            ('dostowin', {
                'default' : {'AREP_Record' : _citi_tags[0] + _citi_tags[1], '.' : _citi_tags[3]},
            }),
            ('iso', {
                'errors'  : {'.' : _citi_tags[3]},
            }),
        ),
    ),
    'BIN_BANK' : (
        None, (
            ('wintodos', {
                'default' : {'.' : _bin_bank_tags[0]},
            }),
        ),
    ),
}

PAN_TAGS = 'PAN:PANWIDE:PANCVC2:DLV_Record:DTC_Record:PIN_Record:OTK_Track1:OTK_Track2:TRACK1:TRACK2:PROCESS_ERR_MSG'

SEMAPHORE = {
    'count'    : 7,
    'timeout'  : 5000,
    'action'   : '901',
    'speed'    : '100:1000',
    'seen_at'  : (5,10,),
    'inc'      : (1,1,1,1,1,1,1,),
    'duration' : (9999, 5000, 0, 0, 0, 3000, -1,),
}

INDIGO_FILETYPES = ('Raiffeisen_ID', 'PostBank_ID', 'PostBank_IDM')
INDIGO_DEFAULT_IMAGE = '/static/img/no-image.jpg'
INDIGO_DEFAULT_MODE = 'base64'
INDIGO_DEFAULT_SIZE = (200, 120) # None
INDIGO_IMAGE_TYPE = 'jpg'

PROCESS_INFO = {
    'clients'   : ('PostBank:$P', 'PostBank:$E',),
    'filetypes' : ('PostBank_ID', 'PostBank_IDM', 'PostBank_CL',),
}

DATE_KEYWORDS = ('today', 'yesterday', 'tomorrow',)
EXTRA_ = '__'

APP_MODULES = (
    'admin',
    'bankperso',
    'calculator',
    'cards',
    'configurator',
    'diamond',
    'persostation',
    'provision',
)

APP_MENUS = [
    'default',
    'bankperso',
    'calculator',
    'diamond',
    'personal',
    'persostation',
    'provision',
    'sale',
    'purchase',
    'headoffice',
    'demo',
]

CALENDAR_HOLIDAYS = (
    '20200101', '20200102', '20200103', '20200104', '20200105', '20200106', '20200107', '20200108', '20200109', '20200110', '20200111', '20200112', 
    '20200224', 
    '20200309', 
    '20200501', '20200504', '20200505', '20200511', 
    '20200612', 
    '20201104', 
    '20210101', '20210104', '20210105', '20210106', '20210107', '20210108', 
    '20210222', '20210223', 
    '20210308', 
    '20210503', '20210510', 
    '20210614', 
    '20211104', '20211105', 
    '20211231', 
)

CALENDAR_WORKDAYS = (
    '20210220', 
)

CEO_LOGIN = 'aybazov'

## ================================================== ##

_agent = None
_user_agent = None

def IsAndroid():
    return _agent.platform == 'android'
def IsiOS():
    return _agent.platform == 'ios' or 'iOS' in _user_agent.os.family
def IsiPad():
    return _agent.platform == 'ipad' or 'iPad' in _user_agent.os.family
def IsLinux():
    return _agent.platform == 'linux'

def IsChrome():
    return _agent.browser == 'chrome'
def IsFirefox():
    return _agent.browser == 'firefox'
def IsSafari():
    return _agent.browser == 'safari' or 'Safari' in _user_agent.browser.family
def IsOpera():
    return _agent.browser == 'opera' or 'Opera' in _user_agent.browser.family

def IsIE(version=None):
    ie = _agent.browser.lower() in ('explorer', 'msie',)
    if not ie:
        return False
    elif version:
        return float(_agent.version) == version
    return float(_agent.version) < 10
def IsSeaMonkey():
    return _agent.browser.lower() == 'seamonkey'
def IsEdge():
    return 'Edge' in _agent.string
def IsMSIE():
    return _agent.browser.lower() in ('explorer', 'ie', 'msie', 'seamonkey',) or IsEdge()

def IsMobile():
    return IsAndroid() or IsiOS() or IsiPad() or _user_agent.is_mobile or _user_agent.is_tablet
def IsNotBootStrap():
    return IsIE(10) or IsAndroid()
def IsWebKit():
    return IsChrome() or IsFirefox() or IsOpera() or IsSafari()

def BrowserVersion():
    return _agent.version

def BrowserInfo(force=None):
    mobile = 'IsMobile:[%s]' % (IsMobile() and '1' or '0')
    info = 'Browser:[%s] %s Agent:[%s]' % (_agent.browser, mobile, _agent.string)
    browser = IsMSIE() and 'IE' or IsOpera() and 'Opera' or IsChrome() and 'Chrome' or IsFirefox() and 'FireFox' or IsSafari() and 'Safari' or None
    if force:
        return info
    return browser and '%s:%s' % (browser, mobile) or info

## -------------------------------------------------- ##

def get_request_item(name, check_int=None, args=None, is_iterable=None):
    if args:
        x = args.get(name)
    elif request.method.upper() == 'POST':
        if is_iterable:
            return request.form.getlist(name)
        else:
            x = request.form.get(name)
    else:
        x = None
    if not x and (not check_int or (check_int and x in (None, ''))):
        x = request.args.get(name)
    if check_int:
        if x in (None, ''):
            return None
        elif x.isdigit():
            return int(x)
        elif ':' in x:
            return x
        elif x in 'yY':
            return 1
        elif x in 'nN':
            return 0
        else:
            return None
    if x:
        if x == DEFAULT_UNDEFINED or x.upper() == 'NONE':
            x = None
        elif x.startswith('{') and x.endswith('}'):
            return eval(re.sub('null', '""', x))
    return x or ''

def get_request_items():
    return request.method.upper() == 'POST' and request.form or request.args

def has_request_item(name):
    return name in request.form or name in request.args

def get_request_search():
    return get_request_item('reset_search') != '1' and get_request_item('search') or ''

def get_page_params(view=None):
    is_admin = g.current_user.is_administrator(private=True)
    is_manager = g.current_user.is_manager(private=True)
    is_operator = g.current_user.is_operator(private=True)

    page = 0
    per_page = int(get_request_item('per_page') or get_request_item('per-page') or 0)

    default_per_page = view and g.current_user.get_pagesize(view) or (
        #view in ('admin',) and DEFAULT_ADMIN_PER_PAGE or
        is_manager and DEFAULT_MANAGER_PER_PAGE or
        #is_operator and DEFAULT_OPER_PER_PAGE or
        view in ('cards',) and DEFAULT_PER_PAGE * 2 or
        DEFAULT_PER_PAGE
        )
    
    try:
        if not per_page:
            per_page = default_per_page
        else:
            g.current_user.set_pagesize(view, per_page)
        page = int(get_request_item('page') or DEFAULT_PAGE)
    except:
        if IsPrintExceptions:
            print_exception()
        per_page = default_per_page
        page = DEFAULT_PAGE
    finally:
        if per_page <= 0 or per_page > 1000:
            per_page = default_per_page
        if page <= 0:
            page = DEFAULT_PAGE

    next = get_request_item('next') and True or False
    prev = get_request_item('prev') and True or False

    if next:
        page += 1
    if prev and page > 1:
        page -= 1
    
    return page, per_page

def default_user_avatar(user=None):
    return DEFAULT_USER_AVATAR[0] % (DEFAULT_USER_AVATAR[1], user and user.get_user_post() or DEFAULT_USER_AVATAR[2], user and user.login or '')

def make_platform(mode=None, debug=None):
    global _agent, _user_agent

    agent = request.user_agent
    browser = agent.browser

    if browser is None:
        return { 'error' : 'Access is not allowed!' }

    os = agent.platform
    root = '%s/' % request.script_root

    _agent = agent
    _user_agent = user_agent_parse(agent.string)

    if IsTrace and g.system_config.IsLogAgent:
        print_to(errorlog, '\n==> agent:%s[%s], browser:%s' % (repr(agent), _user_agent, browser), request=request)

    is_owner = False
    is_admin = False
    is_manager = True
    is_operator = False

    avatar = None
    sidebar_collapse = False

    try:
        is_owner = g.current_user.is_owner()
        is_admin = g.current_user.is_administrator(private=False)
        is_manager = g.current_user.is_manager(private=True)
        is_operator = g.current_user.is_operator(private=True)
        avatar = g.current_user.get_avatar()

        if has_request_item('sidebar'):
            sidebar_collapse = get_request_item('sidebar', check_int=True) == 0 and True or False
            if sidebar_collapse != g.current_user.sidebar_collapse:
                g.current_user.sidebar_collapse = sidebar_collapse
        else:
            sidebar_collapse = g.current_user.sidebar_collapse
    except:
        pass

    sidebar_state = not sidebar_collapse and 1 or 0

    referer = ''
    links = {}

    is_mobile = IsMobile()
    is_default = 1 or os in ('ipad', 'android',) and browser in ('safari', 'chrome',) and 1 or 0 
    is_frame = not is_mobile and 1 or 0

    version = agent.version
    css = IsMSIE() and 'ie' or is_mobile and 'mobile' or 'web'

    platform = '[os:%s, browser:%s (%s), css:%s, %s %s%s%s]' % (
        os, 
        browser, 
        version, 
        css, 
        default_locale, 
        is_default and ' default' or ' flex',
        is_frame and ' frame' or '', 
        debug and ' debug' or '',
    )

    kw = {
        'os'             : os, 
        'platform'       : platform,
        'root'           : root, 
        'back'           : '',
        'agent'          : agent.string,
        'version'        : version, 
        'browser'        : browser, 
        'browser_info'   : BrowserInfo(0),
        'is_linux'       : IsLinux() and 1 or 0,
        'is_demo'        : 0, 
        'is_frame'       : is_frame, 
        'is_mobile'      : is_mobile and 1 or 0,
        'is_admin'       : is_admin and 1 or 0,
        'is_operator'    : (is_operator or is_manager or is_admin) and not is_owner and 1 or 0,
        'is_show_loader' : IsShowLoader,
        'is_explorer'    : IsMSIE() and 1 or 0,
        'css'            : css, 
        'referer'        : referer, 
        'bootstrap'      : '',
    }

    if mode:
        kw[mode] = True

    if mode in ('auth',):
        kw['bootstrap'] = '-new'

    kw.update({
        'links'          : links, 
        'style'          : {'default' : is_default, 'header' : datetime.today().day%2==1 and 'dark' or 'light', 'show_scroller' : 0},
        'screen'         : request.form.get('screen') or '',
        'scale'          : request.form.get('scale') or '',
        'usertype'       : is_manager and 'manager' or is_operator and 'operator' or 'default',
        'sidebar'        : {'state' : sidebar_state, 'title' : gettext('Click to close top menu')},
        'avatar'         : avatar,
        'with_avatar'    : 1,
        'with_post'      : 1,
        'logo'           : '', 
        'image_loader'   : '%s%s' % (root, 'static/img/loader.gif'), 
    })

    kw['is_active_scroller'] = 0 if IsMSIE() or IsFirefox() or is_mobile else (g.system_config.IsActiveScroller and 1 or 0)

    if IsTrace and IsDeepDebug:
        print_to(errorlog, '--> make_platform:%s' % mode)

    return kw

def make_keywords():
    return (
        # --------------
        # Error Messages
        # --------------
        "'Execution error':'%s'" % gettext('Execution error'),
        # -------
        # Buttons
        # -------
        "'Add':'%s'" % gettext('Add'),
        "'Back':'%s'" % gettext('Back'),
        "'Calculate':'%s'" % gettext('Calculate'),
        "'Cancel':'%s'" % gettext('Cancel'),
        "'Confirm':'%s'" % gettext('Confirm'),
        "'Close':'%s'" % gettext('Close'),
        "'Execute':'%s'" % gettext('Execute'),
        "'Finished':'%s'" % gettext('Done'),
        "'Frozen link':'%s'" % gettext('Frozen link'),
        "'Link':'%s'" % gettext('Link'),
        "'OK':'%s'" % gettext('OK'),
        "'Open':'%s'" % gettext('Open'),
        "'Reject':'%s'" % gettext('Decline'),
        "'Rejected':'%s'" % gettext('Rejected'),
        "'Remove':'%s'" % gettext('Remove'),
        "'Run':'%s'" % gettext('Run'),
        "'Save':'%s'" % gettext('Save'),
        "'Search':'%s'" % gettext('Search'),
        "'Select':'%s'" % gettext('Select'),
        "'Update':'%s'" % gettext('Update'),
        # ----
        # Help
        # ----
        "'Attention':'%s'" % gettext('Attention'),
        "'All':'%s'" % gettext('All'),
        "'Commands':'%s'" % gettext('Commands'),
        "'Help':'%s'" % gettext('Help'),
        "'Help information':'%s'" % gettext('Help information'),
        "'Helper keypress guide':'%s'" % gettext('Helper keypress guide'),
        "'System information':'%s'" % gettext('System information'),
        "'Total':'%s'" % gettext('Total'),
        # --------------------
        # Flags & Simple Items
        # --------------------
        "'error':'%s'" % gettext('error'),
        "'yes':'%s'" % gettext('Yes'),
        "'no':'%s'" % gettext('No'),
        "'none':'%s'" % gettext('None'),
        "'true':'%s'" % 'true',
        "'false':'%s'" % 'false',
        # ------------------------
        # Miscellaneous Dictionary
        # ------------------------
        "'batch':'%s'" % gettext('batch'),
        "'Choose a File':'%s...'" % gettext('Choose a File'),
        "'Confirm notification form':'%s'" % gettext('Confirm notification form'),
        "'create selected file':'%s'" % gettext('create selected file'),
        "'delete selected file':'%s'" % gettext('delete selected file'),
        "'report of selected file':'%s'" % gettext('report of selected file'),
        "'file':'%s'" % gettext('file'),
        "'group stocklist':'%s'" % gettext('Group stocklist action'),
        "'Image view':'%s'" % gettext('Image view'),
        "'Option:Keep status history':'%s'" % gettext('Option: Keep status history'),
        "'ID provision order':'%s'" % gettext('ID order'),
        "'ID sale order':'%s'" % gettext('ID document'),
        "'ID purchase order':'%s'" % gettext('ID document'),
        "'ID workflow order':'%s'" % gettext('ID document'),
        "'No data':'%s'" % gettext('No data'),
        "'No data or access denied':'%s'" % gettext('No data'),
        "'No documents':'%s'" % gettext('No documents'),
        "'Notification form':'%s'" % gettext('Notification form'),
        "'of batch':'%s'" % gettext('of batch'),
        "'of file':'%s'" % gettext('of file'),
        "'order confirmation':'%s'" % gettext('Are you really going to'),
        "'select referenced item':'%s:'" % gettext('Choice the requested item from the given list'),
        "'shortcut version':'%s'" % '1.0',
        "'status confirmation':'%s'" % gettext('Are you really going to change the status'),
        "'status confirmation request':'%s:'" % gettext('Choice the requested status from the given list'),
        "'please confirm':'%s.'" % gettext('Please, confirm'),
        "'Print processing info':'%s'" % gettext('Print processing info'),
        "'Processing info':'%s'" % gettext('Processing info'),
        "'Recovery is impossible!':'%s'" % gettext('Recovery is impossible!'),
        "'Status confirmation form':'%s'" % gettext('Status confirmation form'),
        "'top-close':'%s'" % gettext('Click to close top menu'),
        "'top-open':'%s'" % gettext('Click to open top menu'),
        # -------------
        # Notifications
        # -------------
        "'Admin Find':'%s'" % gettext('Find (name, login, email)'),
        "'Assign delivery date for the current order':'%s'" % gettext('Assign delivery date for the current order.'),
        "'Assign failure date for the current order':'%s'" % gettext('Assign failure date for the current order.'),
        "'Assign pay date for the current order':'%s'" % gettext('Assign pay date for the current order.'),
        "'Data corresponds to the current status':'%s'" % gettext('Data corresponds to the current status.'),
        "'Data will be filtered accordingly':'%s'" % gettext('Data will be filtered accordingly.'),
        "'Do you realy wish to accept selected payments':'%s'" % gettext('Do you realy wish to accept selected payments'),
        "'Do you realy wish to reject selected payments':'%s'" % gettext('Do you realy wish to reject selected payments'),
        "'Check form items to apply Seller attributes':'%s'" % gettext('Check form items to apply Seller attributes in the orders.'),
        "'Check form items to apply Stock attributes':'%s'" % gettext('Check form items to apply Stock attributes in the orders.'),
        "'Command:Activate selected batch':'%s'" % gettext('Command: Activate selected batch?'),
        "'Command:Activate selected batches':'%s'" % gettext('Command: Activate selected batches?'),
        "'Command:Config item removing':'%s'" % gettext('Command: Do you really want to remove the config item?'),
        "'Command:Config scenario removing':'%s'" % gettext('Command: Do you really want to remove the config scenario?'),
        "'Command:Decree finish':'%s'" % gettext('Command: Do you really want to finish the current decree?'),
        "'Command:Decree reject':'%s'" % gettext('Command: Do you really want to reject the current decree?'),
        "'Command:Decree remove':'%s'" % gettext('Command: Do you really want to remove the current decree?'),
        "'Command:Item was changed. Continue?':'%s'" % gettext('Command: Item was changed. Continue?'),
        "'Command:Photo item removing. Continue?':'%s'" % gettext('Command: Photo item removing. Continue?'),
        "'Command:Provision Order removing':'%s'" % gettext('Command: Do you really want to remove the document?'),
        "'Command:Provision Orders downloading':'%s'" % gettext('Command: Do you really want to download the document?'),
        "'Command:Provision Orders deleting':'%s'" % gettext('Command: Do you really want to remove documents?'),
        "'Command:Provision Orders history clearing':'%s'" % gettext('Command: Do you really want to clear document history?'),
        "'Command:Reference item removing':'%s'" % gettext('Command: Do you really want to remove the reference item?'),
        "'Command:Reject activation':'%s'" % gettext('Command: Do you really want to reject selected batches?'),
        "'Command:Provision Orders send approval request':'%s'" % gettext('Command: Do you wish to send approval request to the Order author?'),
        "'Command:Provision Order notification request':'%s'" % gettext('Command: Do you wish to send notification request to the Order reviewers?'),
        "'Command:Provision Review notification request':'%s'" % gettext('Command: Do you wish to send notification requests to reviewers?'),
        "'Command:Send request to the warehouse':'%s'" % gettext('Command: Send request to the warehouse?'),
        "'Command:Workflow Order removing':'%s'" % gettext('Command: Do you really want to remove the document?'),
        "'Exclamation:exists_inactive':'%s'" % gettext('Exclamation: Exist inactive batches'),
        "'Exclamation:exists_materials':'%s'" % gettext('Exclamation: Exist materials to send in order'),
        "'Input form items to edit Seller attributes':'%s'" % gettext('Input form items to edit Seller attributes.'),
        "'Input form items to edit Stock attributes':'%s'" % gettext('Input form items to edit Stock attributes.'),
        "'Item will be removed from database!':'%s'" % gettext("Be carefull! Item will be removed from database."),
        "'Its not realized yet!':'%s'" % gettext("Sorry! Its not realized yet."),
        "'Message:Action was done successfully':'%s'" % gettext('Message: Action was done successfully.'),
        "'Message:Request sent successfully':'%s'" % gettext('Message: Request was sent successfully.'),
        "'OK:exists_inactive':'%s'" % gettext('OK: All batches done'),
        "'OK:exists_materials':'%s'" % gettext('OK: Materials OK'),
        "'Order delivery date':'%s'" % gettext('Order delivery date'),
        "'Order delivery date assigment see in the application documentation':'%s'" % gettext('Order delivery date assigment see in the application documentation.'),
        "'Order failure date':'%s'" % gettext('Order failure date'),
        "'Order failure date assigment see in the application documentation':'%s'" % gettext('Order failure date assigment see in the application documentation.'),
        "'Order pay date':'%s'" % gettext('Order pay date'),
        "'Order pay date assigment see in the application documentation':'%s'" % gettext('Order pay date assigment see in the application documentation.'),
        "'Payments Review confirmation':'%s'" % gettext('Payments Review confirmation'),
        "'Review due date':'%s'" % gettext('Review due date'),
        "'Review confirmation rules see in the application documentation':'%s'" % gettext('Review confirmation rules see in the application documentation.'),
        "'Seller rules see in the application documentation':'%s'" % gettext('Seller rules see in the application documentation.'),
        "'Stock rules see in the application documentation':'%s'" % gettext('Stock rules see in the application documentation.'),
        "'Title:Create form of':'%s '" % gettext('Create form of'),
        "'Title:Update form of':'%s '" % gettext('Update form of'),
        "'Title:Clone form of':'%s '" % gettext('Clone form of'),
        "'You have to assign due date for confirmation of the order':'%s'" % gettext('You have to assign due date for confirmation of the order.'),
        "'Warning:No inactive batches':'%s'" % gettext('Warning: All batches for the given file are already activated.'),
        "'Warning:No report data':'%s'" % gettext('Warning: No report data.'),
        "'Warning:No selected items':'%s'" % gettext('Warning: Please, select items to execute before.'),
        "'Warning:This operation may take a long time':'%s'" % gettext('Warning: This operation may take a long time. Are you sure?'),
    )

def init_response(title):
    host = request.form.get('host') or request.host_url

    if 'debug' in request.args:
        debug = request.args['debug'] == '1' and True or False
    else:
        debug = None

    kw = make_platform(debug=debug)
    keywords = make_keywords()
    forms = ('index', 'admin',)

    now = datetime.today().strftime(DEFAULT_DATE_FORMAT[1])

    kw.update({
        'title'        : '%s. %s' % (gettext('ROSAN'), gettext(title)),
        'host'         : host,
        'locale'       : default_locale, 
        'language'     : 'ru',
        'keywords'     : keywords, 
        'forms'        : forms,
        'now'          : now,
        'action_id'    : get_request_item('action_id') or '0',
        'batch_id'     : get_request_item('batch_id') or '0',
        'event_id'     : get_request_item('event_id') or '0',
        'file_id'      : get_request_item('file_id') or '0',
        'oper_id'      : get_request_item('oper_id') or '0',
        'order_id'     : get_request_item('order_id') or '0',
        'pers_id'      : get_request_item('pers_id') or '0',
        'preload_id'   : get_request_item('preload_id') or '0',
        'review_id'    : get_request_item('review_id') or '0',
    })

    kw['selected_data_menu_id'] = get_request_item('selected_data_menu_id')
    kw['window_scroll'] = get_request_item('window_scroll')
    kw['avatar_width'] = '80'

    return debug, kw

def vsc(force=False):
    return (IsIE() or IsForceRefresh or force) and ('?%s' % str(int(random.random()*10**12))) or ''

def is_app_public():
    return IsPublic and request.host_url == PUBLIC_URL

def is_app_bankperso():
    return IsBankperso and not is_app_public() and 1 or 0

def is_app_provision():
    return IsProvision

def get_navigation():
    is_admin = g.current_user.is_administrator()
    is_superuser = g.current_user.is_superuser()
    is_manager = g.current_user.is_manager()
    is_operator = g.current_user.is_operator()

    items = []

    app_menu = g.current_user.app_menu
    base_url = g.current_user.base_url

    def _item(key):
        return key, '/%s' % key

    def _get_item_url(key):
        x = key in base_url and base_url or key
        return '%s%s' % (request.script_root, x.startswith('/') and x or '/' + x)

    if g.current_user.is_authenticated:
        if app_menu in ('bankperso', 'default'):
            if is_superuser:
                items.append({'link'  : '%s/admin/index' % request.script_root, 
                              'id'    : 'mainmenu-admin',
                              'title' : 'Администратор', 
                              'class' : '/admin' in request.url and 'selected' or ''})

        if is_app_bankperso():
            if app_menu in ('bankperso', 'default'):
                key, link = _item('bankperso')
                if (USE_FULL_MENU or link not in request.url) and not is_limited(key):
                    items.append({'link'  : '%s/bankperso' % request.script_root, 
                                  'id'    : 'mainmenu-bankperso',
                                  'title' : 'БанкПерсо', 
                                  'class' : (link in request.url or request.url_rule.rule == '/') and 'selected' or ''})

                key, link = _item('cards')
                if (is_admin or is_operator) and (USE_FULL_MENU or link not in request.url) and not is_limited(key):
                    items.append({'link'  : '%s/cards' % request.script_root,
                                  'id'    : 'mainmenu-cards',
                                  'title' : 'Персонализация', 
                                  'class' : link in request.url and 'selected' or ''})

                key, link = _item('configurator')
                if (USE_FULL_MENU or (link not in request.url and is_admin)) and not is_limited(key):
                    items.append({'link'  : '%s/%s' % (request.script_root, key), 
                                  'id'    : 'mainmenu-configurator',
                                  'title' : 'Конфигуратор',
                                  'class' : link in request.url and 'selected' or ''})

        if is_app_provision():
            if app_menu in ('calculator', 'demo', 'default',):
                if not is_forbidden('show') and (USE_FULL_MENU or '/show' not in request.url):
                    items.append({'link'  : _get_item_url('show'),
                                  'id'    : 'mainmenu-show',
                                  'title' : 'Калькулятор',
                                  'class' : '/show' in request.url and 'selected' or ''})
            if app_menu in ('diamond', 'demo', 'default',):
                if not is_forbidden('catalog') and (USE_FULL_MENU or '/catalog' not in request.url):
                    items.append({'link'  : _get_item_url('catalog'),
                                  'id'    : 'mainmenu-catalog',
                                  'title' : 'Продукция',
                                  'class' : '/catalog' in request.url and 'selected' or ''})
            if app_menu in ('workflow', 'diamond', 'personal', 'provision', 'workflow', 'demo', 'headoffice', 'default',):
                if not is_forbidden('workflow') and (USE_FULL_MENU or '/workflow' not in request.url):
                    items.append({'link'  : _get_item_url('workflow'),
                                  'id'    : 'mainmenu-workflow',
                                  'title' : 'Секретариат', 
                                  'class' : '/workflow' in request.url and 'selected' or ''})
            if app_menu in ('diamond', 'personal', 'provision', 'sale', 'demo', 'headoffice', 'default',):
                if not is_forbidden('sale') and (USE_FULL_MENU or '/sale' not in request.url):
                    items.append({'link'  : _get_item_url('sale'),
                                  'id'    : 'mainmenu-sale',
                                  'title' : 'Продажи', 
                                  'class' : '/sale' in request.url and 'selected' or ''})
            if app_menu in ('diamond', 'personal', 'provision', 'purchase', 'demo', 'headoffice', 'default',):
                if not is_forbidden('purchase') and (USE_FULL_MENU or '/purchase' not in request.url):
                    items.append({'link'  : _get_item_url('purchase'),
                                  'id'    : 'mainmenu-purchase',
                                  'title' : 'Закупки', 
                                  'class' : '/purchase' in request.url and 'selected' or ''})
            """
            if app_menu in ('demo', 'personal', 'headoffice', 'default',):
                if not is_forbidden('personal') and (USE_FULL_MENU or '/personal' not in request.url):
                    items.append({'link'  : _get_item_url('personal'),
                                  'id'    : 'mainmenu-personal',
                                  'title' : 'Персонал', 
                                  'class' : '/personal' in request.url and 'selected' or ''})
            if app_menu in ('demo', 'diamond', 'headoffice', 'default',):
                if not is_forbidden('diamond') and (USE_FULL_MENU or '/diamond' not in request.url):
                    items.append({'link'  : _get_item_url('diamond'),
                                  'id'    : 'mainmenu-diamond',
                                  'title' : 'Производство', 
                                  'class' : '/diamond' in request.url and 'selected' or ''})
            """
            if app_menu in ('diamond', 'personal', 'provision', 'demo', 'headoffice', 'default',):
                if is_manager and (USE_FULL_MENU or '/provision' not in request.url):
                    items.append({'link'  : _get_item_url('provision'),
                                  'id'    : 'mainmenu-provision',
                                  'title' : 'Снабжение', 
                                  'class' : '/provision' in request.url and 'selected' or ''})
            if app_menu in ('diamond', 'sale', 'personal', 'provision', 'demo', 'headoffice', 'default',):
                if is_manager and (USE_FULL_MENU or '/provision/payments' not in request.url):
                    items.append({'link'  : '%s/provision/payments/current' % request.script_root,
                                  'id'    : 'mainmenu-payments',
                                  'title' : 'Платежи', 
                                  'class' : '/provision/payments' in request.url and 'selected' or '',
                                  'target': '_blank'})
            if app_menu in ('diamond', 'sale', 'personal', 'provision', 'demo', 'headoffice', 'default',):
                if is_manager and (USE_FULL_MENU or '/decrees/' not in request.url):
                    args = '?with_login=1'
                    try:
                        if g.page.app_role_ceo:
                            args = ''
                    except:
                        pass
                    items.append({'link'  : '%s/decrees/default%s' % (request.script_root, args),
                                  'id'    : 'mainmenu-decrees',
                                  'title' : 'Поручения', 
                                  'class' : '/decrees/default' in request.url and 'selected' or '',
                                  'target': '_blank'})
            if app_menu in ('headoffice', 'default',):
                if is_manager and (USE_FULL_MENU or '/finance' not in request.url):
                    items.append({'link'  : '%s/provision/finance' % request.script_root,
                                  'id'    : 'mainmenu-finance',
                                  'title' : 'Статистика', 
                                  'class' : '/finance' in request.url and 'selected' or '',
                                  'target': '_blank'})
            if app_menu in ('provision', 'demo', 'headoffice', 'default',):
                if is_manager and (USE_FULL_MENU or '/barcode' not in request.url):
                    items.append({'link'  : '%s/provision/barcode' % request.script_root,
                                  'id'    : 'mainmenu-barcode',
                                  'title' : 'Склад', 
                                  'class' : '/barcode' in request.url and 'selected' or '',
                                  'target': '_blank'})

        items.append({'link' : '%s/auth/logout' % request.script_root, 'title': 'Выход', 'class':''})
    else:
        items.append({'link' : '%s/auth/login' % request.script_root, 'title': 'Вход', 'class':''})

    return items

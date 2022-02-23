# -*- coding: utf-8 -*-

import random

from config import (
     SEMAPHORE_TEMPLATE, CONNECTION, 
     IsDebug, IsDeepDebug, IsSemaphoreTrace, IsTrace, IsBankperso, LocalDebug, errorlog, print_to, print_exception,
     default_unicode, default_encoding,
     UTC_FULL_TIMESTAMP
     )

from . import semaphore

from ..settings import *
from ..database import database_config, DatabaseEngine
from ..utils import getToday, getDate, getTime

##  =================
##  Semaphore Package
##  =================

default_page = 'semaphore'
default_template = SEMAPHORE_TEMPLATE or 'bankperso.semaphore'
default_action = '900'
engine = None

IsLocalDebug = LocalDebug[default_page]

def before(f):
    def wrapper(**kw):
        global engine
        name = kw.get('engine') or 'semaphore'
        engine = DatabaseEngine(name=name, connection=CONNECTION[name])
        return f(**kw)
    return wrapper

@before
def refresh(**kw):
    return

def _get_state(semaphore):
    return '%(count)s::%(timeout)s::%(action)s::%(speed)s' % semaphore

def _get_item(value, duration):
    return {'value':value, 'duration':duration}

@before
def initDefaultSemaphore(**kw):
    lid = '0:0'

    template = kw.get('template') or default_template

    seen_at = SEMAPHORE['seen_at']

    params = "0,0,0,null,''"
    cursor = engine.runQuery(template, params=params)
    if cursor:
        oid, bid = cursor[0]

        if seen_at and oid and bid:
            if len(seen_at) > 0 and seen_at[0] > 0:
                oid -= seen_at[0]
            if len(seen_at) > 1 and seen_at[1] > 0:
                bid -= seen_at[1]

        lid = '%s:%s' % (oid or 0, bid or 0)

    if template.startswith('provision'):
        titles = (
                'Provision Order created',
                'Provision Order deleted',
                'Provision Order changed or reviewed',
                'Review Paid',
                'Review Finished',
                'Review Accepted',
                'Review Rejected',
            )
    elif template.startswith('cards'):
        titles = (
                'New batch created',
                'Batch deleted',
                'Status changed',
                'Oper is activated',
                'Batch/Oper is finished',
                'Batch is successfully completed',
                'Batch error',
            )
    else:
        titles = (
                'New order created',
                'Order deleted',
                'Status changed',
                'Batch is activated',
                'Order/Batch is finished',
                'Order is successfully completed',
                'Order error',
            )

    return {
        'state' : '%s::%s::%s' % (
                template, lid, _get_state(SEMAPHORE)
            ),
        'count' : SEMAPHORE['count'],
        'ids'   : ['%s' % n for n in range(SEMAPHORE['count'])],
        'items' : [_get_item(0, 0) for n in range(SEMAPHORE['count'])],
        'titles': titles,
    }

def getCurrentState(template, lid):
    """
        Semapore items:
            0 -- blue: new file created 'I'
            1 -- magenta: file deleted 'D'
            2 -- yellow: status changed 'U'
            3 -- orange: batch is activated 'U'
            4 -- cyan: status of order/batch is finished 'U'
            5 -- green: order is ready
            6 -- red: error
    """
    items = [0 for n in range(SEMAPHORE['count'])]

    oid, bid = [int(x) for x in lid.split(':')]
    new_lid = [oid, bid]

    if IsLocalDebug:
        #items = [0 for n in range(SEMAPHORE['count'])] #random.randint(0, 3)
        if template.startswith('cards'):
            test_oid = oid = random.randint(2316000, oid)
            test_bid = bid = random.randint(6709900, bid)
        else:
            test_oid = oid = random.randint(3527800, oid)
            test_bid = bid = random.randint(5711470, bid)

    inc = SEMAPHORE['inc']

    # ----------------------
    # FileOrders/Batches log
    # ----------------------

    params = "1,%s,%s,null,''" % (oid, bid)
    encode_columns = IsBankperso and ('Status',) or None
    
    cursor = engine.runQuery(template, params=params, as_dict=True, encode_columns=encode_columns)
    if cursor:
        for n, row in enumerate(cursor):
            if not row['LID'] or not ':' in row['LID']:
                continue

            oid, bid = [int(x) for x in row['LID'].split(':')]
            status = None
            oper = row['Oper'].upper()

            state_error = state_ready = state_active = state_finished = False

            if template.startswith('provision'):
                status = row['Status']

                if bid:
                    state_error = status == 3
                    state_ready = status == 2
                    state_active = status == 6
                    state_finished = status == 7

                if not oper or oper not in 'IUD':
                    continue
                elif oper == 'I' and not bid:
                    items[0] += inc[0]
                elif oper == 'D' and not bid:
                    items[1] += inc[1]
                elif oper == 'I' and bid:
                    if state_error:
                        items[6] += inc[6]
                    elif state_ready:
                        items[5] += inc[5]
                    elif state_finished:
                        items[4] += inc[4]
                    elif state_active:
                        items[3] += inc[3]
                    else:
                        items[2] += inc[2]
                else:
                    items[2] += inc[2]

            else:
                status = row['Status'].lower()

                if oid:
                    state_error = 'ошибка' in status or 'отбраков' in status
                    state_ready = 'заказ обработан' in status or 'готов к отгрузке' in status
                    state_finished = 'обработка завершена' in status

                if bid:
                    state_active = status in ('готова к обработке', 'на обработке', 'активна')
                    state_finished = 'обработка завершена' in status

                if not oper or oper not in 'IUD':
                    continue
                elif oper == 'I' and not bid:
                    items[0] += inc[0]
                elif oper == 'D' and not bid:
                    items[1] += inc[1]
                elif oper == 'U':
                    if state_error:
                        items[6] += inc[6]
                    elif state_ready:
                        items[5] += inc[5]
                    elif state_finished:
                        items[4] += inc[4]
                    elif state_active:
                        items[3] += inc[3]
                    else:
                        items[2] += inc[2]
                else:
                    items[2] += inc[2]

            if oid > new_lid[0]:
                new_lid[0] = oid
            if bid > new_lid[1]:
                new_lid[1] = bid

    lid = '%s:%s' % (new_lid[0], new_lid[1])

    if IsLocalDebug:
        lid = '%s:%s' % (test_oid, test_bid)

    return {
        'state' : '%s::%s' % (template, lid),
        'items' : [_get_item(value, SEMAPHORE['duration'][i]) for i, value in enumerate(items)],
    }

@semaphore.after_request
def after_request(response):
    if engine is not None:
        engine.close()
    return response

@semaphore.route('/loader', methods = ['GET','POST'])
@login_required
def loader():
    exchange_error = ''
    exchange_message = ''

    refresh()

    action = get_request_item('action') or default_action
    selected_menu_action = get_request_item('selected_menu_action') or action != default_action and action or '901'

    response = {}

    template = IsBankperso and get_request_item('template') or default_template
    lid = get_request_item('lid')

    if IsDeepDebug:
        print('--> action:%s %s lid:%s' % (action, template, lid))

    if IsSemaphoreTrace:
        print_to(errorlog, '--> loader:%s %s [%s:%s:%s] %s' % (action, g.current_user.login, template, lid, selected_menu_action, 
            getTime(UTC_FULL_TIMESTAMP)))

    state = {}

    try:
        if action == default_action:
            action = selected_menu_action

        if not action:
            pass

        elif action == '901':
            state = getCurrentState(template, lid)

    except:
        print_exception()

    response.update({ \
        'action'           : action,
        # --------------
        # Service Errors
        # --------------
        'exchange_error'   : exchange_error, 
        'exchange_message' : exchange_message,
        # -------------------------
        # Results (Semaphore state)
        # -------------------------
        'state'            : state,
    })

    return jsonify(response)

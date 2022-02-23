# -*- coding: utf-8 -*-

import re
from decimal import *
from operator import itemgetter

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, errorlog, print_to, print_exception,
     default_unicode, default_encoding
     )

from ..settings import *
from ..utils import (
     isIterable, getToday, Capitalize, spent_time,
     getString, getHtmlString, getHtmlCaption, getMoney, getCurrency
     )

from ..models import User


class Base:

    def __init__(self, engine, *args, **kwargs):
        if IsDeepDebug:
            print('Base init')

        super().__init__(*args, **kwargs)

        self.engine = engine
        self.login = g.current_user.login

    def _init_state(self, attrs, factory, *args, **kwargs):
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


class UserProfile(Base):

    def __init__(self, engine, id, **kw):
        if IsDeepDebug:
            print('UserProfile init')

        super().__init__(engine)

        self._id = id
        self._errors = []

        self._locator = None
        self._page = None

        self._attrs = {}

    def _init_state(self, attrs=None, factory=None):
        if IsDeepDebug:
            print('UserProfile initstate')

        super()._init_state(attrs, factory)

        if attrs:
            self._locator = attrs.get('locator')
            self._page = attrs.get('page')

        self._extra = 0
        self._colored = 0

        if factory:
            for key in factory.keys():
                setattr(self, '_%s' % key, self.set_factory(key, factory))

        self._get_attrs()

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
    def locator(self):
        return self._locator
    @property
    def blank(self):
        return 'blank'
    @property
    def attrs(self):
        return self._attrs
    @property
    def query_string(self):
        return '?login=%s' % self.id
    @property
    def sql_params(self):
        return ''

    def _get_attrs(self):
        self._attrs['id'] = self.id
        self._attrs['title'] = 'Информация о пользователе %s' % self._attrs['id']

    def _get_where(self, mode=None):
        if mode == 'decrees_out':
            where = "Author='%s'" % ( 
                self.id,
                )
        elif mode == 'decrees_in':
            where = "Executor='%s'" % ( 
                self.id,
                )
        else:
            where = "Author='%s' and Status<%s%s" % ( 
                self.id, 
                self.page.valid_status,
                self.sql_params and (' and %s' % self.sql_params) or '',
                )

        if IsTrace and IsDeepDebug:
            print_to(None, '--> profile:%s, where=%s' % (self.login, where))

        return where

    def render_reviewer(self, **kw):
        """
            Render UserProfile data as a Reviewer by the given ID (user login)
        """
        data = {}

        self._started = getToday()

        if IsTrace:
            print_to(None, '>>> profile started')

        login = self.id

        user = User.get_user_by_login(login)

        avatar = user.get_small_avatar(size=(240, None), clean=True)

        privileges = filter(None, [
            user.app_is_manager and 'Менеджер',
            user.app_is_consultant and 'Консультант',
            user.app_is_author and 'Автор',
            '---',
            user.app_is_office_ceo and 'Роль: Высшее Руководство',
            user.app_is_office_direction and 'Роль: Административное руководство',
            user.app_is_office_execution and 'Роль: Исполнительное руководство',
            user.app_is_stock_manager and 'Роль: Менеджер складского хозяйства',
            user.app_is_auditor and 'Роль: Финансовый аудитор',
            user.app_is_payments_manager and 'Роль: Ввод платежей',
            user.app_is_provision_manager and 'Роль: Менеджер снабжения',
            user.app_is_personal_manager and 'Роль: Менеджер персонала',
            user.app_is_diamond_manager and 'Роль: Менеджеры Даймонд',
            user.app_is_purchase_manager and 'Роль: Менеджер закупок',
            user.app_is_sale_manager and 'Роль: Менеджер продаж',
            user.app_role_ceo and 'Роль: Генеральный директор',
            user.app_role_headoffice and 'Роль: Исполнительный директор',
            user.app_role_assistant and 'Роль: Заместитель Генерального директора',
            user.app_role_cao and 'Роль: Главный бухгалтер',
            user.app_role_cto and 'Роль: Главный инженер',
            user.app_role_chief and 'Роль: Руководитель подразделения',
        ])

        link = self.page.page_link[0] % ''

        where = self._get_where()
        orders = self._get_orders(where=where)
        total_orders = len(orders)
        orders_tag = total_orders and'<a target="_%s" href="%s?author=%s"><div>%s</div></a>' % (self.blank, link, login, total_orders) or '0'

        where = self._get_where(mode='decrees_out')
        decrees_out = self._get_decrees(where=where)
        total_out = len(decrees_out)
        ids = ':'.join([str(x['OrderID']) for x in decrees_out])
        decrees_out_tag = total_out and '<a target="_%s" href="%s?_ids=%s"><div>%s</div></a>' % (self.blank, link, ids, total_out) or '0'

        where = self._get_where(mode='decrees_in')
        decrees_in = self._get_decrees(where=where)
        total_in = len(decrees_in)
        ids = ':'.join([str(x['OrderID']) for x in decrees_in])
        decrees_in_tag = total_in and '<a target="_%s" href="%s?_ids=%s"><div>%s</div></a>' % (self.blank, link, ids, total_in) or '0'

        # Get data from user's profile
        data = {
            'login'         : login,                    # Логин
            'avatar'        : avatar,                   # Аватар
            'full_name'     : user.full_name(),         # ФИО
            'subdivision'   : user.subdivision_name,    # Подразделение
            'post'          : user.get_post(),          # Должность
            'role_name'     : user.role_name,           # Роль
            'app_role_name' : user.app_role_name,       # Функциональная роль
            'privileges'    : '<br>'.join(privileges),  # Полномочия
            'orders'        : orders_tag,               # Заявки пользователя
            'decrees_out'   : decrees_out_tag,          # Поручения выданные
            'decrees_in'    : decrees_in_tag,           # Поручения полученные
            'ob_types'      : self.page.object_types[2]
            
        }

        self._finished = getToday()

        if IsTrace:
            print_to(None, '>>> profile finished: %s sec' % spent_time(self._started, self._finished))

        return data

# -*- coding: utf-8 -*-

from operator import itemgetter

from ..settings import *
from ..models import User
from ..utils import (
     getToday, getDate, getDateOnly, spent_time, makeSearchQuery, checkDate, 
     getString, getSQLString, getHtmlString, getHtmlCaption, getMoney, getCurrency
     )


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


class Decree(Base):

    def __init__(self, engine, **kw):
        if IsDeepDebug:
            print('Decree init')

        super().__init__(engine)

        self._locator = None
        self._page = None

        self._order_id = kw.get('order_id')
        self._review_id = kw.get('review_id')
        self._decree_id = kw.get('decree_id')
        self._report_id = kw.get('report_id')

        self._attrs = {}

    def _init_state(self, attrs=None, factory=None, **kw):
        if IsDeepDebug:
            print('Decree initstate')

        super()._init_state(attrs, factory)

        self._decree = None

        self._note = None
        self._report = None

        self._status = {}
        self._decree_status = None

        self.is_overdue = False
        self.overdue = ''

        self.is_accepted = False
        self.accepted = ''

        if attrs:
            self._locator = attrs.get('locator')
            self._page = attrs.get('page')
            self._view = attrs.get('view')

        if factory:
            for key in factory.keys():
                setattr(self, '_%s' % key, self.set_factory(key, factory))

        self.today = getDateOnly(getToday())

        self._get_attrs()

    @property
    def page(self):
        return self._page
    @property
    def is_error(self):
        return self.engine.is_error
    @property
    def locator(self):
        return self._locator
    @property
    def blank(self):
        return 'self'
    @property
    def attrs(self):
        return self._attrs
    @property
    def view(self):
        return self._view
    @property
    def encode_columns(self):
        return ('Reviewer', 'Note')
    @property
    def order_id(self):
        return self._order_id
    @property
    def review_id(self):
        return self._review_id
    @property
    def decree_id(self):
        return self._decree_id
    @property
    def report_id(self):
        return self._report_id
    @property
    def decree_status(self):
        """
            Item status: 0,1,...
        """
        return self._decree_status
    @property
    def status(self):
        """
            Dictionary: id, key, short, full
        """
        return self._status
    @property
    def note(self):
        return self._note
    @property
    def report(self):
        return self._report

    def _get_attrs(self):
        self._attrs['title'] = ''
        self._attrs['rendered_name'] = 'Справка Секретариата'
        self._attrs['details'] = '%s %s' % (g.page.user_post(self.login), g.page.user_short_name(self.login))
        self._attrs['company'] = gettext('ROSAN FINANCE')

    def _get_where(self, args=None, with_login=None, without_status=None):
        params = {
            'login' : self.login,
        }
        if args:
            ids = 'ids' in args and [x for x in args['ids'] if x] or None
            login = args.get('login')
            executor = args.get('executor')
            status = args.get('status')
            where = 'ReviewStatus=9%s%s%s%s%s' % (
                ids and (' and TID in (%s)' % (','.join(ids))) or '',
                login and (" and (Author='%s' or Executor='%s')" % (login, login)) or '',
                executor and executor != 'any' and (" and Executor='%s'" % executor) or '',
                status and int(status) in (0,1,3) and (" and DecreeStatus=%s" % status) or '',
                with_login and (" and (Author='%(login)s' or Executor='%(login)s')" % params) or ''
                )
        else:
            where = '%s%s%s%s' % ( 
                without_status and 'ReviewStatus=9' or 'DecreeStatus=0',
                self.review_id and (' and ReviewID=%s' % self.review_id) or '', 
                self.order_id and (' and OrderID=%s' % self.order_id) or '', 
                with_login and (" and (Author='%(login)s' or Executor='%(login)s')" % params) or ''
                )

        if IsTrace and IsDeepDebug:
            print_to(None, '--> decrees:%s, where=%s' % (self.login, where))

        return where

    def _get_sum_total(self, total):
        return '%s: <span class="total_count">%s</span>&nbsp;%s: <span class="total_count">%s</span>&nbsp;%s: <span class="total_count">%s</span>&nbsp;' % (
            gettext('Total decrees'), 
            total[0], 
            gettext('of ougoing'), 
            total[1], 
            gettext('of incoming'), 
            total[2], 
            )

    def _check_decree(self):
        if not (self.order_id and self.review_id):
            return

        ob = None

        cursor = self._get_decrees(where=self._get_where(without_status=True))

        if cursor and len(cursor) > 0:
            ob = cursor[0]

        if ob is None:
            return

        self._decree_id = ob['TID']
        self._review_id = ob['ReviewID']
        self._report_id = ob['ReportID']
        self._decree_status = ob['DecreeStatus']

        self._decree = ob

    def _check_decree_status(self):
        if self._decree is None:
            return

        self._decree_status = self._decree['DecreeStatus']

        self.is_overdue = g.page.is_decree_overdue(self._decree) #self.decree_status == 0 and self._decree['DueDate'] < self.today
        self.overdue = self.is_overdue and ' (%s)' % gettext('Overdue') or ''

        self.is_accepted = g.page.is_decree_accepted(self._decree) #self.decree_status == 0 and self._decree.get('Accepted') is not None
        self.accepted = self.is_accepted and ' = %s: %s' % (gettext('Decree Accepted'), getDate(self._decree['Accepted'], format=LOCAL_EASY_TIMESTAMP)) or ''

        status = g.page.get_decree_status(self.decree_status)

        self._status = {
            'id'    : status[0],
            'key'   : status[1],
            'short' : ('%s%s' % (status[1], self.overdue) or '...').upper(),
            'full'  : ('%s%s%s' % (status[1], self.overdue, self.accepted) or '...').upper(),
        }

    def refresh(self, order=None, action_id=None):
        if action_id:
            self._review_id = action_id

        self._check_decree()

        if self._decree is None or order is None:
            return

        setattr(order, '_decree_status', self._decree_status)
        setattr(order, '_decree_id', self._decree_id)
        setattr(order, '_review_id', self._review_id)
        setattr(order, '_report_id', self._report_id)

    @staticmethod
    def get_types():
        pass

    def registry(self):
        return {
            'selected_columns' : ''
        }

    @staticmethod
    def date_state(item):
        rd = ''
        states = g.page.id == 'workflow' and \
            ('исполнено', 'оплачено', 'подписано', 'обосновано', 'проект документа',) or \
            ('исполнено', 'оплачено', 'согласовано', 'обосновано', 'создано',)

        if 'dates' not in item:
            return ''

        items = len(item['dates'])
        for i, k in enumerate([4, 3, 2, 1, 0]):
            if k < items and item['dates'][k][2]:
                rd = '%s (%s)' % (item['dates'][k][2], states[i])
                break

        return rd or ''

    def make_note(self, original_note, **kw):
        note = ''
        if original_note:
            note = getString(original_note, save_links=True, with_html=True)
        else:
            executor = kw['executor']
            kw['note'] = getString(kw['note'], save_links=True)
            kw['executor'] = User.get_by_login(executor).full_name()
            note = '%(title)s\n\n%(note)s\n\nИсполнитель: %(executor)s\nСрок исполнения: %(duedate)s' % kw
        self._note = note.strip()

    def parse_note(self, original_note, with_html=None):
        p1 = note = p2 = ''

        s = original_note.split('\n\n')

        if len(s) < 3:
            note = s[0]
        else:
            p1 = s[0].strip()
            note = getHtmlCaption(s[1].strip())
            p2 = s[-1].strip()

        if note and not with_html:
            note = getString(note, save_links=True, without_html=True)

        if IsDeepDebug:
            print('... note:', note)

        return p1, note, p2

    def get_report(self, with_html=None):
        report = ''

        if self.report_id:
            reviews, selected_id = self._get_reviews(self.order_id, review_id=self.report_id)
            if reviews and len(reviews) > 0:
                report = reviews[0]['Note']

        if report and not with_html:
            report = getString(report, save_links=True, with_html=True, without_html=True)

        if IsDeepDebug:
            print('... report:', report)

        return report or ''

    def make_report(self, is_accept_decree=None, **kw):
        report = ''
        if kw.get('report'):
            report = getString(kw['report'], save_links=True, with_html=True)
        if is_accept_decree:
            now = getDate(getToday(), format=LOCAL_EASY_TIMESTAMP)
            report = 'Принято к исполнению: %s\n\n%s' % (now, report)
        self._report = report.strip()

    def parse_report(self, with_html=None, with_header=None, as_is=None):
        p1 = report = ''

        report = self.get_report(with_html=with_html)

        if as_is:
            return report

        s = report.split('\n\n')

        if self._decree.get('Accepted'):
            p1 = s[0].strip()
            report = getHtmlCaption('\n'.join([x.strip() for x in s[1:]]).strip())
        else:
            report = s[0]

        if report and not with_html:
            report = getString(report, save_links=True, without_html=True)

        if with_header:
            return p1, report

        return report

    def get_item(self, command, **kw):
        data = {}

        self._check_decree()

        if self._decree:
            is_author = (self.login == self._decree.get('Author') or (
                self._decree.get('Author') in g.system_config.WORKFLOW_OFFICE_GROUP and g.page.app_role_ceo))

            is_executor = self.login == self._decree.get('Executor')

            is_disabled = self.decree_status in (
                g.page.provision_decree_statuses['done'], g.page.provision_decree_statuses['rejected'])

            title, note, info = self.parse_note(self._decree.get('Note'))

            data = {
                'decree_id'   : self._decree.get('TID'),
                'report_id'   : self._decree.get('ReportID') or 0,
                'title'       : title,
                'note'        : note,
                'author'      : self._decree.get('Author'),
                'executor'    : self._decree.get('Executor'),
                'duedate'     : self._get_date(self._decree.get('DueDate'), format=LOCAL_EASY_DATESTAMP),
                'report'      : '',
                'is_author'   : is_author,
                'is_executor' : is_executor,
                'is_disabled' : is_disabled,
            }

        if self.report_id:
            data.update({
                'report_id' : self.report_id,
                'report'    : self.parse_report(),
            })

        props = {
            'author'   : ['title', 'note', 'duedate', 'executor'],
            'executor' : ['report'],
        }

        self._check_decree_status()

        props['status'] = (self.decree_status, g.page.get_decree_status(self.decree_status))
        props['decree_status'] = self.status['full']

        return data, tuple(data.keys()), props

    def sort(self, params):
        return self.render(params, sort_by_duedate=1)

    def render(self, params, sort_by_duedate=0, **kw):
        """
            Render Decrees data by the given params
        """
        decrees = []
        controls = {}
        titles = {}
        items = {}

        self._started = getToday()

        given_page = params.get('page')
        ids = params.get('ids')
        date_from = params.get('date_from')
        login = params.get('login')
        executor = params.get('executor')
        status = params.get('status')
        with_login = params.get('with_login') and True or False

        if login == 'any':
            login = ''

        if IsTrace:
            print_to(None, '>>> decrees started')

        columns = (
            'np', 
            'review_id',
            'showbar', 
            'AuthorName',
            'Article', 
            'ExecutorName', 
            'Page',
            'DueDate', 
        )

        config = 'provision-decrees'

        content_state = params.get('content_state') and 'collapsed' or 'expanded'

        models = g.page.models

        pages = (given_page == 'default' or not given_page) and models.keys() or [g.page.id]

        currency = 'RUB'
        currency_header = self.page.get_header('OrderPrice')

        args = {}

        if ids:
            args['ids'] = ids
        if login:
            args['login'] = login
        elif executor:
            args['executor'] = executor
        if status:
            args['status'] = status

        where = self._get_where(args=args, with_login=with_login)

        if args.get('executor') == 'any':
            args['executor'] = ''
        if login:
            args['executor'] = login
        if 'status' in args:
            args['status'] = int(args['status'])

        if IsDeepDebug:
            print('... decree args:', args)

        total = [0, 0, 0]
        n = 0

        for page in pages:
            model = models.get(page)

            self._init_default(model)

            self._refresh()

            if IsDeepDebug:
                print('... decree page:', page, model, g.page.id)

            disabled = False

            for decree in self._get_decrees(where=where, order=kw.get('order')):
                self._order_id = decree['OrderID']
                self._review_id = decree['ReviewID']
                self._decree_id = decree['TID']
                self._report_id = decree['ReportID'] or 0

                self._decree = decree

                oid = decree['id'] = '%s_%s_%s_%s_%s' % (
                    page, self._order_id, self._review_id, self._decree_id, self._report_id)

                n += 1

                author = decree['Author']
                executor = decree['Executor']
                
                self._check_decree_status()

                disabled = self.decree_status > 0

                is_author = self.login == author and '1' or ''
                is_executor = self.login == executor and '1' or ''

                requested_status = args.get('status', -1)

                if requested_status == g.page.provision_decree_statuses['overdue'] and not self.is_overdue:
                    continue
                if requested_status == g.page.provision_decree_statuses['accepted'] and not self.is_accepted:
                    continue
                if requested_status == g.page.provision_decree_statuses['changed'] and not g.page.is_decree_changed(self._decree):
                    continue
                if requested_status == g.page.provision_decree_statuses['reported'] and not g.page.is_decree_reported(self._decree):
                    continue
                if requested_status == g.page.provision_decree_statuses['discard'] and not g.page.is_decree_discard(self._decree):
                    continue
                if requested_status == g.page.provision_decree_statuses['oversight'] and not g.page.is_decree_oversight(self._decree):
                    continue

                total[0] += 1

                if is_author:
                    total[1] += 1
                elif is_executor:
                    total[2] += 1

                order = self._get_order(self.order_id)

                info = self._info(order_id=self.order_id, no_extra=True, no_seller=True, order=order)
                item = info[1]

                decree['np'] = n
                decree['review_id'] = self._review_id
                decree['status'] = self.decree_status
                decree['disabled'] = disabled and 'disabled' or ''
                decree['is_accepted'] = self.is_accepted and 1 or 0
                decree['AuthorName'] = decree['Reviewer']
                decree['ExecutorName'] = g.page.user_full_name(executor)
                decree['DueDate'] = getDate(decree['DueDate'], format=LOCAL_EASY_DATESTAMP)
                decree['Page'] = g.page.get_page_name(page)

                title, note, info = self.parse_note(decree.get('Note'), with_html=not is_author and 1 or 0)

                decree['Article'] = title

                if not (order.get('Price') and item.get('price')):
                    order['Price'] = 0
                    order['Total'] = 0

                decree['showbar'] = ''
                decree['classes'] = {
                    'np'      : self.is_overdue and 'overdue' or self.status['id'] or '',
                    'showbar' : content_state,
                }

                report = self.parse_report(with_html=not is_executor and 1 or 0, as_is=not is_executor and 1 or 0)

                item['num'] = self._get_order_link(order, name=item['num'])
                item['decree_id'] = '%02d:%s:%s' % (g.page.model, self._review_id, self._decree_id)
                item['category_title'] = \
                    page == 'provision' and gettext('Provision order') or \
                    '%s № %s' % (item['category']['title'], order.get('Account') or '')
                item['note'] = note
                item['report'] = report
                item['decree_status'] = self.status['full']
                item['is_author'] = is_author
                item['is_executor'] = is_executor
                item['author'] = author
                item['executor'] = executor
                item['review_date'] = getDate(decree['ReviewDate'], format=LOCAL_EASY_TIMESTAMP)
                item['RD'] = self.date_state(item)

                items[oid] = item

                decrees.append(decree)
        
                titles[oid] = {
                    'np'        : '№ п/п = %s' % self.status['short'],
                    'review_id' : self.page.get_header('ReviewID', config=config),
                    'showbar'   : '',
                }
                for column in columns:
                    if column not in titles[oid]:
                        titles[oid][column] = self.page.get_header(column, config=config)

                controls[oid] = {
                    'note'   : is_author and 1 or 0,
                    'report' : is_executor and 1 or 0,
                }

                if IsTrace and IsDeepDebug:
                    print_to(None, '>>> decrees %02d: %s' % (n, getToday()))

        if sort_by_duedate:
            decrees = sorted(decrees, key=itemgetter('DueDate'), reverse=False)
            n = 0
            for decree in decrees:
                n += 1
                decree['np'] = n

        keys = [
            'num',
            'category_title',
            #'equipment_title',
            'RD',
            'purpose',
            'review_date',
            'note',
            'report',
            #'subdivision',
            #'author',
            'decree_status',
            'decree_id',
        ]

        headers = {
            'num'             : {'class' : 'num', 'title' : self.page.get_header('num')},
            'category_title'  : {'class' : 'category', 'title' : self.page.get_header('Category')},
            'equipment_title' : {'class' : 'equipment_title', 'title' : self.page.get_header('Equipment')},
            'purpose'         : {'class' : 'purpose', 'title' : self.page.get_header('Purpose')},
            'note'            : {'class' : 'note', 'title' : self.page.get_header('Purpose', config=config)},
            'report'          : {'class' : 'report', 'title' : self.page.get_header('Report', config=config)},
            'subdivision'     : {'class' : 'subdivision', 'title' : self.page.get_header('Subdivision')},
            'author'          : {'class' : 'author', 'title' : self.page.get_header('Author', config=config)},
            'decree_status'   : {'class' : 'author', 'title' : self.page.get_header('Status', config=config)},
            'decree_id'       : {'class' : 'decree_id', 'title' : self.page.get_header('id', config=config)},
            'RD'              : {'class' : 'RD', 'title' : self.page.get_header('OrderDate')},
            'review_date'     : {'class' : 'RD', 'title' : self.page.get_header('ReviewDate', config=config)},
        }

        statuses = g.page.ref_decree_statuses()
        executors = g.page.ref_short_users()

        data = {
            'attrs'     : self.attrs,
            'args'      : args,
            'columns'   : columns,
            'controls'  : controls,
            'titles'    : titles,
            'headers'   : headers,
            'keys'      : keys,
            'decrees'   : decrees,
            'items'     : items,
            'statuses'  : statuses,
            'executors' : executors,
            'sum_total' : self._get_sum_total(total),
            'types'     : self.get_types(),
            'registry'  : self.registry(),
        }

        data['is_page_manager'] = self.page.is_page_manager

        self._finished = getToday()

        if IsTrace:
            print_to(None, '>>> decrees finished: %s sec' % spent_time(self._started, self._finished))

        return data

    def render_html(self):
        where = 'TID=%s' % self.id

        decrees = self._get_decrees(where=where)

        content = '<div>%s</div>' % '<br>'.join(['<span>%s</span>' % x['Note'] for x in decrees])

        return 'Decree ID: %s, Total decrees: %d %s<br>Is_Error:%s' % (self.id, len(decrees), content, self.is_error)

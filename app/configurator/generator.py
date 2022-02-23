# -*- coding: utf-8 -*-

import re
from operator import itemgetter

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, errorlog, print_to, print_exception,
     default_unicode, default_encoding
     )

from ..settings import gettext
from ..database import Connection, DBEngine
from ..utils import isIterable

PLASTIC_TYPE = 'PlasticType'

TAG_PARAMS = {
    'default' : {
        'ERP'         : 6,
        'CardType'    : 36,
        'PlasticType' : 41,
        'FrontSide'   : 24,
        'BackSide'    : 27,
    },
}

BATCH_PARAMS = {
    'cardstandard' : {
        'Pin'         : ( 2, 3, 2, 1, 1),
        'PinInc'      : ( 5, 2, 2, 0, 1),
        'Crd'         : ( 7, 3, 2, 0, 1),
        'CrdInc'      : (10, 3, 2, 1, 1),
        'ChipGen'     : (17, 2, 2, 0, 1),
    },
    'easy' : {
        'Crd'         : ( 7, 3, 2, 0, 1),
        'CrdInc'      : (10, 3, 2, 1, 1),
    },
}

PROCESS_PARAMS = {
    'cardstandard' : {
        'Pin'         : ( 7, 10, 11, '', 1, 2),
        'PinInc'      : (11, 17, 75, '', None, None),
        'Crd'         : (46, 21, 22, '', None, None),
        'CrdInc'      : (22, 27, 61, '', None, None),
        'ChipGen'     : (12, 44, 45, '', 2, None),
    },
    'easy' : {
        'Crd'         : ( 7, 21, 22, '', 1, 2),
        'CrdInc'      : (22, 27, 61, '', None, None),
    },
}

OPER_PARAMS = {
    'cardstandard' : {
        'PinIncR'     : ( 5, 0),
        'PinIncL'     : (61, 0),
        'CrdDatacard' : ( 1, 0),
        'CrdOTK'      : ( 3, 0),
        'CrdIncR'     : ( 4, 0),
        'CrdIncL'     : (60, 0),
    },
    'easy' : {
        'CrdDatacard' : ( 1, 0),
        'CrdOTK'      : ( 3, 0),
        'CrdIncR'     : ( 4, 0),
        'CrdIncL'     : (60, 0),
    },
}

_SQL = {
    'OrderFiles_BatchList' : {
        'del' : 'DELETE FROM [dbo].[OrderFiles_BatchList_tb] WHERE FilterID in (select TID from [dbo].[DIC_FilterList_tb] where FileTypeID=%d)',
    },
    'DIC_FileType' : {
        'exists' : 'SELECT 1 FROM [dbo].[DIC_FileType_tb] WHERE TID=%d',
    },
    'DIC_FilterList' : {
        'del' : 'DELETE FROM [dbo].[DIC_FilterList_tb] WHERE FileTypeID=%d',
    },
    'DIC_FilterList_Values' : {
        'del' : 'DELETE FROM [dbo].[DIC_FilterList_Values_tb] WHERE FilterID in (select TID from [dbo].[DIC_FilterList_tb] where FileTypeID=%d)',
    },
    'DIC_FileType_BatchType' : {
        'tid' : 'SELECT max(TID) FROM [dbo].[DIC_FileType_BatchType_tb]',
        #'set' : "select [dbo].[GEN_BatchTypeID_ByName_fn](%d, %s, %d) from dbo.sysobjects where id = object_id(N'[dbo].[DIC_FileType_BatchType_tb]') and OBJECTPROPERTY(id, N'IsTable') = 1",
        'set' : "SELECT max(b.TID) FROM [dbo].[DIC_FileType_BatchType_tb] b INNER JOIN [dbo].[DIC_BatchType_tb] t on t.TID=b.BatchTypeID WHERE FileTypeID=%d and t.CName like %s",
        'add' : 'INSERT INTO [dbo].[DIC_FileType_BatchType_tb] VALUES(%d, %d, %d, %d, %d, %d, %d, %d, %d)',
        'del' : 'DELETE FROM [dbo].[DIC_FileType_BatchType_tb] where FileTypeID=%d',
    },
    'DIC_OrderFileProcess' : {
        'tid' : 'SELECT max(TID) FROM [dbo].[DIC_OrderFileProcess_tb]',
        'add' : 'INSERT INTO [dbo].[DIC_OrderFileProcess_tb] VALUES(%d, %d, %d, %d, %d, %s, %d, %d)',
        'del' : 'DELETE FROM [dbo].[DIC_OrderFileProcess_tb] WHERE LinkID in (select TID from [dbo].[DIC_FileType_BatchType_tb] where FileTypeID=%d)',
    },
    'DIC_FileType_BatchType_OperList' : {
        'tid' : 'SELECT max(TID) FROM [dbo].[DIC_FileType_BatchType_OperList_tb]',
        'add' : 'INSERT INTO [dbo].[DIC_FileType_BatchType_OperList_tb] VALUES(%d, %d, %d, %d)',
        'del' : 'DELETE FROM [dbo].[DIC_FileType_BatchType_OperList_tb] where FBLinkID in (select TID from [dbo].[DIC_FileType_BatchType_tb] where FileTypeID=%d)',
    },
    'DIC_FileType_BatchType_OperList_Params' : {
        'add' : 'INSERT INTO [dbo].[DIC_FileType_BatchType_OperList_Params_tb] VALUES(%d, %s, %s, %s)',
        'del' : 'DELETE FROM [dbo].[DIC_FileType_BatchType_OperList_Params_tb] WHERE FBOLinkID in (select TID from [dbo].[DIC_FileType_BatchType_OperList_tb] where FBLinkID in (select TID from [dbo].[DIC_FileType_BatchType_tb] where FileTypeID=%d))',
    },
    'DIC_FileType_TagList' : {
        'plastic_type' : "SELECT TOP 1 TID FROM [dbo].[DIC_FileType_TagList_tb] WHERE FileTypeID=%d and TName=%s",
        'tid' : 'SELECT max(TID) FROM [dbo].[DIC_FileType_TagList_tb]',
        'add' : 'INSERT INTO [dbo].[DIC_FileType_TagList_tb] VALUES(%d, %d, %s, %s)',
        'del' : 'DELETE FROM [dbo].[DIC_FileType_TagList_tb] WHERE FileTypeID=%d',
    },
    'DIC_FileType_TagList_TagValues' : {
        'get' : "SELECT TID FROM [dbo].[DIC_FileType_TagList_TagValues_tb] WHERE FTLinkID=%d and TValue=%s",
        'add' : 'INSERT INTO [dbo].[DIC_FileType_TagList_TagValues_tb] VALUES(%d, %s)',
        'del' : 'DELETE FROM [dbo].[DIC_FileType_TagList_TagValues_tb] WHERE FTLinkID in (select TID FROM [dbo].[DIC_FileType_TagList_tb] where FileTypeID=%d)',
    },
    'DIC_FileType_BatchType_FilterShema' : {
        'add' : 'INSERT INTO [dbo].[DIC_FileType_BatchType_FilterShema_tb] VALUES(%d, %d, %s)',
        'del' : 'DELETE FROM [dbo].[DIC_FileType_BatchType_FilterShema_tb] WHERE FBLinkID in (select TID from [dbo].[DIC_FileType_BatchType_tb] where FileTypeID=%d)',
    },
    'DIC_FTV_TZ' : {
        'add' : 'INSERT INTO [dbo].[DIC_FTV_TZ_tb] VALUES(%d, %d, %s, %s, %d)',
        'del' : 'DELETE FROM [dbo].[DIC_FTV_TZ_tb] SELECT TID FROM [dbo].[DIC_FileType_TagList_TagValues_tb] WHERE FTLinkID in (select TID FROM [dbo].[DIC_FileType_TagList_tb] where FileTypeID=%d)',
    },
    'DIC_FTV_ERPCODE' : {
        'add' : 'INSERT INTO [dbo].[DIC_FTV_ERPCODE_tb] VALUES(%d, %s, %d, %d)',
        'del' : 'DELETE FROM [dbo].[DIC_FTV_ERPCODE_tb] where FTVLinkID in (select TID from [dbo].[DIC_FileType_TagList_TagValues_tb] where FTLinkID in (select TID FROM [dbo].[DIC_FileType_TagList_tb] where FileTypeID=%d))',
    },
    'DIC_FTV_MATERIAL' : {
        'del' : 'DELETE FROM [dbo].[DIC_FTV_MATERIAL_tb] where FTVLinkID in (select TID from [dbo].[DIC_FileType_TagList_TagValues_tb] where FTLinkID in (select TID FROM [dbo].[DIC_FileType_TagList_tb] where FileTypeID=%d))',
    },
    'DIC_FTV_POST' : {
        'del' : 'DELETE FROM [dbo].[DIC_FTV_POST_tb] where FTVLinkID in (select TID from [dbo].[DIC_FileType_TagList_TagValues_tb] where FTLinkID in (select TID FROM [dbo].[DIC_FileType_TagList_tb] where FileTypeID=%d))',
    },
    'DIC_FTV_OPER_PARAMS' : {
        'del' : 'DELETE FROM [dbo].[DIC_FTV_OPER_PARAMS_tb] where FTV_OPER_ID in (SELECT TID FROM [dbo].[DIC_FTV_OPER_tb] where FTVLinkID in (select TID from [dbo].[DIC_FileType_TagList_TagValues_tb] where FTLinkID in (select TID FROM [dbo].[DIC_FileType_TagList_tb] where FileTypeID=%d)))',
    },
    'DIC_FTV_OPER' : {
        'del' : 'DELETE FROM [dbo].[DIC_FTV_OPER_tb] where FTVLinkID in (select TID from [dbo].[DIC_FileType_TagList_TagValues_tb] where FTLinkID in (select TID FROM [dbo].[DIC_FileType_TagList_tb] where FileTypeID=%d))',
    },
}

##  ====================================
##  Application Settings Generator Class
##  ====================================

class FileTypeSettingsGenerator(DBEngine):
    
    def __init__(self, connection, requested_object, filetype_id=None):
        if IsDeepDebug:
            print('FileTypeSettingsGenerator')

        super().__init__(connection)

        self.requested_object = requested_object

        self._id = filetype_id or self.requested_object.get('TID')
        self._auto_id = 0

        self.name = 'default'

    @property
    def id(self):
        return self._id

    @staticmethod
    def get_value(x):
        return x and len(x) > 0 and x[0][0] or None
    @staticmethod
    def get_sql(mode, key):
        return _SQL[mode][key]

    def runQuery(self, mode, key, args, no_traceback=None, raise_error=None):
        return self.run(self.get_sql(mode, key), args, no_traceback=no_traceback, raise_error=raise_error)

    def runCommand(self, mode, key, args, no_traceback=None, raise_error=False):
        self.run(self.get_sql(mode, key), args, no_cursor=True, no_traceback=no_traceback, raise_error=raise_error)

    def _set_tid(self, mode):
        return self.get_value(self.runQuery(mode, 'tid', None))

    def _get_value(self, mode, args):
        return self.get_value(self.runQuery(mode, 'get', args))

    def mod_create_batch(self, key, title, sort):
        self._auto_id += 1

        cursor = self.runQuery('DIC_FileType_BatchType', 'set', (
            self.id,
            title,
        ))

        batch_id = self.get_value(cursor) or self._auto_id

        params = BATCH_PARAMS.get(self.name)

        self.runCommand('DIC_FileType_BatchType', 'add', (
            batch_id,
            self.id,
            params[key][0],
            params[key][1],
            params[key][2],
            self._maxbatchsize,
            params[key][3],
            sort,
            params[key][4],
        ))

        return batch_id

    def mod_create_scenario(self, batchtype_id, key):
        self._auto_id += 1

        params = PROCESS_PARAMS.get(self.name)

        self.runCommand('DIC_OrderFileProcess', 'add', (
            self._auto_id,
            batchtype_id,
            params[key][0],
            params[key][1],
            params[key][2],
            params[key][3],
            params[key][4],
            params[key][5],
        ))

        return self._auto_id

    def mod_create_oper(self, batchtype_id, key):
        self._auto_id += 1

        params = OPER_PARAMS.get(self.name)

        self.runCommand('DIC_FileType_BatchType_OperList', 'add', (
            self._auto_id,
            batchtype_id,
            params[key][0],
            params[key][1],
        ))

        return self._auto_id

    def mod_create_operparam(self, oper_id, name, value, comment=None):
        self.runCommand('DIC_FileType_BatchType_OperList_Params', 'add', (
            oper_id,
            name,
            value,
            comment,
        ))

    def mod_create_tag(self, name, comment=None):
        self._auto_id += 1

        self.runCommand('DIC_FileType_TagList', 'add', (
            self._auto_id,
            self.id,
            name,
            comment,
        ))

        return self._auto_id

    def mod_create_tagvalue(self, tag_id, value):
        if not tag_id:
            return

        self.runCommand('DIC_FileType_TagList_TagValues', 'add', (
            tag_id,
            value,
        ))

    def mod_create_filterschema(self, batch_id, tag_id, value=''):
        self.runCommand('DIC_FileType_BatchType_FilterShema', 'add', (
            batch_id, 
            tag_id,
            value,
        ))

    def mod_create_tz(self, tag_link_id, param_id, value, comment, sort):
        self.runCommand('DIC_FTV_TZ', 'add', (
            tag_link_id, 
            param_id, 
            value, 
            comment, 
            sort,
        ))

    def removeScenario(self):
        """
            Remove Config scenario
        """
        errors = []

        def remove(mode):
            self.runCommand(mode, 'del', (
                self.id,
            ))

        # --------------
        # Start removing
        # --------------

        self.open(with_transaction=True)

        #
        # Check FileTypeID
        #
        cursor = self.runQuery('DIC_FileType', 'exists', (
                self.id,
        ))

        if self.is_error:
            errors.append('%s %s' % (gettext('Warning: FileTypeID is not exist:'), self.id))
            return errors

        remove('DIC_FTV_TZ')
        remove('DIC_FTV_ERPCODE')
        remove('DIC_FileType_TagList_TagValues')
        remove('DIC_FileType_TagList')
        remove('DIC_FileType_BatchType_OperList_Params')
        remove('DIC_FileType_BatchType_OperList')
        remove('DIC_OrderFileProcess')
        remove('DIC_FileType_BatchType_FilterShema')
        remove('DIC_FilterList_Values')
        remove('DIC_FilterList')
        remove('DIC_FileType_BatchType')
        remove('DIC_FTV_OPER_PARAMS')
        remove('DIC_FTV_OPER')
        remove('DIC_FTV_MATERIAL')
        remove('DIC_FTV_POST')
        remove('OrderFiles_BatchList')

        # ------
        # Finish
        # ------

        self.close()

        if self.is_error:
            errors.append('%s' % gettext('Error: SQL broken. See transaction log.'))

        return errors

    def createCardStandardScenario(self, attrs):
        """
            Check & Create CardStandard Config scenario
        """
        self.name = 'cardstandard'

        self._pcode = attrs.get('pcode')
        self._filter = attrs.get('filter')
        self._clientname = attrs.get('clientname')
        self._clientid = attrs.get('clientid')
        self._deliverytype = attrs.get('deliverytype')
        self._dumpbankflag = attrs.get('dumpbankflag')
        self._idvsp = attrs.get('idvsp')
        self._ischip = attrs.get('ischip')
        self._ispost = attrs.get('ispost')
        self._packagecode = attrs.get('packagecode')
        self._paysystem = attrs.get('paysystem')
        self._plastictype = attrs.get('plastictype')
        self._readydate = attrs.get('readydate')
        self._registerdate = attrs.get('registerdate')
        self._maxbatchsize = int(attrs.get('maxbatchsize') or 500)
        self._pinincreg = attrs.get('pinincreg') or ''
        self._crdincreg = attrs.get('crdincreg') or ''

        self._auto_id = 0

        with_pininc = self._pcode and True or False
        batchtype_pininc_id = None
        oper_pinincreg_id = None

        errors = []

        # ----------------
        # Start generation
        # ----------------

        self.open(with_transaction=True)

        #
        # Check FileTypeID
        #
        cursor = self.runQuery('DIC_FileType', 'exists', (
                self.id,
        ))

        if self.is_error:
            errors.append('%s %s' % (gettext('Warning: FileTypeID is not exist:'), self.id))
            return errors
        #
        # Типы партий
        #
        self._auto_id = self._set_tid('DIC_FileType_BatchType')

        batchtype_pin_id = self.mod_create_batch('Pin', 'печать пин-конвертов', 10)
        if with_pininc:
            batchtype_pininc_id = self.mod_create_batch('PinInc', 'инкассация(пин-конверты)', 20)
        batchtype_chipgen_id = self.mod_create_batch('ChipGen', 'генерация банковских чиповых данных', 30)
        batchtype_crd_id = self.mod_create_batch('Crd', 'персонализация карт', 40)
        batchtype_crdinc_id = self.mod_create_batch('CrdInc', 'инкассация(карты)', 50)
        #
        # Сценарии
        #
        self._auto_id = self._set_tid('DIC_OrderFileProcess')

        self.mod_create_scenario(batchtype_pin_id, 'Pin')
        if with_pininc:
            self.mod_create_scenario(batchtype_pininc_id, 'PinInc')
        self.mod_create_scenario(batchtype_crd_id, 'Crd')
        self.mod_create_scenario(batchtype_crdinc_id, 'CrdInc')
        self.mod_create_scenario(batchtype_chipgen_id, 'ChipGen')
        #
        # Операции
        #
        self._auto_id = self._set_tid('DIC_FileType_BatchType_OperList')

        if with_pininc:
            oper_pinincreg_id = self.mod_create_oper(batchtype_pininc_id, 'PinIncR')
            self.mod_create_oper(batchtype_pininc_id, 'PinIncL')
        self.mod_create_oper(batchtype_crd_id, 'CrdDatacard')
        self.mod_create_oper(batchtype_crd_id, 'CrdOTK')
        oper_crdincreg_id = self.mod_create_oper(batchtype_crdinc_id, 'CrdIncR')
        self.mod_create_oper(batchtype_crdinc_id, 'CrdIncL')
        #
        # Параметры операций
        #
        if with_pininc:
            self.mod_create_operparam(oper_pinincreg_id, 'TEMPLATE', self._pinincreg)
            self.mod_create_operparam(oper_pinincreg_id, 'ENGINE', '2.0')
        self.mod_create_operparam(oper_crdincreg_id, 'TEMPLATE', self._crdincreg)
        self.mod_create_operparam(oper_crdincreg_id, 'ENGINE', '2.0')
        #
        # Теги
        #
        self._auto_id = self._set_tid('DIC_FileType_TagList')

        clientid_id = self._clientid and self.mod_create_tag('CLIENTID', '') or None
        deliverytype_id = self._deliverytype and self.mod_create_tag('DeliveryType', '') or None
        dumpbankflag_id = self._dumpbankflag and self.mod_create_tag('DUMPBANK_FLAG', '') or None
        idvsp_id = self._idvsp and self.mod_create_tag('ID_VSP', '') or None
        ischip_id = self._ischip and self.mod_create_tag('IsChip', '') or None
        ispost_id = self._ispost and self.mod_create_tag('IsPost', '') or None
        packagecode_id = self._packagecode and self.mod_create_tag('PackageCode', '') or None
        paysystem_id = self._paysystem and self.mod_create_tag('PAY_SYSTEM', '') or None
        plastictype_id = self._plastictype and self.mod_create_tag('PlasticType', '') or None
        readydate_id = self._readydate and self.mod_create_tag('ReadyDate', '') or None
        registerdate_id = self._registerdate and self.mod_create_tag('RegisterDate', '') or None
        #
        # Значения тегов
        #
        self.mod_create_tagvalue(clientid_id, self._clientid)
        self.mod_create_tagvalue(deliverytype_id, '01')
        self.mod_create_tagvalue(dumpbankflag_id, '0')
        self.mod_create_tagvalue(dumpbankflag_id, '1')
        self.mod_create_tagvalue(ischip_id, '0')
        self.mod_create_tagvalue(ischip_id, '1')
        self.mod_create_tagvalue(ispost_id, '0')
        self.mod_create_tagvalue(ispost_id, '1')
        self.mod_create_tagvalue(packagecode_id, '00')
        self.mod_create_tagvalue(packagecode_id, '01')
        self.mod_create_tagvalue(paysystem_id, 'OTHER')
        #
        # Фильтры тегов типов партий
        #
        if self._filter:
            for tag, id in [
                (self._clientid, clientid_id),
                (self._deliverytype, deliverytype_id),
                (self._dumpbankflag, dumpbankflag_id),
                (self._idvsp, idvsp_id),
                (self._ischip, ischip_id),
                (self._ispost, ispost_id),
                (self._packagecode, packagecode_id),
                (self._paysystem, paysystem_id),
                (self._plastictype, plastictype_id),
                (self._readydate, readydate_id),
                (self._registerdate, registerdate_id),
                ]:
                if tag and id:
                    self.mod_create_filterschema(batchtype_pin_id, id, '')
                    if with_pininc:
                        self.mod_create_filterschema(batchtype_pininc_id, id, '')
                    self.mod_create_filterschema(batchtype_chipgen_id, id, '')
                    self.mod_create_filterschema(batchtype_crd_id, id, '')
                    self.mod_create_filterschema(batchtype_crdinc_id, id, '')
        #
        # Параметры ТЗ
        #
        clientid_id_link = self._get_value('DIC_FileType_TagList_TagValues', (clientid_id, self._clientid))
        self.mod_create_tz(clientid_id_link, 22, self._clientname, '', 10)

        if deliverytype_id:
            deliverytype_id_link = self._get_value('DIC_FileType_TagList_TagValues', (deliverytype_id, '01'))
            self.mod_create_tz(deliverytype_id_link, 29, 'Отгрузка уполномоченному представителю Банка', '', 300)

        if packagecode_id:
            packagecode_id_link = self._get_value('DIC_FileType_TagList_TagValues', (packagecode_id, '00'))
            self.mod_create_tz(packagecode_id_link, 21, 'Печать ПИН-конверта, при этом ПИН-конверты должны быть разорваны по линии перфорации, укладка лицевой стороной в одном направлении.', '', 400)

            packagecode_id_link = self._get_value('DIC_FileType_TagList_TagValues', (packagecode_id, '01'))
            self.mod_create_tz(packagecode_id_link, 21, 'БЕЗ печати ПИН-конверта.', '', 400)

        # ------
        # Finish
        # ------

        self.close()

        if self.is_error:
            errors.append('%s' % gettext('Error: SQL broken. See transaction log.'))

        return errors

    def createEasyScenario(self, attrs):
        """
            Check & Create CardStandard Easy Config scenario.
        """
        self.name = 'easy'

        self._pcode = attrs.get('pcode')
        self._filter = attrs.get('filter')
        self._clientname = attrs.get('clientname')
        self._clientid = attrs.get('clientid')
        self._deliverytype = attrs.get('deliverytype')
        self._dumpbankflag = attrs.get('dumpbankflag')
        self._idvsp = attrs.get('idvsp')
        self._ischip = attrs.get('ischip')
        self._ispost = attrs.get('ispost')
        self._packagecode = attrs.get('packagecode')
        self._paysystem = attrs.get('paysystem')
        self._plastictype = attrs.get('plastictype')
        self._readydate = attrs.get('readydate')
        self._registerdate = attrs.get('registerdate')
        self._maxbatchsize = int(attrs.get('maxbatchsize') or 500)
        self._pinincreg = attrs.get('pinincreg') or ''
        self._crdincreg = attrs.get('crdincreg') or ''

        self._auto_id = 0

        errors = []

        # ----------------
        # Start generation
        # ----------------

        self.open(with_transaction=True)

        #
        # Check FileTypeID
        #
        cursor = self.runQuery('DIC_FileType', 'exists', (
                self.id,
        ))

        if self.is_error:
            errors.append('%s %s' % (gettext('Warning: FileTypeID is not exist:'), self.id))
            return errors
        #
        # Типы партий
        #
        self._auto_id = self._set_tid('DIC_FileType_BatchType')

        batchtype_crd_id = self.mod_create_batch('Crd', 'персонализация карт', 10)
        batchtype_crdinc_id = self.mod_create_batch('CrdInc', 'инкассация(карты)', 20)
        #
        # Сценарии
        #
        self._auto_id = self._set_tid('DIC_OrderFileProcess')

        self.mod_create_scenario(batchtype_crd_id, 'Crd')
        self.mod_create_scenario(batchtype_crdinc_id, 'CrdInc')
        #
        # Операции
        #
        self._auto_id = self._set_tid('DIC_FileType_BatchType_OperList')

        self.mod_create_oper(batchtype_crd_id, 'CrdDatacard')
        self.mod_create_oper(batchtype_crd_id, 'CrdOTK')
        oper_crdincreg_id = self.mod_create_oper(batchtype_crdinc_id, 'CrdIncR')
        self.mod_create_oper(batchtype_crdinc_id, 'CrdIncL')
        #
        # Параметры операций
        #
        self.mod_create_operparam(oper_crdincreg_id, 'TEMPLATE', self._crdincreg)
        self.mod_create_operparam(oper_crdincreg_id, 'ENGINE', '2.0')
        #
        # Теги
        #
        self._auto_id = self._set_tid('DIC_FileType_TagList')

        clientid_id = self._clientid and self.mod_create_tag('CLIENTID', '') or None
        deliverytype_id = self._deliverytype and self.mod_create_tag('DeliveryType', '') or None
        dumpbankflag_id = self._dumpbankflag and self.mod_create_tag('DUMPBANK_FLAG', '') or None
        idvsp_id = self._idvsp and self.mod_create_tag('ID_VSP', '') or None
        ischip_id = self._ischip and self.mod_create_tag('IsChip', '') or None
        ispost_id = self._ispost and self.mod_create_tag('IsPost', '') or None
        packagecode_id = self._packagecode and self.mod_create_tag('PackageCode', '') or None
        paysystem_id = self._paysystem and self.mod_create_tag('PAY_SYSTEM', '') or None
        plastictype_id = self._plastictype and self.mod_create_tag('PlasticType', '') or None
        readydate_id = self._readydate and self.mod_create_tag('ReadyDate', '') or None
        registerdate_id = self._registerdate and self.mod_create_tag('RegisterDate', '') or None
        #
        # Значения тегов
        #
        self.mod_create_tagvalue(clientid_id, self._clientid)
        self.mod_create_tagvalue(deliverytype_id, '01')
        self.mod_create_tagvalue(dumpbankflag_id, '0')
        self.mod_create_tagvalue(dumpbankflag_id, '1')
        self.mod_create_tagvalue(ischip_id, '0')
        self.mod_create_tagvalue(ischip_id, '1')
        self.mod_create_tagvalue(ispost_id, '0')
        self.mod_create_tagvalue(ispost_id, '1')
        self.mod_create_tagvalue(packagecode_id, '00')
        self.mod_create_tagvalue(packagecode_id, '01')
        self.mod_create_tagvalue(paysystem_id, 'OTHER')
        #
        # Фильтры тегов типов партий
        #
        if self._filter:
            for tag, id in [
                    (self._clientid, clientid_id),
                    (self._deliverytype, deliverytype_id),
                    (self._dumpbankflag, dumpbankflag_id),
                    (self._idvsp, idvsp_id),
                    (self._ischip, ischip_id),
                    (self._ispost, ispost_id),
                    (self._packagecode, packagecode_id),
                    (self._paysystem, paysystem_id),
                    (self._plastictype, plastictype_id),
                    (self._readydate, readydate_id),
                    (self._registerdate, registerdate_id),
                    ]:
                if tag and id:
                    self.mod_create_filterschema(batchtype_crd_id, id, '')
                    self.mod_create_filterschema(batchtype_crdinc_id, id, '')
        #
        # Параметры ТЗ
        #
        clientid_id_link = self._get_value('DIC_FileType_TagList_TagValues', (clientid_id, self._clientid))
        self.mod_create_tz(clientid_id_link, 22, self._clientname, '', 10)

        if deliverytype_id:
            deliverytype_id_link = self._get_value('DIC_FileType_TagList_TagValues', (deliverytype_id, '01'))
            self.mod_create_tz(deliverytype_id_link, 29, 'Отгрузка уполномоченному представителю Банка', '', 300)

        # ------
        # Finish
        # ------

        self.close()

        if self.is_error:
            errors.append('%s' % gettext('Error: SQL broken. See transaction log.'))

        return errors

    def createNewDesign(self, attrs):
        """
            Check & Create CardStandard design
        """
        self._cardtype = attrs.get('cardtype')
        self._bin = attrs.get('bin')
        self._erp = attrs.get('erp')
        self._prerp = attrs.get('prerp')
        self._code = attrs.get('code')
        self._design = attrs.get('design')
        self._frontside = attrs.get('frontside')
        self._backside = attrs.get('backside')

        errors = []

        tag_params = {
            'CardType'    : (1, self._cardtype, 'Тип карты',), 
            'BIN'         : (2, self._bin, 'БИН',),
            'ERP'         : (3, self._erp, 'ERP ТЗ',),
            'PRERP'       : (4, self._prerp, 'Производственное ТЗ',),
            'PlasticType' : (5, self._code, 'Код пластика',),
            'Design'      : (6, self._design, 'Номер дизайна'),
            'FrontSide'   : (7, self._frontside, 'Лицевая сторона',),
            'BackSide'    : (8, self._backside, 'Оборотная сторона',),
        }
        #
        # Check attrs are present
        #
        n = 0
        for index, attr, title in sorted(tag_params.values(), key=itemgetter(1)):
            if index not in (3,4) and not attr:
                errors.append('%s %s' % (gettext('Warning: Parameter is empty:'), title))
                n += 1

        if errors:
            if n > 5:
                return ['%s' % gettext('Warning: Form is empty!')]
            return errors

        if not self._bin.isdigit() or len(self._bin) not in (4,6,8):
            errors.append('%s %s' % (gettext('Warning: Invalid BIN:'), self._bin))

        if not self._design.isdigit():
            errors.append('%s %s' % (gettext('Warning: Design should be a number:'), self._design))

        if errors:
            return errors

        # ----------------
        # Start generation
        # ----------------

        self.open(with_transaction=True)

        #
        # Check FileTypeID
        #
        cursor = self.runQuery('DIC_FileType', 'exists', (
                self.id,
        ))

        if self.is_error:
            errors.append('%s %s' % (gettext('Warning: FileTypeID is not exist:'), self.id))
            return errors
        #
        # Check `PlasticType` tag
        #
        cursor = self.runQuery('DIC_FileType_TagList', 'plastic_type', (
                self.id,
                PLASTIC_TYPE,
        ))

        plastic_type_id = self.get_value(cursor)

        if self.is_error or not plastic_type_id:
            errors.append('%s %s' % (gettext('Warning: Tag is not exist:'), PLASTIC_TYPE))
            return errors
        #
        # Insert & Check `PlasticType` tag value
        #
        cursor = self.runQuery('DIC_FileType_TagList_TagValues', 'get', (
                plastic_type_id,
                self._code,
        ))

        if self.get_value(cursor):
            errors.append('%s %s' % (gettext('Warning: Design already exists:'), self._code))
            return errors

        self.runCommand('DIC_FileType_TagList_TagValues', 'add', (
                plastic_type_id,
                self._code,
        ))

        cursor = self.runQuery('DIC_FileType_TagList_TagValues', 'get', (
                plastic_type_id,
                self._code,
        ))

        plastic_type_value = self.get_value(cursor)

        if self.is_error or not plastic_type_value:
            errors.append('%s %s' % (gettext('Warning: Error on TagValue generation:'), PLASTIC_TYPE))
            return errors
        #
        # Insert TZ items
        #
        params = TAG_PARAMS['default']

        self.runCommand('DIC_FTV_TZ', 'add', (
                plastic_type_value,
                params['ERP'],
                '${ERPTZ}',
                '',
                20
        ))

        self.runCommand('DIC_FTV_TZ', 'add', (
                plastic_type_value,
                params['CardType'],
                '%s Производственное ТЗ %s' % (self._cardtype, self._prerp),
                '',
                30
        ))

        self.runCommand('DIC_FTV_TZ', 'add', (
                plastic_type_value,
                params['PlasticType'],
                '%s Дизайн № %s БИН %s' % (self._code, self._design, self._bin),
                '',
                40
        ))

        self.runCommand('DIC_FTV_TZ', 'add', (
                plastic_type_value,
                params['FrontSide'],
                self._frontside,
                '',
                50
        ))

        self.runCommand('DIC_FTV_TZ', 'add', (
                plastic_type_value,
                params['BackSide'],
                self._backside,
                '',
                60
        ))
        #
        # Insert ERP code
        #
        if self._erp:
            self.runCommand('DIC_FTV_ERPCODE', 'add', (
                plastic_type_value,
                self._erp,
                7,
                2
            ))

        self.close()

        # ------
        # Finish
        # ------

        if self.is_error:
            errors.append('%s' % gettext('Error: SQL broken. See transaction log.'))

        return errors

    def checkFileExists(self, filename):
        cursor = self.runQuery('OrderFiles', 'check', (
            filename, 
        ))
        return not self.is_error and self.get_body(cursor) and True or False

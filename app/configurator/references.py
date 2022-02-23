# -*- coding: utf-8 -*-

__all__ = ['reference_factory',]

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsPrintExceptions, errorlog, print_to, print_exception,
     default_unicode, default_encoding
     )

from ..settings import gettext
from ..references import AbstractReference

#from ..database import getReferenceConfig
#from ..booleval import Token, new_token
#from ..utils import isIterable

#_UNDEFINED_ERROR = 2
#_ERROR = 1
#_WARNING = 0

##  =======================
##  Configurator.References
##  =======================

class ConfiguratorReference(AbstractReference):

    pass

##  =================
##  BankDB.References
##  =================

class DicClients(ConfiguratorReference):

    def __init__(self, engine):
        super(DicClients, self).__init__(engine, 'reference.clients')

    def addItem(self, items, id=None, **kw):
        return super(DicClients, self).addItem(items, calculated_pk=True)

    @property
    def title(self):
        return 'Клиенты'

    @property
    def editable_columns(self):
        return ('CName',)


class DicFileStatus(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFileStatus, self).__init__(engine, 'reference.file-status')

    def addItem(self, items, id=None, **kw):
        return super(DicFileStatus, self).addItem(items, explicit_pk=True)

    @property
    def title(self):
        return 'Статусы файлов'

    @property
    def editable_columns(self):
        return ('TID', 'StatusTypeID', 'CName',)


class DicFileType(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFileType, self).__init__(engine, 'reference.file-type')

    def addItem(self, items, id=None, **kw):
        return super(DicFileType, self).addItem(items, calculated_pk=True)

    @property
    def title(self):
        return 'Типы файлов'

    @property
    def searchable(self):
        return ('CName', 'ReportPrefix',)

    @property
    def numeric(self):
        return ('TID', 'ClientID',)

    @property
    def editable_columns(self):
        return ('ClientID', 'CName', 'ReportPrefix',)


class DicBatchCreateType(ConfiguratorReference):

    def __init__(self, engine):
        super(DicBatchCreateType, self).__init__(engine, 'reference.batch-create-type')

    def addItem(self, items, id=None, **kw):
        return super(DicBatchCreateType, self).addItem(items, calculated_pk=True)

    @property
    def title(self):
        return 'Признак создания партии'

    @property
    def editable_columns(self):
        return ('CName',)


class DicBatchResultType(ConfiguratorReference):

    def __init__(self, engine):
        super(DicBatchResultType, self).__init__(engine, 'reference.batch-result-type')

    def addItem(self, items, id=None, **kw):
        return super(DicBatchResultType, self).addItem(items, calculated_pk=True)

    @property
    def title(self):
        return 'Признак создания файла результата партии'

    @property
    def editable_columns(self):
        return ('CName',)


class DicBatchStatus(ConfiguratorReference):

    def __init__(self, engine):
        super(DicBatchStatus, self).__init__(engine, 'reference.batch-status')

    def addItem(self, items, id=None, **kw):
        return super(DicBatchStatus, self).addItem(items, calculated_pk=True)

    @property
    def title(self):
        return 'Статусы партий'

    @property
    def editable_columns(self):
        return ('CName',)


class DicBatchType(ConfiguratorReference):

    def __init__(self, engine):
        super(DicBatchType, self).__init__(engine, 'reference.batch-type')

    def addItem(self, items, id=None, **kw):
        return super(DicBatchType, self).addItem(items, calculated_pk=True)

    @property
    def title(self):
        return 'Типы партий'

    @property
    def editable_columns(self):
        return ('CName',)


class DicOperList(ConfiguratorReference):

    def __init__(self, engine):
        super(DicOperList, self).__init__(engine, 'reference.oper-list')

    def addItem(self, items, id=None, **kw):
        return super(DicOperList, self).addItem(items, calculated_pk=True)

    @property
    def title(self):
        return 'Операции'

    @property
    def editable_columns(self):
        return ('TypeID', 'CName',)


class DicOperType(ConfiguratorReference):

    def __init__(self, engine):
        super(DicOperType, self).__init__(engine, 'reference.oper-type')

    def addItem(self, items, id=None, **kw):
        return super(DicOperType, self).addItem(items, calculated_pk=True)

    @property
    def value(self):
        return 'SName'

    @property
    def title(self):
        return 'Типы операций'

    @property
    def searchable(self):
        return ('CName', 'SName',)

    @property
    def editable_columns(self):
        return ('CName', 'SName',)


class DicTagParams(ConfiguratorReference):

    def __init__(self, engine):
        super(DicTagParams, self).__init__(engine, 'reference.tag-params')

    def addItem(self, items, id=None, **kw):
        return super(DicTagParams, self).addItem(items, with_identity=True)

    @property
    def value(self):
        return 'PName'

    @property
    def title(self):
        return 'Параметры тегов'

    @property
    def searchable(self):
        return ('PName', 'Comment',)

    @property
    def editable_columns(self):
        return ('PName', 'Comment',)


class DicFTBPost(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFTBPost, self).__init__(engine, 'reference.ftb-post')

    def addItem(self, items, id=None, **kw):
        return super(DicFTBPost, self).addItem(items, with_identity=True)

    @property
    def title(self):
        return 'Параметры почты'

    @property
    def searchable(self):
        return ('PValue', 'Comment',)

    @property
    def numeric(self):
        return ('TID', 'FBLinkID', 'TagParamID',)

    @property
    def editable_columns(self):
        return ('FBLinkID', 'TagParamID', 'PValue', 'PSortIndex', 'Comment',)


class DicFTVOperParams(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFTVOperParams, self).__init__(engine, 'reference.ftv-oper-params')

    def addItem(self, items, id=None, **kw):
        return super(DicFTVOperParams, self).addItem(items, with_identity=True)

    @property
    def title(self):
        return 'Параметры персонализации'

    @property
    def searchable(self):
        return ('PName', 'PValue',)

    @property
    def numeric(self):
        return ('TID', 'FTV_OPER_ID',)

    @property
    def editable_columns(self):
        return ('FTV_OPER_ID', 'PName', 'PValue',)


class DicLinkedBatches(ConfiguratorReference):

    def __init__(self, engine):
        super(DicLinkedBatches, self).__init__(engine, 'reference.linked-batches')

    @property
    def title(self):
        return 'Партии типа файла (***)'

    @property
    def value(self):
        return 'BatchType'

    @property
    def searchable(self):
        return ('FileType', 'BatchType',)

    @property
    def numeric(self):
        return ('TID', 'FileTypeID', 'BatchTypeID',)

    @property
    def editable_columns(self):
        return []

    @property
    def has_links(self):
        return True


class DicLinkedOpers(ConfiguratorReference):

    def __init__(self, engine):
        super(DicLinkedOpers, self).__init__(engine, 'reference.linked-opers')

    @property
    def title(self):
        return 'Операции типа файла (***)'

    @property
    def value(self):
        return 'OperType'

    @property
    def searchable(self):
        return ('FileType', 'BatchType', 'OperTypeName', 'OperType',)

    @property
    def numeric(self):
        return ('TID', 'FBLinkID', 'FileTypeID', 'BatchTypeID', 'OperID', 'OperSortIndex',)

    @property
    def editable_columns(self):
        return []

    @property
    def has_links(self):
        return True


class DicLinkedTags(ConfiguratorReference):

    def __init__(self, engine):
        super(DicLinkedTags, self).__init__(engine, 'reference.linked-tags')

    @property
    def title(self):
        return 'Теги типа файла (***)'

    @property
    def value(self):
        return 'TName'

    @property
    def searchable(self):
        return ('FileType', 'TName',)

    @property
    def numeric(self):
        return ('TID', 'FileTypeID',)

    @property
    def editable_columns(self):
        return []

    @property
    def has_links(self):
        return True


class DicLinkedTagValues(ConfiguratorReference):

    def __init__(self, engine):
        super(DicLinkedTagValues, self).__init__(engine, 'reference.linked-tagvalues')

    @property
    def title(self):
        return 'Значения тегов типа файла (***)'

    @property
    def value(self):
        return 'TagValue'

    @property
    def searchable(self):
        return ('FileType', 'TName', 'TValue',)

    @property
    def numeric(self):
        return ('TID', 'FTLinkID', 'FileTypeID',)

    @property
    def editable_columns(self):
        return []

    @property
    def filtered_columns(self):
        return ['TID', 'FTLinkID', 'FileTypeID', 'TName', 'TValue',]

    @property
    def has_links(self):
        return True


class DicLinkedTagOpers(ConfiguratorReference):

    def __init__(self, engine):
        super(DicLinkedTagOpers, self).__init__(engine, 'reference.linked-tagopers')

    @property
    def title(self):
        return 'Операции персонализации (***)'

    @property
    def value(self):
        return 'PValue'

    @property
    def searchable(self):
        return ('FileType', 'TName', 'TValue', 'OperType', 'Oper', 'PName', 'PValue', 'Comment',)

    @property
    def numeric(self):
        return ('TID', 'FTVLinkID', 'FileTypeID', 'TagParamID', 'OperTypeID', 'OperSortIndex',)

    @property
    def editable_columns(self):
        return []

    @property
    def has_links(self):
        return True


class DicFileType_BatchType(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFileType_BatchType, self).__init__(engine, 'reference.file-type-batch-type')

    def addItem(self, items, id=None, **kw):
        return super(DicFileType_BatchType, self).addItem(items, calculated_pk=True)

    @property
    def title(self):
        return 'Тип партии файла'

    @property
    def configurator(self):
        return 'configurator-batches'

    @property
    def editable_columns(self):
        return ('FileTypeID', 'BatchTypeID', 'BatchCreateTypeID', 'BatchResultTypeID', 'BatchMaxQty', 'IsErpBatch', 'CreateBatchSortIndex', 'CreateBatchGroupIndex',)


class DicOrderFileProcess(ConfiguratorReference):

    def __init__(self, engine):
        super(DicOrderFileProcess, self).__init__(engine, 'reference.order-file-process')

    def addItem(self, items, id=None, **kw):
        return super(DicOrderFileProcess, self).addItem(items, calculated_pk=True)

    @property
    def title(self):
        return 'Сценарии типа файла'

    @property
    def configurator(self):
        return 'configurator-processes'

    @property
    def editable_columns(self):
        return ('LinkID', 'CurrFileStatusID', 'NextFileStatusID', 'CloseFileStatusID', 'Memo', 'ActivateBatchStatus', 'ARMBatchStatus',)


class DicFileType_BatchType_OperList(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFileType_BatchType_OperList, self).__init__(engine, 'reference.file-type-batch-type-opers')

    def addItem(self, items, id=None, **kw):
        return super(DicFileType_BatchType_OperList, self).addItem(items, calculated_pk=True)

    @property
    def title(self):
        return 'Операции типа файла'

    @property
    def configurator(self):
        return 'configurator-opers'

    @property
    def editable_columns(self):
        return ('FBLinkID', 'OperID', 'OperSortIndex',)


class DicFileType_BatchType_OperList_Params(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFileType_BatchType_OperList_Params, self).__init__(engine, 'reference.file-type-batch-type-operparams')

    def addItem(self, items, id=None, **kw):
        return super(DicFileType_BatchType_OperList_Params, self).addItem(items, with_identity=True)

    @property
    def title(self):
        return 'Параметры операций типа файла'

    @property
    def configurator(self):
        return 'configurator-operparams'

    @property
    def editable_columns(self):
        return ('FBOLinkID', 'PName', 'PValue', 'Comment',)


class DicFileType_TagList(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFileType_TagList, self).__init__(engine, 'reference.file-type-tags')

    def addItem(self, items, id=None, **kw):
        return super(DicFileType_TagList, self).addItem(items, calculated_pk=True)

    @property
    def title(self):
        return 'Теги типа файла'

    @property
    def configurator(self):
        return 'configurator-tags'

    @property
    def editable_columns(self):
        return ('FileTypeID', 'TName', 'TMemo',)


class DicFileType_TagList_TagValues(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFileType_TagList_TagValues, self).__init__(engine, 'reference.file-type-tagvalues')

    def addItem(self, items, id=None, **kw):
        return super(DicFileType_TagList_TagValues, self).addItem(items, with_identity=True)

    @property
    def title(self):
        return 'Значения тегов типа файла'

    @property
    def configurator(self):
        return 'configurator-tagvalues'

    @property
    def editable_columns(self):
        return ('FTLinkID', 'TValue',)


class DicFileType_BatchType_FilterShema(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFileType_BatchType_FilterShema, self).__init__(engine, 'reference.file-type-batch-type-filters')

    def addItem(self, items, id=None, **kw):
        return super(DicFileType_BatchType_FilterShema, self).addItem(items, with_identity=True)

    @property
    def title(self):
        return 'Фильтры типа файла'

    @property
    def configurator(self):
        return 'configurator-filters'

    @property
    def sorted_columns(self):
        return ('TID', 'FileTypeID', 'FBLinkID', 'FTLinkID', 'CriticalValues',)

    @property
    def editable_columns(self):
        return ('FBLinkID', 'FTLinkID', 'CriticalValues',)


class DicFTV_TZ(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFTV_TZ, self).__init__(engine, 'reference.file-type-tzs')

    def addItem(self, items, id=None, **kw):
        return super(DicFTV_TZ, self).addItem(items, with_identity=True)

    @property
    def title(self):
        return 'Параметры ТЗ'

    @property
    def configurator(self):
        return 'configurator-tzs'

    @property
    def editable_columns(self):
        return ('FTVLinkID', 'TagParamID', 'PValue', 'Comment', 'PSortIndex',)


class DicFTV_ERPCODE(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFTV_ERPCODE, self).__init__(engine, 'reference.file-type-erpcodes')

    def addItem(self, items, id=None, **kw):
        return super(DicFTV_ERPCODE, self).addItem(items, with_identity=True)

    @property
    def title(self):
        return 'Коды ЕРП'

    @property
    def configurator(self):
        return 'configurator-erpcodes'

    @property
    def sorted_columns(self):
        return ('TID', 'BatchTypeID', 'FTVLinkID', 'ERP_CODE', 'AdditionalInfo',)

    @property
    def editable_columns(self):
        return ('FTVLinkID', 'ERP_CODE', 'BatchTypeID', 'AdditionalInfo',)


class DicFTV_MATERIAL(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFTV_MATERIAL, self).__init__(engine, 'reference.file-type-materials')

    def addItem(self, items, id=None, **kw):
        return super(DicFTV_MATERIAL, self).addItem(items, with_identity=True)

    @property
    def title(self):
        return 'Материалы'

    @property
    def configurator(self):
        return 'configurator-materials'

    @property
    def sorted_columns(self):
        return ('TID', 'BatchTypeID', 'FTVLinkID', 'TagParamID', 'QtyMode', 'MMin', 'MBadPercent',)

    @property
    def editable_columns(self):
        return ('FTVLinkID', 'TagParamID', 'BatchTypeID', 'MMin', 'MBadPercent', 'QtyMode',)


class DicFTV_POST(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFTV_POST, self).__init__(engine, 'reference.file-type-posts')

    def addItem(self, items, id=None, **kw):
        return super(DicFTV_POST, self).addItem(items, with_identity=True)

    @property
    def title(self):
        return 'Почтовые параметры'

    @property
    def configurator(self):
        return 'configurator-posts'

    @property
    def sorted_columns(self):
        return ('TID', 'FTVLinkID', 'TagParamID', 'PValue', 'Comment',)

    @property
    def editable_columns(self):
        return ('FTVLinkID', 'TagParamID', 'PValue', 'Comment',)


class DicFTV_OPER(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFTV_OPER, self).__init__(engine, 'reference.file-type-tagopers')

    def addItem(self, items, id=None, **kw):
        return super(DicFTV_OPER, self).addItem(items, with_identity=True)

    @property
    def title(self):
        return 'Операции персонализации'

    @property
    def configurator(self):
        return 'configurator-tagopers'

    @property
    def sorted_columns(self):
        return ('TID', 'FTVLinkID', 'TagParamID', 'OperTypeID', 'PValue', 'OperSortIndex', 'Comment',)

    @property
    def editable_columns(self):
        return ('FTVLinkID', 'TagParamID', 'OperTypeID', 'PValue', 'Comment', 'OperSortIndex',)


class DicFTV_OPER_PARAMS(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFTV_OPER_PARAMS, self).__init__(engine, 'reference.file-type-tagoperparams')

    def addItem(self, items, id=None, **kw):
        return super(DicFTV_OPER_PARAMS, self).addItem(items, with_identity=True)

    @property
    def title(self):
        return 'Параметры операций персонализации'

    @property
    def configurator(self):
        return 'configurator-tagoperparams'

    @property
    def sorted_columns(self):
        return ('TID', 'FTV_OPER_ID', 'PName', 'PValue',)

    @property
    def editable_columns(self):
        return ('FTV_OPER_ID', 'PName', 'PValue',)


class DicFTV_PROCESSPARAMS(ConfiguratorReference):

    def __init__(self, engine):
        super(DicFTV_PROCESSPARAMS, self).__init__(engine, 'reference.file-type-processparams')

    def addItem(self, items, id=None, **kw):
        return super(DicFTV_PROCESSPARAMS, self).addItem(items, with_identity=True)

    @property
    def title(self):
        return 'Параметры процессов'

    @property
    def configurator(self):
        return 'configurator-processparams'

    @property
    def sorted_columns(self):
        return ('TID', 'FTVLinkID', 'TagParamID', 'PValue', 'PSortIndex', 'Comment',)

    @property
    def editable_columns(self):
        return ('FTVLinkID', 'TagParamID', 'PValue', 'Comment', 'PSortIndex',)


reference_factory = {
    # ----------
    # References
    # ----------
    'batch-create-type'     : DicBatchCreateType,
    'batch-result-type'     : DicBatchResultType,
    'batch-status'          : DicBatchStatus,
    'batch-type'            : DicBatchType,
    'clients'               : DicClients,
    'file-status'           : DicFileStatus,
    'file-type'             : DicFileType,
    'ftb-post'              : DicFTBPost,
    'ftv-oper-params'       : DicFTVOperParams,
    'oper-list'             : DicOperList,
    'oper-type'             : DicOperType,
    'tag-params'            : DicTagParams,
    # ----
    # Tabs
    # ----
    'batches'               : DicFileType_BatchType,
    'processes'             : DicOrderFileProcess,
    'opers'                 : DicFileType_BatchType_OperList,
    'operparams'            : DicFileType_BatchType_OperList_Params,
    'tags'                  : DicFileType_TagList,
    'tagvalues'             : DicFileType_TagList_TagValues,
    'filters'               : DicFileType_BatchType_FilterShema,
    'tzs'                   : DicFTV_TZ,
    'erpcodes'              : DicFTV_ERPCODE,
    'materials'             : DicFTV_MATERIAL,
    'posts'                 : DicFTV_POST,
    'tagopers'              : DicFTV_OPER,
    'tagoperparams'         : DicFTV_OPER_PARAMS,
    'processparams'         : DicFTV_PROCESSPARAMS,
    # -----------------
    # Linked references
    # -----------------
    'linked-batches'        : DicLinkedBatches,
    'linked-opers'          : DicLinkedOpers,
    'linked-tags'           : DicLinkedTags,
    'linked-tagvalues'      : DicLinkedTagValues,
    'linked-tagopers'       : DicLinkedTagOpers,
}

# -*- coding: utf-8 -*-

import os
import re
import zlib

from lxml import etree as LET
import xml.etree.ElementTree as ET

from config import (
     IsDebug, IsDeepDebug, IsTrace, IsTmpClean, IsUseDecodeCyrillic, IsDecoderTrace, IsPrintExceptions, IsDecoderTrace,
     basedir, errorlog, print_to, print_exception,
     default_print_encoding, default_unicode, default_encoding, image_encoding, cr,
     LOCAL_EASY_DATESTAMP, UTC_FULL_TIMESTAMP
     )

from flask_log_request_id import current_request_id

from .settings import MAX_XML_BODY_LEN, MAX_XML_TREE_NODES, PAN_TAGS
from .utils import (
     del_file, default_indent, indentXMLTree, getMaskedPAN,
     decoder, normpath, isIterable
     )
from .worker import getBOM


def _get_image_encoding(client, file_type, data_type=None):
    encodings = image_encoding.get(file_type) or image_encoding.get(client)
    if not encodings:
        return image_encoding['default']
    elif isinstance(encodings, dict):
        return encodings.get(data_type or 'body')
    return encodings


class FileImageDecoder:
    """
        Order File/Image Body Decoder
    """

    def __init__(self, engine, encoding=None):
        self._engine = engine
        self._encoding = encoding or default_encoding
        self._request_id = current_request_id()

        if IsDeepDebug:
            print('--> decoder: %s' % self._request_id)

        self._requested_object = None
        self._file_id = None
        self._client = None
        self._file_type = None
        self._file_status = None
        self._total = 0

        # Encodings list
        self._encodings = None
        # Temp file object name
        self._tmp = None
        # Image decoded content
        self._image = None
        # List of application tags
        self._tags = None
        # XML iterator
        self._iter = None

        self.has_body = False

    def _init_state(self, requested_object, **kw):
        self._requested_object = requested_object

        self._file_id = self._requested_object.get('FileID')
        self._client = self._requested_object.get('BankName')
        self._file_type = self._requested_object.get('FileType')
        self._file_status = self._requested_object.get('FileStatusID')

        self._tags = kw.get('tags')

        self._tmp = '%s/%s%s' % (self.tmp_folder, str(self._request_id), '%s')

        if IsDeepDebug:
            print('--> tmp: %s, file_id: %s' % (self._tmp, self._file_id))

        self._image = ''
        self._total = 0

    ##  -----------------
    ##  Internal services
    ##  -----------------

    def _decompress(self, xml, body):
        try:
            self.file_setter(xml, zlib.decompress(body))
        except:
            if IsTrace:
                print_to(errorlog, 'FileImageDecoder._decompress Error:%s' % self._file_id)
            if IsPrintExceptions:
                print_exception()

    def _clean(self):
        if not IsTmpClean:
            return
        if not (self._tmp and self.tmp_folder in self._tmp):
            return

        try:
            del_file(self.tmp_body)
            del_file(self.tmp_image)
            del_file(self.tmp_xml)

        except Exception as ex:
            print_to(None, 'FileImageDecoder.clean Error: [%s] %s' % (self.tmp_folder, str(ex)))
            if IsPrintExceptions:
                print_exception()

    def _clear_iter(self):
        if hasattr(self, '_iter'):
            del self._iter

    ##  ------------------------
    ##  Temp files specification
    ##  ------------------------

    @property
    def tmp_folder(self):
        return normpath(os.path.join(basedir, 'tmp'))
    @property
    def tmp_body(self):
        return self._tmp % '$body.dump'
    @property
    def tmp_image(self):
        return self._tmp % '$image.dump'
    @property
    def tmp_xml(self):
        return self._tmp % '.xml'

    ##  ------------------------
    ##  Public class XML objects
    ##  ------------------------

    @property
    def image(self):
        return self._image
    @property
    def root(self):
        return self._image.getroot()
    def header(self, parser='default', tags=None):
        return '%s<?xml version="1.0" encoding="%s" parser="%s"%s?>%s' % (
            getBOM(default_unicode), 
            self.encoding, 
            parser, 
            tags and ' tags="%s"' % tags or '', 
            cr
            )
    @property
    def encoding(self):
        return self._encoding
    @property
    def image_is_empty(self):
        return (self._image is None or isinstance(self._image, str) and len(self._image) == 0) and True or False
    @property
    def root_is_empty(self):
        return self.root is None and True or False
    @property
    def is_empty(self):
        return not self.has_body

    ##  --------------------
    ##  FileOrder Attributes
    ##  --------------------

    @property
    def file_id(self):
        return self._file_id
    @property
    def file_status(self):
        return self._file_status

    ##  ---------------
    ##  Public services
    ##  ---------------

    def upload(self, item=None, header=None, encoding="unicode"):
        content = item if item is not None else self._image
        return '%s%s' % (str(header or ''), ET.tostring(content, encoding=encoding))

    def flash(self):
        self._image = None

        del self._image

        self._clear_iter()
        self._clean()

    ##  --------
    ##  File I/O
    ##  --------

    @staticmethod
    def file_setter(source, data, mode='wb'):
        with open(source, mode) as fo:
            fo.write(data)

    @staticmethod
    def file_getter(source, mode='rb'):
        with open(source, mode) as fi:
            return fi.read()

    @staticmethod
    def decode_input(s, encoding, option=None):
        # Returns input data as a decoded string (str)
        # ***
        if s and isinstance(s, bytes):
            return option and s.decode(encoding, option) or s.decode(encoding)
        return not s and '' or s

    ##  ------------------------
    ##  Decoding Implementations
    ##  ------------------------

    def dumpBody(self, body):
        self.file_setter(self.tmp_body, body)

        if IsDeepDebug:
            print('>>> dump: %s' % self.tmp_body)

    def makeImage(self, body=None):
        self._decompress(self.tmp_image, body or self.file_getter(self.tmp_body))

        if IsDeepDebug:
            print('>>> image: %s' % self.tmp_image)

    def makeXml(self, body=None):
        self._decompress(self.tmp_xml, body or self.file_getter(self.tmp_body))

        if IsDeepDebug:
            print('>>> xml: %s' % self.tmp_xml)

    def _image_fromstring(self, source=None):
        """
            Makes an image ElementTree or source string object with applied encoding.

            Returns:
                image       -- ElementTree or str, an image root ElementTree object
                encoding    -- str, decoder encoding.
        """
        if source is not None:
            self._image = ET.fromstring(self.file_getter(source, mode='r'))
        else:
            size = self._image is not None and len(self._image) or 0
            if size == 0:
                return
            limit = max(size, MAX_XML_BODY_LEN)
            n = self._image.find('<FileData>')
            if n > -1:
                self._image = ET.fromstring(self._image[n:limit+n])

    def read(self, mode, file_status=None):
        """
            Reads Order Body/Image with given attrs form DB, decompress it and makes source temp file
        """
        if not self._file_id:
            return

        if not hasattr(self, '_image'):
            self._image = None

        cursor = None
        key = ''

        self.has_body = False

        if mode is not None and mode == 'image':
            key = 'FBody'
            params = "%s" % self._file_id
            cursor = self._engine.runQuery('image', as_dict=True, params=params)
        else:
            key = 'IBody'
            params = "%s, %s" % (self._file_id, file_status or 'null')
            cursor = self._engine.runQuery('body', as_dict=True, params=params)

        if not (cursor and cursor[0][key]):
            return

        self.dumpBody(cursor[0][key])

        if mode is not None and mode == 'image':
            self.makeImage()
        else:
            self._file_status = cursor[0]['FileStatusID']
            self.makeXml()

        del cursor

        self.has_body = True

    def decode(self, tmp, **kw):
        self._image, self._encoding = decoder(None, self._encodings, info='%s %s' % (self._file_id, self._client), 
                                              is_trace=kw.get('is_trace') and True or IsDecoderTrace, 
                                              limit=None,
                                              source=tmp,
                                              )
        if kw.get('as_file'):
            if self._image is not None:
                n = self._image.find('<FileData>')
            else:
                n = -1

            if n == -1 or not tmp:
                return

            self.file_setter(tmp, self._image[n:].encode(self._encoding))
            self._clear_iter()

    def check_encodings(self, encoding, data_type):
        if encoding is None:
            self._encodings = _get_image_encoding(self._client, self._file_type, data_type=data_type)
        else:
            self._encodings = (encoding,)

    """
        Read Body $ Parse XML as ByteIO without encode errors.

        Arguments:
            file_status -- str, file status
            encoding    -- str, default encoding
            data_type   -- str, data type: {image|body}, 'body' by default

        Ketword arguments:
            is_trace    -- Flag, 0/1 - trace decoding output

        Returns:
            image       -- ElementTree, an image root ElementTree object
            encoding    -- str, decoder encoding.
    """

    def decodeImage(self, encoding=None, data_type='image', **kw):
        self.read(data_type)

        if not self.has_body:
            return

        self.check_encodings(encoding, data_type)
        self.decode(self.tmp_image, **kw)

    def loadImage(self, encoding=None, data_type='image', **kw):
        self.read(data_type)

    def decodeBody(self, file_status=None, encoding=None, data_type='body', **kw):
        self.read(data_type, file_status=file_status)

        if not self.has_body:
            return

        self.decode_and_parse_image(encoding=encoding, data_type=data_type, **kw)

    def decode_and_parse_image(self, encoding=None, data_type='body', **kw):
        self.check_encodings(encoding, data_type)
        self.decode(self.tmp_xml, is_trace=kw.get('is_trace'))

        if kw.get('as_file'):
            self._image_fromstring(self.tmp_xml)
        else:
            self._image_fromstring()

    def getBody(self, file_status=None, encoding=None, data_type='body', **kw):
        self.read(data_type, file_status=file_status)

        if not self.has_body:
            return

        self.parse_image()

    def parse_image(self):
        self._image = ET.parse(self.tmp_xml)

    def loadBody(self, file_status=None, encoding=None, data_type='body', **kw):
        self.read(data_type, file_status=file_status)

    def chooseBodyParser(self, file_status=None, tag=None, forced=None):
        self.loadBody(file_status=file_status)

        if self.is_empty:
            return None

        tag = tag or 'FileBody_Record'

        # -----------------------------
        # lxml.etree Incremental parser
        # -----------------------------

        mode = 1

        if tag == 'PROCESS_ERR_MSG':
            search = './/RPT_Record[descendant::%s]' % tag
        elif tag == 'error':
            search = './/errorList[descendant::%s]' % tag
        else:
            search = tag

        try:
            if not forced or forced == mode:
                parser = LET.iterparse(self.tmp_xml, tag=search)
                return RecordsParser(parser, mode)
        except Exception as ex:
            pass

        # ----------------------------------------------------
        # xml.etree.ElementTree Incremental parser from a file
        # ----------------------------------------------------

        mode = 2

        if tag == 'PROCESS_ERR_MSG':
            search = './/RPT_Record'
        elif tag == 'error':
            search = './/errorList'
        else:
            search = tag

        try:
            if not forced or forced == mode:
                self.parse_image()
                return not self.root_is_empty and RecordsParser(self.root.iter(search), mode)
        except Exception as ex:
            pass

        # ---------------------------------------
        # xml.etree.ElementTree.fromstring parser
        # ---------------------------------------

        mode = 3

        self.decode_and_parse_image()

        if not self.image_is_empty:
            return RecordsParser(self.image.findall(search), mode, no_test=True)

        return None

    def chooseBodyState(self, file_status=None, limit=None, is_extra=False, no_cyrillic=False):
        try:
            return self.getBodyRaw(file_status=file_status, limit=limit, is_extra=is_extra)
        except:
            return self.getBodyState(file_status=file_status, limit=limit, is_extra=is_extra, no_cyrillic=no_cyrillic)

    ##  ------------
    ##  Applications
    ##  ------------

    def makeIndents(self, item=None, level=1, limit=None):
        indentXMLTree(item or self.image, level=level, limit=limit and MAX_XML_TREE_NODES or None)

    def maskContent(self, item=None, mask='//', **kw):
        """
            Hide security fields (make masked confidential keys: PAN, etc.)
        """
        forced_tag = kw.get('tag')

        if item is None:
            item = self._image

        for tag in self._tags.get('PAN'):
            if forced_tag:
                if tag != forced_tag:
                    continue
                item.text = getMaskedPAN(item.text)
                return
            else:
                #for pan in item.xpath('%s%s' % (mask, tag)):
                for pan in item.findall('.%s%s' % (mask, tag)):
                    pan.text = getMaskedPAN(pan.text)

        for x in self._tags.get('cardholders'):
            for name in (isinstance(x, str) and [x] or x):
                if forced_tag:
                    if name != forced_tag:
                        continue
                    item.text = getMaskedPAN(item.text)
                    return
                else:
                    #for tag in item.xpath('%s%s' % (mask, name)):
                    for tag in item.findall('.%s%s' % (mask, name)):
                        if tag.text is not None:
                            tag.text = '*' * len(tag.text)

    def decodeCyrillic(self, item, key='default', client=None, **kw):
        """
            Try to decode cyrillic from `IMAGE_TAGS_DECODE_CYRILLIC` tags for given `client`
            
            IMAGE_TAGS_DECODE_CYRILLIC:
            
                -- Dict, list of schemes to apply while decoding by Client or FileType:
                
                   <client> : <settings>
                
            Settings to apply:

                -- Tuple, (<FyleTypes>, <Schemes>)

            FyleTypes:

                -- Tuple, applied to given FileTypes or if empty applied to everyone

            Schemes:

                -- Tuple, list of `modes-scheme` pairs:

                   (<Mode>, <Scheme>), ...

            Mode:
            
                -- String, decoder fuction mode name: <dostowin|wintodos|iso>, look at the code `_decode`

            Scheme:

                -- Dict, lists of tags by type of scheme declaration, types: <default|record|image>:
                
                   <type> : <Parents>
            
            Parents:

                -- Dict, records to decode such as <AREP_Record>, <BANKOFFICE_Record>: 
                
                   <parent> : <Tags>

            Tags:

                -- String, tag names string with separator ':' to decode: 'TAG1:TAG2:...'
            
        """
        if not IsUseDecodeCyrillic:
            return

        if client is None:
            client = self._client

        cyrillic = self._tags.get('cyrillic') or {}

        default = cyrillic.get('default') or (None, None)
        filetypes, schemes = client and cyrillic.get(client) or default

        if not schemes:
            return

        if filetypes and self._file_type not in filetypes:
            return

        splitter = '||'
        max_len = 8000

        def _decode(text, mode):
            errors = 'ignore'
            try:
                if not mode:
                    pass
                elif mode == 'dostowin':
                    text = text.encode(default_print_encoding).decode(default_encoding)
                elif mode == 'wintodos':
                    text = text.encode(default_encoding, errors).decode(default_print_encoding)
                elif mode == 'wintowin':
                    text = text.encode(default_encoding, errors).decode(default_encoding)
                elif mode == 'dostodos':
                    text = text.encode(default_print_encoding).decode(default_print_encoding)
                elif mode == 'iso':
                    try:
                        text = text.encode(default_print_encoding).decode(default_encoding)
                    except:
                        text = text.encode(default_unicode).decode(default_unicode)
            except:
                if IsPrintExceptions:
                    print_exception()
            return text

        is_string_type = isinstance(item, str)
        forced_tag = kw.get('tag')

        for mode, scheme in schemes:
            if key not in scheme:
                continue

            tags = []
            values = []
            s = ''

            for parent in scheme[key].keys():
                for name in scheme[key][parent].split(':'):
                    if is_string_type or not name:
                        break
                    else:
                        if forced_tag:
                            if name != forced_tag:
                                continue
                            tags = [item]
                            s = item.text
                            break
                        else:
                            #mask = parent == '.' and ('./%s' % name) or ('//%s//%s' % (parent, name))
                            #for tag in item.xpath(mask):
                            mask = parent == '.' and ('.//%s' % name) or ('.//%s//%s' % (parent, name))
                            for nodes in item.findall(mask):
                                for tag in isinstance(nodes, list) and nodes or [nodes]:
                                    if tag.text is not None and len(tag.text.strip()):
                                        tags.append(tag)
                                        if len(s) > 0:
                                            s += splitter
                                        s += tag.text

            while s:
                n = len(s) > max_len and s.rfind(splitter, 0, max_len) or -1
                values += _decode(n > 0 and s[0:n] or s, mode).split(splitter)
                s = n > -1 and s[n+len(splitter):] or ''

            for n, tag in enumerate(tags):
                if is_string_type:
                    break
                else:
                    tag.text = values[n]

    def getBodyState(self, file_status=None, limit=None, is_extra=False, no_cyrillic=False):
        """
            Get $ Make readable file body content
        """
        self.decodeBody(file_status=file_status)

        try:
            if self.image is not None:
                if not no_cyrillic:
                    self.decodeCyrillic(self.image)

                if not is_extra:
                    self.maskContent(self.image)

                self.makeIndents(self.image, limit=limit and MAX_XML_TREE_NODES or None)
                return self.upload(header=self.header(parser='ET.fromstring'))

        except:
            if IsPrintExceptions:
                print_exception()

        finally:
            self.flash()

    def getBodyRaw(self, file_status=None, limit=None, is_extra=False):
        """
            Get $ Make raw file body content
        """
        self.getBody(file_status=file_status)

        try:
            if self.root is not None:
                if not is_extra:
                    self.maskContent(self.root)

                self.makeIndents(self.root, limit=limit and MAX_XML_TREE_NODES or None)
                return self.upload(item=self.root, header=self.header(parser='ET.parse'))

        except:
            if IsPrintExceptions:
                print_exception()

        finally:
            self.flash()

    def makeNodeContent(self, node, level=1, is_extra=False):
        """
            Get $ Make readable XML node content
        """
        self.decodeCyrillic(node)

        if not is_extra:
            self.maskContent(node)

        self.makeIndents(node, level=level)


class RecordsParser(object):
    
    def __init__(self, parser, mode, no_test=False):
        self._parser = parser
        self._mode = mode

        self._stopped = False
        self._item = None
        self._index = -1

        if not no_test:
            self.inner_valid()

        if IsTrace:
            print_to(errorlog, 'RecordsParser[%s]' % self._mode)

    def __iter__(self):
        return self

    def __next__(self):
        if self._item is not None:
            x, self._item = self._item, None
            return x

        self._index += 1

        try:
            if self._mode == 1:
                return next(self._parser)[1]
            if self._mode == 2:
                return next(self._parser)
            if self._mode == 3:
                return self._parser[self._index]
        except Exception as ex:
            print_to(None, 'RecordsParser.next Error: [%s] index:%s %s' % (self._mode, self._index, str(ex)))
            self._stopped = True
            raise StopIteration

    def info(self):
        return self._mode == 1 and 'LET.iterparse' or self._mode == 2 and 'ET.parse' or 'ET.fromstring'

    def inner_valid(self):
        self._item = self.__next__()
        if self._stopped:
            raise Exception('RecordsParser:invalid')

    def findall(self, node, search):
        if self._mode == 1:
            return node.xpath(search)
        return node.findall(search)

    def find(self, node, tag, encoding=None):
        item = None
        if self._mode == 1:
            items = node.xpath(tag)
            if items is not None and isinstance(items, list) and len(items) > 0:
                item = items[0]
        else:
            item = node.find(tag)
        value = item is not None and item.text or ''
        """
        if encoding:
            value = value.encode(encoding, 'ignore').decode(encoding, 'ignore')
        """
        return value and value.strip() or None

    def clear(self, node):
        if self._mode == 1:
            node.clear()
            while node.getprevious() is not None:
                del node.getparent()[0]

        if IsDeepDebug:
            print(self._index)

    def upload(self, node, encoding="unicode"):
        if self._mode == 1:
            return LET.tostring(node, encoding=encoding)
        return ET.tostring(node, encoding=encoding)


class FileDecoder():
    
    def __init__(self):
        if IsDeepDebug:
            print_to(None, 'FileDecoder.init')

        self._original = ''
        self._tmp = '%s'

        self._request_id = None

    def _init_state(self, **kw):
        if IsDeepDebug:
            print_to(None, 'FileDecoder.inistate')

        self._original = kw.get('original') or ''
        self._request_id = current_request_id()

        self._tmp = '%s/%s%s' % (self.tmp_folder, str(self._request_id), '%s')

    @property
    def original(self):
        return self._original
    @original.setter
    def original(self, value):
        self._original = value
    @property
    def request_id(self):
        return self._request_id

    @property
    def tmp_folder(self):
        return normpath(os.path.join(basedir, 'tmp'))
    @property
    def tmp_source(self):
        return '%s/%s' % (self.tmp_folder, self.original)
    @property
    def tmp_image(self):
        return self._tmp % '_image.dump'
    @property
    def tmp_compressed(self):
        return self._tmp % '_comp'
    @property
    def tmp_decompressed(self):
        return self._tmp % '_decomp'

    @staticmethod
    def file_setter(destination, data, mode='wb'):
        with open(destination, mode) as fo:
            fo.write(data)

        return len(data)

    @staticmethod
    def file_getter(source, mode='rb'):
        with open(source, mode) as fi:
            return fi.read()

    def _decompress(self, destination, data):
        self.file_setter(destination, zlib.decompress(data))

    def _compress(self, destination, source):
        self.file_setter(destination, zlib.compress(self.file_getter(source)))

    def _clean(self):
        if not IsTmpClean:
            return
        if not (self._tmp and self.tmp_folder in self._tmp):
            return

        try:
            del_file(self.tmp_decompressed)
            del_file(self.tmp_compressed)
            del_file(self.tmp_image)

        except Exception as ex:
            print_to(None, 'FileDecoder.clean Error: [%s] %s' % (self.tmp_folder, str(ex)))
            if IsPrintExceptions:
                print_exception()

    def dispose(self):
        self._clean()

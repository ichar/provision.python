# -*- coding: utf-8 -*-

import datetime
import codecs
import sys
import os
import re
import time
from operator import itemgetter

from config import (
     BP_ROOT, INFOEXCHANGE_ROOT, SDC_ROOT, EXCHANGE_ROOT, IsDebug, IsDeepDebug, IsTrace, IsLogTrace, IsPrintExceptions,
     default_unicode, default_encoding, UTC_FULL_TIMESTAMP,
     print_to, print_exception
     )

from .settings import DEFAULT_DATETIME_FORMAT, DEFAULT_DATETIME_INLINE_FORMAT, MAX_LOGS_LEN
from .utils import normpath, cdate, getDate, getToday, decoder, pickupKeyInLine
from .booleval import Token

try:
    from types import UnicodeType, StringType
    StringTypes = (UnicodeType, StringType,)
except:
    StringTypes = (str,)

is_v3 = sys.version_info[0] > 2 and True or False

if is_v3:
    from imp import reload

IsCheckFolders = 0
IsDisableOutput = 0

perso_log_config = { \
    'root'    : 'Bin',
    'dir'     : ('Log_.*',), # 'HomeCredit_.*',
    'file'    : ('\d{8}_.*\.log',),
    'error'   : 'ERROR',
    'suspend' : ( \
        'Log_AllExecute',
        'Log_ConvertBinaryDumpToHexString',
        'Log_BMVIRTUON_PourOrderFile',
        'Log_DHL_PreProc',
        #'Log_BatchResult',
        #'Log_BatchStep',
        #'Log_CardsLoad',
        #'Log_CardsUnLoad',
        'Log_EGOVMergerAfterSDC',
        'Log_Indigo',
        'Log_Schedule',
        'Log_SDCDivider',
        'Log_Response_OW',
        #'Log_ReportRunnerV02',
        'Log_Pony_PreProc',
    ),
    'ignore'  : ( \
        'не может быть номером задания (PersID)',
        'Не найдено ни одного файла соответствующего файлу',
        'не найден входной каталог',
    ),
}

infoexchange_log_config = { \
    'root'    : '', #'Log_OutReceiver',
    'dir'     : (),
    'file'    : ('\d{8}_OutReceiver.log',),
    'error'   : 'ERROR',
    'suspend' : ( \
    ),
}

sdc_log_config = { \
    'root'    : 'LOG',
    'dir'     : ('.*',),
    'file'    : ('sdc_.*\.txt',),
    'error'   : 'ERROR',
    'suspend' : ( \
    ),
    'ignore'  : ( \
        '--BEGIN--',
        '--END--',
    ),
}

exchange_log_config = { \
    'root'    : '#logs',
    'dir'     : ('.*',),
    'file'    : ('.*\.(txt|log)',),
    'error'   : 'ERROR',
    'suspend' : ( \
    ),
}

xre = re.compile(r'. ([\d-]*) ([\d:.\.]*) (.*): (.*)')

EOL = '\n'

config = None

ansi = not sys.platform.startswith("win")

## ==================================================== ##

def _pout(s, **kw):
    if not is_v3:
        print(s, end='end' in kw and kw.get('end') or None)
        if 'flush' in kw and kw['flush'] == True:
            sys.stdout.flush()
    else:
        print(s, **kw)

def set_globals(config):
    global IsDebug, IsDeepDebug, IsTrace, IsLogTrace, IsPrintExceptions
    if not config:
        return
    if 'debug' in config:
        IsDebug = config.get('debug') or 0
    if 'deepdebug' in config:
        IsDeepDebug = config.get('deepdebug') or 0
    if 'trace' in config:
        IsTrace = config.get('trace') or 0
    if 'logtrace' in config:
        IsLogTrace = config.get('logtrace') or 0
    if 'printexceptions' in config:
        IsPrintExceptions = config.get('printexceptions') or 0

#   ------------------------------
#   General arguments definitions:
#   ------------------------------
#       logs              -- list: Log-items collection [output]
#       filename          -- string: name of current Log-file
#       filemask          -- string: mask of Log-file to match a date (`sdc|exchange` special)
#       encoding          -- string: preffered encoding for a Log-file
#       keys              -- list of strings: `Order` keywords list
#       split_by          -- string: Log-line items separator (TAB by default)
#       columns           -- tuple of strings: Log-item columns list
#       dates             -- tuple of datetimes: dates for Log-file names validation
#       client            -- string: `Order` client name
#       aliases           -- list of strings: client aliases
#       fmt               -- tuple of strings: format of datetime for matching in Log-file lines
#       date_format       -- string: `strftime` mask of date to make string timestamp (DEFAULT_DATETIME_FORMAT by default)
#       options           -- string: extra-options for Log-item performing (`sdc|exchange` special)
#       case_insensitive  -- boolean: use case-insensitive keys search
#       no_span           -- boolean: make `span` tag or not
#       config            -- tuple: Log-config as (encoding, root, filemask, options)
#       files             -- dict: FSO pointers for launched Log-files [output]
#       lines             -- list of tuples: new Log-lines extracted under last checked Log-file FSO-pointer [input/output]
#                               ((filename, line), (filename, line), ...)
#       pointers          -- boolean: FSO-pointers setup flag
#   -------------------
#   Trace/Debug levels:
#   -------------------
#       IsDebug           -- flag: Log-items `getter` errors
#       IsDeepDebug       -- flag: unexpected errors (!!!)
#       IsTrace           -- flag: trace of start/finish events
#       IsLogTrace        -- flag: trace of open/decode/empty/file/folder detailed info
#       IsPrintExceptions -- flag: `checkfile/checkline` ValueError, UnicodeError, `getter` conversion errors
#       decoder_trace     -- boolean: argument of `checkfile`, prints decoder errors
#

class Logger():
    def __init__(self, to_file=None, encoding=default_unicode, mode='w+', bom=True, end_of_line=EOL):
        self.is_to_file = to_file and 1 or 0
        self.encoding = encoding
        self.fo = None
        self.end_of_line = end_of_line

        if IsDisableOutput and to_file:
            pass
        elif to_file:
            self.fo = codecs.open(to_file, encoding=self.encoding, mode=mode)
            if bom:
                self.fo.write(codecs.BOM_UTF8.decode(self.encoding))
            self.out(to_file, console_forced=True)  # _pout('--> %s' % to_file)
        else:
            pass

    def get_to_file(self):
        return self.fo

    def set_default_encoding(self, encoding=default_unicode):
        if sys.getdefaultencoding() == 'ascii':
            reload(sys)
            sys.setdefaultencoding(encoding)
        _pout('--> %s' % sys.getdefaultencoding())

    def out(self, line, console_forced=False, without_decoration=False):
        if not line:
            return
        elif console_forced or not (self.fo or self.is_to_file):
            mask = '%s' % (not without_decoration and '--> ' or '')
            try:
                _pout('%s%s' % (mask, line))
            except:
                if is_v3:
                    pass
                elif type(line) is UnicodeType:
                    v = ''
                    for x in line:
                        try:
                            _pout(x, end='')
                            v += x.encode(default_encoding, 'ignore')
                        except:
                            v += '?'
                    _pout('')
                else:
                    _pout('%s%s' % (mask, line.decode(default_encoding, 'ignore')))
        elif IsDisableOutput:
            return
        else:
            if type(line) in StringTypes:
                try:
                    self.fo.write(line)
                except:
                    if is_v3:
                        return
                    try:
                        self.fo.write(unicode(line, self.encoding))
                    except:
                        try:
                            self.fo.write(line.decode(default_encoding))  # , 'replace'
                        except:
                            raise
                if not line == self.end_of_line:
                    self.fo.write(self.end_of_line)

    def progress(self, line=None, mode='continue'):
        if mode == 'start':
            _pout('--> %s:' % (line or ''), end=' ')
        elif mode == 'end':
            _pout('', end='\n')
        else:
            _pout('#', end='', flush=True)

    def close(self):
        if IsDisableOutput:
            return
        if not self.fo:
            return
        self.fo.close()

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

## ==================================================== ##

def getBOM(encoding):
    return codecs.BOM_UTF8.decode(encoding)

def get_opposite_encoding(encoding):
    return encoding == default_encoding and default_unicode or default_encoding

def _extract_keys(keys):
    if isinstance(keys, Token):
        return keys.get_keys()
    return keys or []

def _register_error(logs, e, **kw):
    logs.append({
        'Date' : cdate(getToday(), kw.get('date_format') or UTC_FULL_TIMESTAMP),
        'exception' : str(e),
    })

def _findkey(line, key, **kw):
    n = -1
    
    case_insensitive = kw.get('case_insensitive') and True or False
    no_span = kw.get('no_span') and True or False
    
    if case_insensitive:
        n = line.lower().find(key.lower())
    else:
        n = line.find(key)

    if IsDeepDebug and IsLogTrace:
        print_to(None, '... _findkey[%s]: %s %s' % (n, case_insensitive, no_span))
    
    if n > -1 and key.lower() not in ('error', 'warning', 'info',) and not no_span:
        line = pickupKeyInLine(line, key)
    
    return line, n > -1 and True or False

def openfile(filename, mode='r', encoding=default_encoding, use_codecs=False):
    is_opened = False
    forced_encoding = encoding

    default_mode = 'r'
    fo = None
    line = ''

    try:
        if 'b' in mode:
            fo = open(filename, mode)
        elif use_codecs:
            fo = codecs.open(filename, mode, encoding=forced_encoding)
        else:
            fo = open(filename, mode, encoding=forced_encoding)
        #
        # Check content valid encoding
        #
        line = fo.readline()
        fo.seek(0)
        is_opened = True
        line = None

    except:
        if IsLogTrace:
            print_to(None, '>>> openfile error: [%s] mode:%s encoding:%s' % (filename, mode, forced_encoding))

        forced_encoding = get_opposite_encoding(forced_encoding)

        if fo is not None and not fo.closed:
            fo.close()
        #
        # Try to reopen file in opposite encoding
        #
        try:
            if use_codecs:
                fo = codecs.open(filename, default_mode, encoding=forced_encoding)
            else:
                fo = open(filename, default_mode, encoding=forced_encoding)
            is_opened = True
        except:
            print_to(None, '!!! openfile error: cannot open file')
            fo = None

    return fo or [], forced_encoding, is_opened

def closefile(fin):
    if fin and not fin.closed:
        fin.close()

def is_valid_line(line, is_bytes):
    keys = is_bytes and (b'-->', b'==>', b'>>>',) or ('-->', '==>', '>>>',)
    return line and len([1 for key in keys if key not in line]) == len(keys) and True or False

def checkfile(filename, mode, encoding, logs, keys, getter, msg, **kw):
    """
        Checks Log-file lines, decodes their and generates Logs-items.

        Function reads given Log-file and generates Log-items collection matched with the given keys.
        If passed `lines`, function doesn't make logs and returns lines content only.

        Arguments:
            filename         -- string: full path to Log-file
            mode             -- string: file open mode (r|rb ...)
            encoding         -- string: preffered encoding to decode messages
            logs             -- list: logged items collection, [output]
            keys             -- iterable: searching keys set
            getter           -- callable: log-item fabric
            msg              -- string: text to output in trace

        Keyword arguments:
            forced           -- bool: add a new item to logs forced
            unique           -- bool: log unique items only
            with_count       -- bool: count number of unique messages
            case_insensitive -- bool: if True, use case-insensitive keys check
            no_span          -- bool: if True, don't insert <span> tag inside the log context
            decoder_trace    -- bool: lines decoder trace
            files            -- dict: processed Logs-files seek pointers, [output]
            lines            -- list: obtained Log-lines only, [output]

        Returns [output] by ref.
    """
    forced = kw.get('forced') or False
    unique = kw.get('unique') or False
    with_count = kw.get('with_count') or False
    case_insensitive = kw.get('case_insensitive') or False
    no_span = kw.get('no_span') or False
    decoder_trace = kw.get('decoder_trace') or False
    files = kw.get('files') or None
    lines = kw.get('lines')

    set_globals(kw.get('globals'))

    line = ''

    fin, forced_encoding, is_opened = openfile(filename, mode, encoding)

    is_bytes = 'b' in mode
    #
    # Check if keys prepared as a `booleval` Token expression
    #
    IsToken = isinstance(keys, Token)

    if IsToken:
        token = keys
        keys = token.get_keys()
    else:
        token = None
    #
    # Prepare insensitive search
    #
    if case_insensitive:
        if IsToken:
            pass
        else:
            keys = [key.lower() for key in keys]
    #
    # Set opposite encoding for decoder-tricks
    #
    encodings = (encoding, get_opposite_encoding(encoding),)
    #
    # Get FSO-pointer for a given Log-file
    #
    spointer = files is not None and filename in files and files[filename] or None
    #
    # Check lines-mode only
    #
    IsLinesOnly = lines is not None and True or False

    num_logged = 0
    num_line = 0
    pointer = 0

    try:
        #
        # Start reading the file from the last seek-position
        #
        if is_opened and spointer is not None:
            fin.seek(spointer, 0)

        while is_opened:
            size = 0
            pointer = fin.tell()

            if pointer == os.path.getsize(filename):
                break

            if IsDeepDebug and IsLogTrace:
                print_to(None, '... pointer[%s]: %s' % (pointer, num_logged))

            try:
                line = fin.readline()
                size = len(line)
                num_line += 1

                if not is_valid_line(line, is_bytes):
                    continue

                info = '%d:%d:%d' % (num_line, size, pointer)
                line_save = line
                #
                # Decode bytes as string with more preffered encoding
                #
                if is_bytes:
                    line, encoding = decoder(line, encodings, info=info, is_trace=decoder_trace)
                #
                # Check end of the stream
                #
                if not line:
                    if size > 0:
                        if IsDeepDebug and IsLogTrace:
                            print_to(None, '!!! NO LINE DECODED[%s]: %s %s' % (filename, info, line_save))
                    continue
                if IsLinesOnly:
                    lines.append((filename, line,))
                    num_logged += 1
                    continue
                if forced:
                    logs.append(getter(line))
                    num_logged += 1
                    continue
                #
                # Search keys and add a new item to the logs-collection
                #
                logged = checkline(line, logs, keys, getter, 
                                   token=token, unique=unique, with_count=with_count, case_insensitive=case_insensitive, no_span=no_span)

                if logged > 0:
                    num_logged += logged

            except (ValueError, UnicodeError):
                if IsLogTrace:
                    print_to(None, '>>> INVALID %s LINE[%s]: %s %s' % (msg, filename, info, line))
                if IsPrintExceptions:
                    print_exception()
                if size > 0 and fin.tell() - pointer > size:
                    fin.seek(pointer+size, 0)
            except:
                if IsDeepDebug and IsLogTrace:
                    print_to(None, '!!! CHECKFILE ERROR[%s]: %s %s' % (filename, info, line))
                if IsPrintExceptions:
                    print_exception()
                raise

    except EOFError:
        pass

    closefile(fin)

    if files is not None and pointer > 0: # and num_logged > 0
        files[filename] = pointer

    if IsLogTrace:
        print_to(None, '--> file: %s %s %s %s [%d]: %d' % ( \
            mdate(filename), filename, forced_encoding, is_opened, num_logged, pointer
            ))

def lines_emitter(filename, mode, encoding, msg, **kw):
    """
        Emitter of Log-file lines, decodes their and generates Logs-items.

        Arguments:
            filename         -- string: full path to Log-file
            mode             -- string: file open mode (r|rb ...)
            encoding         -- string: preffered encoding to decode messages
            msg              -- string: text to output in trace

        Keyword arguments:
            decoder_trace    -- bool: lines decoder trace
            files            -- dict: processed Logs-files seek pointers, [output]
    """
    decoder_trace = kw.get('decoder_trace') or False
    files = kw.get('files') or None

    set_globals(kw.get('globals'))

    line = ''
    
    fin, forced_encoding, is_opened = openfile(filename, mode, encoding)
    
    is_bytes = 'b' in mode
    #
    # Set opposite encoding for decoder-tricks
    #
    encodings = (encoding, get_opposite_encoding(encoding),)
    #
    # Get FSO-pointer for a given Log-file
    #
    spointer = files is not None and filename in files and files[filename] or None

    num_line = 0
    pointer = 0

    try:
        #
        # Start reading the file from the last seek-position
        #
        if is_opened and spointer is not None:
            fin.seek(spointer, 0)

        while is_opened:
            size = 0
            pointer = fin.tell()

            if pointer == os.path.getsize(filename):
                break

            try:
                line = fin.readline()
                size = len(line)
                num_line += 1

                if not is_valid_line(line, is_bytes):
                    continue

                info = '%d:%d:%d' % (num_line, size, pointer)
                line_save = line
                #
                # Decode bytes as string with more preffered encoding
                #
                if is_bytes:
                    line, encoding = decoder(line, encodings, info=info, is_trace=decoder_trace)
                #
                # Check end of the stream
                #
                if not line:
                    if size > 0:
                        if IsDebug or IsLogTrace:
                            print_to(None, '!!! NO LINE DECODED[%s]: %s\n%s' % (filename, info, line_save))
                    continue
                #
                # Generate a new line output
                #
                yield line.strip()

            except (ValueError, UnicodeError):
                if IsLogTrace:
                    print_to(None, '>>> INVALID %s LINE[%s]: %s\n%s' % (msg, filename, info, line))
                if IsPrintExceptions:
                    print_exception()
                if size > 0 and fin.tell() - pointer > size:
                    fin.seek(pointer+size, 0)
            except:
                if IsLogTrace:
                    print_to(None, '!!! EMITTER ERROR[%s]: %s\n%s' % (filename, info, line))
                if IsPrintExceptions:
                    print_exception(1)
                else:
                    raise

    except EOFError:
        pass

    closefile(fin)

    if files is not None and pointer > 0:
        files[filename] = pointer

    if IsLogTrace:
        print_to(None, '--> file: %s %s %s %s [%d]: %d' % ( \
            mdate(filename), filename, forced_encoding, is_opened, num_line, pointer
            ))

def checkline(line, logs, keys, getter, **kw):
    """
        Checks the Log-file line and makes a new logs-item
    """
    token = kw.get('token') or None
    unique = kw.get('unique') or False
    with_count = kw.get('with_count') or False
    case_insensitive = kw.get('case_insensitive') or False
    no_span = kw.get('no_span') or False

    mcre = re.compile(r'\[(\d+)\]')
    
    logged = 0

    def _has_unique(ob):
        #
        # Call it if the log-item should be unique
        #
        for log in logs:
            if log.get('filename') == ob.get('filename'):
                if log.get('Date') == ob.get('Date') and log.get('Message') == ob.get('Message'):
                    s = 'Module'
                    if with_count and s in log:
                        module = log[s] or ''
                        m = mcre.search(module)
                        if m:
                            cnt = int(m.group(1) or '1')
                        else:
                            module += '[1]'
                            cnt = 1
                        log[s] = re.sub(r'\d+', str(cnt+1), module)
                    return True
        return False

    def _is_ignore_line(line):
        for x in config.get('ignore', []):
            if x and x in line:
                return True
        return False

    if line:
        #
        # Check if line should be ignored
        #
        if _is_ignore_line(line):
            return -1
        IsFound = False
        #
        # Search given keys
        #
        if IsDeepDebug and IsLogTrace:
            print_to(None, '... checkline[%s]: token:%s keys:%s' % (line, token and 1 or 0, keys))

        if token is not None:
            for key in keys:
                line, is_found = _findkey(line, key['value'], case_insensitive=case_insensitive, no_span=no_span)
                key['res'] = is_found
            token.set_values(keys)
            IsFound = token()
        else:
            for key in keys:
                line, is_found = _findkey(line, key, case_insensitive=case_insensitive, no_span=no_span)
                if is_found:
                    IsFound = True
                    break
        #
        # Add a new item to logs
        #
        if IsFound:
            item = getter(line)
            if item is not None and not (unique and _has_unique(item)):
                logs.append(item)
                logged = 1

    else:
        if IsLogTrace:
            print_to(None, '!!! empty line[%s]' % line)

    return logged

def mdate(filename):
    try:
        t = os.path.getmtime(filename)
        return datetime.datetime.fromtimestamp(t)
    except:
        if IsPrintExceptions:
            print_exception()
        return None

def is_mask_matched(mask, value):
    return mask and value and re.match(mask, value)

def is_today_file(name, dates=None, filemask=None, filename=None, format=None):
    """
        Checks filename date.
        
        Arguments:
            name     -- string: name of file only
            dates    -- tuple of dates: (date_from[, date_to]) of given period
            filemask -- string: datetime mask to get date of the file
            filename -- string: full file name with path
            format   -- tuple of datetime formats: preffered format for a given type of source (settings)
    """
    #
    # Даты не заданы - текущая дата
    #
    if not dates:
        now = datetime.datetime.now()
        return mdate((filename or name)).date() == now.date()
    #
    # Имя файла начинается с даты (bankperso): 20170509_Load_SyncroResTinkoff.log
    #
    elif len(dates) < 2:
        date = name.split('_')[0]
        return date in dates
    #
    # Дата файла кодируется по заданной маске в имени файла (SDC, Exchange): '<name>_(.*)_(\d{2}\.\d{2}\.\d{4}).*'
    # Should be present 2 groups: `module`, `sdate`
    #
    elif filemask is not None:
        rfile = re.compile(filemask)
        m = rfile.search(name)
        sdate = m and len(m.groups()) > 1 and m.group(2) or None
        if not dates:
            return sdate and True or False
        date = getDate(sdate, format=format[0], is_date=True)
        if len(dates) == 2 and date:
            return date >= dates[0] and (dates[1] is None or date <= dates[1])
        else:
            return False
    #
    # Диапазон дат (не менее 2-х дат)
    #
    else:
        date = getDate(name.split('_')[0], format[0], is_date=True)
        return date is not None and (date >= dates[0] and (dates[1] is None or date <= dates[1]))

def valid_name(mode, value):
    if not config.get(mode):
        return True
    for mask in config.get(mode):
        if is_mask_matched(mask, value) is not None:
            return True
    return False

def check_path(root, logger):
    for name in os.listdir(root):
        folder = normpath(os.path.join(root, name))

        logger.out('--> %s' % folder)

        if os.path.isdir(folder):
            check_path(folder, logger)

def check_aliases(folder, aliases):
    for alias in aliases:
        if alias.lower() in folder.lower():
            return True
    return False

def walk(logs, checker, root, **kw):
    client = kw.get('client')
    options = kw.get('options') or ''
    aliases = kw.get('aliases') or None
    files = kw.get('files')

    obs, n = [], 0

    while n < 3:
        try:
            obs = os.listdir(root)
            break
        except:
            if IsLogTrace:
                print_to(None, '... walk:%s, root:%s' % (n, root))

            time.sleep(3)
            n += 1

    for name in obs:
        folder = normpath(os.path.join(root, name))
        #
        # Check Logs limit
        #
        if logs and len(logs) > MAX_LOGS_LEN:
            break

        if not os.path.exists(folder):
            continue

        if name in config.get('suspend'):
            continue
        #
        # Check folder name
        #
        elif os.path.isdir(folder): # and not os.path.islink(folder):
            if not valid_name('dir', name):
                continue
            if '*' in options:
                pass
            elif 'with_aliases' in options and aliases is not None:
                if not check_aliases(folder, aliases):
                    continue
                if IsLogTrace:
                    print_to(None, '--> folder: %s' % folder)
            walk(logs, checker, folder, **kw)
        #
        # Check file name & start log-checker
        #
        else:
            if not valid_name('file', name):
                continue
            filename = normpath(os.path.join(root, name))
            if not is_today_file(name, dates=kw.get('dates'), filemask=kw.get('filemask'), 
                                 filename=filename, format=kw.get('fmt')):
                continue
            if 'pointers' in kw:
                if files is not None:
                    files[filename] = os.path.getsize(filename)
            elif checker is None:
                continue
            else:
                checker(logs, filename, **kw)

## ==================================================== ##
##                 BANKPERSO LOG PARSER                 ##
## ==================================================== ##

def check_perso_log(logs, filename, encoding=default_encoding, **kw):
    keys = kw.get('keys')
    split_by = kw.get('split_by') or '\t'
    columns = kw.get('columns')
    fmt = kw.get('fmt')
    date_format = kw.get('date_format') or DEFAULT_DATETIME_FORMAT
    case_insensitive = kw.get('case_insensitive')
    no_span = kw.get('no_span')

    forced = kw.get('forced') and True or False
    unresolved = kw.get('unresolved') and True or False

    set_globals(kw.get('globals'))

    def _get_log_item(line):
        values = line.split(split_by)
        ob = {'filename': filename}

        try:
            for n, column in enumerate(columns):
                ob[column] = values[n].strip()
        except:
            pass

        try:
            x = datetime.datetime.strptime('%s' % ob['Date'], fmt[1])
            ob['Date'] = cdate(x, date_format)
        except:
            if IsDebug and IsPrintExceptions:
                print_exception()
            return None

        if 'Code' in ob:
            ob['Code'] = re.sub(r'[\[\]]', '', ob['Code'].upper())
        return ob

    if 'lines' in kw:
        lines = kw.get('lines')

        # ------------------------------
        # Observer Log-lines constructor
        # ------------------------------
        """
        if case_insensitive:
            keys = [key.lower() for key in keys]
        """
        i = 0
        while lines and i < len(lines):
            filename, line = lines[i]
            x = checkline(line, logs, keys, getter=_get_log_item, 
                          token=None, unique=False, with_count=False,
                          case_insensitive=case_insensitive,
                          no_span=no_span,
                          )
            if x != 0:
                lines.pop(i)
            else:
                """
                if IsDeepDebug and unresolved:
                    print_to(None, '!!! UNRESOLVED:\n%s\n%s%s\n' % (filename, line, keys))
                """
                i += 1
        return

    checkfile(filename, 'rb', encoding, logs, keys, getter=_get_log_item, msg='BANKPERSOLOG', 
              forced=forced, 
              case_insensitive=case_insensitive,
              no_span=no_span,
              files=kw.get('files'),
              )

def getClientConfig(client):
    if not client or client not in BP_ROOT:
        client = 'default'

    return BP_ROOT[client]

def getPersoLogInfo(**kw):
    global config

    logs = []
    
    encoding, root = kw.get('config') or getClientConfig(kw.get('client'))

    if root is None:
        return logs

    set_globals(kw.get('globals'))

    config = perso_log_config
    root = normpath(os.path.join(root, config['root']))

    if IsTrace:
        keys = _extract_keys(kw.get('keys')) or []
        print_to(None, '\n==> CHECK_PERSO_LOG: %s STARTED [%s:%s:%s]' % ( 
            datetime.datetime.now().strftime(UTC_FULL_TIMESTAMP),
            len(keys) > 0 and keys[0] or '',
            kw.get('client'),
            kw.get('dates'),
            ))

    try:
        if IsCheckFolders:
            logger = Logger('./folders.txt', encoding=default_encoding)
            check_path(".", logger)
            logger.close()

        walk(logs, check_perso_log, root, encoding=encoding, **kw)
    except Exception as e:
        _register_error(logs, e, **kw)

        if IsPrintExceptions:
            print_exception()

    logs = sorted(logs, key=itemgetter('Date'))

    if IsTrace:
        print_to(None, '==> CHECK_PERSO_LOG: %s FINISHED' % datetime.datetime.now().strftime(UTC_FULL_TIMESTAMP))
    
    return logs

def getPersoLogFile(**kw):
    global config

    logs = []

    encoding, root = getClientConfig(kw.get('client'))

    filename = normpath(os.path.join(root, 'Bin', kw.get('perso_log')))
    config = perso_log_config

    if os.path.exists(filename):
        check_perso_log(logs, filename, encoding=encoding, forced=True, **kw)

    return logs

## ==================================================== ##
##               INFOEXCHANGE LOG PARSER                ##
## ==================================================== ##

def check_infoexchange_log(logs, filename, encoding=default_encoding, **kw):
    keys = kw.get('keys')
    split_by = kw.get('split_by') or '\t'
    columns = kw.get('columns')
    fmt = kw.get('fmt')
    date_format = kw.get('date_format') or DEFAULT_DATETIME_INLINE_FORMAT
    case_insensitive = kw.get('case_insensitive')
    no_span = kw.get('no_span')

    forced = kw.get('forced') and True or False

    original_logger = kw.get('original_logger') and True or False

    def _get_log_item(line):
        if not line:
            return None
        values = line.split(split_by)
        if len(values) != len(columns):
            return None
        ob = {'filename': filename}

        try:
            for n, column in enumerate(columns):
                ob[column] = values[n].strip()
        except:
            if IsDebug and IsPrintExceptions:
                print_exception()

        try:
            x = datetime.datetime.strptime('%s' % ob['Date'], fmt[1])
            ob['Date'] = cdate(x, date_format)
        except:
            if IsDebug and IsPrintExceptions:
                print_exception()

        if 'Code' in ob:
            ob['Code'] = re.sub(r'[\[\]]', '', ob['Code'].upper())
        return ob

    if IsLogTrace:
        print_to(None, '--> file: %s %s' % (mdate(filename), filename))

    # ---------------------------------------------
    # Output Log from native view (Original Logger)
    # ---------------------------------------------

    if original_logger:
        fin, forced_encoding, is_opened = openfile(filename, 'r', encoding=encoding)

        IsOutput = IsFound = False
        lines, n = [], 0

        for line in fin:
            if IsDeepDebug and IsLogTrace:
                print_to(None, '... line[%s]: %s' % (n, len(lines)))

            n += 1

            try:
                if forced:
                    logs.append(_get_log_item(line))
                    continue

                if not IsOutput and 'Version' in line:
                    IsOutput = True

                for key in keys:
                    line, is_found = _findkey(line, key, case_insensitive=case_insensitive, no_span=no_span)
                    if is_found:
                        IsFound = True

                if IsOutput:
                    lines.append(_get_log_item(line))

                if 'Выход' in line:
                    if IsFound:
                        logs += list(filter(None, lines))

                    IsOutput = IsFound = False
                    lines = []
            except:
                if IsLogTrace:
                    print_to(None, '>>> INVALID INFOEXCHAGE LINE[%s]: %s' % (filename, line))
                    print_exception()

        if lines and IsFound:
            logs += list(filter(None, lines))

        closefile(fin)

        return

    # -----------------
    # Used in LogSearch
    # -----------------

    checkfile(filename, 'rb', encoding, logs, keys, getter=_get_log_item, msg='INFOEXCHANGELOG', 
              forced=forced, 
              case_insensitive=case_insensitive,
              no_span=no_span,
              files=kw.get('files'),
              )

def getInfoExchangeConfig(client):
    if not client or client not in INFOEXCHANGE_ROOT:
        client = 'default'

    return INFOEXCHANGE_ROOT[client]
    
def getInfoExchangeLogInfo(**kw):
    global config

    logs = []
    
    encoding, root = getInfoExchangeConfig(kw.get('client'))

    if root is None:
        return logs

    config = infoexchange_log_config
    root = normpath(os.path.join(root, kw.get('base') or '', config['root']))

    if IsTrace:
        keys = _extract_keys(kw.get('keys')) or []
        print_to(None, '\n==> CHECK_INFOEXCHANGE_LOG: %s STARTED [%s:%s:%s]' % ( 
            datetime.datetime.now().strftime(UTC_FULL_TIMESTAMP),
            len(keys) > 0 and keys[0] or '',
            kw.get('client'),
            kw.get('dates'),
            ))

    try:
        if IsCheckFolders:
            logger = Logger('./folders.txt', encoding=default_encoding)
            check_path(".", logger)
            logger.close()

        walk(logs, check_infoexchange_log, root, encoding=encoding, **kw)
    except Exception as e:
        _register_error(logs, e, **kw)

        if IsPrintExceptions:
            print_exception()
    
    logs = sorted(logs, key=itemgetter('Date'))

    if IsTrace:
        print_to(None, '==> CHECK_INFOEXCHANGE_LOG: %s FINISHED' % datetime.datetime.now().strftime(UTC_FULL_TIMESTAMP))

    #if 'files' in kw:
    #    return logs, kw.get('files')
    
    return logs

## ==================================================== ##
##                    SDC LOG PARSER                    ##
## ==================================================== ##

def check_sdc_log(logs, filename, encoding=default_encoding, **kw):
    keys = kw.get('keys')
    split_by = kw.get('split_by') or '\t'
    columns = kw.get('columns')
    fmt = kw.get('fmt')
    date_format = kw.get('date_format') or DEFAULT_DATETIME_FORMAT
    case_insensitive = kw.get('case_insensitive')
    no_span = kw.get('no_span')
    
    forced = kw.get('forced') and True or False
    unresolved = kw.get('unresolved') and True or False

    set_globals(kw.get('globals'))

    def _get_log_item(line):
        values = line.split(split_by)
        ob = {'filename': filename}

        try:
            for n, column in enumerate(columns):
                ob[column] = values[n].strip()
        except:
            pass

        try:
            x = datetime.datetime.strptime('%s %s' % (ob['Date'], ob['Time']), fmt[1])
            ob['Date'] = cdate(x, date_format)
        except:
            return None

        if 'Code' in ob:
            ob['Code'] = re.sub(r'[\[\]]', '', ob['Code'].upper())
        return ob

    if 'lines' in kw:
        lines = kw.get('lines')

        # ------------------------------
        # Observer Log-lines constructor
        # ------------------------------
        """
        if case_insensitive:
            keys = [key.lower() for key in keys]
        """
        i = 0
        while lines and i < len(lines):
            filename, line = lines[i]
            x = checkline(line, logs, keys, getter=_get_log_item, 
                          token=None, unique=False, with_count=False,
                          case_insensitive=case_insensitive,
                          no_span=no_span,
                          )
            if x != 0:
                lines.pop(i)
            else:
                """
                if IsDeepDebug and unresolved:
                    print_to(None, '!!! UNRESOLVED:\n%s\n%s%s\n' % (filename, line, keys))
                """
                i += 1
        return

    checkfile(filename, 'rb', encoding, logs, keys, getter=_get_log_item, msg='SDCLOG', 
              forced=forced, 
              case_insensitive=case_insensitive,
              no_span=no_span,
              files=kw.get('files'),
              )

def getSDCConfig(client):
    if not client or client not in SDC_ROOT:
        client = 'default'

    return SDC_ROOT[client]

def getSDCLogInfo(**kw):
    global config

    logs = []

    encoding, root, filemask, options = kw.get('config') or getSDCConfig(kw.get('client'))

    if root is None:
        return logs

    set_globals(kw.get('globals'))

    config = sdc_log_config
    root = normpath(os.path.join(root, config['root']))

    kw['filemask'] = filemask
    kw['options'] = options

    if IsTrace:
        keys = _extract_keys(kw.get('keys')) or []
        print_to(None, '\n==> CHECK_SDC_LOG: %s STARTED [%s:%s:%s]' % ( 
            datetime.datetime.now().strftime(UTC_FULL_TIMESTAMP),
            len(keys) > 0 and keys[0] or '',
            kw.get('client'),
            kw.get('dates'),
            ))

    try:
        if IsCheckFolders:
            logger = Logger('./folders.txt', encoding=default_encoding)
            check_path(".", logger)
            logger.close()

        walk(logs, check_sdc_log, root, encoding=encoding, **kw)
    except Exception as e:
        _register_error(logs, e, **kw)

        if IsPrintExceptions:
            print_exception()

    logs = sorted(logs, key=itemgetter('Date'))

    if IsTrace:
        print_to(None, '==> CHECK_SDC_LOG: %s FINISHED' % datetime.datetime.now().strftime(UTC_FULL_TIMESTAMP))

    return logs

## ==================================================== ##
##                 EXCHANGE LOG PARSER                  ##
## ==================================================== ##

def check_exchange_log(logs, filename, encoding=default_encoding, **kw):
    keys = kw.get('keys')
    split_by = kw.get('split_by') or '\t'
    columns = kw.get('columns')
    fmt = kw.get('fmt')
    date_format = kw.get('date_format') or DEFAULT_DATETIME_FORMAT
    case_insensitive = kw.get('case_insensitive')
    no_span = kw.get('no_span')
    forced = kw.get('forced') and True or False
    options = kw.get('options') or ''

    set_globals(kw.get('globals'))
    #
    # Check JZDO log format
    #
    is_jzdo = 'jzdo' in options and 'jzdo' in filename.lower()

    def _get_log_item(line):
        m = None

        if split_by in line:
            values = line.split(split_by)
        elif line.startswith('. 2'):
            m = re.search(xre, line)
            if m:
                values = m.groups()
            else:
                return None
        else:
            v = line.split()
            n = len(columns)

            if len(v) >= n:
                v[n-1] = ' '.join([x.strip() for x in v[n-1:]])
                values = v[0:n]
            else:
                return None

        if is_jzdo:
            s = values[0] and values[0][0] or '.'
            values = (
                values[1],
                values[2],
                'SSH:%s' % ( \
                    s == '.' and 'CHECK' or 
                    s == '<' and 'GET' or 
                    s == '>' and 'PUT' or 
                    s or '?'),
                'INFO', 
                ' '.join([x.strip() for x in values[3:]]),
            )
            datetime_format = '%Y-%m-%d %H:%M:%S.%f'
        else:
            datetime_format = fmt[1]

        ob = {'filename': filename}

        try:
            if not m:
                for n, column in enumerate(columns):
                    ob[column] = values[n].strip()
            else:
                ob['Date'] = values[0]
                ob['Time'] = values[1] #.split('.')[0]
                ob['Module'] = 'SSH/SFTP'
                ob['Code'] = values[2]
                ob['Message'] = values[3]
        except:
            pass

        if IsDeepDebug and IsLogTrace:
            print_to(None, '..._get_log_item[%s]: %s %s %s' % (filename, columns, date_format, ob))

        try:
            x = datetime.datetime.strptime('%s %s' % (ob['Date'], ob['Time']), fmt[1])
            ob['Date'] = cdate(x, date_format)
        except:
            return None

        if 'Module' in ob:
            ob['Module'] = re.sub(r'[\[\]]', '', ob['Module'].upper())
        if 'Code' in ob:
            ob['Code'] = re.sub(r'[\[\]]', '', ob['Code'].upper())

        if IsDebug and IsLogTrace:
            print_to(None, '..._get_log_item[OK]: %s' % ob)

        return ob

    if 'lines' in kw:
        lines = kw.get('lines')

        # ------------------------------
        # Observer Log-lines constructor
        # ------------------------------
        """
        if case_insensitive:
            keys = [key.lower() for key in keys]
        """
        i = 0
        while lines and i < len(lines):
            filename, line = lines[i]
            x = checkline(line, logs, keys, getter=_get_log_item, 
                          token=None, unique='unique' in options, with_count='count' in options,
                          case_insensitive=case_insensitive,
                          no_span=no_span,
                          )
            if x != 0:
                lines.pop(i)
            else:
                i += 1
        return

    checkfile(filename, 'rb', encoding, logs, keys, getter=_get_log_item, msg='EXCHANGELOG', forced=forced, 
              unique='unique' in options, with_count='count' in options, 
              case_insensitive=case_insensitive,
              no_span=no_span,
              files=kw.get('files'),
              )

def getExchangeConfig(client):
    if not client or client not in EXCHANGE_ROOT:
        client = 'default'

    return EXCHANGE_ROOT[client]

def getExchangeLogInfo(**kw):
    global config

    logs = []

    encoding, root, filemask, options = kw.get('config') or getExchangeConfig(kw.get('client'))

    if root is None:
        return logs

    set_globals(kw.get('globals'))

    config = exchange_log_config
    root = normpath(os.path.join(root, config['root']))

    kw['filemask'] = filemask
    kw['options'] = options

    if IsTrace:
        keys = _extract_keys(kw.get('keys')) or []
        print_to(None, '\n==> CHECK_EXCHANGE_LOG: %s STARTED [%s:%s:%s:%s:%s]' % ( 
            datetime.datetime.now().strftime(UTC_FULL_TIMESTAMP),
            len(keys) > 0 and keys[0] or '',
            kw.get('client'),
            kw.get('dates'),
            kw.get('case_insensitive'),
            kw.get('no_span'),
            ))

    try:
        if IsCheckFolders:
            logger = Logger('./folders.txt', encoding=default_encoding)
            check_path(".", logger)
            logger.close()

        walk(logs, check_exchange_log, root, encoding=encoding, **kw)
    except Exception as e:
        _register_error(logs, e, **kw)

        if IsPrintExceptions:
            print_exception()

    logs = sorted(logs, key=itemgetter('Date'))

    if IsTrace:
        print_to(None, '==> CHECK_EXCHANGE_LOG: %s FINISHED' % datetime.datetime.now().strftime(UTC_FULL_TIMESTAMP))

    return logs

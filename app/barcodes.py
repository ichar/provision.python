"""
barcodes.py
===========

This module provides an easy way to create standard barcodes incude BASE64 decoded line
based on pyBarcode package. Checksum is used.

Note: PIL required(!)

Setup:

>>> pip install pyBarcode==0.8b1

Read corresponding package info please.
"""

__all__ = ['genBarcode']

import sys
import io
from base64 import b64encode

from PIL import Image

import barcode

try:
    from config import (
        IsDebug, IsDeepDebug, IsPrintExceptions, errorlog, print_to, print_exception
    )
except:
    IsDebug = 1
    IsPrintExceptions = 0
    print_exception = None

## ---------------
## Local Constants
## ---------------

_INCH = 72.0
_CM = _INCH / 2.54
_MM = _CM * 0.1
_PICA = 12.0

_barcode_types = 'code128:code39:ean:ean13:ean14:ean8:gs1:gtin:isbn:isbn10:isbn13:issn:itf:jan:pzn:upc:upca'
_default_barcode_type = _barcode_types.split(':')[0]
_barcode_formats = ('SVG', 'BMP', 'GIF', 'JPEG', 'MSP', 'PCX', 'PNG', 'TIFF', 'XBM')
_default_barcode_format = _barcode_formats[0]

_default_options = {
    'quiet_zone'    : 0,    #6.5
    'font_size'     : 7, 
    'module_width'  : 0.12, #0.1196
    'module_height' : 4.0,  #3.5
    'text_distance' : 1,    #5
    'write_text'    : True,
    'center_text'   : False, 
}

cr = '\n'

def genBarcode(value, text='', code=None, filename=None, format=None, **kw):
    """
        Barcode generator.
        
        Arguments:
            value       -- String: value for coding

            text        -- String: text to output under the barcode image, default: ''

            code        -- String: barcode type such as any possible `_barcode_types` item, default: 'code128'

            filename    -- String: output file name to save result stream, default: None (don't save a file)

            format      -- String: output file format as any possible `_barcode_formats` item (if `filename is defined`), default: 'SVG'

        Parameters (kw):
            `size`      -- Tuple of Int: (width, height) - new size of image for utils.image_base64

                           Note! For resizing use: (width, None) or (None, height).

        Parameters (kw, not implemented):
            `scale`     -- Float: scale value
            
            `width`     -- Int: width of barcode image (px)
            
            `height`    -- Int: height of barcode image (px)
            
            `font`      -- Tuple: (<family>[, <size>[, <bold>]])
            
            `readable`  -- Boolean: human legend, 1/0

        Options:
            `options`   -- Dict: pyBarcode-module writer options, default: `_default_options`.

        Returns:
            String: by default output stream as base64 decoded line.
    """
    barcode_type = code and (code+':') in _barcode_types and code or _default_barcode_type

    if IsDeepDebug:
        print('--> code: %s, text:%s' % (barcode_type, text))

    if 'readable' in kw:
        readable = kw.get('readable') and True or False
    else:
        readable = False

    options = _default_options

    if 'options' in kw:
        options = kw.get('options')
        del kw['options']

    if text and options['write_text'] and not options['center_text']:
        text = text and ('%s%s' % (' '*11, text)) or ''

    return _generate_barcode(
        barcode_type,
        value,
        text,
        readable,
        filename,
        format and format.upper() or _default_barcode_format,
        options,
        **kw
        )

def _generate(output, options, text, size=None):
    fp = io.BytesIO()
    output.write(fp, options=options, text=text)
    fp.seek(0)
    data = None
    if size and len(size) == 2:
        from .utils import image_base64
        data = image_base64(None, None, size, fp.getvalue())
    else:
        data = b64encode(fp.getvalue()).decode()
    fp.close()
    return data

def _generate_barcode(barcode_type, value, text, readable, filename, format, options, **kw):
    """ Internal generator """

    scale = kw.get('scale') or 0.05 * _INCH
    font = kw.get('font') or ('Arial', 12, False)

    # ----------------------
    # Generate barcode image
    # ----------------------

    try:
        GEN = barcode.get_barcode_class(barcode_type)
    except:
        if print_exception is not None and IsPrintExceptions:
            print_exception()
        else:
            raise
    
    # ----------------
    # Save as SVG-file
    # ----------------

    if filename and format == _default_barcode_format:
        output = GEN(value)
        return output.save(filename)
    
    # -----------------------------------
    # Save as image-file (PNG by default)
    # -----------------------------------

    try:
        from barcode.writer import ImageWriter, SVGWriter
    except:
        if print_exception is not None and IsPrintExceptions:
            print_exception()
        else:
            raise

    output = GEN(value, writer=ImageWriter())

    if filename:
        return output.save(filename, options={'type':format})

    # -------------------------
    # Make output BASE64 stream
    # -------------------------

    size = kw.get('size')

    data = {
        'output'  : _generate(output, options, text, size=size),
        'default' : _generate(output, None, text),
        'code'    : output.code,
    }

    return data

def print_html(filename, output):
    html = (
            '<html>',
            '<head>',
            '<style type="text/css">',
            'div { margin:10px auto; padding:10px; border:0px solid black; text-align:center; }',
            'img { padding:10px; }',
            'img.c0 { border: 1px solid gray; }',
            'img.c1 { width:350px; }',
            '</style>',
            '</head>',
            '<body>',
            '<div>',
                '<img src="data:image/png+xml;base64,%(default)s"><br>',
                '<img src="data:image/png;base64,%(output)s"><br>',
                '<img class="c0" src="data:image/png+xml;base64,%(output)s"><br>',
                '<img class="c1" src="data:image/png+xml;base64,%(output)s"><br>',
            '</div>',
            '</body>',
            '</html>',
    )
    with open(filename, 'w') as fo:
        fo.write((cr.join(html)) % output)


if __name__ == "__main__":
    argv = sys.argv

    if len(argv) < 2 or argv[1].lower() in ('/h', '/help', '-h', 'help', '--help'):
        pass
    else:
        value, text = argv[1].split('|')
        code = len(argv) > 2 and argv[2] or None
        filename = len(argv) > 3 and argv[3] or None
        format = len(argv) > 4 and argv[4] or None

        if IsDeepDebug:
            print('--> value: [%s]' % value)
            print('--> text:  [%s]' % text)
            print('--> filename: %s' % filename)
            print('--> format: %s' % format)

        data = genBarcode(value, text, code, filename=filename, format=format)

        if IsDeepDebug:
            if isinstance(data, dict):
                print_html('output.html', data)
                print('--> size: %s' % len(data['output']))
            else:
                print('--> size: %s' % len(data))
            print('OK')

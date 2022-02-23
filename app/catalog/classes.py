# -*- coding: utf-8 -*-

import re

from .definitions import *

rcolor = re.compile(r'(.*)\[(.*)\]', re.I+re.DOTALL)


class ControlBase:
    
    def __init__(self, id, **kw):
        self.oid = id
        self.key = kw.get('key') or ''
        self.css = kw.get('css') or ''

    def add(self, id, value, title):
        pass


class ControlCheckbox(ControlBase):
    
    def __init__(self, id, name, **kw):
        super().__init__(id, **kw)

        self.ctype = TYPE_CHECKBOX

        if not self.key:
            self.key = ITEM_CHECKBOX

        self.id = 'item_%s_%s' % (self.key, id)
        self.name = '%s:%s' % (self.key, name or id)


class ControlRadio(ControlBase):
    
    def __init__(self, id, name, **kw):
        super().__init__(id, **kw)

        self.ctype = TYPE_RADIO

        if not self.key:
            self.key = ITEM_RADIO

        if self.key in ITEM_TYPES:
            self.id = 'item_%s_%s' % (self.key, id)
        else:
            self.id = 'item_%s' % id
        #self.name = '%s:%s' % (self.key, name)
        self.name = 'item:%s' % name

        self.value = kw.get('value') or 1


class ControlNumber(ControlBase):
    
    def __init__(self, id, name, **kw):
        super().__init__(id, **kw)

        self.ctype = TYPE_NUMBER

        if not self.key:
            self.key = ITEM_NUMBER

        self.id = 'item_%s_%s' % (self.key, id)
        self.name = '%s:%s' % (self.key, name or id)

        self.min = 0
        self.max = kw.get('max') or 1


class ControlOption(ControlBase):
    
    def __init__(self, id, value, title, **kw):
        super().__init__(id, **kw)

        self.ctype = TYPE_OPTION

        if not self.key:
            self.key = ITEM_OPTION

        self.id = '%s_%s' % (self.key, id)
        self.name = id

        self.value = value
        self.title = title


class ControlSelect(ControlBase):
    
    def __init__(self, id, name, title, **kw):
        super().__init__(id, **kw)

        self.ctype = TYPE_SELECT

        if not self.key:
            self.key = ITEM_SELECT

        self.id = 'item_%s_%s' % (self.key, id)
        self.name = '%s:%s' % (self.key, name or id)

        self.title = title

        self.options = []

        if self.key == 'color' and 'values' in kw:
            self.init_colors(kw['values'])

    def add(self, id, value, title):
        option = ControlOption(id, value, title)
        self.options.append(option)
        return option

    def init_colors(self, colors):
        for i, color in enumerate(colors):
            id = '%s-%s' % (self.oid, i)
            value = i                       # +1 XXX
            title = color[1]
            option = ControlOption(id, value, title, key='color')
            self.options.append(option)


class TagBase:
    
    def __init__(self, id, title):
        self.id = id
        self.css = ''

        if ':' in title:
            self.title, self.css = title.split(':')
        else:
            self.title = title

        self._disabled = None

    @property
    def disabled(self):
        return self._disabled
    @disabled.setter
    def disabled(self, value):
        self._disabled = value and True or False


class Tab(TagBase):
    
    def __init__(self, id, stype, title):
        super().__init__(id, title)

        self.stype = stype
        self.selected = self.id == '1' and 'selected' or ''


class Group(TagBase):
    
    def __init__(self, id, name, ctype, title, options):
        super().__init__(id, title)

        self.name = name or id
        self.ctype = ctype

        self.options = options


class Item(TagBase):
    
    def __init__(self, id, name, ctype, group, title):
        super().__init__(id, title)

        self.name = name
        self.ctype = ctype
        self.group = group
        self.checked = None
        self.value = None

        self.controls = {}

        self.face = False
        self.back = False

        self.values = []
        #
        # For Catalog view
        #
        self.info = ''
        self.image = ''
        self.price = 0

        self.comments = []
        self.images = []

        self.options = []
        self.prices = []

    def _init_state(self):
        if self.ctype.startswith(TYPE_RADIOCOLOR) or self.ctype.startswith(TYPE_CHECKBOXCOLOR):
            m = rcolor.search(self.ctype)
            if m:
                self.ctype = m.group(1)
                for color in list(m.group(2)):
                    self.values.append((color, DEFAULT_COLORS[color]))
            else:
                pass

        if not self.name:
            self.name = self.ctype == TYPE_RADIO and self.group or self.id

    def add_value(self, id, value):
        self.value[id] = value

    def add_comments(self, comments):
        if not comments:
            return
        self.info = comments[0]
        if len(comments) > 1:
            self.comments = comments[1:]

    def add_images(self, images):
        if not images:
            return
        self.image = images[0]
        if len(images) > 1:
            self.images = images

    def add_prices(self, prices):
        if not prices:
            return
        self.price = prices[0]
        if len(prices) > 1:
            self.prices = prices

    def registry_option(self, ob):
        self.options.append(ob)

    def set_controls(self, gtype, options, css, items=None):
        code = True

        self._init_state()

        if self.ctype == TYPE_SELECT:
            self.name = self.id
            self.value = {}
            self.controls['item'] = ControlSelect(self.id, self.name, self.title, css=css)

        elif self.ctype == TYPE_OPTION:
            if not self.name:
                pass
            else:
                parent = items.get(self.name)
                if parent:
                    self.value = options[0]
                    option = parent.controls['item'].add(self.id, self.value, self.title)
                    parent.add_value(self.id, option)
                    code = False

        elif gtype == TYPE_GROUP_DEFAULT:
            try:
                self.value = options[0]
            except:
                pass

            if not self.ctype:
                pass
            elif self.ctype in (TYPE_RADIO, TYPE_RADIOCOLOR):
                self.checked = options[0] == '00' and 'checked' or ''
                self.controls['item'] = ControlRadio(self.id, self.name)
            elif self.ctype == TYPE_NUMBER:
                self.controls['item'] = ControlNumber(self.id, self.name, key='item')
            elif self.ctype == TYPE_CHECKBOXCOLOR:
                self.controls['item'] = ControlCheckbox(self.id, self.name)
            else:
                self.controls['item'] = ControlCheckbox(self.id, self.name)

            if self.ctype in (TYPE_CHECKBOXCOLOR, TYPE_RADIOCOLOR):
                self.controls['color'] = ControlSelect(self.id, self.id, self.title, key='color', values=self.values)

        elif gtype == TYPE_GROUP_DOUBLE:
            try:
                face, back = options
            except:
                return

            if not self.ctype:
                pass
            elif self.ctype == TYPE_CHECKBOX:
                self.controls['face'] = face == '1' and ControlCheckbox(self.id, self.name, key='face') or None
                self.controls['back'] = back == '1' and ControlCheckbox(self.id, self.name, key='back') or None
            elif self.ctype == TYPE_NUMBER:
                self.controls['face'] = face > '0' and ControlNumber(self.id, self.name, key='face', max=face) or None
                self.controls['back'] = back > '0' and ControlNumber(self.id, self.name, key='back', max=back) or None
            elif self.ctype == TYPE_RADIO:
                self.checked = options[0] == '00' and 'checked' or ''
                self.controls['face'] = face and ControlRadio(self.id, self.name, key='face', value=face) or None
                self.controls['back'] = back and ControlRadio(self.id, self.name, key='back', value=back) or None

        return code


class Option(TagBase):
    
    def __init__(self, id, name, ctype, group, title):
        super().__init__(id, title)

        self.name = name
        self.ctype = ctype

        self.choices = []

    def registry_choice(self, ob, **kw):
        self.choices.append(ob)

        ob.value = kw.get('options') or ''

        if len(self.choices) == 1 or ob.value == '00':
            ob.checked = True

class Choice(TagBase):
    
    def __init__(self, id, name, ctype, group, title):
        super().__init__(id, title)

        self.name = name
        self.ctype = ctype and ctype.isdigit() and VALID_ITEMS[int(ctype)] or ctype

        self.value = ''

        self.checked = False

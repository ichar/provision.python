

class ControlBase:
    
    def __init__(self, **kw):
        self.key = kw.get('key') or ''


class ControlCheckbox(ControlBase):
    
    def __init__(self, id, name, **kw):
        super().__init__(**kw)

        self.id = 'item_%s_%s' % (self.key, id)
        self.name = '%s:%s' % (self.key or 'item', id)


class ControlRadio(ControlBase):
    
    def __init__(self, id, name, **kw):
        super().__init__(**kw)

        self.id = 'item_%s' % id
        self.name = 'item:%s' % name

        self.value = kw.get('value') or 1


class ControlNumber(ControlBase):
    
    def __init__(self, id, name, **kw):
        super().__init__(**kw)

        self.id = 'item_%s_%s' % (self.key, id)
        self.name = '%s:%s' % (self.key, name)

        self.min = 0
        self.max = kw.get('max') or 1


class Tab:
    
    def __init__(self, id, stype, title):
        self.id = id
        self.stype = stype
        self.title = title

        self.selected = self.id == '1' and 'selected' or ''


class Group:
    
    def __init__(self, id, name, ctype, title, options):
        self.id = id
        self.name = name
        self.ctype = ctype
        self.title = title
        self.options = options


class Item:
    
    def __init__(self, id, name, ctype, group, title):
        self.id = id
        self.name = name
        self.title = title
        self.ctype = ctype
        self.group = group
        self.checked = None
        self.value = None

        self.control = {}

        self.face = False
        self.back = False

    def set_controls(self, gtype, options):
        if not gtype or gtype == '0':
            self.value = options[0]

            if self.ctype == '2':
                self.checked = options[0] == '00' and 'checked' or ''
                self.control['item'] = ControlRadio(self.id, self.name)
            elif self.ctype == '1':
                self.control['item'] = ControlNumber(self.id, self.name, key='item')
            else:
                self.control['item'] = ControlCheckbox(self.id, self.name)

        elif gtype == '1':
            face, back = options
            if self.ctype == '0':
                self.control['face'] = face == '1' and ControlCheckbox(self.id, self.name, key='face') or None
                self.control['back'] = back == '1' and ControlCheckbox(self.id, self.name, key='back') or None
            elif self.ctype == '1':
                self.control['face'] = face > '0' and ControlNumber(self.id, self.name, key='face', max=face) or None
                self.control['back'] = back > '0' and ControlNumber(self.id, self.name, key='back', max=back) or None
            elif self.ctype == '2':
                self.checked = options[0] == '00' and 'checked' or ''
                self.control['face'] = face and ControlRadio(self.id, self.name, key='face', value=face) or None
                self.control['back'] = back and ControlRadio(self.id, self.name, key='back', value=back) or None


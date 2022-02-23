# -*- coding: utf-8 -*-

KEY_TABS = 'Tabs'
KEY_ITEMS = 'Items'
KEY_PRICES = 'Prices'
KEY_COMMENTS = 'Comments'
KEY_IMAGES = 'Images'
KEY_MEASURES = 'Measures'
KEY_CONDITIONS = 'Conditions'
KEY_DEPENDENCES = 'Dependences'

TYPE_GROUP_DEFAULT = '0'
TYPE_GROUP_DOUBLE = '1'

TYPE_CHECKBOX = '0'
TYPE_NUMBER = '1'
TYPE_RADIO = '2'
TYPE_SELECT = '3'
TYPE_OPTION = '4'
TYPE_CHECKBOXCOLOR = '11'
TYPE_RADIOCOLOR = '21'

ITEM_DELIMETER = ';'
ITEM_SPLITTER = ('|', ':', '-')

ITEM_DEFAULT = 'item'
ITEM_CHECKBOX = 'checkbox'
ITEM_RADIO = 'radio'
ITEM_NUMBER = 'number'
ITEM_SELECT = 'select'
ITEM_OPTION = 'option'
ITEM_TYPES = ('face', 'back')

VALID_ITEMS = (ITEM_DEFAULT, ITEM_CHECKBOX, ITEM_RADIO, ITEM_NUMBER, ITEM_SELECT,)

ITEM_COLOR = 'color'

DEFAULT_COLORS = {
    '-' : '---',
    'F' : 'белый',
    '0' : 'черный',
    '6' : 'коричневый',
    '4' : 'красный',
    '2' : 'зеленый',
    '1' : 'синий',
    'G' : 'золотой',
    'S' : 'серебрянный',
    'T' : 'прозрачный',
}
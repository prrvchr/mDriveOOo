#!
# -*- coding: utf_8 -*-

import unohelper

from com.sun.star.container import NoSuchElementException
from com.sun.star.lang import IndexOutOfBoundsException

from com.sun.star.auth import XRestKeyMap

from collections import OrderedDict
import json



class KeyMap(unohelper.Base,
             XRestKeyMap):
    def __init__(self, **kwargs):
        self._value = OrderedDict(kwargs)

    def __len__(self):
        return len(self._value)

    def __iter__(self):
        for value in self._value.values():
            yield self._getValue(value)

    def __getitem__(self, index):
        return self.getValueByIndex(index)

    def __add__(self, other):
        if isinstance(other, type(self)):
            self._value.update(other._value)
        return self

    def __radd__(self, other):
        return self.__add__(other)

    def __iadd__(self, other):
        return self.__add__(other)

    def __repr__(self):
        return self._value.__repr__()

    def __str__(self):
        return self._value.__str__()

    def _getValue(self, value):
        if isinstance(value, dict):
            value = KeyMap(**value)
        elif isinstance(value, list):
            value = tuple(value)
        return value

    # XStringKeyMap
    @property
    def Count(self):
        return self.__len__()

    def getValue(self, key):
        if key in self._value:
            value = self._value[key]
            return self._getValue(value)
        print("KeyMap.getValue() Error: %s  **************************************" % key)
        raise NoSuchElementException()

    def hasValue(self, key):
        return key in self._value

    def insertValue(self, key, value):
        self._value[key] = value

    def setValue(self, key, value):
        self._value[key] = value

    def getKeyByIndex(self, index):
        if 0 <= index < self.Count:
            return self._value.keys()[index]
        raise IndexOutOfBoundsException()

    def getValueByIndex(self, index):
        key = self.getKeyByIndex(index)
        value = self._value[key]
        return self._getValue(value)

    # XRestKeyMap
    def getKeys(self):
        return tuple(self._value.keys())

    def getDefaultValue(self, key, default=None):
        if key in self._value:
            value = self._value[key]
            return self._getValue(value)
        else:
            return default

    def getType(self, key):
        if self.hasValue(key):
            value = self._value[key]
            if isinstance(value, dict):
                return 'KeyMap'
            if isinstance(value, (list, tuple)):
                return 'Enumerator'
        return 'Value'

    def isKeyMap(self, key):
        if self.hasValue(key):
            value = self._value[key]
            return isinstance(value, KeyMap)
        return False

    def fromJson(self, jsonstr):
        self._value = json.loads(jsonstr)
    def fromJsonKey(self, jsonstr, key):
        self._value[key] = json.loads(jsonstr)

    def toJson(self):
        return json.dumps(self._value)
    def toJsonKey(self, key):
        return json.dumps(self._value[key])

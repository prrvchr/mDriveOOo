#!
# -*- coding: utf-8 -*-

import uno
import unohelper

from com.sun.star.beans import XPropertyContainer

from .unotools import getProperty


class PropertyContainer(unohelper.Base,
                        XPropertyContainer):
    def __init__(self):
        self._propertySetInfo = {}

    # XPropertyContainer
    def addProperty(self, name, attributes, default):
        print("PropertyContainer.addProperty() *********************************************")
        property = getProperty(name, default.type, attributes)
        self._propertySetInfo.update({name: property})
        setattr(self, name, default.value)
    def removeProperty(self, name):
        print("PropertyContainer.removeProperty() ******************************************")
        self._propertySetInfo.pop(name, None)
        if hasattr(self, name):
            delattr(self, name)

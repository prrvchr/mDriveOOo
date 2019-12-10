#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.beans import XPropertySet
from com.sun.star.beans import XPropertySetInfo
from com.sun.star.beans import XPropertiesChangeNotifier
from com.sun.star.beans import XPropertySetInfoChangeNotifier
from com.sun.star.beans import UnknownPropertyException
from com.sun.star.lang import XInitialization
from com.sun.star.task import XInteractionHandler


class InteractionHandler(unohelper.Base,
                         XInteractionHandler):
    # XInteractionHandler
    def handle(self, requester):
        pass


class PropertySetInfo(unohelper.Base,
                      XPropertySetInfo):
    def __init__(self, properties={}):
        self.properties = properties

    # XPropertySetInfo
    def getProperties(self):
        return tuple(self.properties.values())
    def getPropertyByName(self, name):
        if name in self.properties:
            return self.properties[name]
        raise UnknownPropertyException("UnknownPropertyException", None)
    def hasPropertyByName(self, name):
        print("PropertySetInfo.hasPropertyByName() %s" % name)
        return name in self.properties


class PropertySet(XPropertySet):
    def _getPropertySetInfo(self):
        raise NotImplementedError

    # XPropertySet
    def getPropertySetInfo(self):
        properties = self._getPropertySetInfo()
        return PropertySetInfo(properties)
    def setPropertyValue(self, name, value):
        properties = self._getPropertySetInfo()
        if name in properties and hasattr(self, name):
            setattr(self, name, value)
        else:
            message = 'Cant setPropertyValue, UnknownProperty: %s - %s' % (name, value)
            raise UnknownPropertyException(message, self)
    def getPropertyValue(self, name):
        if name in self._getPropertySetInfo() and hasattr(self, name):
            return getattr(self, name)
        else:
            message = 'Cant getPropertyValue, UnknownProperty: %s' % name
            raise UnknownPropertyException(message, self)
    def addPropertyChangeListener(self, name, listener):
        pass
    def removePropertyChangeListener(self, name, listener):
        pass
    def addVetoableChangeListener(self, name, listener):
        pass
    def removeVetoableChangeListener(self, name, listener):
        pass

class Initialization(XInitialization,
                     PropertySet):
    # XInitialization
    def initialize(self, namedvalues=()):
        for namedvalue in namedvalues:
            if hasattr(namedvalue, 'Name') and hasattr(namedvalue, 'Value'):
                self.setPropertyValue(namedvalue.Name, namedvalue.Value)

class PropertiesChangeNotifier(XPropertiesChangeNotifier):
    def __init__(self):
        print("PyPropertiesChangeNotifier.__init__()")
        self.propertiesListener = {}
    #XPropertiesChangeNotifier
    def addPropertiesChangeListener(self, names, listener):
        print("PyPropertiesChangeNotifier.addPropertiesChangeListener() %s" % self.__class__.__name__)
        for name in names:
            if name not in self.propertiesListener:
                self.propertiesListener[name] = []
            self.propertiesListener[name].append(listener)
    def removePropertiesChangeListener(self, names, listener):
        print("PyPropertiesChangeNotifier.removePropertiesChangeListener()")
        for name in names:
            if name in self.propertiesListener:
                if listener in self.propertiesListener[name]:
                    self.propertiesListener[name].remove(listener)


class PropertySetInfoChangeNotifier(XPropertySetInfoChangeNotifier):
    def __init__(self):
        self.propertyInfoListeners = []
    # XPropertySetInfoChangeNotifier
    def addPropertySetInfoChangeListener(self, listener):
        self.propertyInfoListeners.append(listener)
    def removePropertySetInfoChangeListener(self, listener):
        if listener in self.propertyInfoListeners:
            self.propertyInfoListeners.remove(listener)

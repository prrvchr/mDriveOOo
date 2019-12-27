#!
# -*- coding: utf-8 -*-

import uno

from com.sun.star.beans import UnknownPropertyException
from com.sun.star.lang import IllegalArgumentException
from com.sun.star.lang import IllegalAccessException
from com.sun.star.ucb.ContentAction import INSERTED
from com.sun.star.ucb.ContentAction import REMOVED
from com.sun.star.ucb.ContentAction import DELETED
from com.sun.star.ucb.ContentAction import EXCHANGED
from com.sun.star.beans.PropertyAttribute import READONLY
from com.sun.star.uno import Exception as UnoException

from unolib import getNamedValue
from unolib import getPropertyValueSet

from .contenttools import getCommand
from .contenttools import getContentEvent
from .contenttools import getUcp
from .contenttools import getInteractiveAugmentedIOException
from .logger import logMessage


def getPropertiesValues(ctx, source, properties):
    namedvalues = []
    for property in properties:
        value = None
        if all((hasattr(property, 'Name'),
                property.Name in source._propertySetInfo,
                source.MetaData.hasValue(property.Name))):
            value = source.MetaData.getValue(property.Name)
            msg = "Name: %s - Value: %s" % (property.Name, value)
            level = uno.getConstantByName('com.sun.star.logging.LogLevel.INFO')
            print("contentcore.getPropertiesValues(): %s: %s" % (property.Name, value))
        else:
            msg = "ERROR: Requested property: %s is not available" % property.Name
            level = uno.getConstantByName('com.sun.star.logging.LogLevel.SEVERE')
        logMessage(ctx, level, msg, source.__class__.__name__, 'getPropertiesValues()')
        namedvalues.append(getNamedValue(property.Name, value))
    return tuple(namedvalues)

def setPropertiesValues(ctx, source, context, properties):
    results = []
    for property in properties:
        if all((hasattr(property, 'Name'),
                hasattr(property, 'Value'),
                property.Name in source._propertySetInfo)):
            result, level, msg = _setPropertyValue(source, context, property)
        else:
            msg = "ERROR: Requested property: %s is not available" % property.Name
            level = uno.getConstantByName('com.sun.star.logging.LogLevel.SEVERE')
            error = UnknownPropertyException(msg, source)
            result = uno.Any('com.sun.star.beans.UnknownPropertyException', error)
        logMessage(ctx, level, msg, source.__class__.__name__, 'setPropertiesValues()')
        results.append(result)
    return tuple(results)

def _setPropertyValue(source, context, property):
    name, value = property.Name, property.Value
    if source._propertySetInfo.get(name).Attributes & READONLY:
        msg = "ERROR: Requested property: %s is READONLY" % name
        level = uno.getConstantByName('com.sun.star.logging.LogLevel.SEVERE')
        error = IllegalAccessException(msg, source)
        result = uno.Any('com.sun.star.lang.IllegalAccessException', error)
    else:
        result, level, msg = _setProperty(source, context, name, value)
    return result, level, msg

def _setProperty(source, context, name, value):
    if name == 'Title':
        result, level, msg = _setTitle(source, context, value)
    else:
        source.MetaData.insertValue(name, value)
        msg = "Set property: %s value: %s" % (name, value)
        level = uno.getConstantByName('com.sun.star.logging.LogLevel.INFO')
        result = None
    return result, level, msg

def _setTitle(source, context, title):
    identifier = source.Identifier
    parent = identifier.getParent()
    count = parent.countChildTitle(title)
    if u'~' in title:
        msg = "Can't set property: Title value: %s contains invalid character: '~'." % title
        level = uno.getConstantByName('com.sun.star.logging.LogLevel.SEVERE')
        data = getPropertyValueSet({'Uri': identifier.getContentIdentifier(),'ResourceName': title})
        error = getInteractiveAugmentedIOException(msg, context, 'ERROR', 'INVALID_CHARACTER', data)
        result = uno.Any('com.sun.star.ucb.InteractiveAugmentedIOException', error)
    elif (identifier.IsNew and count == 1) or (not identifier.IsNew and count != 0):
        msg = "Can't set property: %s value: %s - Name Clash Error" % ('Title', title)
        level = uno.getConstantByName('com.sun.star.logging.LogLevel.SEVERE')
        data = getPropertyValueSet({'TargetFolderURL': parent.getContentIdentifier(),
                                    'ClashingName': title,
                                    'ProposedNewName': '%s(1)' % title})
        #data = getPropertyValueSet({'Uri': identifier.getContentIdentifier(),'ResourceName': title})
        error = getInteractiveAugmentedIOException(msg, context, 'ERROR', 'ALREADY_EXISTING', data)
        result = uno.Any('com.sun.star.ucb.InteractiveAugmentedIOException', error)
    else:
        if identifier.IsNew:
           source.MetaData.insertValue('Title', identifier.setTitle(title, source.IsFolder))
        else:
            default = source.MetaData.getValue('Title')
            source.MetaData.insertValue('Title', identifier.updateTitle(title, default))
        msg = "Set property: %s value: %s" % ('Title', title)
        level = uno.getConstantByName('com.sun.star.logging.LogLevel.INFO')
        result = None
    return result, level, msg

def notifyContentListener(ctx, source, action, identifier=None):
    if action == INSERTED:
        identifier = source.getIdentifier().getParent()
        parent = getUcp(ctx, identifier.getContentProviderScheme()).queryContent(identifier)
        parent.notify(getContentEvent(action, source, identifier))
    elif action == DELETED:
        identifier = source.getIdentifier()
        source.notify(getContentEvent(action, source, identifier))
    elif action == EXCHANGED:
        source.notify(getContentEvent(action, source, identifier))

def executeContentCommand(content, name, argument, environment):
    command = getCommand(name, argument)
    return content.execute(command, 0, environment)

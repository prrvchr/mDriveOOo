#!
# -*- coding: utf-8 -*-

import uno

from com.sun.star.beans import UnknownPropertyException
from com.sun.star.lang import IllegalAccessException

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb.ContentAction import INSERTED
from com.sun.star.ucb.ContentAction import REMOVED
from com.sun.star.ucb.ContentAction import DELETED
from com.sun.star.ucb.ContentAction import EXCHANGED

from com.sun.star.beans.PropertyAttribute import READONLY

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
                property.Name in source.Identifier._propertySetInfo,
                source.MetaData.hasValue(property.Name))):
            value = source.MetaData.getValue(property.Name)
            msg = "Name: %s - Value: %s" % (property.Name, value)
            level = INFO
            print("contentcore.getPropertiesValues(): %s: %s" % (property.Name, value))
        else:
            msg = "ERROR: Requested property: %s is not available" % property.Name
            level = SEVERE
        logMessage(ctx, level, msg, source.__class__.__name__, 'getPropertiesValues()')
        namedvalues.append(getNamedValue(property.Name, value))
    return tuple(namedvalues)

def setPropertiesValues(ctx, source, context, properties):
    results = []
    for property in properties:
        if all((hasattr(property, 'Name'),
                hasattr(property, 'Value'),
                property.Name in source.Identifier._propertySetInfo)):
            result, level, msg = _setPropertyValue(source, context, property)
        else:
            msg = "ERROR: Requested property: %s is not available" % property.Name
            level = SEVERE
            error = UnknownPropertyException(msg, source)
            result = uno.Any('com.sun.star.beans.UnknownPropertyException', error)
        logMessage(ctx, level, msg, source.__class__.__name__, 'setPropertiesValues()')
        results.append(result)
    return tuple(results)

def _setPropertyValue(source, context, property):
    name, value = property.Name, property.Value
    print("Content._setPropertyValue() 1 %s - %s" % (name, value))
    if source.Identifier._propertySetInfo.get(name).Attributes & READONLY:
        msg = "ERROR: Requested property: %s is READONLY" % name
        level = SEVERE
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
        level = INFO
        result = None
    return result, level, msg

def _setTitle(source, context, title):
    try:
        print("ContentCore._setTitle() 1")
        identifier = source.Identifier
        user = identifier.User
        if u'~' in title:
            msg = "Can't set property: Title value: %s contains invalid character: '~'." % title
            level = SEVERE
            data = getPropertyValueSet({'Uri': identifier.getContentIdentifier(),'ResourceName': title})
            error = getInteractiveAugmentedIOException(msg, context, 'ERROR', 'INVALID_CHARACTER', data)
            result = uno.Any('com.sun.star.ucb.InteractiveAugmentedIOException', error)
        elif user.DataBase.countChildTitle(user.Id, identifier.ParentId, title) > 0:
            msg = "Can't set property: %s value: %s - Name Clash Error" % ('Title', title)
            level = SEVERE
            data = getPropertyValueSet({'TargetFolderURL': identifier.getContentIdentifier(),
                                        'ClashingName': title,
                                        'ProposedNewName': '%s(1)' % title})
            #data = getPropertyValueSet({'Uri': identifier.getContentIdentifier(),'ResourceName': title})
            error = getInteractiveAugmentedIOException(msg, context, 'ERROR', 'ALREADY_EXISTING', data)
            result = uno.Any('com.sun.star.ucb.InteractiveAugmentedIOException', error)
        else:
            # When you change Title you must change also the Identifier.getContentIdentifier()
            # It's done by Identifier.setTitle()
            print("ContentCore._setTitle() 2")
            source.MetaData.setValue('Title', identifier.setTitle(title))
            print("ContentCore._setTitle() 3 *********************** %s" % identifier.Id)
            if not identifier.IsNew:
                user.DataBase.updateContent(user.Id, identifier.Id, 'Title', title)
                print("ContentCore._setTitle() 4")
            msg = "Set property: %s value: %s" % ('Title', title)
            level = INFO
            result = None
        print("ContentCore._setTitle() OK")
        return result, level, msg
    except Exception as e:
        msg += " ERROR: %s" % e
        print(msg)

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

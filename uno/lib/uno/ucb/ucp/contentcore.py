#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020 https://prrvchr.github.io                                     ║
║                                                                                    ║
║   Permission is hereby granted, free of charge, to any person obtaining            ║
║   a copy of this software and associated documentation files (the "Software"),     ║
║   to deal in the Software without restriction, including without limitation        ║
║   the rights to use, copy, modify, merge, publish, distribute, sublicense,         ║
║   and/or sell copies of the Software, and to permit persons to whom the Software   ║
║   is furnished to do so, subject to the following conditions:                      ║
║                                                                                    ║
║   The above copyright notice and this permission notice shall be included in       ║
║   all copies or substantial portions of the Software.                              ║
║                                                                                    ║
║   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,                  ║
║   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES                  ║
║   OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.        ║
║   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY             ║
║   CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,             ║
║   TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE       ║
║   OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                                    ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝
"""

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

from ..unotool import getNamedValue
from ..unotool import getPropertyValueSet

from .contenttools import getCommand
from .contenttools import getContentEvent
from .contenttools import getInteractiveAugmentedIOException


def getPropertiesValues(logger, content, properties):
    values = []
    for property in properties:
        value = None
        if all((hasattr(property, 'Name'),
                property.Name in content._propertySetInfo,
                content.MetaData.hasValue(property.Name))):
            value = content.MetaData.getValue(property.Name)
            msg = "Name: %s - Value: %s" % (property.Name, value)
            level = INFO
            print("contentcore.getPropertiesValues(): %s: %s" % (property.Name, value))
        else:
            msg = "ERROR: Requested property: %s is not available" % property.Name
            level = SEVERE
        logger.logp(level, 'Content', 'getPropertiesValues()', msg)
        values.append(getNamedValue(property.Name, value))
    return tuple(values)

def setPropertiesValues(logger, content, context, properties):
    results = []
    for property in properties:
        if all((hasattr(property, 'Name'),
                hasattr(property, 'Value'),
                property.Name in content._propertySetInfo)):
            result, level, msg = _setPropertyValue(content, context, property)
        else:
            msg = "ERROR: Requested property: %s is not available" % property.Name
            level = SEVERE
            error = UnknownPropertyException(msg, content)
            result = uno.Any('com.sun.star.beans.UnknownPropertyException', error)
        logger.logp(level, 'Content', 'setPropertiesValues()', msg)
        results.append(result)
    return tuple(results)

def _setPropertyValue(content, context, property):
    name, value = property.Name, property.Value
    print("Content._setPropertyValue() 1 %s - %s" % (name, value))
    if content._propertySetInfo.get(name).Attributes & READONLY:
        msg = "ERROR: Requested property: %s is READONLY" % name
        level = SEVERE
        error = IllegalAccessException(msg, content)
        result = uno.Any('com.sun.star.lang.IllegalAccessException', error)
    else:
        result, level, msg = _setProperty(content, context, name, value)
    return result, level, msg

def _setProperty(content, context, name, value):
    if name == 'Title':
        result, level, msg = _setTitle(content, context, value)
    else:
        content.MetaData.insertValue(name, value)
        msg = "Set property: %s value: %s" % (name, value)
        level = INFO
        result = None
    return result, level, msg

def _setTitle(content, context, title):
    identifier = content.getIdentifier()
    user = content._user
    if u'~' in title:
        msg = "Can't set property: Title value: %s contains invalid character: '~'." % title
        level = SEVERE
        data = getPropertyValueSet({'Uri': identifier.getContentIdentifier(),'ResourceName': title})
        error = getInteractiveAugmentedIOException(msg, context, 'QUERY', 'INVALID_CHARACTER', data)
        result = uno.Any('com.sun.star.ucb.InteractiveAugmentedIOException', error)
    elif not user.Provider.SupportDuplicate and user.DataBase.hasTitle(user.Id, content.ParentId, title):
    #elif user.DataBase.hasTitle(user.Id, identifier.ParentId, title):
            msg = "Can't set property: %s value: %s - Name Clash Error" % ('Title', title)
            level = SEVERE
            data = getPropertyValueSet({'TargetFolderURL': identifier.getContentIdentifier(),
                                        'ClashingName': title,
                                        'ProposedNewName': '%s(1)' % title})
            #data = getPropertyValueSet({'Uri': identifier.getContentIdentifier(),'ResourceName': title})
            error = getInteractiveAugmentedIOException(msg, context, 'QUERY', 'ALREADY_EXISTING', data)
            result = uno.Any('com.sun.star.ucb.InteractiveAugmentedIOException', error)
    else:
        # When you change Title you must change also the Identifier.getContentIdentifier()
        # It's done by Identifier.setTitle()
        content._setTitle(title)
        msg = "Set property: %s value: %s" % ('Title', title)
        level = INFO
        result = None
    return result, level, msg

def notifyContentListener(ctx, content, action, identifier=None):
    if action == INSERTED:
        identifier = content.getIdentifier()
        parent = identifier.getParent()
        parent.notify(getContentEvent(action, content, identifier))
    elif action == DELETED:
        identifier = content.getIdentifier()
        content.notify(getContentEvent(action, content, identifier))
    elif action == EXCHANGED:
        content.notify(getContentEvent(action, content, identifier))

def executeContentCommand(content, name, argument, environment):
    command = getCommand(name, argument)
    return content.execute(command, 0, environment)
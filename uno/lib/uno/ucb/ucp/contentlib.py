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
import unohelper

from com.sun.star.container import XIndexAccess
from com.sun.star.sdb import XInteractionSupplyParameters
from com.sun.star.sdbc import XRow
from com.sun.star.sdbc import XResultSet
from com.sun.star.sdbc import XResultSetMetaDataSupplier
from com.sun.star.task import XInteractionRequest
from com.sun.star.task import XInteractionAbort
from com.sun.star.ucb import XContentAccess
from com.sun.star.ucb import XDynamicResultSet
from com.sun.star.ucb import XCommandInfo
from com.sun.star.ucb import XCommandInfoChangeNotifier
from com.sun.star.ucb import UnsupportedCommandException

from ..oauth2 import g_oauth2

from ..unolib import PropertySet

from ..unotool import getProperty

from .contenthelper import getParametersRequest

import traceback


class NoOAuth2(object):
    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return not self == other

    def __call__(self, request):
        return request


class OAuth2OOo(NoOAuth2):
    def __init__(self, ctx, scheme, username=None):
        self.service = ctx.ServiceManager.createInstanceWithContext(g_oauth2, ctx)
        self.service.ResourceUrl = scheme
        if username is not None:
            self.service.UserName = username

    @property
    def UserName(self):
        return self.service.UserName
    @UserName.setter
    def UserName(self, username):
        self.service.UserName = username
    @property
    def Scheme(self):
        return self.service.ResourceUrl

    def __eq__(self, other):
        return all((self.UserName == getattr(other, 'UserName', None),
                    self.Scheme == getattr(other, 'Scheme', None)))

    def __call__(self, r):
        r.headers['Authorization'] = self.service.getToken('Bearer %s')
        return r


class InteractionAbort(unohelper.Base,
                       XInteractionAbort):
    # XInteractionAbort
    def select(self):
        pass


class InteractionSupplyParameters(unohelper.Base,
                                  XInteractionSupplyParameters):
    def __init__(self, result):
        self._result = result
        self._username = ''
    # XInteractionSupplyParameters
    def setParameters(self, properties):
        for property in properties:
            if property.Name == 'UserName':
                self._username = property.Value
    def select(self):
        self._result.Value = self._username
        self._result.IsPresent = True


class InteractionRequestParameters(unohelper.Base,
                                   XInteractionRequest):
    def __init__(self, source, connection, message, result):
        self.request = getParametersRequest(source, connection, message)
        self.request.Parameters = RequestParameters(message)
        self.continuations = (InteractionSupplyParameters(result), InteractionAbort())
    # XInteractionRequest
    def getRequest(self):
        return self.request
    def getContinuations(self):
        return self.continuations


class RequestParameters(unohelper.Base,
                        XIndexAccess):
    def __init__(self, description):
        self.description = description
    # XIndexAccess
    def getCount(self):
        return 1
    def getByIndex(self, index):
        return Parameters(self.description)
    def getElementType(self):
        return uno.getTypeByName('string')
    def hasElements(self):
        return True


class Parameters(unohelper.Base,
                 PropertySet):
    def __init__(self, description):
        self.Name = 'UserName'
        self.Type = uno.getConstantByName('com.sun.star.sdbc.DataType.VARCHAR')
        self.TypeName = 'VARCHAR'
        self.Precision = 0
        self.Scale = 0
        self.IsNullable = uno.getConstantByName('com.sun.star.sdbc.ColumnValue.NO_NULLS')
        self.IsAutoIncrement = False
        self.IsCurrency = False
        self.IsRowVersion = False
        self.Description = description
        self.DefaultValue = ''
    def _getPropertySetInfo(self):
        properties = {}
        bound = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.BOUND')
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        properties['Name'] = getProperty('Name', 'string', bound | readonly)
        properties['Type'] = getProperty('Type', 'long', bound | readonly)
        properties['TypeName'] = getProperty('TypeName', 'string', bound | readonly)
        properties['Precision'] = getProperty('Precision', 'long', bound | readonly)
        properties['Scale'] = getProperty('Scale', 'long', bound | readonly)
        properties['IsNullable'] = getProperty('IsNullable', 'long', bound | readonly)
        properties['IsAutoIncrement'] = getProperty('IsAutoIncrement', 'boolean', bound | readonly)
        properties['IsCurrency'] = getProperty('IsCurrency', 'boolean', bound | readonly)
        properties['IsRowVersion'] = getProperty('IsRowVersion', 'boolean', bound | readonly)
        properties['Description'] = getProperty('Description', 'string', bound | readonly)
        properties['DefaultValue'] = getProperty('DefaultValue', 'string', bound | readonly)
        return properties


class CommandInfo(unohelper.Base,
                  XCommandInfo):
    def __init__(self, commands={}):
        self.commands = commands
        print("CommandInfo.__init__()")
    # XCommandInfo
    def getCommands(self):
        print("CommandInfo.getCommands()")
        return tuple(self.commands.values())
    def getCommandInfoByName(self, name):
        print("CommandInfo.getCommandInfoByName(): %s" % name)
        if name in self.commands:
            return self.commands[name]
        print("CommandInfo.getCommandInfoByName() Error: %s" % name)
        msg = 'Cant getCommandInfoByName, UnsupportedCommandException: %s' % name
        raise UnsupportedCommandException(msg, self)
    def getCommandInfoByHandle(self, handle):
        print("CommandInfo.getCommandInfoByHandle(): %s" % handle)
        for command in self.commands.values():
            if command.Handle == handle:
                return command
        print("CommandInfo.getCommandInfoByHandle() Error: %s" % handle)
        msg = 'Cant getCommandInfoByHandle, UnsupportedCommandException: %s' % handle
        raise UnsupportedCommandException(msg, self)
    def hasCommandByName(self, name):
        print("CommandInfo.hasCommandByName(): %s" % name)
        return name in self.commands
    def hasCommandByHandle(self, handle):
        print("CommandInfo.hasCommandByHandle(): %s" % handle)
        for command in self.commands.values():
            if command.Handle == handle:
                return True
        return False


class CommandInfoChangeNotifier(XCommandInfoChangeNotifier):
    def __init__(self):
        self.commandInfoListeners = []
    # XCommandInfoChangeNotifier
    def addCommandInfoChangeListener(self, listener):
        self.commandInfoListeners.append(listener)
    def removeCommandInfoChangeListener(self, listener):
        if listener in self.commandInfoListeners:
            self.commandInfoListeners.remove(listener)


class Row(unohelper.Base,
          XRow):
    def __init__(self, values):
        self._values = values
        self._isnull = False

    # XRow
    def wasNull(self):
        return self._isnull
    def getString(self, index):
        return self._getValue(index -1)
    def getBoolean(self, index):
        return self._getValue(index -1)
    def getByte(self, index):
        return self._getValue(index -1)
    def getShort(self, index):
        return self._getValue(index -1)
    def getInt(self, index):
        return self._getValue(index -1)
    def getLong(self, index):
        return self._getValue(index -1)
    def getFloat(self, index):
        return self._getValue(index -1)
    def getDouble(self, index):
        return self._getValue(index -1)
    def getBytes(self, index):
        return self._getValue(index -1)
    def getDate(self, index):
        return self._getValue(index -1)
    def getTime(self, index):
        return self._getValue(index -1)
    def getTimestamp(self, index):
        return self._getValue(index -1)
    def getBinaryStream(self, index):
        return self._getValue(index -1)
    def getCharacterStream(self, index):
        return self._getValue(index -1)
    def getObject(self, index, map):
        return self._getValue(index -1)
    def getRef(self, index):
        return self._getValue(index -1)
    def getBlob(self, index):
        return self._getValue(index -1)
    def getClob(self, index):
        return self._getValue(index -1)
    def getArray(self, index):
        return self._getValue(index -1)

    def _getValue(self, index):
        value  = None
        self._isnull = True
        if 0 <= index < len(self._values):
            value = self._values[index].Value
            self._isnull = value is None
        return value


class DynamicResultSet(unohelper.Base,
                       XDynamicResultSet):
    def __init__(self, user, path, authority, select):
        self._user = user
        self._path = path
        self._authority = authority
        self._select = select

    # XDynamicResultSet
    def getStaticResultSet(self):
        return ContentResultSet(self._user, self._path, self._authority, self._select)
    def setListener(self, listener):
        pass
    def connectToCache(self, cache):
        pass
    def getCapabilities(self):
        return uno.getConstantByName('com.sun.star.ucb.ContentResultSetCapability.SORTED')


class ContentResultSet(unohelper.Base,
                       PropertySet,
                       XResultSet,
                       XRow,
                       XResultSetMetaDataSupplier,
                       XContentAccess):
    def __init__(self, user, path, authority, select):
        try:
            self._user = user
            self._path = path
            self._authority = authority
            result = select.executeQuery()
            result.last()
            self.RowCount = result.getRow()
            self.IsRowCountFinal = True
            result.beforeFirst()
            self._result = result
            print("ContentResultSet.__init__() %s" % self.RowCount)
        except Exception as e:
            msg = "Error: %s" % traceback.print_exc()
            print(msg)

    # XResultSet
    def next(self):
        return self._result.next()
    def isBeforeFirst(self):
        return self._result.isBeforeFirst()
    def isAfterLast(self):
        return self._result.isAfterLast()
    def isFirst(self):
        return self._result.isFirst()
    def isLast(self):
        return self._result.isLast()
    def beforeFirst(self):
        self._result.beforeFirst()
    def afterLast(self):
        self._result.afterLast()
    def first(self):
        return self._result.first()
    def last(self):
        return self._result.last()
    def getRow(self):
        return self._result.getRow()
    def absolute(self, row):
        return self._result.absolute(row)
    def relative(self, row):
        return self._result.relative(row)
    def previous(self):
        return self._result.previous()
    def refreshRow(self):
        self._result.refreshRow()
    def rowUpdated(self):
        return self._result.rowUpdated()
    def rowInserted(self):
        return self._result.rowInserted()
    def rowDeleted(self):
        return self._result.rowDeleted()
    def getStatement(self):
        return self._result.getStatement()

    # XRow
    def wasNull(self):
        return self._result.wasNull()
    def getString(self, index):
        return self._result.getString(index)
    def getBoolean(self, index):
        return self._result.getBoolean(index)
    def getByte(self, index):
        return self._result.getByte(index)
    def getShort(self, index):
        return self._result.getShort(index)
    def getInt(self, index):
        return self._result.getInt(index)
    def getLong(self, index):
        return self._result.getLong(index)
    def getFloat(self, index):
        return self._result.getFloat(index)
    def getDouble(self, index):
        return self._result.getDouble(index)
    def getBytes(self, index):
        return self._result.getBytes(index)
    def getDate(self, index):
        return self._result.getDate(index)
    def getTime(self, index):
        return self._result.getTime(index)
    def getTimestamp(self, index):
        return self._result.getTimestamp(index)
    def getBinaryStream(self, index):
        return self._result.getBinaryStream(index)
    def getCharacterStream(self, index):
        return self._result.getCharacterStream(index)
    def getObject(self, index, map):
        return self._result.getObject(index, map)
    def getRef(self, index):
        return self._result.getRef(index)
    def getBlob(self, index):
        return self._result.getBlob(index)
    def getClob(self, index):
        return self._result.getClob(index)
    def getArray(self, index):
        return self._result.getArray(index)

    # XResultSetMetaDataSupplier
    def getMetaData(self):
        return self._result.getMetaData()

    # XContentAccess
    def queryContentIdentifierString(self):
        return  self._result.getString(self._result.findColumn('TargetURL'))
    def queryContentIdentifier(self):
        return ContentIdentifier(self.queryContentIdentifierString())
    def queryContent(self):
        title = self._result.getString(self._result.findColumn('Title'))
        path = self._user.getContentPath(self._path, title)
        return self._user.getContent(path, self._authority)

    def _getPropertySetInfo(self):
        properties = {}
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        properties['RowCount'] = getProperty('RowCount', 'long', readonly)
        properties['IsRowCountFinal'] = getProperty('IsRowCountFinal', 'boolean', readonly)
        return properties


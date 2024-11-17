#!
# -*- coding: utf_8 -*-

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

from com.sun.star.beans import XFastPropertySet
from com.sun.star.beans import XMultiPropertySet
from com.sun.star.beans import XPropertySet

from com.sun.star.container import XContainerListener

from com.sun.star.lang import XComponent
from com.sun.star.lang import XInitialization
from com.sun.star.lang import XServiceInfo

from com.sun.star.sdb import XBookmarksSupplier
from com.sun.star.sdb import XCompletedConnection
from com.sun.star.sdb import XDocumentDataSource
from com.sun.star.sdb import XQueryDefinitionsSupplier

from com.sun.star.sdbc import XDataSource
from com.sun.star.sdbc import XIsolatedConnection

from com.sun.star.sdbcx import XTablesSupplier

from com.sun.star.util import XFlushable
from com.sun.star.util import XFlushListener

from .database import DataBase

from ..unotool import createService

import traceback


class DataSource(unohelper.Base,
                 XBookmarksSupplier,
                 XCompletedConnection,
                 XComponent,
                 XContainerListener,
                 XDataSource,
                 XDocumentDataSource,
                 XFastPropertySet,
                 XFlushable,
                 XFlushListener,
                 XInitialization,
                 XIsolatedConnection,
                 XMultiPropertySet,
                 XPropertySet,
                 XQueryDefinitionsSupplier,
                 XServiceInfo,
                 XTablesSupplier):

    def __init__(self, ctx, datasource):
        self._ctx = ctx
        self._datasource = datasource

    @property
    def Info(self):
        return self._datasource.Info
    @Info.setter
    def Info(self, info):
        self._datasource.Info = info
    @property
    def IsPasswordRequired(self):
        return self._datasource.IsPasswordRequired
    @IsPasswordRequired.setter
    def IsPasswordRequired(self, state):
        self._datasource.IsPasswordRequired = state
    @property
    def IsReadOnly(self):
        return self._datasource.IsReadOnly
    @property
    def LayoutInformation(self):
        return self._datasource.LayoutInformation
    @LayoutInformation.setter
    def LayoutInformation(self, layout):
        self._datasource.LayoutInformation = layout
    @property
    def Name(self):
        return self._datasource.Name
    @property
    def NumberFormatsSupplier(self):
        return self._datasource.NumberFormatsSupplier
    @property
    def Password(self):
        return self._datasource.Password
    @Password.setter
    def Password(self, password):
        self._datasource.Password = password
    @property
    def Settings(self):
        return self._datasource.Settings
    @property
    def SuppressVersionColumns(self):
        return self._datasource.SuppressVersionColumns
    @SuppressVersionColumns.setter
    def SuppressVersionColumns(self, state):
        self._datasource.SuppressVersionColumns = state
    @property
    def TableFilter(self):
        return self._datasource.TableFilter
    @TableFilter.setter
    def TableFilter(self, filter):
        self._datasource.TableFilter = filter
    @property
    def TableTypeFilter(self):
        return self._datasource.TableTypeFilter
    @TableTypeFilter.setter
    def TableTypeFilter(self, filter):
        self._datasource.TableTypeFilter = filter
    @property
    def URL(self):
        return self._datasource.URL
    @URL.setter
    def URL(self, url):
        self._datasource.URL = url
    @property
    def User(self):
        return self._datasource.User
    @User.setter
    def User(self, user):
        self._datasource.User = user

# XBookmarksSupplier
    def getBookmarks(self):
        return self._datasource.getBookmarks()

# XCompletedConnection
    def connectWithCompletion(self, handler):
        # TODO: This wrapping is only there for the following lines:
        connection = self._datasource.connectWithCompletion(handler)
        return connection

# XComponent
    def dispose(self):
        self._datasource.dispose()
    def addEventListener(self, listener):
        self._datasource.addEventListener(listener)
    def removeEventListener(self, listener):
        self._datasource.removeEventListener(listener)

# XContainerListener
    def elementInserted(self, event):
       self._datasource.elementInserted(event)
    def elementRemoved(self, event):
       self._datasource.elementRemoved(event)
    def elementReplaced(self, event):
       self._datasource.elementReplaced(event)

# XDataSource
    def getConnection(self, user, password):
        # TODO: This wrapping is only there for the following lines:
        connection = self._datasource.getConnection(user, password)
        #mri = createService(self._ctx, 'mytools.Mri')
        #mri.inspect(connection)
        return connection
    def setLoginTimeout(self, seconds):
        self._datasource.setLoginTimeout(seconds)
    def getLoginTimeout(self):
        return self._datasource.getLoginTimeout()

# XDocumentDataSource
    @property
    def DatabaseDocument(self):
        # TODO: This wrapping is only there for the following lines:
        database = self._datasource.DatabaseDocument
        return DataBase(database, self)

# XEventListener <- XContainerListener
    def disposing(self, source):
        self._datasource.disposing(source)

# XFastPropertySet
    def setFastPropertyValue(self, handle, value):
        self._datasource.setFastPropertyValue(handle, value)
    def getFastPropertyValue(self, handle):
        return self._datasource.getFastPropertyValue(handle)

# XFlushable
    def flush(self):
        self._datasource.flush()
    def addFlushListener(self, listener):
        self._datasource.addFlushListener(listener)
    def removeFlushListener(self, listener):
        self._datasource.removeFlushListener(listener)

# XFlushListener
    def flushed(self, event):
        self._datasource.flushed(event)

# XInitialization
    def initialize(self, arguments):
        self._datasource.initialize(arguments)

# XIsolatedConnection
    def getIsolatedConnectionWithCompletion(self, handler):
        # TODO: This wrapping is only there for the following lines:
        connection = self._datasource.getIsolatedConnectionWithCompletion(handler)
        return connection
    def getIsolatedConnection(self, user, password):
        # TODO: This wrapping is only there for the following lines:
        connection = self._datasource.getIsolatedConnection(user, password)
        return connection

# XMultiPropertySet
    def setPropertyValues(self, names, values):
        self._datasource.setPropertyValues(names, values)
    def getPropertyValues(self, names):
        return self._datasource.getPropertyValues(names)
    def addPropertiesChangeListener(self, names, listener):
        self._datasource.addPropertiesChangeListener(names, listener)
    def removePropertiesChangeListener(self, listener):
        self._datasource.removePropertiesChangeListener(listener)
    def firePropertiesChangeEvent(self, names, listener):
        self._datasource.firePropertiesChangeEvent(names, listener)

# XPropertySet
    def getPropertySetInfo(self):
        return self._datasource.getPropertySetInfo()
    def setPropertyValue(self, name, value):
        self._datasource.setPropertyValue(name, value)
    def getPropertyValue(self, name):
        return self._datasource.getPropertyValue(name)
    def addPropertyChangeListener(self, name, listener):
        self._datasource.addPropertyChangeListener(name, value)
    def removePropertyChangeListener(self, name, listener):
        self._datasource.removePropertyChangeListener(name, listener)
    def addVetoableChangeListener(self, name, listener):
        self._datasource.addVetoableChangeListener(name, value)
    def removeVetoableChangeListener(self, name, listener):
        self._datasource.removeVetoableChangeListener(name, listener)

# XQueryDefinitionsSupplier
    def getQueryDefinitions(self):
        return self._datasource.getQueryDefinitions()

# XServiceInfo
    def supportsService(self, service):
        return self._datasource.supportsService(service)
    def getImplementationName(self):
        return self._datasource.getImplementationName()
    def getSupportedServiceNames(self):
        return self._datasource.getSupportedServiceNames()

# XTablesSupplier
    def getTables(self):
        return self._datasource.getTables()

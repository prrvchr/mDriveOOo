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

from com.sun.star.beans.PropertyAttribute import READONLY

from com.sun.star.container import XChild
from com.sun.star.container import XElementAccess
from com.sun.star.container import XEnumerationAccess
from com.sun.star.container import XNameAccess
from com.sun.star.container import XIndexAccess

from com.sun.star.lang import XComponent
from com.sun.star.lang import XMultiServiceFactory
from com.sun.star.lang import XServiceInfo

from com.sun.star.sdb.CommandType import TABLE
from com.sun.star.sdb.CommandType import QUERY
from com.sun.star.sdb.CommandType import COMMAND

from com.sun.star.sdb import XCommandPreparation
from com.sun.star.sdb import XQueriesSupplier
from com.sun.star.sdb import XSQLQueryComposerFactory

from com.sun.star.sdb.application import XTableUIProvider
from com.sun.star.sdb.tools import XConnectionTools

from com.sun.star.sdbc import XConnection
from com.sun.star.sdbc import XCloseable
from com.sun.star.sdbc import XWarningsSupplier

from com.sun.star.sdbc import SQLException

from com.sun.star.sdbcx import XTablesSupplier
from com.sun.star.sdbcx import XViewsSupplier
from com.sun.star.sdbcx import XUsersSupplier
from com.sun.star.sdbcx import XGroupsSupplier
from com.sun.star.sdbcx import XUser

from com.sun.star.uno import XWeak

from .databasemetadata import DatabaseMetaData

from .datasource import DataSource

from .statement import Statement
from .statement import PreparedStatement
from .statement import CallableStatement

from .unotool import createService

import traceback


class Connection(unohelper.Base,
                 XServiceInfo,
                 XComponent,
                 XWarningsSupplier,
                 XConnection,
                 XCloseable,
                 XCommandPreparation,
                 XQueriesSupplier,
                 XSQLQueryComposerFactory,
                 XMultiServiceFactory,
                 XChild,
                 XTablesSupplier,
                 XViewsSupplier,
                 XUsersSupplier,
                 XGroupsSupplier,
                 XTableUIProvider,
                 XConnectionTools,
                 XWeak):
    def __init__(self, driver, datasource, location, url, infos, user, password):
        self._connection = driver.connect(location, infos)
        self._datasource = datasource
        self._url = url
        self._infos = infos
        self._username = user

    # XComponent
    def dispose(self):
        self._connection.dispose()

    def addEventListener(self, listener):
        self._connection.addEventListener(listener)

    def removeEventListener(self, listener):
        self._connection.removeEventListener(listener)

    # XWeak
    def queryAdapter(self):
        #return self._connection.queryAdapter()
        return self

    # XTableUIProvider
    def getTableIcon(self, tablename, colormode):
        return self._connection.getTableIcon(tablename, colormode)
    def getTableEditor(self, document, tablename):
        return self._connection.getTableEditor(document, tablename)

    # XConnectionTools
    def createTableName(self):
        return self._connection.createTableName()
    def getObjectNames(self):
        return self._connection.getObjectNames()
    def getDataSourceMetaData(self):
        print("Connection.getDataSourceMetaData()")
        return self._connection.getDataSourceMetaData()
    def getFieldsByCommandDescriptor(self, commandtype, command, keep):
        fields, keep = self._connection.getFieldsByCommandDescriptor(commandtype, command, keep)
        return fields, keep
    def getComposer(self, commandtype, command):
        return self._connection.getComposer(commandtype, command)

    # XCloseable
    def close(self):
        self._connection.close()

    # XCommandPreparation
    def prepareCommand(self, command, commandtype):
        composer = self._connection.getComposer(commandtype, command)
        query = composer.getQuery()
        composer.dipose()
        # TODO: sometime we cannot use: connection.prepareStatement(sql)
        # TODO: it trow a: java.lang.IncompatibleClassChangeError
        # TODO: if self._patched: fallback to connection.prepareCall(sql)
        if query is not None:
            return CallableStatement(self, query)
        raise SQLException()

    # XQueriesSupplier
    def getQueries(self):
        return self._connection.getQueries()

    # XSQLQueryComposerFactory
    def createQueryComposer(self):
        return self._connection.createQueryComposer()

    # XMultiServiceFactory
    def createInstance(self, service):
        return self._connection.createInstance(service)
    def createInstanceWithArguments(self, service, arguments):
        return self._connection.createInstanceWithArguments(service, arguments)
    def getAvailableServiceNames(self):
        return self._connection.getAvailableServiceNames()

    # XChild
    def getParent(self):
        return DataSource(self._datasource, self._username, self._url)
    def setParent(self):
        pass

    # XTablesSupplier
    def getTables(self):
        return self._connection.getTables()

    # XViewsSupplier
    def getViews(self):
        return self._connection.getViews()

    # XUsersSupplier
    def getUsers(self):
        return self._connection.getUsers()

    # XGroupsSupplier
    def getGroups(self):
        return self._connection.getGroups()

    # XWarningsSupplier
    def getWarnings(self):
        return self._connection.getWarnings()

    def clearWarnings(self):
        self._connection.clearWarnings()

    # XConnection
    def createStatement(self):
        return Statement(self)
    def prepareStatement(self, sql):
        # TODO: sometime we cannot use: connection.prepareStatement(sql)
        # TODO: it trow a: java.lang.IncompatibleClassChangeError
        # TODO: if self._patched: fallback to connection.prepareCall(sql)
        return PreparedStatement(self, sql)
    def prepareCall(self, sql):
        return CallableStatement(self, sql)
    def nativeSQL(self, sql):
        return self._connection.nativeSQL(sql)
    def setAutoCommit(self, auto):
        self._connection.setAutoCommit(auto)
    def getAutoCommit(self):
        return self._connection.getAutoCommit()
    def commit(self):
        self._connection.commit()
    def rollback(self):
        self._connection.rollback()
    def isClosed(self):
        return self._connection.isClosed()
    def getMetaData(self):
        metadata = self._connection.getMetaData()
        return DatabaseMetaData(self, metadata, self._url, self._infos, self._username)
    def setReadOnly(self, readonly):
        self._connection.setReadOnly(readonly)
    def isReadOnly(self):
        return self._connection.isReadOnly()
    def setCatalog(self, catalog):
        self._connection.setCatalog(catalog)
    def getCatalog(self):
        return self._connection.getCatalog()
    def setTransactionIsolation(self, level):
        self._connection.setTransactionIsolation(level)
    def getTransactionIsolation(self):
        return self._connection.getTransactionIsolation()
    def getTypeMap(self):
        return self._connection.getTypeMap()
    def setTypeMap(self, typemap):
        self._connection.setTypeMap(typemap)

    # XServiceInfo
    def supportsService(self, service):
        return self._connection.supportsService(service)
    def getImplementationName(self):
        return self._connection.getImplementationName()
    def getSupportedServiceNames(self):
        return self._connection.getSupportedServiceNames()


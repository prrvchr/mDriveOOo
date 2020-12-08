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

from com.sun.star.lang import XServiceInfo
from com.sun.star.lang import XComponent
from com.sun.star.sdbc import XConnection
from com.sun.star.sdbc import XCloseable
from com.sun.star.sdbc import XWarningsSupplier
from com.sun.star.sdb import XCommandPreparation
from com.sun.star.sdb import XQueriesSupplier
from com.sun.star.sdb import XSQLQueryComposerFactory
from com.sun.star.lang import XMultiServiceFactory
from com.sun.star.container import XChild
from com.sun.star.sdb.application import XTableUIProvider
from com.sun.star.sdb.tools import XConnectionTools
from com.sun.star.sdb.CommandType import TABLE
from com.sun.star.sdb.CommandType import QUERY
from com.sun.star.sdb.CommandType import COMMAND
from com.sun.star.beans.PropertyAttribute import READONLY

from com.sun.star.sdbc import SQLException

from com.sun.star.uno import XWeak
from com.sun.star.uno import XAdapter

from com.sun.star.sdbcx import XTablesSupplier
from com.sun.star.sdbcx import XViewsSupplier
from com.sun.star.sdbcx import XUsersSupplier
from com.sun.star.sdbcx import XGroupsSupplier

from com.sun.star.sdbcx import XUser
from com.sun.star.container import XNameAccess
from com.sun.star.container import XIndexAccess
from com.sun.star.container import XEnumerationAccess
from com.sun.star.container import XElementAccess

from unolib import PropertySet
from unolib import getProperty
from unolib import createService

from .dbtools import getSequenceFromResult
from .dbtools import getKeyMapSequenceFromResult
from .dbqueries import getSqlQuery

from .documentdatasource import DocumentDataSource
from .databasemetadata import DatabaseMetaData
from .statement import Statement
from .statement import PreparedStatement
from .statement import CallableStatement

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
    def __init__(self, ctx, connection, protocols, username, event=None):
        self.ctx = ctx
        self._connection = connection
        self._protocols = protocols
        self._username = username
        self._event = event

    # XComponent
    def dispose(self):
        print("Connection.dispose()")
        self.close()
        self._connection.dispose()
    def addEventListener(self, listener):
        print("Connection.addEventListener()")
        self._connection.addEventListener(listener)
    def removeEventListener(self, listener):
        print("Connection.removeEventListener()")
        self._connection.removeEventListener(listener)

    # XWeak
    def queryAdapter(self):
        print("Connection.queryAdapter()")
        return self._connection.queryAdapter()

    # XTableUIProvider
    def getTableIcon(self, tablename, colormode):
        print("Connection.getTableIcon()")
        return self._connection.getTableIcon(tablename, colormode)
    def getTableEditor(self, documentui, tablename):
        print("Connection.getTableEditor()")
        return self._connection.getTableEditor(documentui, tablename)

    # XConnectionTools
    def createTableName(self):
        print("Connection.createTableName()")
        return self._connection.createTableName()
    def getObjectNames(self):
        print("Connection.getObjectNames()")
        return self._connection.getObjectNames()
    def getDataSourceMetaData(self):
        print("Connection.getDataSourceMetaData()")
        return self._connection.getDataSourceMetaData()
    def getFieldsByCommandDescriptor(self, commandtype, command, keep):
        print("Connection.getFieldsByCommandDescriptor() 1")
        fields, keep = self._connection.getFieldsByCommandDescriptor(commandtype, command, keep)
        print("Connection.getFieldsByCommandDescriptor() 2")
        return fields, keep
    def getComposer(self, commandtype, command):
        print("Connection.getComposer()")
        return self._connection.getComposer(commandtype, command)

    # XCloseable
    def close(self):
        print("Connection.close()********* 1")
        if not self._connection.isClosed():
            self._connection.close()
        if self._event is not None:
            self._event.set()
        print("Connection.close()********* 2")

    # XCommandPreparation
    def prepareCommand(self, command, commandtype):
        # TODO: cannot use: self._connection.prepareCommand()
        # TODO: it trow a: java.lang.IncompatibleClassChangeError
        # TODO: in the same way when using self._connection.prepareStatement(sql)
        # TODO: fallback to: self._connection.prepareCall(sql)
        print("Connection.prepareCommand()")
        query = None
        if commandtype == TABLE:
            query = 'SELECT * FROM "%s"' % command
        elif commandtype == QUERY:
            queries = self.getQueries()
            if queries.hasByName(command):
                query = queries.getByName(command).Command
        elif commandtype == COMMAND:
            query = command
        if query is not None:
            statement = CallableStatement(self, query)
            return statement
        raise SQLException()

    # XQueriesSupplier
    def getQueries(self):
        print("Connection.getQueries()")
        return self._connection.getQueries()

    # XSQLQueryComposerFactory
    def createQueryComposer(self):
        print("Connection.getQueries()")
        return self._connection.createQueryComposer()

    # XMultiServiceFactory
    def createInstance(self, service):
        print("Connection.createInstance() %s" % service)
        return self._connection.createInstance(service)
    def createInstanceWithArguments(self, service, arguments):
        print("Connection.createInstanceWithArguments()")
        return self._connection.createInstanceWithArguments(service, arguments)
    def getAvailableServiceNames(self):
        print("Connection.getAvailableServiceNames()")
        return self._connection.getAvailableServiceNames()

    # XChild
    def getParent(self):
        parent = self._connection.getParent()
        return DocumentDataSource(parent, self._protocols, self._username)
    def setParent(self):
        pass

    # XTablesSupplier
    def getTables(self):
        print("Connection.getTables()")
        return self._connection.getTables()

    # XViewsSupplier
    def getViews(self):
        print("Connection.getViews()")
        return self._connection.getViews()

    # XUsersSupplier
    def getUsers(self):
        try:
            print("Connection.getUsers()1")
            query = getSqlQuery(self.ctx, 'getUsers')
            result = self._connection.createStatement().executeQuery(query)
            users = getSequenceFromResult(result)
            #query = getSqlQuery(self.ctx, 'getPrivileges')
            #result = self._connection.createStatement().executeQuery(query)
            #privileges = getKeyMapSequenceFromResult(result)
            #mri = createService(self.ctx, 'mytools.Mri')
            #mri.inspect(tuple(privileges))
            print("Connection.getUsers()2 %s" % (users, ))
            return DataContainer(self.ctx, self._connection, users, 'string')
        except Exception as e:
            print("Connection.getUsers(): %s - %s" % (e, traceback.print_exc()))

    # XGroupsSupplier
    def getGroups(self):
        print("Connection.getGroups()")
        return self._connection.getGroups()

    # XWarningsSupplier
    def getWarnings(self):
        print("Connection.getWarnings() 1")
        warning = self._connection.getWarnings()
        print("Connection.getWarnings() 2 %s" % warning)
        return warning
    def clearWarnings(self):
        print("Connection.clearWarnings()")
        self._connection.clearWarnings()

    # XConnection
    def createStatement(self):
        print("Connection.createStatement()")
        return Statement(self)
    def prepareStatement(self, sql):
        print("Connection.prepareStatement(): %s" % sql)
        statement = PreparedStatement(self, sql)
        #mri = self.ctx.ServiceManager.createInstance('mytools.Mri')
        #mri.inspect(statement)
        return statement
    def prepareCall(self, sql):
        print("Connection.prepareCall(): %s" % sql)
        return CallableStatement(self, sql)
    def nativeSQL(self, sql):
        print("Connection.nativeSQL()")
        return self._connection.nativeSQL(sql)
    def setAutoCommit(self, auto):
        print("Connection.setAutoCommit()")
        self._connection.setAutoCommit(auto)
    def getAutoCommit(self):
        print("Connection.getAutoCommit()")
        return self._connection.getAutoCommit()
    def commit(self):
        print("Connection.commit()")
        self._connection.commit()
    def rollback(self):
        print("Connection.rollback()")
        self._connection.rollback()
    def isClosed(self):
        print("Connection.isClosed()")
        return self._connection.isClosed()
    def getMetaData(self):
        #print("Connection.getMetaData()")
        metadata = self._connection.getMetaData()
        return DatabaseMetaData(self, metadata, self._protocols, self._username)
    def setReadOnly(self, readonly):
        print("Connection.setReadOnly()")
        self._connection.setReadOnly(readonly)
    def isReadOnly(self):
        print("Connection.isReadOnly()")
        return self._connection.isReadOnly()
    def setCatalog(self, catalog):
        print("Connection.setCatalog()")
        self._connection.setCatalog(catalog)
    def getCatalog(self):
        print("Connection.getCatalog()")
        return self._connection.getCatalog()
    def setTransactionIsolation(self, level):
        print("Connection.setTransactionIsolation()")
        self._connection.setTransactionIsolation(level)
    def getTransactionIsolation(self):
        print("Connection.getTransactionIsolation()")
        return self._connection.getTransactionIsolation()
    def getTypeMap(self):
        print("Connection.getTypeMap()")
        return self._connection.getTypeMap()
    def setTypeMap(self, typemap):
        print("Connection.setTypeMap()")
        self._connection.setTypeMap(typemap)

    # XServiceInfo
    def supportsService(self, service):
        return self._connection.supportsService(service)
    def getImplementationName(self):
        return self._connection.getImplementationName()
    def getSupportedServiceNames(self):
        return self._connection.getSupportedServiceNames()


class DataContainer(unohelper.Base,
                    XWeak,
                    XAdapter,
                    XNameAccess,
                    XIndexAccess,
                    XEnumerationAccess):
    def __init__(self, ctx, connection, names, typename):
        self._elements = {name: DataBaseUser(ctx, connection, name) for name in names}
        self._typename = typename
        print("DataContainer.__init__()")

    # XWeak
    def queryAdapter(self):
        print("DataContainer.queryAdapter()")
        return self
    # XAdapter
    def queryAdapted(self):
        print("DataContainer.queryAdapter()")
        return self
    def addReference(self, reference):
        pass
    def removeReference(self, reference):
        pass

    # XNameAccess
    def getByName(self, name):
        print("DataContainer.getByName() %s" % name)
        return self._elements[name]
    def getElementNames(self):
        elements = tuple(self._elements.keys())
        print("DataContainer.getElementNames() %s" % (elements, ))
        return elements
    def hasByName(self, name):
        print("DataContainer.hasByName() %s" % name)
        return name in self._elements

    # XIndexAccess
    def getCount(self):
        print("DataContainer.getCount()")
        return len(self._elements)
    def getByIndex(self, index):
        print("DataContainer.getByIndex() %s" % index)
        return None

    # XEnumerationAccess
    def createEnumeration(self):
        print("DataContainer.createEnumeration()")

    # XElementAccess
    def getElementType(self):
        print("DataContainer.getElementType()")
        return uno.getTypeByName(self._typename)
    def hasElements(self):
        print("DataContainer.hasElements()")
        return len(self._elements) != 0


class DataBaseUser(unohelper.Base,
                   XUser,
                   XWeak,
                   XAdapter,
                   XGroupsSupplier,
                   PropertySet):
    def __init__(self, ctx, connection, username):
        self.ctx = ctx
        self._connection = connection
        self.Name = username
        print("DataBaseUser.__init__() %s" % username)

    # XWeak
    def queryAdapter(self):
        print("DataBaseUser.queryAdapter()")
        return self
    # XAdapter
    def queryAdapted(self):
        print("DataBaseUser.queryAdapted()")
        return self
    def addReference(self, reference):
        pass
    def removeReference(self, reference):
        pass

    # XUser
    def changePassword(self, oldpwd, newpwd):
        print("DataBaseUser.changePassword()")
        query = getSqlQuery(self.ctx, 'changePassword', newpwd)
        print("DataBaseUser.changePassword() %s" % query)
        result = self._connection.createStatement().executeUpdate(query)
        print("DataBaseUser.changePassword() %s" % result)
    # XAuthorizable
    def getPrivileges(self, objname, objtype):
        print("DataBaseUser.getPrivileges() %s - %s" % (objname, objtype))
        pass
    def getGrantablePrivileges(self, objname, objtype):
        print("DataBaseUser.getGrantablePrivileges() %s - %s" % (objname, objtype))
        pass
    def grantPrivileges(self, objname, objtype, objprivilege):
        print("DataBaseUser.grantPrivileges() %s - %s - %s" % (objname, objtype, objprivilege))
        pass
    def revokePrivileges(self, objname, objtype, objprivilege):
        print("DataBaseUser.revokePrivileges() %s - %s - %s" % (objname, objtype, objprivilege))
        pass

    # XGroupsSupplier
    def getGroups(self):
        print("DataBaseUser.getGroups()")
        return None

    # XPropertySet
    def _getPropertySetInfo(self):
        properties = {}
        properties['Name'] = getProperty('Name', 'string', READONLY)
        return properties

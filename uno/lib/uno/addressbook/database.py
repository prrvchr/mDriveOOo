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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.sdb.CommandType import QUERY

from com.sun.star.sdbc import XRestDataBase

from .unolib import KeyMap

from .unotool import parseDateTime
from .unotool import createService
from .unotool import getConfiguration
from .unotool import getResourceLocation
from .unotool import getSimpleFile
from .unotool import getUrlPresentation

from .configuration import g_identifier
from .configuration import g_admin
from .configuration import g_group
from .configuration import g_host

from .dbqueries import getSqlQuery

from .dbconfig import g_dba
from .dbconfig import g_folder
from .dbconfig import g_jar
from .dbconfig import g_role

from .dbtool import checkDataBase
from .dbtool import createDataSource
from .dbtool import createStaticTable
from .dbtool import getConnectionInfo
from .dbtool import getDataBaseConnection
from .dbtool import getDataBaseUrl
from .dbtool import executeSqlQueries
from .dbtool import getDataSourceCall
from .dbtool import getDataSourceConnection
from .dbtool import executeQueries
from .dbtool import getDictFromResult
from .dbtool import getKeyMapFromResult
from .dbtool import getSequenceFromResult
from .dbtool import getKeyMapKeyMapFromResult

from .dbinit import getStaticTables
from .dbinit import getQueries
from .dbinit import getTablesAndStatements
from .dbinit import getViewsAndTriggers

from .logger import logMessage
from .logger import getMessage

from collections import OrderedDict
import traceback
from time import sleep


class DataBase(unohelper.Base,
               XRestDataBase):
    def __init__(self, ctx):
        print("gContact.DataBase.init() start")
        self._ctx = ctx
        self._statement = None
        self._embedded = False
        self._fieldsMap = {}
        self._batchedCalls = OrderedDict()
        self._addressbook = None
        location = getResourceLocation(ctx, g_identifier, g_folder)
        url = getUrlPresentation(ctx, location)
        self._url = url + '/' + g_host
        if self._embedded:
            self._path = url + '/' + g_jar
        else:
            self._path = None
        odb = self._url + '.odb'
        exist = getSimpleFile(ctx).exists(odb)
        if not exist:
            connection = getDataSourceConnection(ctx, self._url)
            error = self._createDataBase(connection)
            if error is None:
                datasource = connection.getParent()
                #datasource.SuppressVersionColumns = True
                datasource.DatabaseDocument.storeAsURL(odb, ())
                datasource.dispose()
            connection.close()
        print("gContact.DataBase.init() end")

    @property
    def Connection(self):
        if self._statement is None:
            connection = self.getConnection()
            self._statement = connection.createStatement()
        return self._statement.getConnection()

    def getConnection(self, user='', password=''):
        #info = getConnectionInfo(user, password, self._path)
        return getDataSourceConnection(self._ctx, self._url, user, password, False)

    def dispose(self):
        if self._statement is not None:
            connection = self._statement.getConnection()
            self._statement.dispose()
            self._statement = None
            #connection.getParent().dispose()
            connection.close()
            print("gContact.DataBase.dispose() ***************** database: %s closed!!!" % g_host)

# Procedures called by Initialization
    def _createDataBase(self, connection):
        version, error = checkDataBase(self._ctx, connection)
        if error is None:
            statement = connection.createStatement()
            createStaticTable(self._ctx, statement, getStaticTables())
            tables, queries = getTablesAndStatements(self._ctx, statement, version)
            executeSqlQueries(statement, tables)
            executeQueries(self._ctx, statement, getQueries())
            executeSqlQueries(statement, queries)
            views, triggers = getViewsAndTriggers(self._ctx, statement, self._getViewName())
            executeSqlQueries(statement, views)
            statement.close()
        return error

    def getDataSource(self):
        return self.Connection.getParent()

    def getDatabaseDocument(self):
        return self.getDataSource().DatabaseDocument

    def addCloseListener(self, listener):
        datasource = self.Connection.getParent()
        document = datasource.DatabaseDocument
        document.addCloseListener(listener)

    def shutdownDataBase(self, compact=False):
        statement = self.Connection.createStatement()
        query = getSqlQuery(self._ctx, 'shutdown', compact)
        statement.execute(query)
        statement.close()

    def createUser(self, name, password):
        statement = self.Connection.createStatement()
        format = {'User': name, 'Password': password, 'Admin': g_admin}
        query = getSqlQuery(self._ctx, 'createUser', format)
        status = statement.executeUpdate(query)
        statement.close()
        return status == 0

    def insertUser(self, userid, account):
        user = KeyMap()
        call = self._getCall('insertUser')
        call.setString(1, userid)
        call.setString(2, account)
        call.setString(3, g_group)
        result = call.executeQuery()
        if result.next():
            user = getKeyMapFromResult(result)
        call.close()
        return user

    def selectUser(self, account):
        user = None
        call = self._getCall('getPerson')
        call.setString(1, account)
        result = call.executeQuery()
        if result.next():
            user = getKeyMapFromResult(result)
        call.close()
        return user

    def truncatGroup(self, start):
        statement = self.Connection.createStatement()
        format = {'TimeStamp': unparseTimeStamp(start)}
        query = getSqlQuery(self._ctx, 'truncatGroup', format)
        statement.execute(query)
        statement.close()

    def initUser(self, format):
        statement = self.Connection.createStatement()
        format['View'] = self._getViewName()
        query = getSqlQuery(self._ctx, 'createUserSchema', format)
        statement.execute(query)
        query = getSqlQuery(self._ctx, 'setUserAuthorization', format)
        statement.execute(query)
        query = getSqlQuery(self._ctx, 'createUserSynonym', format)
        statement.execute(query)
        query = getSqlQuery(self._ctx, 'setUserSchema', format)
        statement.execute(query)
        statement.close()

    def createGroupView(self, user, group, groupid):
        statement = self.Connection.createStatement()
        format = {'Schema': user.Resource,
                  'User': user.Account,
                  'Name': group,
                  'View': self._getViewName(),
                  'GroupId': groupid}
        query = getSqlQuery(self._ctx, 'dropGroupView', format)
        statement.execute(query)
        query = getSqlQuery(self._ctx, 'createGroupView', format)
        statement.execute(query)
        statement.close()

# Procedures called by the User
    def getUserFields(self):
        fields = []
        call = self._getCall('getFieldNames')
        result = call.executeQuery()
        fields = getSequenceFromResult(result)
        call.close()
        return tuple(fields)

# Procedures called by the Replicator
    def getDefaultType(self):
        default = {}
        call = self._getCall('getDefaultType')
        result = call.executeQuery()
        default = getDictFromResult(result)
        call.close()
        return default

    def setLoggingChanges(self, state):
        statement = self.Connection.createStatement()
        query = getSqlQuery(self._ctx, 'loggingChanges', state)
        statement.execute(query)
        statement.close()

    def saveChanges(self, compact=False):
        statement = self.Connection.createStatement()
        query = getSqlQuery(self._ctx, 'saveChanges', compact)
        statement.execute(query)
        statement.close()

    def getFieldsMap(self, method, reverse):
        if method not in self._fieldsMap:
            self._fieldsMap[method] = self._getFieldsMap(method)
        if reverse:
            map = KeyMap(**{i: {'Map': j, 'Type': k, 'Table': l} for i, j, k, l in self._fieldsMap[method]})
        else:
            map = KeyMap(**{j: {'Map': i, 'Type': k, 'Table': l} for i, j, k, l in self._fieldsMap[method]})
        return map

    def getUpdatedGroups(self, user, prefix):
        groups = None
        call = self._getCall('selectUpdatedGroup')
        call.setString(1, prefix)
        call.setLong(2, user.People)
        call.setString(3, user.Resource)
        result = call.executeQuery()
        groups = getKeyMapKeyMapFromResult(result)
        call.close()
        return groups

    def updateSyncToken(self, user, token, data, timestamp):
        value = data.getValue(token)
        call = self._getBatchedCall('update%s' % token)
        call.setString(1, value)
        call.setTimestamp(2, timestamp)
        call.setLong(3, user.People)
        call.addBatch()
        return KeyMap(**{token: value})

    def mergePeople(self, user, resource, timestamp, deleted):
        call = self._getBatchedCall('mergePeople')
        call.setString(1, 'people/')
        call.setString(2, resource)
        call.setLong(3, user.Group)
        call.setTimestamp(4, timestamp)
        call.setBoolean(5, deleted)
        call.addBatch()
        return (0, 1) if deleted else (1, 0)

    def mergePeopleData(self, table, resource, typename, label, value, timestamp):
        format = {'Table': table, 'Type': typename}
        call = self._getBatchedCall(table, 'mergePeopleData', format)
        call.setString(1, 'people/')
        call.setString(2, resource)
        call.setString(3, label)
        call.setString(4, value)
        call.setTimestamp(5, timestamp)
        if typename is not None:
            call.setString(6, table)
            call.setString(7, typename)
        call.addBatch()
        return 1

    def mergeGroup(self, user, resource, name, timestamp, deleted):
        call = self._getBatchedCall('mergeGroup')
        call.setString(1, 'contactGroups/')
        call.setLong(2, user.People)
        call.setString(3, resource)
        call.setString(4, name)
        call.setTimestamp(5, timestamp)
        call.setBoolean(6, deleted)
        call.addBatch()
        return (0, 1) if deleted else (1, 0)

    def mergeConnection(self, user, data, timestamp):
        separator = ','
        call = self._getBatchedCall('mergeConnection')
        call.setString(1, 'contactGroups/')
        call.setString(2, 'people/')
        call.setString(3, data.getValue('Resource'))
        call.setTimestamp(4, timestamp)
        call.setString(5, separator)
        members = data.getDefaultValue('Connections', ())
        call.setString(6, separator.join(members))
        call.addBatch()
        print("DataBase._mergeConnection() %s - %s" % (data.getValue('Resource'), len(members)))
        return len(members)

    def executeBatchCall(self):
        for name in self._batchedCalls:
            call = self._batchedCalls[name]
            call.executeBatch()
            call.close()
        self._batchedCalls = OrderedDict()

# Procedures called internaly
    def _getFieldsMap(self, method):
        map = []
        call = self._getCall('getFieldsMap')
        call.setString(1, method)
        r = call.executeQuery()
        while r.next():
            map.append((r.getString(1), r.getString(2), r.getString(3), r.getString(4)))
        call.close()
        return tuple(map)

    def _getViewName(self):
        if self._addressbook is None:
            configuration = getConfiguration(self._ctx, g_identifier, False)
            self._addressbook = configuration.getByName('AddressBookName')
        return self._addressbook

    def _getCall(self, name, format=None):
        return getDataSourceCall(self._ctx, self.Connection, name, format)

    def _getBatchedCall(self, key, name=None, format=None):
        if key not in self._batchedCalls:
            name = key if name is None else name
            self._batchedCalls[key] = getDataSourceCall(self._ctx, self.Connection, name, format)
        return self._batchedCalls[key]

    def _getPreparedCall(self, name):
        # TODO: cannot use: call = self.Connection.prepareCommand(name, QUERY)
        # TODO: it trow a: java.lang.IncompatibleClassChangeError
        #query = self.Connection.getQueries().getByName(name).Command
        #self._CallsPool[name] = self.Connection.prepareCall(query)
        return self.Connection.prepareCommand(name, QUERY)

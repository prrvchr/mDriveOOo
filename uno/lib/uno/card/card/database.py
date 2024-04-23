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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.sdb.CommandType import QUERY

from com.sun.star.sdbc.DataType import VARCHAR

from ..dbtool import Array
from ..dbtool import currentDateTimeInTZ
from ..dbtool import getDataFromResult
from ..dbtool import getDataSourceCall
from ..dbtool import getDataSourceConnection
from ..dbtool import getSequenceFromResult
from ..dbtool import getValueFromResult

from ..unotool import checkVersion
from ..unotool import getConfiguration
from ..unotool import getSimpleFile

from ..configuration import g_identifier
from ..configuration import g_admin
from ..configuration import g_host

from ..dbqueries import getSqlQuery

from ..dbconfig import g_cardview
from ..dbconfig import g_bookmark
from ..dbconfig import g_dotcode
from ..dbconfig import g_version

from ..dbinit import getDataBaseConnection
from ..dbinit import createDataBase

from collections import OrderedDict
import json
import traceback


class DataBase(object):
    def __init__(self, ctx, url, user='', pwd=''):
        try:
            print("DataBase.__init__() 1")
            self._ctx = ctx
            self._statement = None
            self._fieldsMap = {}
            self._batchedCalls = OrderedDict()
            config = getConfiguration(ctx, g_identifier, False)
            self._addressbook = config.getByName('AddressBookName')
            self._url = url
            odb = url + '.odb'
            new = not getSimpleFile(ctx).exists(odb)
            print("DataBase.__init__() 2")
            connection = getDataBaseConnection(ctx, url, user, pwd, new)
            print("DataBase.__init__() 3")
            self._version = connection.getMetaData().getDriverVersion()
            if new and self.isUptoDate():
                print("DataBase.__init__() 4")
                createDataBase(ctx, connection, odb, self._addressbook)
                print("DataBase.__init__() 5")
            connection.close()
        except Exception as e:
            traceback.print_exc()

    @property
    def Connection(self):
        if self._statement is None:
            connection = self.getConnection()
            self._statement = connection.createStatement()
        return self._statement.getConnection()

    @property
    def Url(self):
        return self._url
    @property
    def Version(self):
        return self._version

    def isUptoDate(self):
        return checkVersion(self._version, g_version)

    def getConnection(self, user='', password=''):
        return getDataSourceConnection(self._ctx, self._url, user, password, False)

    def dispose(self):
        if self._statement is not None:
            connection = self._statement.getConnection()
            self._statement.dispose()
            self._statement = None
            #connection.getParent().dispose()
            connection.close()
            print("gContact.DataBase.dispose() ***************** database: %s closed!!!" % g_host)

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

    def getColumnIndexes(self, default=None):
        indexes = {} if default is None else default
        call = self._getCall('getColumns')
        result = call.executeQuery()
        while result.next():
            index = result.getInt(1)
            name = result.getString(2)
            indexes[name] = index
        result.close()
        call.close()
        return indexes

    def getSessionId(self, connection):
        session = None
        call = getDataSourceCall(self._ctx, connection, 'getSessionId')
        result = call.executeQuery()
        if result.next():
            session = getValueFromResult(result)
        call.close()
        return session

    def insertUser(self, uri, scheme, server, path, name):
        metadata = None
        books = []
        call = self._getCall('insertUser')
        call.setString(1, uri)
        call.setString(2, scheme)
        call.setString(3, server)
        call.setString(4, path)
        call.setString(5, name)
        result = call.executeQuery()
        user = call.getInt(6)
        if not call.wasNull():
            metadata = {'User': user,
                        'Uri': uri,
                        'Scheme': scheme,
                        'Server': server,
                        'Path': path,
                        'Name': name}
            while result.next():
                books.append(getDataFromResult(result))
        result.close()
        call.close()
        return metadata, books

    def createUser(self, schema, userid, name, password):
        format = {'Public': 'PUBLIC',
                  'Schema': schema,
                  'User': userid,
                  'Name': name,
                  'Password': password,
                  'CardView': g_cardview,
                  'View': self._getViewName(),
                  'Admin': g_admin}
        statement = self.Connection.createStatement()
        query = getSqlQuery(self._ctx, 'createUser', format)
        status = statement.executeUpdate(query)
        query = getSqlQuery(self._ctx, 'createUserSchema', format)
        statement.execute(query)
        query = getSqlQuery(self._ctx, 'setUserSchema', format)
        statement.execute(query)
        query = getSqlQuery(self._ctx, 'createUserView', format)
        statement.execute(query)
        statement.close()

    def selectUser(self, server, name):
        metadata = None
        books = []
        call = self._getCall('selectUser')
        call.setString(1, server)
        call.setString(2, name)
        result = call.executeQuery()
        user = call.getInt(3)
        if not call.wasNull():
            metadata = {'User': user,
                        'Uri': call.getString(4),
                        'Scheme': call.getString(5),
                        'Server': server,
                        'Path': call.getString(6),
                        'Name': name}
            while result.next():
                books.append(getDataFromResult(result))
        result.close()
        call.close()
        return metadata, books

# Procedures called by the User
    def getUserFields(self):
        fields = []
        call = self._getCall('getFieldNames')
        result = call.executeQuery()
        fields = getSequenceFromResult(result)
        call.close()
        return tuple(fields)

    def initAddressbooks(self, user):
        start = self._getLastAddressbookSync()
        stop = currentDateTimeInTZ()
        for data in self._selectChangedAddressbooks(user.Id, start, stop):
            self._initUserAddressbookView(user, data)
        self._updateAddressbook(stop)

    def initGroups(self, book, iterator):
        uris = []
        names = []
        call = self._getCall('initGroups')
        call.setInt(1, book.Id)
        for uri, name in iterator:
            uris.append(uri)
            names.append(name)
        call.setArray(2, Array('VARCHAR', uris))
        call.setArray(3, Array('VARCHAR', names))
        call.execute()
        remove = json.loads(call.getString(4))
        add = json.loads(call.getString(5))
        #toadd = {'User': user.Id, 'Book': book, 'Schema': user.getSchema(), 'Names': names}
        #toremove = {'User': user.Id, 'Book': book, 'Schema': user.getSchema(), 'Names': remove}
        call.close()
        return remove, add

    def insertGroups(self, user, iterator):
        call = self._getCall('insertGroup')
        call.setInt(1, user.Id)
        for uri, name in iterator:
            call.setString(2, uri)
            call.setString(3, name)
            call.execute()
            gid = call.getInt(4)
            yield {'Query': 'Inserted', 'User': user.Id, 'Group': gid, 'Schema': user.getSchema(), 'Name': name}
        call.close()

    def syncGroups(self):
        start = self._getLastGroupSync()
        stop = currentDateTimeInTZ()
        for data in self._selectChangedGroups(start, stop):
            self.initUserGroupView(data)
        self._updateGroup(stop)

    def _selectChangedAddressbooks(self, userid, start, stop):
        addressbooks = []
        call = self._getCall('selectChangedAddressbooks')
        call.setInt(1, userid)
        call.setObject(2, start)
        call.setObject(3, stop)
        result = call.executeQuery()
        while result.next():
            addressbooks.append(getDataFromResult(result))
        call.close()
        return addressbooks

    def _getLastAddressbookSync(self):
        call = self._getCall('getLastAddressbookSync')
        call.execute()
        start = call.getObject(1, None)
        call.close()
        return start

    def _updateAddressbook(self, stop):
        call = self._getCall('updateAddressbook')
        call.setObject(1, stop)
        call.execute()
        call.close()

    def _getLastGroupSync(self):
        call = self._getCall('getLastGroupSync')
        call.execute()
        start = call.getObject(1, None)
        call.close()
        return start

    def _selectChangedGroups(self, start, stop):
        print("DataBase._selectChangedGroups() 1")
        groups = []
        call = self._getCall('selectChangedGroups')
        call.setObject(1, start)
        call.setObject(2, stop)
        call.setInt(3, g_dotcode)
        result = call.executeQuery()
        while result.next():
            groups.append(getDataFromResult(result))
        print("DataBase._selectChangedGroups() 2 %s" % (groups,))
        result.close()
        call.close()
        return groups

    def _updateGroup(self, stop):
        call = self._getCall('updateGroup')
        call.setObject(1, stop)
        status = call.execute()
        call.close()

    def _initUserAddressbookView(self, user, format):
        statement = self.Connection.createStatement()
        query = format.get('Query')
        format['Schema'] = user.getSchema()
        format['Public'] = 'PUBLIC'
        format['View'] = g_cardview
        if query == 'Deleted':
            self._deleteUserView(statement, format)
        elif query == 'Inserted':
            self._createUserView(statement, 'createBookView', format)
        elif query == 'Updated':
            self._deleteUserView(statement, format)
            self._createUserView(statement, 'createBookView', format)
        statement.close()

    def initGroupView(self, user, remove, add):
        statement = self.Connection.createStatement()
        format = {'Public': 'PUBLIC',
                  'View': g_cardview,
                  'User': user.getName(),
                  'Schema': user.getSchema()}
        if remove:
            for item in remove:
                format.update(item)
                self._deleteUserView(statement, format)
        if add:
            for item in add:
                format.update(item)
                self._createUserView(statement, 'createGroupView', format)
        statement.close()

    def initUserGroupView(self, format):
        statement = self.Connection.createStatement()
        query = format.get('Query')
        format['Public'] = 'PUBLIC'
        format['View'] = g_cardview
        format['Bookmark'] = g_bookmark
        if query == 'Deleted':
            self._deleteUserView(statement, format)
        elif query == 'Inserted':
            self._createUserView(statement, 'createGroupView', format)
        elif query == 'Updated':
            self._deleteUserView(statement, format)
            self._createUserView(statement, 'createGroupView', format)
        statement.close()

    def _createUserView(self, statement, view, format):
        query = getSqlQuery(self._ctx, view, format)
        statement.execute(query)

    def _deleteUserView(self, statement, format):
        query = getSqlQuery(self._ctx, 'deleteView', format)
        statement.execute(query)

    def insertBook(self, user, path, name, tag=None, token=None):
        book = None
        call = self._getCall('insertBook')
        call.setInt(1, user)
        call.setString(2, path)
        call.setString(3, name)
        call.setString(4, tag) if tag is not None else call.setNull(4, VARCHAR)
        call.setString(5, token) if token is not None else call.setNull(5, VARCHAR)
        call.executeUpdate()
        book = call.getInt(6)
        call.close()
        return book

    def updateAddressbookName(self, addressbook, name):
        call = self._getCall('updateAddressbookName')
        call.setInt(1, addressbook)
        call.setString(2, name)
        call.executeUpdate()
        call.close()

    def updateAddressbookToken(self, aid, token):
        call = self._getCall('updateAddressbookToken')
        call.setString(1, token)
        call.setInt(2, aid)
        call.executeUpdate()
        call.close()

# Procedures called by the Replicator
    def mergeCard(self, book, iterator):
        count = 0
        self._setBatchModeOn()
        call = self._getCall('mergeCard')
        call.setInt(1, book)
        for cid, etag, deleted, data in iterator:
            call.setString(2, cid)
            call.setString(3, etag)
            call.setBoolean(4, deleted)
            call.setString(5, data)
            call.addBatch()
            count += 1
        if count:
            call.executeBatch()
        call.close()
        self.Connection.commit()
        self._setBatchModeOff()
        return count

    def getLastUserSync(self):
        call = self._getCall('getLastUserSync')
        call.execute()
        start = call.getObject(1, None)
        call.close()
        return start

    def updateUserSync(self, timestamp):
        call = self._getCall('updateUser')
        call.setObject(1, timestamp)
        call.execute()
        call.close()

    def getChangedCard(self, start, stop):
        call = self._getCall('getChangedCards')
        call.setObject(1, start)
        call.setObject(2, stop)
        result = call.executeQuery()
        while result.next():
            yield result.getInt(1), result.getInt(2), result.getString(3), result.getString(4)
        result.close()
        call.close()

    def getGroups(self, aid):
        call = self._getCall('getGroups')
        call.setInt(1, aid)
        result = call.executeQuery()
        while result.next():
            yield result.getInt(1), result.getString(2)
        result.close()
        call.close()

    def mergeCardValue(self, iterator):
        count = count2 = 0
        self._setBatchModeOn()
        call = self._getCall('mergeCardValue')
        call2 = self._getCall('mergeCardGroups')
        for book, card, column, value in iterator:
            if column != -1:
                call.setInt(1, card)
                call.setInt(2, column)
                call.setString(3, value)
                call.addBatch()
                count += 1
            else:
                call2.setInt(1, book)
                call2.setInt(2, card)
                call2.setArray(3, Array('VARCHAR', value))
                call2.addBatch()
                count2 += 1
        if count:
            call.executeBatch()
        if count2:
            call2.executeBatch()
        call.close()
        call2.close()
        self.Connection.commit()
        self._setBatchModeOff()
        return count

    def mergeGroup(self, aid, iterator):
        count = 0
        self._setBatchModeOn()
        call = self._getCall('mergeGroup')
        call.setString(1, aid)
        for gid, deleted, name, timestamp in iterator:
            print("DataBase.mergeGroup() GID: %s - Name: %s - Deleted: %s" % (gid, name, deleted))
            call.setString(2, gid)
            call.setBoolean(3, deleted)
            call.setString(4, name)
            call.setTimestamp(5, timestamp)
            call.addBatch()
            count += 1
        if count:
            call.executeBatch()
        call.close()
        self.Connection.commit()
        self._setBatchModeOff()
        return count

    def mergeGroupMembers(self, gid, timestamp, members):
        call = self._getCall('mergeGroupMembers')
        call.setInt(1, gid)
        call.setTimestamp(2, timestamp)
        call.setArray(3, Array('VARCHAR', members))
        call.executeUpdate()
        call.close()
        return 1

    def deleteCard(self, urls):
        call = self._getCall('deleteCard')
        call.setArray(1, Array('VARCHAR', urls))
        status = call.executeUpdate()
        call.close()
        return len(urls)

    # Private methods
    def _setBatchModeOn(self):
        self._setLoggingChanges(False)
        self._saveChanges()
        self.Connection.setAutoCommit(False)

    def _setBatchModeOff(self):
        self._setLoggingChanges(True)
        self._saveChanges()
        self.Connection.setAutoCommit(True)

    def _executeBatchCall(self):
        for name in self._batchedCalls:
            call = self._batchedCalls[name]
            call.executeBatch()
            call.close()
        self._batchedCalls = OrderedDict()

    def _setLoggingChanges(self, state):
        statement = self.Connection.createStatement()
        query = getSqlQuery(self._ctx, 'loggingChanges', state)
        statement.execute(query)
        statement.close()

    def _saveChanges(self, compact=False):
        statement = self.Connection.createStatement()
        query = getSqlQuery(self._ctx, 'saveChanges', compact)
        statement.execute(query)
        statement.close()

# Procedures called internaly
    def _getViewName(self):
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

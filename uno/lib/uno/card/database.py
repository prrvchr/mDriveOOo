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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.sdb.CommandType import QUERY

from com.sun.star.sdbc.DataType import VARCHAR

from com.sun.star.sdbcx.CheckOption import CASCADE
from com.sun.star.sdbcx.PrivilegeObject import TABLE

from .dbtool import Array
from .dbtool import createUser
from .dbtool import createViews
from .dbtool import currentDateTimeInTZ
from .dbtool import getDataFromResult
from .dbtool import getDataSourceCall
from .dbtool import getDataSourceConnection
from .dbtool import getSequenceFromResult
from .dbtool import getValueFromResult

from .unotool import checkVersion
from .unotool import getConfiguration
from .unotool import getSimpleFile

from .configuration import g_identifier
from .configuration import g_host

from .dbqueries import getSqlQuery

from .dbconfig import g_catalog
from .dbconfig import g_schema
from .dbconfig import g_version

from .dbinit import getDataBaseConnection
from .dbinit import createDataBase

from collections import OrderedDict
import json
import traceback


class DataBase():
    def __init__(self, ctx, logger, url, user='', pwd=''):
        self._cls = 'DataBase'
        mtd = '__init__'
        self._ctx = ctx
        self._statement = None
        self._fieldsMap = {}
        self._batchedCalls = OrderedDict()
        self._url = url
        odb = url + '.odb'
        new = not getSimpleFile(ctx).exists(odb)
        connection = getDataBaseConnection(ctx, url, user, pwd, new)
        self._version = connection.getMetaData().getDriverVersion()
        if new and self.isUptoDate():
            logger.logprb(INFO, self._cls, mtd, 1251)
            createDataBase(ctx, connection, odb)
            logger.logprb(INFO, self._cls, mtd, 1252)
        connection.close()

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
        call = self._getCall('insertUser')
        call.setString(1, uri)
        call.setString(2, scheme)
        call.setString(3, server)
        call.setString(4, path)
        call.setString(5, name)
        call.execute()
        user = call.getInt(6)
        if not call.wasNull():
            metadata = {'User': user,
                        'Uri': uri,
                        'Scheme': scheme,
                        'Server': server,
                        'Path': path,
                        'Name': name}
        call.close()
        return metadata, ()

    def createUser(self, schema, userid, name, password):
        try:
            if createUser(self.Connection, name, password):
                statement = self.Connection.createStatement()
                template = {'Schema': schema, 'Name': name}
                query = getSqlQuery(self._ctx, 'createUserSchema', template)
                statement.execute(query)
                query = getSqlQuery(self._ctx, 'setUserSchema', template)
                statement.execute(query)
                statement.close()
                view = self._getViewName()
                template = {'Catalog': g_catalog, 'Schema': g_schema, 'User': userid}
                command = getSqlQuery(self._ctx, 'getUserViewCommand', template)
                self._createUserView(g_catalog, schema, view, command, CASCADE)
                self._grantPrivileges(g_catalog, schema, view, name, TABLE, 1)
        except Exception:
            print("DataBase.createUser() ERROR: %s" % traceback.format_exc())

    def _createUserView(self, catalog, schema, name, command, option):
        views = self._getItemOptions(catalog, schema, name, command, option)
        createViews(self.Connection.getViews(), views)

    def _getItemOptions(self, catalog, schema, name, *options):
        yield catalog, schema, name, *options

    def selectUser(self, server, name):
        metadata = None
        args = []
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
                args.append(getDataFromResult(result))
        result.close()
        call.close()
        return metadata, args

# Procedures called by the User
    def getUserFields(self):
        call = self._getCall('getFieldNames')
        result = call.executeQuery()
        fields = getSequenceFromResult(result)
        call.close()
        return tuple(fields)

    def initAddressbooks(self, user):
        start = self.getLastSync('BookSync', user)
        stop = currentDateTimeInTZ()
        for args in self._selectChangedItems(user, start, stop, 'Books'):
            self._initUserView('Book', *args)
        self._updateBookSync(user, stop)

    def initGroups(self, user, book, iterator):
        uris = []
        names = []
        call = self._getCall('initGroups')
        call.setInt(1, user.getBook(book).Id)
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

    def insertGroup(self, bookid, uri, name):
        args = None
        call = self._getCall('insertGroup')
        call.setInt(1, bookid)
        call.setString(2, uri)
        call.setString(3, name)
        call.execute()
        group = call.getInt(4)
        if not call.wasNull():
            args = (group, uri, name)
        call.close()
        return args

    def syncGroups(self, user):
        start = self.getLastSync('GroupSync', user)
        stop = currentDateTimeInTZ()
        for args in self._selectChangedItems(user, start, stop, 'Groups'):
            self._initUserView('Group', *args)
        self._updateGroupSync(user, stop)

    def _selectChangedItems(self, user, start, stop, method):
        call = self._getCall('selectChanged%s' % method)
        call.setInt(1, user.Id)
        call.setObject(2, start)
        call.setObject(3, stop)
        result = call.executeQuery()
        while result.next():
            query = result.getString(1)
            itemid = result.getInt(2)
            oldname = result.getString(3)
            newname = result.getString(4)
            yield query, user.getSchema(), user.Name, itemid, oldname, newname
        result.close()
        call.close()

    def getLastSync(self, method, user=None):
        i = 1
        call = self._getCall('getLast%s' % method)
        if user is not None:
            call.setInt(i, user.Id)
            i += 1
        call.execute()
        start = call.getObject(i, None)
        call.close()
        return start

    def _updateBookSync(self, user, stop):
        call = self._getCall('updateBookSync')
        call.setInt(1, user.Id)
        call.setObject(2, stop)
        call.execute()
        call.close()

    def _updateGroupSync(self, user, stop):
        call = self._getCall('updateGroupSync')
        call.setInt(1, user.Id)
        call.setObject(2, stop)
        call.execute()
        call.close()

    def _initUserView(self, view, query, schema, user, item, oldname, newname):
        if query == 'Deleted' or query == 'Updated':
            self._deleteUserView(g_catalog, schema, oldname)
        if query == 'Inserted' or query == 'Updated':
            template = {'Catalog': g_catalog, 'Schema': g_schema, 'ItemId': item}
            command = getSqlQuery(self._ctx, 'get%sViewCommand' % view, template)
            self._createUserView(g_catalog, schema, newname, command, CASCADE)
            self._grantPrivileges(g_catalog, schema, newname, user, TABLE, 1)

    def _grantPrivileges(self, catalog, schema, name, user, ptype, privileges):
        self.Connection.getUsers().getByName(user).grantPrivileges(f'{catalog}.{schema}.{name}', ptype, privileges)

    def _deleteUserView(self, catalog, schema, name):
        views = self.Connection.getViews()
        view = f'{catalog}.{schema}.{name}'
        if views.hasByName(view):
            views.dropByName(view)

    def _renameUserView(self, catalog, schema, newname, oldname):
        views = self.Connection.getViews()
        newview = f'{catalog}.{schema}.{newname}'
        oldview = f'{catalog}.{schema}.{oldname}'
        if views.hasByName(oldview) and not views.hasByName(newview):
            views.rename(oldview, newview)

    def insertBook(self, userid, uri, name, tag=None, token=None):
        book = None
        call = self._getCall('insertBook')
        call.setInt(1, userid)
        call.setString(2, uri)
        call.setString(3, name)
        if tag is None:
            call.setNull(4, VARCHAR)
        else:
            call.setString(4, tag)
        if token is None:
            call.setNull(5, VARCHAR)
        else:
            call.setString(5, token)
        call.executeUpdate()
        bookid = call.getInt(6)
        if not call.wasNull():
            book = {'Book': bookid, 'Uri': uri, 'Name': name, 'Tag': tag, 'Token': token}
        call.close()
        return book

    def createGroupView(self, user, group):
        schema = user.getSchema()
        template = {'Catalog': g_catalog, 'Schema':  g_schema, 'ItemId': group.Id}
        command = getSqlQuery(self._ctx, 'getGroupViewCommand', template)
        self._createUserView(g_catalog, schema, group.Name, command, CASCADE)
        self._grantPrivileges(g_catalog, schema, group.Name, user.Name, TABLE, 1)

    def removeGroupView(self, user, group):
        self._deleteUserView(g_catalog, user.getSchema(), group.Name)

    def renameGroupView(self, user, group, name):
        self._renameUserView(g_catalog, user.getSchema(), group.Name, name)

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

    def updateCardSync(self, timestamp):
        call = self._getCall('updateCardSync')
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
        call.executeUpdate()
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
        config = getConfiguration(self._ctx, g_identifier, False)
        return config.getByName('AddressBookName')

    def _getCall(self, name, template=None):
        return getDataSourceCall(self._ctx, self.Connection, name, template)

    def _getBatchedCall(self, key, name=None, template=None):
        if key not in self._batchedCalls:
            name = key if name is None else name
            self._batchedCalls[key] = getDataSourceCall(self._ctx, self.Connection, name, template)
        return self._batchedCalls[key]

    def _getPreparedCall(self, name):
        # TODO: cannot use: call = self.Connection.prepareCommand(name, QUERY)
        # TODO: it trow a: java.lang.IncompatibleClassChangeError
        #query = self.Connection.getQueries().getByName(name).Command
        #self._CallsPool[name] = self.Connection.prepareCall(query)
        return self.Connection.prepareCommand(name, QUERY)

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

from io.github.prrvchr.css.util import DateTimeWithTimezone

from .unolib import KeyMap

from .unotool import createService

from .dbqueries import getSqlQuery
from .dbconfig import g_role
from .dbconfig import g_dba

from .dbtool import Array

from .dbtool import checkDataBase
from .dbtool import createStaticTable
from .dbtool import currentDateTimeInTZ
from .dbtool import currentUnoDateTime
from .dbtool import executeSqlQueries
from .dbtool import getDataSourceCall
from .dbtool import getDateTimeInTZToString
from .dbtool import getKeyMapFromResult
from .dbtool import executeQueries

from .dbinit import getStaticTables
from .dbinit import getQueries
from .dbinit import getTablesAndStatements

from .configuration import g_admin
from .configuration import g_scheme

import traceback


class DataBase():
    def __init__(self, ctx, datasource, name='', password='', sync=None):
        self._ctx = ctx
        self._statement = datasource.getIsolatedConnection(name, password).createStatement()
        self._sync = sync

    @property
    def Connection(self):
        return self._statement.getConnection()

# Procedures called by the DataSource
    def createDataBase(self):
        try:
            print("DataBase.createDataBase() 1")
            version, error = checkDataBase(self._ctx, self.Connection)
            if error is None:
                createStaticTable(self._ctx, self._statement, getStaticTables(), True)
                tables, statements = getTablesAndStatements(self._ctx, self._statement, version)
                print("DataBase.createDataBase() 2")
                executeSqlQueries(self._statement, tables)
                executeQueries(self._ctx, self._statement, getQueries())
                print("DataBase.createDataBase() 3")
            print("DataBase.createDataBase() 4")
            return error
        except Exception as e:
            msg = "Error: %s" % traceback.print_exc()
            print(msg)

    def getDataSource(self):
        return self.Connection.getParent().DatabaseDocument.DataSource

    def storeDataBase(self, url):
        self.Connection.getParent().DatabaseDocument.storeAsURL(url, ())

    def addCloseListener(self, listener):
        self.Connection.Parent.DatabaseDocument.addCloseListener(listener)

    def shutdownDataBase(self, compact=False):
        if compact:
            query = getSqlQuery(self._ctx, 'shutdownCompact')
        else:
            query = getSqlQuery(self._ctx, 'shutdown')
        self._statement.execute(query)

    def createUser(self, name, password):
        format = {'User': name, 'Password': password, 'Role': g_role, 'Admin': g_admin}
        sql = getSqlQuery(self._ctx, 'createUser', format)
        status = self._statement.executeUpdate(sql)
        sql = getSqlQuery(self._ctx, 'grantRole', format)
        status += self._statement.executeUpdate(sql)
        return status == 0

    def selectUser(self, name):
        user = None
        select = self._getCall('getUser')
        select.setString(1, name)
        result = select.executeQuery()
        if result.next():
            user = getKeyMapFromResult(result)
        result.close()
        select.close()
        return user

    def getDefaultUserTimeStamp(self):
        dtz = DateTimeWithTimezone()
        dtz.DateTimeInTZ.Year = 1970
        dtz.DateTimeInTZ.Month = 1
        dtz.DateTimeInTZ.Day = 1
        return dtz

    def insertUser(self, provider, user, root):
        userid = provider.getUserId(user)
        username = provider.getUserName(user)
        displayname = provider.getUserDisplayName(user)
        rootid = provider.getRootId(root)
        rootname = provider.getRootTitle(root)
        timestamp = currentDateTimeInTZ()
        call = self._getCall('insertUser')
        call.setString(1, userid)
        call.setString(2, rootid)
        call.setString(3, username)
        call.setString(4, displayname)
        call.setObject(5, timestamp)
        call.execute()
        call.close()
        self._mergeRoot(provider, userid, rootid, rootname, root, timestamp)
        data = KeyMap()
        data.insertValue('UserId', userid)
        data.insertValue('UserName', username)
        data.insertValue('RootId', rootid)
        data.insertValue('RootName', rootname)
        data.insertValue('Token', '')
        data.insertValue('SyncMode', 0)
        print("DataBase.insertUser() TimeStamp: %s" % getDateTimeInTZToString(timestamp))
        data.insertValue('TimeStamp', timestamp)
        return data

    def getContentType(self):
        call = self._getCall('getContentType')
        result = call.executeQuery()
        if result.next():
            folder = result.getString(1)
            link = result.getString(2)
        result.close()
        call.close()
        return folder, link

# Procedures called by the Replicator
    def getMetaData(self, user, item):
        itemid = item.getValue('ItemId')
        metadata = self.getItem(user, itemid, False)
        atroot = metadata.getValue('ParentId') == user.RootId
        metadata.insertValue('AtRoot', atroot)
        return metadata

# Procedures called by the Content
        #TODO: Can't have a simple SELECT ResultSet with a Procedure,
    def getItem(self, user, itemid, rewite=True):
        item = None
        isroot = itemid == user.RootId
        print("Content.getItem() 1 isroot: '%s'" % isroot)
        call = 'getRoot' if isroot else 'getItem'
        select = self._getCall(call)
        select.setString(1, user.Id if isroot else itemid)
        if not isroot:
             select.setBoolean(2, rewite)
        result = select.executeQuery()
        if result.next():
            print("Content.getItem() 2 isroot: '%s'" % isroot)
            item = getKeyMapFromResult(result)
        result.close()
        select.close()
        return item

    def updateFolderContent(self, user, content):
        rows = []
        timestamp = currentDateTimeInTZ()
        call = self._getCall('mergeItem')
        call.setString(1, user.Id)
        call.setLong(2, 0)
        call.setObject(3, timestamp)
        enumerator = user.Provider.getFolderContent(user.Request, content)
        while enumerator.hasMoreElements():
            item = enumerator.nextElement()
            itemid = user.Provider.getItemId(item)
            parents = user.Provider.getItemParent(item, user.RootId)
            rows.append(self._mergeItem(call, user.Provider, item, itemid, parents, timestamp))
            call.addBatch()
        if enumerator.RowCount > 0:
            call.executeBatch()
        call.close()
        return all(rows)

    def getChildren(self, username, itemid, properties, mode, scheme):
        #TODO: Can't have a ResultSet of type SCROLL_INSENSITIVE with a Procedure,
        #TODO: as a workaround we use a simple quey...
        select = self._getCall('getChildren', properties)
        scroll = uno.getConstantByName('com.sun.star.sdbc.ResultSetType.SCROLL_INSENSITIVE')
        select.ResultSetType = scroll
        # OpenOffice / LibreOffice Columns:
        #    ['Title', 'Size', 'DateModified', 'DateCreated', 'IsFolder', 'TargetURL', 'IsHidden',
        #    'IsVolume', 'IsRemote', 'IsRemoveable', 'IsFloppy', 'IsCompactDisc']
        # "TargetURL" is done by: the database view Path
        select.setString(1, scheme)
        select.setShort(2, mode)
        select.setString(3, itemid)
        return select

    def updateConnectionMode(self, userid, itemid, value, default):
        update = self._getCall('updateConnectionMode')
        update.setLong(1, value)
        update.setString(2, itemid)
        update.executeUpdate()
        update.close()
        return value

    def getIdentifier(self, user, url):
        print("DataBase.getIdentifier() Url: '%s'" % url)
        call = self._getCall('getIdentifier')
        call.setString(1, user.Id)
        call.setString(2, url)
        call.execute()
        itemid = call.getString(3)
        if call.wasNull():
            itemid = None
        call.close()
        return itemid

    def getNewIdentifier(self, userid):
        identifier = ''
        select = self._getCall('getNewIdentifier')
        select.setString(1, userid)
        result = select.executeQuery()
        if result.next():
            identifier = result.getString(1)
        result.close()
        select.close()
        return identifier

    def deleteNewIdentifier(self, userid, itemid):
        print("DataBase.deleteNewIdentifier() NewID: %s" % itemid)
        call = self._getCall('deleteNewIdentifier')
        call.setString(1, userid)
        call.setString(2, itemid)
        call.executeUpdate()
        call.close()

    def updateContent(self, userid, itemid, property, value):
        updated = False
        timestamp = currentDateTimeInTZ()
        if property == 'Title':
            update = self._getCall('updateTitle')
            update.setObject(1, timestamp)
            update.setString(2, value)
            update.setString(3, itemid)
            updated = update.execute() == 0
            update.close()
        elif property == 'Size':
            update = self._getCall('updateSize')
            # FIXME: If we update the Size, we need to update the DateModified too...
            update.setObject(1, timestamp)
            update.setLong(2, value)
            update.setTimestamp(3, currentUnoDateTime())
            update.setString(4, itemid)
            updated = update.execute() == 0
            update.close()
        elif property == 'Trashed':
            update = self._getCall('updateTrashed')
            update.setObject(1, timestamp)
            update.setBoolean(2, value)
            update.setString(3, itemid)
            updated = update.execute() == 0
            update.close()
        if updated:
            # Start Replicator for pushing changes…
            self._sync.set()

    def getNewTitle(self, title, parentid, isfolder):
        call = self._getCall('getNewTitle')
        call.setString(1, title)
        call.setString(2, parentid)
        call.setBoolean(3, isfolder)
        call.execute()
        newtitle = call.getString(4)
        call.close()
        return newtitle

    def insertNewContent(self, userid, content, timestamp):
        call = self._getCall('insertItem')
        call.setString(1, userid)
        call.setLong(2, 1)
        call.setObject(3, timestamp)
        call.setString(4, content.getValue("Id"))
        call.setString(5, content.getValue("Title"))
        call.setTimestamp(6, content.getValue('DateCreated'))
        call.setTimestamp(7, content.getValue('DateModified'))
        call.setString(8, content.getValue('MediaType'))
        call.setLong(9, content.getValue('Size'))
        call.setBoolean(10, content.getValue('Trashed'))
        call.setBoolean(11, content.getValue('CanAddChild'))
        call.setBoolean(12, content.getValue('CanRename'))
        call.setBoolean(13, content.getValue('IsReadOnly'))
        call.setBoolean(14, content.getValue('IsVersionable'))
        call.setString(15, content.getValue("ParentId"))
        status = call.execute() == 0
        content.setValue('BaseURI', call.getString(16))
        content.setValue('Title', call.getString(17))
        content.setValue('TitleOnServer', call.getString(18))
        call.close()
        if status:
            # Start Replicator for pushing changes…
            self._sync.set()

    def hasTitle(self, userid, parentid, title):
        has = True
        call = self._getCall('hasTitle')
        call.setString(1, userid)
        call.setString(2, parentid)
        call.setString(3, title)
        result = call.executeQuery()
        if result.next():
            has = result.getBoolean(1)
        result.close()
        call.close()
        return has

    def getChildId(self, parentid, title):
        id = None
        call = self._getCall('getChildId')
        call.setString(1, parentid)
        call.setString(2, title)
        result = call.executeQuery()
        if result.next():
            id = result.getString(1)
        result.close()
        call.close()
        return id

# Procedures called by the Replicator
    # Synchronization pull token update procedure
    def updateToken(self, userid, token):
        update = self._getCall('updateToken')
        update.setString(1, token)
        update.setString(2, userid)
        updated = update.executeUpdate() == 1
        update.close()
        return updated

    # Identifier counting procedure
    def countIdentifier(self, userid):
        count = 0
        call = self._getCall('countNewIdentifier')
        call.setString(1, userid)
        result = call.executeQuery()
        if result.next():
            count = result.getLong(1)
        result.close()
        call.close()
        return count

    # Identifier inserting procedure
    def insertIdentifier(self, enumerator, userid):
        result = []
        insert = self._getCall('insertNewIdentifier')
        insert.setString(1, userid)
        while enumerator.hasMoreElements():
            item = enumerator.nextElement()
            self._doInsert(insert, item)
        if enumerator.RowCount > 0:
            insert.executeBatch()
        insert.close()

    def _doInsert(self, insert, identifier):
        insert.setString(2, identifier)
        insert.addBatch()

    # First pull procedure: header of merge request
    def getFirstPullCall(self, userid, connectionmode, timestamp):
        call = self._getCall('mergeItem')
        call.setString(1, userid)
        call.setInt(2, connectionmode)
        call.setObject(3, timestamp)
        return call

    # First pull procedure: body of merge request
    def setFirstPullCall(self, call, provider, item, itemid, parents, timestamp):
        row = self._mergeItem(call, provider, item, itemid, parents, timestamp)
        call.addBatch()
        return row

    def updateUserSyncMode(self, userid, mode):
        update = self._getCall('updateUserSyncMode')
        update.setInt(1, mode)
        update.setString(2, userid)
        update.executeUpdate()
        update.close()

    def setSession(self, user=g_dba):
        query = getSqlQuery(self._ctx, 'setSession', user)
        self._statement.execute(query)

    # Procedure to retrieve all the UPDATE AND INSERT in the 'Capabilities' table
    def getPushItems(self, userid, start, end):
        items = []
        select = self._getCall('getPushItems')
        select.setString(1, userid)
        select.setObject(2, start)
        select.setObject(3, end)
        result = select.executeQuery()
        while result.next():
            items.append(getKeyMapFromResult(result))
        result.close()
        select.close()
        return items

    def getPushProperties(self, userid, itemid, start, end):
        properties = []
        select = self._getCall('getPushProperties')
        select.setString(1, userid)
        select.setString(2, itemid)
        select.setObject(3, start)
        select.setObject(4, end)
        result = select.executeQuery()
        while result.next():
            properties.append(getKeyMapFromResult(result))
        result.close()
        select.close()
        return properties

    def updatePushItems(self, user, itemids):
        call = self._getCall('updatePushItems')
        call.setString(1, user.Id)
        call.setArray(2, Array('VARCHAR', itemids))
        call.execute()
        timestamp = call.getObject(3, None)
        call.close()
        user.TimeStamp = timestamp

    def getItemParentIds(self, itemid, metadata, start, end):
        call = self._getCall('getItemParentIds')
        call.setString(1, itemid)
        call.setObject(2, start)
        call.setObject(3, end)
        call.execute()
        old = call.getArray(4)
        new = call.getArray(5)
        call.close()
        metadata.insertValue('ParentToAdd', set(new) - set(old))
        metadata.insertValue('ParentToRemove', set(old) - set(new))

    def updateItemId(self, provider, itemid, response):
        newid = provider.getResponseId(response, itemid)
        if newid != itemid:
            update = self._getCall('updateItemId')
            update.setString(1, newid)
            update.setString(2, itemid)
            update.executeUpdate()
            update.close()

# Procedures called internally
    def _mergeItem(self, call, provider, item, id, parents, timestamp):
        call.setString(4, id)
        call.setString(5, provider.getItemTitle(item))
        call.setTimestamp(6, provider.getItemCreated(item, timestamp))
        call.setTimestamp(7, provider.getItemModified(item, timestamp))
        call.setString(8, provider.getItemMediaType(item))
        call.setLong(9, provider.getItemSize(item))
        call.setBoolean(10, provider.getItemTrashed(item))
        call.setBoolean(11, provider.getItemCanAddChild(item))
        call.setBoolean(12, provider.getItemCanRename(item))
        call.setBoolean(13, provider.getItemIsReadOnly(item))
        call.setBoolean(14, provider.getItemIsVersionable(item))
        call.setArray(15, Array('VARCHAR', parents))
        return 1

    def _mergeRoot(self, provider, userid, rootid, rootname, root, timestamp):
        call = self._getCall('mergeItem')
        call.setString(1, userid)
        call.setLong(2, 0)
        call.setObject(3, timestamp)
        call.setString(4, rootid)
        call.setString(5, rootname)
        call.setTimestamp(6, provider.getRootCreated(root, timestamp))
        call.setTimestamp(7, provider.getRootModified(root, timestamp))
        call.setString(8, provider.getRootMediaType(root))
        call.setLong(9, provider.getRootSize(root))
        call.setBoolean(10, provider.getRootTrashed(root))
        call.setBoolean(11, provider.getRootCanAddChild(root))
        call.setBoolean(12, provider.getRootCanRename(root))
        call.setBoolean(13, provider.getRootIsReadOnly(root))
        call.setBoolean(14, provider.getRootIsVersionable(root))
        call.setArray(15, Array('VARCHAR'))
        call.executeUpdate()
        call.close()

    def _getCall(self, name, format=None):
        return getDataSourceCall(self._ctx, self.Connection, name, format)

    def _getPreparedCall(self, name):
        # TODO: cannot use: call = self.Connection.prepareCommand(name, QUERY)
        # TODO: it trow a: java.lang.IncompatibleClassChangeError
        #query = self.Connection.getQueries().getByName(name).Command
        #self._CallsPool[name] = self.Connection.prepareCall(query)
        return self.Connection.prepareCommand(name, QUERY)

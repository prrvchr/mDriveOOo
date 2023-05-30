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
from com.sun.star.sdbc.DataType import ARRAY

from io.github.prrvchr.css.util import DateTimeWithTimezone

from .unotool import createService

from .dbqueries import getSqlQuery
from .dbconfig import g_role
from .dbconfig import g_dba
from .dbconfig import g_csv

from .dbtool import Array

from .dbtool import checkDataBase
from .dbtool import createStaticTable
from .dbtool import currentDateTimeInTZ
from .dbtool import currentUnoDateTime
from .dbtool import executeSqlQueries
from .dbtool import getDataSourceCall
from .dbtool import getDateTimeInTZToString
from .dbtool import getDataFromResult
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
                createStaticTable(self._ctx, self._statement, getStaticTables(), g_csv, True)
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
            user = getDataFromResult(result)
        result.close()
        select.close()
        return user

    def getDefaultUserTimeStamp(self):
        dtz = DateTimeWithTimezone()
        dtz.DateTimeInTZ.Year = 1970
        dtz.DateTimeInTZ.Month = 1
        dtz.DateTimeInTZ.Day = 1
        return dtz

    def insertUser(self, user, root):
        data = None
        timestamp = currentDateTimeInTZ()
        call = self._getCall('insertUser')
        call.setString(1, user[0])
        call.setString(2, user[1])
        call.setString(3, user[2])
        call.setString(4, root[0])
        call.setString(5, root[1])
        call.setTimestamp(6, root[2])
        call.setTimestamp(7, root[3])
        call.setString(8, root[4])
        call.setBoolean(9, root[5])
        call.setBoolean(10, root[6])
        call.setBoolean(11, root[7])
        call.setBoolean(12, root[8])
        call.setBoolean(13, root[9])
        call.setObject(14, timestamp)
        result = call.executeQuery() 
        if result.next():
            data = getDataFromResult(result)
        result.close()
        call.close()
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
        itemid = item.get('ItemId')
        metadata = self.getItem(user, itemid, False)
        atroot = metadata.get('ParentId') == user.RootId
        metadata['AtRoot'] = atroot
        return metadata

    def updateNewItemId(self, item, newitem):
        newid, created, modified = newitem
        print("DataBase.mergeNewFolder() 1 Item Id: %s - New Item Id: %s" % (item.get('Id'), newid))
        call = self._getCall('updateNewItemId')
        call.setString(1, item.get('Id'))
        call.setString(2, newid)
        call.setTimestamp(3, created)
        call.setTimestamp(4, modified)
        call.close()
        print("DataBase.mergeNewFolder() 1 Item Id: %s - New Item Id: %s" % (item.get('Id'), newid))
        item['Id'] = newid
        print("DataBase.mergeNewFolder() 2 Item Id: %s - New Item Id: %s" % (item.get('Id'), newid))
        return True

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
            item = getDataFromResult(result)
        result.close()
        select.close()
        return item

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
        i = 1
        if 'TargetURL' in (property.Name for property in properties):
            select.setString(i, scheme)
            i += 1
        select.setShort(i , mode)
        select.setString(i +1, itemid)
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
        call.setString(4, content.get("Id"))
        call.setString(5, content.get("Title"))
        call.setTimestamp(6, content.get('DateCreated'))
        call.setTimestamp(7, content.get('DateModified'))
        call.setString(8, content.get('MediaType'))
        call.setLong(9, content.get('Size'))
        call.setBoolean(10, content.get('Trashed'))
        call.setBoolean(11, content.get('CanAddChild'))
        call.setBoolean(12, content.get('CanRename'))
        call.setBoolean(13, content.get('IsReadOnly'))
        call.setBoolean(14, content.get('IsVersionable'))
        call.setString(15, content.get("ParentId"))
        status = call.execute() == 0
        content['BaseURI'] = call.getString(16)
        content['Title'] = call.getString(17)
        content['TitleOnServer'] = call.getString(18)
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
    def insertIdentifier(self, iterator, userid):
        count = 0
        call = self._getCall('insertNewIdentifier')
        call.setString(1, userid)
        for itemid in iterator:
            call.setString(2, itemid)
            call.addBatch()
            count += 1
        if count > 0:
            call.executeBatch()
        call.close()

    # Pull procedure
    def pullItems(self, iterator, userid, timestamp):
        count = 0
        call1 = self._getCall('mergeItem')
        call2 = self._getCall('mergeParent')
        call1.setString(1, userid)
        call1.setInt(2, 1)
        call1.setObject(3, timestamp)
        for item in iterator:
            count += self._mergeItem(call1, call2, item, timestamp)
        if count:
            call1.executeBatch()
            call2.executeBatch()
        call1.close()
        call2.close()
        return count

    def pullChanges(self, iterator, userid, timestamp):
        call = self._getCall('pullChanges')
        count = 0
        for item in iterator:
            call.setString(1, userid)
            call.setString(2, item[0])
            call.setBoolean(3, item[1])
            call.setNull(4, VARCHAR) if item[2] is None else call.setString(4, item[2])
            call.setTimestamp(5, item[3])
            call.setObject(6, timestamp)
            call.addBatch()
            count += 1
        if count:
            call.executeBatch()
        call.close()
        return count

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
            items.append(getDataFromResult(result))
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
            properties.append(getDataFromResult(result))
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
    def _mergeItem(self, call1, call2, item, timestamp):
        call1.setString(4, item[0])
        call1.setString(5, item[1])
        call1.setTimestamp(6, item[2])
        call1.setTimestamp(7, item[3])
        call1.setString(8, item[4])
        call1.setLong(9, item[5])
        call1.setBoolean(10, item[6])
        call1.setBoolean(11, item[7])
        call1.setBoolean(12, item[8])
        call1.setBoolean(13, item[9])
        call1.setBoolean(14, item[10])
        call1.addBatch()
        self._mergeParent(call2, item, timestamp)
        return 1

    def _mergeParent(self, call, item, timestamp):
        call.setString(1, item[0])
        self._setPath(call, 2, item[-2])
        call.setArray(3, Array('VARCHAR', item[-1]))
        call.setObject(4, timestamp)
        call.addBatch()

    def _setPath(self, call, i, path):
        call.setNull(i, VARCHAR) if path is None else call.setString(i, path)

    def _mergeRoot(self, provider, userid, rootid, rootname, root, timestamp):
        call = self._getCall('mergeItem')
        call.setString(1, user.get('UserId'))
        call.setLong(2, 0)
        call.setObject(3, timestamp)
        call.setString(4, user.get('RootId'))
        call.setString(5, user.get('RootName'))
        call.setTimestamp(6, user.get('DateCreated'))
        call.setTimestamp(7, user.get('DateModified'))
        call.setString(8, user.get('MediaType'))
        call.setLong(9, user.get('Size'))
        call.setBoolean(10, user.get('Trashed'))
        call.setBoolean(11, user.get('CanAddChild'))
        call.setBoolean(12, user.get('CanRename'))
        call.setBoolean(13, user.get('IsReadOnly'))
        call.setBoolean(14, user.get('IsVersionable'))
        call.setArray(15, Array('VARCHAR', user.get('Parents')))
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

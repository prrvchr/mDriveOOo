#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE
from com.sun.star.sdb.CommandType import QUERY

from com.sun.star.ucb import XRestDataBase

from unolib import KeyMap
from unolib import parseDateTime

from .configuration import g_admin

from .dbqueries import getSqlQuery
from .dbconfig import g_role
from .dbconfig import g_dba

from .dbtools import checkDataBase
from .dbtools import createStaticTable
from .dbtools import executeSqlQueries
from .dbtools import getDataSourceCall
from .dbtools import executeQueries

from .dbinit import getStaticTables
from .dbinit import getQueries
from .dbinit import getTablesAndStatements

from .dbtools import getKeyMapFromResult

from .logger import logMessage
from .logger import getMessage

import traceback


class DataBase(unohelper.Base,
               XRestDataBase):
    def __init__(self, ctx, datasource, name='', password='', sync=None):
        self.ctx = ctx
        self._statement = datasource.getConnection(name, password).createStatement()
        self.sync = sync

    @property
    def Connection(self):
        return self._statement.getConnection()

# Procedures called by the DataSource
    def createDataBase(self):
        version, error = checkDataBase(self.ctx, self.Connection)
        if error is None:
            createStaticTable(self.ctx, self._statement, getStaticTables(), True)
            tables, statements = getTablesAndStatements(self.ctx, self._statement, version)
            executeSqlQueries(self._statement, tables)
            executeQueries(self.ctx, self._statement, getQueries())
        return error

    def getDataSource(self):
        return self.Connection.getParent().DatabaseDocument.DataSource

    def storeDataBase(self, url):
        self.Connection.getParent().DatabaseDocument.storeAsURL(url, ())

    def addCloseListener(self, listener):
        self.Connection.Parent.DatabaseDocument.addCloseListener(listener)

    def shutdownDataBase(self, compact=False):
        if compact:
            query = getSqlQuery(self.ctx, 'shutdownCompact')
        else:
            query = getSqlQuery(self.ctx, 'shutdown')
        self._statement.execute(query)

    def createUser(self, user, password):
        name, password = user.getCredential(password)
        format = {'User': name, 'Password': password, 'Role': g_role, 'Admin': g_admin}
        sql = getSqlQuery(self.ctx, 'createUser', format)
        status = self._statement.executeUpdate(sql)
        sql = getSqlQuery(self.ctx, 'grantRole', format)
        status += self._statement.executeUpdate(sql)
        return status == 0

    def selectUser(self, name):
        user = None
        select = self._getCall('getUser')
        select.setString(1, name)
        result = select.executeQuery()
        if result.next():
            user = getKeyMapFromResult(result)
        select.close()
        return user

    def insertUser(self, provider, user, root):
        userid = provider.getUserId(user)
        username = provider.getUserName(user)
        displayname = provider.getUserDisplayName(user)
        rootid = provider.getRootId(root)
        rootname = provider.getRootTitle(root)
        timestamp = parseDateTime()
        insert = self._getCall('insertUser')
        insert.setString(1, username)
        insert.setString(2, displayname)
        insert.setString(3, rootid)
        insert.setTimestamp(4, timestamp)
        insert.setString(5, userid)
        insert.execute()
        insert.close()
        self._mergeRoot(provider, userid, rootid, rootname, root, timestamp)
        data = KeyMap()
        data.insertValue('UserId', userid)
        data.insertValue('UserName', username)
        data.insertValue('RootId', rootid)
        data.insertValue('RootName', rootname)
        data.insertValue('Token', '')
        return data

    def getContentType(self):
        call = self._getCall('getContentType')
        result = call.executeQuery()
        if result.next():
            folder = result.getString(1)
            link = result.getString(2)
        call.close()
        return folder, link

# Procedures called by the Identifier
    def getItem(self, userid, itemid, parentid):
        #TODO: Can't have a simple SELECT ResultSet with a Procedure,
        #TODO: the malfunction is rather bizard: it always returns the same result
        #TODO: as a workaround we use a simple quey...
        item = None
        call = 'getRoot' if parentid is None else 'getItem'
        select = self._getCall(call)
        select.setString(1, userid)
        select.setString(2, itemid)
        if parentid is not None:
            select.setString(3, parentid)
        result = select.executeQuery()
        if result.next():
            item = getKeyMapFromResult(result)
        select.close()
        return item

    def updateFolderContent(self, user, content):
        rows = []
        separator = ','
        timestamp = parseDateTime()
        call = self._getCall('mergeItem')
        call.setString(1, user.Id)
        call.setString(2, separator)
        call.setLong(3, 0)
        call.setTimestamp(4, timestamp)
        enumerator = user.Provider.getFolderContent(user.Request, content)
        while enumerator.hasMoreElements():
            item = enumerator.nextElement()
            itemid = user.Provider.getItemId(item)
            parents = user.Provider.getItemParent(item, user.RootId)
            rows.append(self._mergeItem(call, user.Provider, item, itemid, parents, separator, timestamp))
            call.addBatch()
        if enumerator.RowCount > 0:
            call.executeBatch()
        call.close()
        return all(rows)

    def getChildren(self, userid, itemid, url, mode):
        #TODO: Can't have a ResultSet of type SCROLL_INSENSITIVE with a Procedure,
        #TODO: as a workaround we use a simple quey...
        select = self._getCall('getChildren')
        scroll = 'com.sun.star.sdbc.ResultSetType.SCROLL_INSENSITIVE'
        select.ResultSetType = uno.getConstantByName(scroll)
        # OpenOffice / LibreOffice Columns:
        #    ['Title', 'Size', 'DateModified', 'DateCreated', 'IsFolder', 'TargetURL', 'IsHidden',
        #    'IsVolume', 'IsRemote', 'IsRemoveable', 'IsFloppy', 'IsCompactDisc']
        # "TargetURL" is done by:
        #    CONCAT(identifier.getContentIdentifier(), Uri) for File and Foder
        select.setString(1, url)
        select.setString(2, userid)
        select.setString(3, itemid)
        select.setShort(4, mode)
        return select

    def updateLoaded(self, userid, itemid, value, default):
        update = self._getCall('updateLoaded')
        update.setLong(1, value)
        update.setString(2, itemid)
        update.executeUpdate()
        update.close()
        return value

    def getIdentifier(self, userid, rootid, uripath):
        call = self._getCall('getIdentifier')
        call.setString(1, userid)
        call.setString(2, rootid)
        call.setString(3, uripath)
        call.setString(4, '/')
        call.execute()
        itemid = call.getString(5)
        if call.wasNull():
            itemid = None
        parentid = call.getString(6)
        if call.wasNull():
            parentid = None
        path = call.getString(7)
        call.close()
        return itemid, parentid, path

    def getNewIdentifier(self, userid):
        identifier = ''
        select = self._getCall('getNewIdentifier')
        select.setString(1, userid)
        result = select.executeQuery()
        if result.next():
            identifier = result.getString(1)
        select.close()
        return identifier

    def deleteNewIdentifier(self, userid, itemid):
        call = self._getCall('deleteNewIdentifier')
        call.setString(1, userid)
        call.setString(2, itemid)
        call.executeUpdate()
        call.close()

    def updateContent(self, userid, itemid, property, value):
        updated = False
        timestamp = parseDateTime()
        if property == 'Title':
            update = self._getCall('updateTitle')
            update.setTimestamp(1, timestamp)
            update.setString(2, value)
            update.setString(3, itemid)
            updated = update.execute() == 0
            update.close()
        elif property == 'Size':
            update = self._getCall('updateSize')
            # The Size of the file is not sufficient to detect a 'Save' of the file,
            # It can be modified and have the same Size...
            # For this we temporarily update the Size to 0
            update.setTimestamp(1, timestamp)
            update.setLong(2, 0)
            update.setString(3, itemid)
            update.execute()
            update.setLong(2, value)
            update.setString(3, itemid)
            updated = update.execute() == 0
            update.close()
        elif property == 'Trashed':
            update = self._getCall('updateTrashed')
            update.setTimestamp(1, timestamp)
            update.setBoolean(2, value)
            update.setString(3, itemid)
            updated = update.execute() == 0
            update.close()
        if updated:
            # TODO: I cannot use a procedure performing the two UPDATE 
            # TODO: without the system versioning malfunctioning...
            # TODO: As a workaround I use two successive UPDATE queries
            update = self._getCall('updateCapabilities')
            update.setTimestamp(1, timestamp)
            update.setString(2, userid)
            update.setString(3, itemid)
            update.execute()
            update.close()
            self.sync.set()

    def insertNewContent(self, userid, itemid, parentid, content, timestamp):
        call = self._getCall('insertItem')
        call.setString(1, userid)
        call.setString(2, ',')
        call.setLong(3, 1)
        call.setTimestamp(4, timestamp)
        call.setString(5, itemid)
        call.setString(6, content.getValue("Title"))
        call.setTimestamp(7, content.getValue('DateCreated'))
        call.setTimestamp(8, content.getValue('DateModified'))
        call.setString(9, content.getValue('MediaType'))
        call.setLong(10, content.getValue('Size'))
        call.setBoolean(11, content.getValue('Trashed'))
        call.setBoolean(12, content.getValue('CanAddChild'))
        call.setBoolean(13, content.getValue('CanRename'))
        call.setBoolean(14, content.getValue('IsReadOnly'))
        call.setBoolean(15, content.getValue('IsVersionable'))
        call.setString(16, parentid)
        result = call.execute() == 0
        call.close()
        if result:
            # Start Replicator for pushing changes…
            self.sync.set()
        return result

    def countChildTitle(self, userid, parentid, title):
        count = 1
        call = self._getCall('countChildTitle')
        call.setString(1, userid)
        call.setString(2, parentid)
        call.setString(3, title)
        result = call.executeQuery()
        if result.next():
            count = result.getLong(1)
        call.close()
        return count

    def getChildId(self, userid, parentid, title):
        id = None
        call = self._getCall('getChildId')
        call.setString(1, userid)
        call.setString(2, parentid)
        call.setString(3, title)
        result = call.executeQuery()
        if result.next():
            id = result.getString(1)
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
    def getFirstPullCall(self, userid, separator, loaded, timestamp):
        call = self._getCall('mergeItem')
        call.setString(1, userid)
        call.setString(2, separator)
        call.setInt(3, loaded)
        call.setTimestamp(4, timestamp)
        return call

    # First pull procedure: body of merge request
    def setFirstPullCall(self, call, provider, item, itemid, parents, separator, timestamp):
        row = self._mergeItem(call, provider, item, itemid, parents, separator, timestamp)
        call.addBatch()
        return row

    def updateUserTimeStamp(self, timestamp, userid=None):
        call = 'updateUsersTimeStamp' if userid is None else 'updateUserTimeStamp'
        update = self._getCall(call)
        update.setTimestamp(1, timestamp)
        if userid is not None:
            update.setString(2, userid)
        update.executeUpdate()
        update.close()

    def getUserTimeStamp(self, userid):
        select = self._getCall('getUserTimeStamp')
        select.setString(1, userid)
        result = select.executeQuery()
        if result.next():
            timestamp = result.getTimestamp(1)
        select.close()
        return timestamp

    def setSession(self, user=g_dba):
        query = getSqlQuery(self.ctx, 'setSession', user)
        self._statement.execute(query)

    # Procedure to retrieve all the UPDATE AND INSERT in the 'Capabilities' table
    def getPushItems(self, start, end):
        items = []
        select = self._getCall('getSyncItems')
        select.setTimestamp(1, end)
        select.setTimestamp(2, start)
        select.setTimestamp(3, end)
        select.setTimestamp(4, start)
        select.setTimestamp(5, end)
        select.setTimestamp(6, start)
        select.setTimestamp(7, end)
        select.setTimestamp(8, end)
        select.setTimestamp(9, start)
        result = select.executeQuery()
        while result.next():
            items.append(getKeyMapFromResult(result))
        select.close()
        return items

    def updateItemId(self, provider, itemid, response):
        newid = provider.getResponseId(response, itemid)
        if newid != itemid:
            update = self._getCall('updateItemId')
            update.setString(1, newid)
            update.setString(2, itemid)
            row = update.executeUpdate()
            msg = "execute UPDATE Items - Old ItemId: %s - New ItemId: %s - RowCount: %s" % (itemid, newid, row)
            logMessage(self.ctx, INFO, msg, "DataBase", "updateItemId")
            update.close()

# Procedures called internally
    def _mergeItem(self, call, provider, item, id, parents, separator, timestamp):
        call.setString(5, id)
        call.setString(6, provider.getItemTitle(item))
        call.setTimestamp(7, provider.getItemCreated(item, timestamp))
        call.setTimestamp(8, provider.getItemModified(item, timestamp))
        call.setString(9, provider.getItemMediaType(item))
        call.setLong(10, provider.getItemSize(item))
        call.setBoolean(11, provider.getItemTrashed(item))
        call.setBoolean(12, provider.getItemCanAddChild(item))
        call.setBoolean(13, provider.getItemCanRename(item))
        call.setBoolean(14, provider.getItemIsReadOnly(item))
        call.setBoolean(15, provider.getItemIsVersionable(item))
        call.setString(16, separator.join(parents))
        return 1

    def _mergeRoot(self, provider, userid, rootid, rootname, root, timestamp):
        call = self._getCall('mergeItem')
        call.setString(1, userid)
        call.setString(2, ',')
        call.setLong(3, 0)
        call.setTimestamp(4, timestamp)
        call.setString(5, rootid)
        call.setString(6, rootname)
        call.setTimestamp(7, provider.getRootCreated(root, timestamp))
        call.setTimestamp(8, provider.getRootModified(root, timestamp))
        call.setString(9, provider.getRootMediaType(root))
        call.setLong(10, provider.getRootSize(root))
        call.setBoolean(11, provider.getRootTrashed(root))
        call.setBoolean(12, provider.getRootCanAddChild(root))
        call.setBoolean(13, provider.getRootCanRename(root))
        call.setBoolean(14, provider.getRootIsReadOnly(root))
        call.setBoolean(15, provider.getRootIsVersionable(root))
        call.setString(16, '')
        call.executeUpdate()
        call.close()

    def _getCall(self, name, format=None):
        return getDataSourceCall(self.ctx, self.Connection, name, format)

    def _getPreparedCall(self, name):
        # TODO: cannot use: call = self.Connection.prepareCommand(name, QUERY)
        # TODO: it trow a: java.lang.IncompatibleClassChangeError
        #query = self.Connection.getQueries().getByName(name).Command
        #self._CallsPool[name] = self.Connection.prepareCall(query)
        return self.Connection.prepareCommand(name, QUERY)

#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-24 https://prrvchr.github.io                                  ║
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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.sdb.CommandType import QUERY

from com.sun.star.sdbc.DataType import VARCHAR

from io.github.prrvchr.css.util import DateTimeWithTimezone

from .dbtool import Array

from .unotool import checkVersion
from .unotool import generateUuid
from .unotool import getSimpleFile

from .dbqueries import getSqlQuery

from .dbtool import createUser
from .dbtool import currentDateTimeInTZ
from .dbtool import currentUnoDateTime
from .dbtool import getDataSourceCall
from .dbtool import getDataFromResult

from .dbinit import createDataBase
from .dbinit import getDataBaseConnection

from .dbconfig import g_role
from .dbconfig import g_version

import os
import traceback


class DataBase():
    def __init__(self, ctx, logger, url, user='', pwd=''):
        self._ctx = ctx
        cls, mtd = 'DataBase', '__init__'
        logger.logprb(INFO, cls, mtd, 401)
        self._url = url
        odb = url + '.odb'
        new = not getSimpleFile(ctx).exists(odb)
        connection = getDataBaseConnection(ctx, url, user, pwd, new)
        version = connection.getMetaData().getDriverVersion()
        if new:
            if checkVersion(version, g_version):
                logger.logprb(INFO, cls, mtd, 402, version)
                createDataBase(ctx, connection, odb)
                logger.logprb(INFO, cls, mtd, 403)
            else:
                logger.logprb(SEVERE, cls, mtd, 404, version, g_version)
        self._statement = connection.createStatement()
        self._version = version
        self._logger = logger
        logger.logprb(INFO, cls, mtd, 405)

    @property
    def Url(self):
        return self._url
    @property
    def Version(self):
        return self._version

    @property
    def Connection(self):
        return self._statement.getConnection()

    def isUptoDate(self):
        return checkVersion(self._version, g_version)

# Procedures called by the DataSource
    def addCloseListener(self, listener):
        self.Connection.getParent().DatabaseDocument.addCloseListener(listener)

    def shutdownDataBase(self, compact=False):
        if compact:
            query = getSqlQuery(self._ctx, 'shutdownCompact')
            self._statement.execute(query)
        #else:
        #    query = getSqlQuery(self._ctx, 'shutdown')
        #self._statement.execute(query)
        self.dispose()

    def dispose(self):
        self._statement.close()

    def createUser(self, name, password):
        return createUser(self.Connection, name, password, g_role)

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

    def insertUser(self, user):
        data = None
        shareid = generateUuid()
        timestamp = currentDateTimeInTZ()
        call = self._getCall('insertUser')
        call.setString(1, user.get('Id'))
        call.setString(2, user.get('Name'))
        call.setString(3, user.get('DisplayName'))
        call.setString(4, user.get('RootId'))
        call.setString(5, shareid)
        call.setTimestamp(6, user.get('DateCreated'))
        call.setTimestamp(7, user.get('DateModified'))
        call.setObject(8, timestamp)
        result = call.executeQuery() 
        if result.next():
            data = getDataFromResult(result)
        result.close()
        call.close()
        return data

# Procedures called by the Replicator
    # XXX: Replicator uses its own database connection
    def getMetaData(self, userid, rootid, itemid):
        if itemid == rootid:
            data = user.getRootMetaData()
        else:
            data = self.getItem(userid, itemid, False)
        data['AtRoot'] = data.get('ParentId') == rootid
        return data

    def updateNewItemId(self, userid, oldid, newid, created, modified):
        call = self._getCall('updateNewItemId')
        call.setString(1, userid)
        call.setString(2, oldid)
        call.setString(3, newid)
        call.setTimestamp(4, created)
        call.setTimestamp(5, modified)
        call.executeUpdate()
        call.close()
        return newid

# Procedures called by the Content
    def getItem(self, userid, uri, ispath=True):
        item = None
        call = self._getCall('getItem')
        call.setString(1, userid)
        call.setString(2, uri)
        call.setBoolean(3, ispath)
        result = call.executeQuery()
        if result.next():
            item = getDataFromResult(result)
        result.close()
        call.close()
        return item

    def getChildren(self, userid, scheme, path, properties, mode):
        #TODO: Can't have a ResultSet of type SCROLL_INSENSITIVE with a Procedure,
        #TODO: as a workaround we use a simple quey...
        call = self._getCall('getChildren', self._getChildrenformat(properties))
        scroll = uno.getConstantByName('com.sun.star.sdbc.ResultSetType.SCROLL_INSENSITIVE')
        call.ResultSetType = scroll
        # OpenOffice / LibreOffice Columns:
        #    ['Title', 'Size', 'DateModified', 'DateCreated', 'IsFolder', 'TargetURL', 'IsHidden',
        #    'IsVolume', 'IsRemote', 'IsRemoveable', 'IsFloppy', 'IsCompactDisc']
        # "TargetURL" is done by: the given scheme + the database view Path + Title
        i = 1
        if 'TargetURL' in (property.Name for property in properties):
            call.setString(i, scheme)
            i += 1
        call.setString(i, userid)
        call.setString(i + 1, path)
        call.setShort(i + 2, mode + 1)
        return call

    def _getChildrenformat(self, properties):
        return {'Children': 'PUBLIC.PUBLIC."Children"',
                'Columns': ', '.join(self._getChildrenColumns(properties))}

    def _getChildrenColumns(self, properties):
        columns = {'Title':         'C."Title"',
                   'Size':          'C."Size"',
                   'DateModified':  'C."DateModified"',
                   'DateCreated':   'C."DateCreated"',
                   'IsFolder':      'C."IsFolder"',
                   'TargetURL':     '? || C."Path" || C."Title"',
                   'IsHidden':      'FALSE',
                   'IsVolume':      'FALSE',
                   'IsRemote':      'C."ConnectionMode" < 0',
                   'IsRemoveable':  'FALSE',
                   'IsFloppy':      'FALSE',
                   'IsCompactDisc': 'FALSE'}
        return ('%s AS "%s"' % (columns[p.Name], p.Name) for p in properties if p.Name in columns)

    def updateConnectionMode(self, userid, itemid, value):
        update = self._getCall('updateConnectionMode')
        update.setShort(1, value)
        update.setString(2, userid)
        update.setString(3, itemid)
        update.executeUpdate()
        update.close()
        return value

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
        call = self._getCall('deleteNewIdentifier')
        call.setString(1, userid)
        call.setString(2, itemid)
        call.executeUpdate()
        call.close()

    def updateContent(self, userid, itemid, property, value):
        updated = clear = False
        timestamp = currentDateTimeInTZ()
        if property == 'Name':
            update = self._getCall('updateName')
            update.setObject(1, timestamp)
            update.setString(2, value)
            update.setString(3, userid)
            update.setString(4, itemid)
            updated = update.execute() == 0
            update.close()
            clear = True
        elif property == 'Size':
            update = self._getCall('updateSize')
            # FIXME: If we update the Size, we need to update the DateModified too...
            update.setObject(1, timestamp)
            update.setLong(2, value)
            update.setTimestamp(3, currentUnoDateTime())
            update.setString(4, userid)
            update.setString(5, itemid)
            updated = update.execute() == 0
            update.close()
        elif property == 'Trashed':
            update = self._getCall('updateTrashed')
            update.setObject(1, timestamp)
            update.setBoolean(2, value)
            update.setString(3, userid)
            update.setString(4, itemid)
            updated = update.execute() == 0
            update.close()
        return updated, clear

    def insertNewContent(self, userid, item, timestamp):
        inserted = False
        call = self._getCall('insertItem')
        call.setString(1, userid)
        call.setLong(2, 1)
        call.setObject(3, timestamp)
        call.setString(4, item.get("Id"))
        call.setString(5, item.get("Name"))
        call.setTimestamp(6, item.get('DateCreated'))
        call.setTimestamp(7, item.get('DateModified'))
        call.setString(8, item.get('MediaType'))
        call.setLong(9, item.get('Size'))
        call.setString(10, item.get('Link'))
        call.setBoolean(11, item.get('Trashed'))
        call.setBoolean(12, item.get('CanAddChild'))
        call.setBoolean(13, item.get('CanRename'))
        call.setBoolean(14, item.get('IsReadOnly'))
        call.setBoolean(15, item.get('IsVersionable'))
        call.setString(16, item.get("ParentId"))
        result = call.executeQuery()
        if result.next():
            item['Name'] = result.getString(1)
            item['Title'] = result.getString(2)
            item['Path'] = result.getString(3)
            inserted = True
        result.close()
        call.close()
        return inserted

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

    def getChildId(self, parentid, path, title):
        itemid = None
        call = self._getCall('getChildId')
        call.setString(1, parentid)
        call.setString(2, path)
        call.setString(3, title)
        result = call.executeQuery()
        if result.next():
            itemid = result.getString(1)
        result.close()
        call.close()
        return itemid

# Procedures called by the Replicator
    # Synchronization pull token update procedure
    def updateToken(self, userid, token):
        update = self._getCall('updateToken')
        update.setString(1, token)
        update.setString(2, userid)
        update.executeUpdate()
        update.close()

    def updateTimeStamp(self, userid, timestamp):
        update = self._getCall('updateTimeStamp')
        update.setObject(1, timestamp)
        update.setString(2, userid)
        update.executeUpdate()
        update.close()

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
        return count

    # Pull procedure
    def mergeItem(self, userid, parentid, datetime, item, mode=1):
        call = self._getMergeItemCall(userid, parentid, datetime, mode)
        if self._mergeItem(call, item):
            call.executeUpdate()
        call.close()
        return 1

    def mergeItems(self, userid, parentid, datetime, items, mode=1):
        count = 0
        call = self._getMergeItemCall(userid, parentid, datetime, mode)
        for item in items:
            count += self._mergeItem(call, item)
            call.addBatch()
            yield item
        if count:
            call.executeBatch()
        call.close()

    # Procedure to retrieve all the UPDATE AND INSERT in the 'Capabilities' table
    def getPushItems(self, userid, start, end):
        select = self._getCall('getPushItems')
        select.setString(1, userid)
        select.setObject(2, start)
        select.setObject(3, end)
        result = select.executeQuery()
        while result.next():
            yield getDataFromResult(result)
        result.close()
        select.close()

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

    def updatePushItems(self, userid, itemids):
        call = self._getCall('updatePushItems')
        call.setString(1, userid)
        call.setArray(2, Array('VARCHAR', itemids))
        call.execute()
        timestamp = call.getObject(3, None)
        if call.wasNull():
            timestamp = None
        call.close()
        return timestamp

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

    def updateItemId(self, userid, newid, oldid):
        print("DataBase.updateItemId () NewId: %s - OldId: %s" % (newid, oldid))
        update = self._getCall('updateItemId')
        update.setString(1, newid)
        update.setString(2, userid)
        update.setString(3, oldid)
        update.executeUpdate()
        update.close()

# Procedures called internally
    def _getMergeItemCall(self, userid, parentid, datetime, mode):
        call = self._getCall('mergeItem')
        call.setString(1, userid)
        call.setString(2, parentid)
        call.setObject(3, datetime)
        call.setInt(4, mode)
        return call

    def _mergeItem(self, call, item):
        call.setString(5, item.get('Id'))
        call.setString(6, item.get('Name'))
        call.setTimestamp(7, item.get('DateCreated'))
        call.setTimestamp(8, item.get('DateModified'))
        call.setString(9, item.get('MediaType'))
        size = item.get('Size')
        if os.name == 'nt':
            mx = 2 ** 32 / 2 -1
            if size > mx:
                size = min(size, mx)
                self._logger.logprb(SEVERE, 'DataBase', '_mergeItem', 451, size, item.get('Size'))
        call.setLong(10, size)
        call.setString(11, item.get('Link'))
        call.setBoolean(12, item.get('Trashed'))
        call.setBoolean(13, item.get('CanAddChild'))
        call.setBoolean(14, item.get('CanRename'))
        call.setBoolean(15, item.get('IsReadOnly'))
        call.setBoolean(16, item.get('IsVersionable'))
        call.setArray(17, Array('VARCHAR', item.get('Parents')))
        path = item.get('Path')
        call.setNull(18, VARCHAR) if path is None else call.setString(18, path)
        return 1

    def _getCall(self, name, format=None):
        return getDataSourceCall(self._ctx, self.Connection, name, format)

    def _getPreparedCall(self, name):
        # TODO: cannot use: call = self.Connection.prepareCommand(name, QUERY)
        # TODO: it trow a: java.lang.IncompatibleClassChangeError
        #query = self.Connection.getQueries().getByName(name).Command
        #self._CallsPool[name] = self.Connection.prepareCall(query)
        return self.Connection.prepareCommand(name, QUERY)


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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.sdb.CommandType import QUERY

from com.sun.star.sdbc.DataType import VARCHAR

from io.github.prrvchr.css.util import DateTimeWithTimezone

from .dbtool import Array

from .unotool import checkVersion
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
        self._logger = logger
        self._url = url
        odb = url + '.odb'
        new = not getSimpleFile(ctx).exists(odb)
        connection = getDataBaseConnection(ctx, url, user, pwd, new)
        version = connection.getMetaData().getDriverVersion()
        if new and checkVersion(version, g_version):
            createDataBase(ctx, logger, connection, odb, version)
        self._statement = connection.createStatement()
        self._version = version
        self._logger.logprb(INFO, 'DataBase', '__init__()', 401)

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
        return createUser(self.Connection, name, password, g_role)

    def createSharedFolder(self, user, itemid, folder, media, timestamp, datetime):
        call = self._getCall('insertSharedFolder')
        call.setString(1, user.Id)
        call.setString(2, user.RootId)
        call.setString(3, itemid)
        call.setString(4, folder)
        call.setString(5, media)
        call.setBoolean(6, False)
        call.setBoolean(7, False)
        call.setBoolean(8, False)
        call.setBoolean(9, False)
        call.setTimestamp(10, timestamp)
        call.setTimestamp(11, timestamp)
        call.setObject(12, datetime)
        call.executeUpdate()
        call.close()

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
        call.setTimestamp(5, root[1])
        call.setTimestamp(6, root[2])
        call.setObject(7, timestamp)
        result = call.executeQuery() 
        if result.next():
            data = getDataFromResult(result)
        result.close()
        call.close()
        return data

# Procedures called by the Replicator
    # XXX: Replicator uses its own database connection
    def getMetaData(self, user, item):
        rootid = user.RootId
        itemid = item.get('Id')
        if item == rootid:
            data = user.getRootMetaData()
        else:
            data = self.getItem(user.Id, itemid, False)
        data['AtRoot'] = data.get('ParentId') == rootid
        return data

    def updateNewItemId(self, oldid, newid, created, modified):
        call = self._getCall('updateNewItemId')
        call.setString(1, oldid)
        call.setString(2, newid)
        call.setTimestamp(3, created)
        call.setTimestamp(4, modified)
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
        call.setShort(i + 2, mode)
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
                   'IsRemote':      'FALSE',
                   'IsRemoveable':  'FALSE',
                   'IsFloppy':      'FALSE',
                   'IsCompactDisc': 'FALSE'}
        return ('%s AS "%s"' % (columns[p.Name], p.Name) for p in properties if p.Name in columns)

    def updateConnectionMode(self, userid, itemid, value):
        update = self._getCall('updateConnectionMode')
        update.setShort(1, value)
        update.setString(2, itemid)
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
        print("DataBase.deleteNewIdentifier() NewID: %s" % itemid)
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
            update.setString(3, itemid)
            updated = update.execute() == 0
            update.close()
            clear = True
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
        return updated, clear

    def getNewTitle(self, title, parentid):
        call = self._getCall('getNewTitle')
        call.setString(1, title)
        call.setString(2, parentid)
        call.execute()
        newtitle = call.getString(3)
        call.close()
        return newtitle

    def insertNewContent(self, userid, item, timestamp):
        try:
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
            print("DataBase.insertNewContent() 1")
            if result.next():
                item['Name'] = result.getString(1)
                item['Title'] = result.getString(2)
                item['Path'] = result.getString(3)
                inserted = True
            result.close()
            call.close()
            print("DataBase.insertNewContent() 2 Inserted: %s" % inserted)
            return inserted
        except Exception as e:
            print("ERROR %s" % traceback.format_exc())

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
        return count

    # Pull procedure
    def pullItems(self, iterator, userid, timestamp, mode=1):
        count = 0
        call1 = self._getCall('mergeItem')
        call2 = self._getCall('mergeParent')
        call1.setString(1, userid)
        call2.setString(1, userid)
        call1.setInt(2, mode)
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

    def updateItemId(self, newid, oldid):
        print("DataBase.updateItemId () NewId: %s - OldId: %s" % (newid, oldid))
        update = self._getCall('updateItemId')
        update.setString(1, newid)
        update.setString(2, oldid)
        update.executeUpdate()
        update.close()

# Procedures called internally
    def _mergeItem(self, call1, call2, item, timestamp):
        itemid = item[0]
        call1.setString(4, itemid)
        call1.setString(5, item[1])
        call1.setTimestamp(6, item[2])
        call1.setTimestamp(7, item[3])
        call1.setString(8, item[4])
        size = item[5]
        if os.name == 'nt':
            mx = 2 ** 32 / 2 -1
            if size > mx:
                size = min(size, mx)
                self._logger.logprb(SEVERE, 'DataBase', '_mergeItem()', 402, size, item[5])
        call1.setLong(9, size)
        call1.setString(10, item[6])
        call1.setBoolean(11, item[7])
        call1.setBoolean(12, item[8])
        call1.setBoolean(13, item[9])
        call1.setBoolean(14, item[10])
        call1.setBoolean(15, item[11])
        call1.addBatch()
        self._mergeParent(call2, item, itemid, timestamp)
        return 1

    def _mergeParent(self, call, item, itemid, timestamp):
        call.setString(2, itemid)
        call.setArray(3, Array('VARCHAR', item[12]))
        path = item[13]
        if path is None:
            call.setNull(4, VARCHAR)
        else:
            call.setString(4, path)
        call.setObject(5, timestamp)
        call.addBatch()

    def _getCall(self, name, format=None):
        return getDataSourceCall(self._ctx, self.Connection, name, format)

    def _getPreparedCall(self, name):
        # TODO: cannot use: call = self.Connection.prepareCommand(name, QUERY)
        # TODO: it trow a: java.lang.IncompatibleClassChangeError
        #query = self.Connection.getQueries().getByName(name).Command
        #self._CallsPool[name] = self.Connection.prepareCall(query)
        return self.Connection.prepareCommand(name, QUERY)


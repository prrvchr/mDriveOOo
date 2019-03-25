#!
# -*- coding: utf_8 -*-

from .drivelib import OutputStream

from .drivetools import updateItem
from .drivetools import getUploadLocation
from .drivetools import parseDateTime
from .drivetools import unparseDateTime

from .drivetools import g_plugin
from .drivetools import g_folder

from .drivetools import RETRIEVED
from .drivetools import CREATED
from .drivetools import FOLDER
from .drivetools import FILE
from .drivetools import RENAMED
from .drivetools import REWRITED
from .drivetools import TRASHED


def selectUser(connection, username):
    user = None
    # selectUser(IN USERNAME VARCHAR(100))
    select = connection.prepareCall('CALL "selectUser"(?)')
    select.setString(1, username)
    result = select.executeQuery()
    if result.next():
        user = _getItemFromResult(result)
    select.close()
    return user

def selectItem(connection, userid, id):
    item = None
    data = ('Name', 'DateCreated', 'DateModified', 'MimeType',
            'Size', 'Trashed', 'Loaded')
    # selectItem(IN USERID VARCHAR(100),IN ID VARCHAR(100))
    select = connection.prepareCall('CALL "selectItem"(?, ?)')
    select.setString(1, userid)
    select.setString(2, id)
    result = select.executeQuery()
    if result.next():
        item = _getItemFromResult(result, data)
    select.close()
    return item

def mergeJsonUser(connection, user, data):
    root = None
    merge = connection.prepareCall('CALL "mergeJsonUser"(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
    merge.setString(1, user.get('id'))
    merge.setString(2, user.get('userPrincipalName'))
    merge.setString(3, user.get('displayName'))
    index = _setJsonData(merge, data, unparseDateTime(), 4)
    result = merge.executeQuery()
    if result.next():
        root = _getItemFromResult(result)
    merge.close()
    return root

def insertJsonItem(connection, userid, rootid, data):
    item = None
    fields = ('Name', 'DateCreated', 'DateModified', 'MimeType',
              'Size', 'Trashed', 'Loaded')
    insert = connection.prepareCall('CALL "insertJsonItem"(?, ?, ?, ?, ?, ?, ?, ?, ?)')
    insert.setString(1, userid)
    index = _setJsonData(insert, data, unparseDateTime(), 2)
    insert.setString(index, data.get('parentReference', {}).get('id', rootid))
    result = insert.executeQuery()
    if result.next():
        item = _getItemFromResult(result, fields)
    insert.close()
    return item

def mergeJsonItemCall(connection, userid):
    merge = connection.prepareCall('CALL "mergeJsonItem"(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
    merge.setString(1, userid)
    return merge, 2

def mergeJsonItem(merge, data, rootid, index=1):
    index = _setJsonData(merge, data, unparseDateTime(), index)
    merge.setString(index, data.get('parentReference', {}).get('id', rootid))
    merge.execute()
    return merge.getLong(index +1)

def doSync(ctx, connection, session, path, userid):
    items = []
    select = connection.prepareCall('CALL "selectSync"(?, ?)')
    select.setString(1, userid)
    select.setLong(2, RETRIEVED)
    result = select.executeQuery()
    while result.next():
        item = _getItemFromResult(result, None, None)
        id = _syncItem(ctx, connection, session, path, userid, item)
        if id is not None:
            _updateSync(connection, userid, id)
            print("items.doSync(): all -> Ok")
        else:
            print("items.doSync(): all -> Error")
    select.close()
    return all(items)

def _syncItem(ctx, connection, session, path, userid, item):
    result = False
    id = item.get('id')
    mode = item.get('mode')
    parent = item.get('parents')
    name = item.get('name')
    data = None
    if mode & CREATED:
        data = {'item': {'@microsoft.graph.conflictBehavior': 'replace'}}
        if mode & FOLDER:
            update = _getUpdateItemId(connection, userid, id)
            newid = updateItem(session, id, parent, data, True)
            _updateItemId(update, newid)
        if mode & FILE:
            update = _getUpdateItemId(connection, userid, id)
            _uploadItem(ctx, session, path, id, parent, name, data, True, update)
    else:
        if mode & REWRITED:
            data = {'item': {'@microsoft.graph.conflictBehavior': 'replace',
                             'name': name}}
            result = _uploadItem(ctx, session, path, id, parent, name, data, False, None)
        if mode & RENAMED:
            data = {'name': name}
            result = updateItem(session, id, parent, data, False)
    if mode & TRASHED:
        result = updateItem(session, id, parent, data, False)
    return result

def _updateSync(connection, userid, id):
    update = connection.prepareCall('CALL "updateSync"(?, ?, ?, ?)')
    update.setString(1, userid)
    update.setString(2, id)
    update.setLong(3, RETRIEVED)
    update.execute()
    r = update.getLong(4)
    update.close()

def _getUpdateItemId(connection, userid, oldid):
    update = connection.prepareCall('CALL "updateItemId"(?, ?, ?, ?, ?)')
    update.setString(1, userid)
    update.setString(2, oldid)
    update.setString(3, RETRIEVED)
    return update

def _updateItemId(update, newid):
    result = False
    update.setString(4, newid)
    update.execute()
    result = update.getString(5)
    update.close()
    return result

def _uploadItem(ctx, session, path, id, parent, name, data, new, update):
    size, stream = _getInputStream(ctx, path, id)
    if size:
        location = getUploadLocation(session, id, parent, name, size, data, new)
        if location is not None:
            pump = ctx.ServiceManager.createInstance('com.sun.star.io.Pump')
            pump.setInputStream(stream)
            pump.setOutputStream(OutputStream(session, location, size, update))
            pump.start()
            return id
    return False

def _getInputStream(ctx, path, id):
    sf = ctx.ServiceManager.createInstance('com.sun.star.ucb.SimpleFileAccess')
    url = '%s/%s' % (path, id)
    if sf.exists(url):
        return sf.getSize(url), sf.openFileRead(url)
    return 0, None

def _setJsonData(call, data, timestamp, index=1):
    # IN Call Parameters for: mergeJsonUser(), insertJsonItem(), mergeJsonItem()
    # Id, Name, DateCreated, DateModified, MimeType, Size, CanAddChild, CanRename, IsReadOnly, IsVersionable, ParentsId
    # OUT Call Parameters for: mergeJsonItem()
    # RowCount
    call.setString(index, data.get('id'))
    index += 1
    call.setString(index, data.get('name'))
    index += 1
    call.setTimestamp(index, parseDateTime(data.get('createdDateTime', timestamp)))
    index += 1
    call.setTimestamp(index, parseDateTime(data.get('lastModifiedDateTime', timestamp)))
    index += 1
    call.setString(index, data.get('file', {}).get('mimeType', g_folder))
    index += 1
    call.setLong(index, int(data.get('size', 0)))
    index += 1
    call.setBoolean(index, data.get('trashed', False))
    index += 1
    return index

def _getItemFromResult(result, data=None, transform=None):
    item = {} if data is None else {'Data':{k: None for k in data}}
    for index in range(1, result.MetaData.ColumnCount +1):
        dbtype = result.MetaData.getColumnTypeName(index)
        name = result.MetaData.getColumnName(index)
        if dbtype == 'VARCHAR':
            value = result.getString(index)
        elif dbtype == 'TIMESTAMP':
            value = result.getTimestamp(index)
        elif dbtype == 'BOOLEAN':
            value = result.getBoolean(index)
        elif dbtype == 'BIGINT' or dbtype == 'SMALLINT':
            value = result.getLong(index)
        else:
            continue
        if transform is not None and name in transform:
            print("items._getItemFromResult() 1: %s: %s" % (name, value))
            value = transform[name](value)
            print("items._getItemFromResult() 2: %s: %s" % (name, value))
        if value is None or result.wasNull():
            continue
        if data is not None and name in data:
            item['Data'][name] = value
        else:
            item[name] = value
    return item

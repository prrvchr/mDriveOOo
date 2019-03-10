#!
# -*- coding: utf_8 -*-

from .drivelib import OutputStream

from .drivetools import updateItem
from .drivetools import getResourceLocation
from .drivetools import getUploadLocation
from .drivetools import parseDateTime
from .drivetools import unparseDateTime

from .drivetools import RETRIEVED
from .drivetools import CREATED
from .drivetools import FOLDER
from .drivetools import FILE
from .drivetools import RENAMED
from .drivetools import REWRITED
from .drivetools import TRASHED


def selectUser(connection, username, mode):
    user, select = None, connection.prepareCall('CALL "selectUser"(?, ?)')
    # selectUser(IN USERNAME VARCHAR(100),IN MODE SMALLINT)
    select.setString(1, username)
    select.setLong(2, mode)
    result = select.executeQuery()
    if result.next():
        user = _getItemFromResult(result)
    select.close()
    return user

def selectItem(connection, userid, id):
    item = None
    data = ('Name', 'DateCreated', 'DateModified', 'MimeType', 'Size', 'Trashed',
            'CanAddChild', 'CanRename', 'IsReadOnly', 'IsVersionable', 'Loaded')
    select = connection.prepareCall('CALL "selectItem"(?, ?)')
    # selectItem(IN USERID VARCHAR(100),IN ID VARCHAR(100))
    select.setString(1, userid)
    select.setString(2, id)
    result = select.executeQuery()
    if result.next():
        item = _getItemFromResult(result, data)
    select.close()
    return item

def mergeJsonUser(connection, user, data, mode):
    root = None
    merge = connection.prepareCall('CALL "mergeJsonUser"(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
    merge.setString(1, user.get('permissionId'))
    merge.setString(2, user.get('emailAddress'))
    merge.setString(3, user.get('displayName'))
    index = _setJsonData(merge, data, unparseDateTime(), 4)
    merge.setLong(index, mode)
    result = merge.executeQuery()
    if result.next():
        root = _getItemFromResult(result)
    merge.close()
    return root

def insertJsonItem(connection, userid, data):
    item = None
    fields = ('Name', 'DateCreated', 'DateModified', 'MimeType', 'Size', 'Trashed',
              'CanAddChild', 'CanRename', 'IsReadOnly', 'IsVersionable', 'Loaded')
    insert = connection.prepareCall('CALL "insertJsonItem"(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
    insert.setString(1, userid)
    index = _setJsonData(insert, data, unparseDateTime(), 2)
    parents = ','.join(data.get('parents', ()))
    insert.setString(index, parents)
    result = insert.executeQuery()
    if result.next():
        item = _getItemFromResult(result, fields)
    insert.close()
    return item

def mergeJsonItemCall(connection, userid):
    merge = connection.prepareCall('CALL "mergeJsonItem"(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
    merge.setString(1, userid)
    return merge, 2

def mergeJsonItem(merge, data, index=1):
    index = _setJsonData(merge, data, unparseDateTime(), index)
    parents = ','.join(data.get('parents', ()))
    merge.setString(index, parents)
    merge.execute()
    return merge.getLong(index +1)

def doSync(ctx, scheme, connection, session, userid):
    items = []
    transform = {'parents': lambda value: value.split(',')}
    select = connection.prepareCall('CALL "selectSync"(?, ?)')
    select.setString(1, userid)
    select.setLong(2, RETRIEVED)
    result = select.executeQuery()
    while result.next():
        item = _getItemFromResult(result, None, transform)
        items.append(_syncItem(ctx, scheme, session, item))
    select.close()
    if items and all(items):
        update = connection.prepareCall('CALL "updateSync"(?, ?, ?, ?)')
        update.setString(1, userid)
        update.setString(2, ','.join(items))
        update.setLong(3, RETRIEVED)
        update.execute()
        r = update.getLong(4)
        print("items.doSync(): all -> Ok %s" % r)
    else:
        print("items.doSync(): all -> Error")
    return all(items)

def _syncItem(ctx, scheme, session, item):
    result = False
    id = item.get('id')
    mode = item.get('mode')
    data = None 
    if mode & CREATED:
        data = {'id': id,
                'parents': item.get('parents'),
                'name': item.get('name'),
                'mimeType': item.get('mimeType')}
        if mode & FOLDER:
            result = updateItem(session, id, data, True)
        if mode & FILE:
            mimetype = item.get('mimeType')
            result = _uploadItem(ctx, scheme, session, id, data, mimetype, True)
    else:
        if mode & REWRITED:
            mimetype = None if item.get('size') else item.get('mimeType')
            result = _uploadItem(ctx, scheme, session, id, data, mimetype, False)
        if mode & RENAMED:
            data = {'name': item.get('name')}
            result = updateItem(session, id, data, False)
    if mode & TRASHED:
        data = {'trashed': True}
        result = updateItem(session, id, data, False)
    return result

def _uploadItem(ctx, scheme, session, id, data, mimetype, new):
    size, stream = _getInputStream(ctx, scheme, id)
    if size: 
        location = getUploadLocation(session, id, data, mimetype, new, size)
        if location is not None:
            mimetype = None
            pump = ctx.ServiceManager.createInstance('com.sun.star.io.Pump')
            pump.setInputStream(stream)
            pump.setOutputStream(OutputStream(session, location, size))
            pump.start()
            return id
    return False

def _getInputStream(ctx, scheme, id):
    sf = ctx.ServiceManager.createInstance('com.sun.star.ucb.SimpleFileAccess')
    url = getResourceLocation(ctx, '%s/%s' % (scheme, id))
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
    call.setTimestamp(index, parseDateTime(data.get('createdTime', timestamp)))
    index += 1
    call.setTimestamp(index, parseDateTime(data.get('modifiedTime', timestamp)))
    index += 1
    call.setString(index, data.get('mimeType', 'application/octet-stream'))
    index += 1
    call.setLong(index, int(data.get('size', 0)))
    index += 1
    call.setBoolean(index, data.get('trashed', False))
    index += 1
    call.setBoolean(index, data.get('capabilities', {}).get('canAddChildren', False))
    index += 1
    call.setBoolean(index, data.get('capabilities', {}).get('canRename', False))
    index += 1
    call.setBoolean(index, not data.get('capabilities', {}).get('canEdit', False))
    index += 1
    call.setBoolean(index, data.get('capabilities', {}).get('canReadRevisions', False))
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

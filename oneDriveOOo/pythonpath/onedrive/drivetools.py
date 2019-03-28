#!
# -*- coding: utf_8 -*-

import uno

import datetime


g_scheme = 'vnd.microsoft-apps'    #vnd.microsoft-apps

g_plugin = 'com.gmail.prrvchr.extensions.oneDriveOOo'
g_provider = 'com.gmail.prrvchr.extensions.CloudUcpOOo'

g_host = 'graph.microsoft.com'
g_version = 'v1.0' # v1.0 or beta
g_url = 'https://%s/%s' % (g_host, g_version)

g_userfields = 'id,userPrincipalName,displayName'
g_drivefields = 'id,createdDateTime,lastModifiedDateTime,name'
g_itemfields = '%s,file,size,parentReference' % g_drivefields

g_capabilityfields = 'canEdit,canRename,canAddChildren,canReadRevisions'
#g_itemfields = 'id,parents,name,mimeType,size,createdTime,modifiedTime,trashed,capabilities(%s)' % g_capabilityfields
g_childfields = 'kind,nextPageToken,files(%s)' % g_itemfields

g_upload = 4194304
# Minimun chunk: 327680 (320Ko) no more uploads if less... (must be a multiple of 64Ko (and 32Ko))
g_chunk = 327680  # Http request maximum data size, must be a multiple of 'g_length'
g_length = 32768  # InputStream (Downloader) maximum 'Buffers' size
g_pages = 100
g_timeout = (15, 60)
g_IdentifierRange = (10, 50)

g_office = 'application/vnd.oasis.opendocument'
g_folder = 'application/vnd.microsoft-apps.folder'
g_link = 'application/vnd.microsoft-apps.link'
g_doc_map = {'application/vnd.microsoft-apps.document':     'application/vnd.oasis.opendocument.text',
             'application/vnd.microsoft-apps.spreadsheet':  'application/x-vnd.oasis.opendocument.spreadsheet',
             'application/vnd.microsoft-apps.presentation': 'application/vnd.oasis.opendocument.presentation',
             'application/vnd.microsoft-apps.drawing':      'application/pdf'}


def getUser(session):
    user, drives = None, None
    url = '%s/me' % g_url
    params = {'select': g_userfields}
    with session.get(url, params=params, timeout=g_timeout) as r:
        print("drivetools.getUser(): %s - %s" % (r.status_code, r.json()))
        if r.status_code == session.codes.ok:
            user = r.json()
            drives = getDrives(session)
    return user, drives

def getDrives(session):
    url = '%s/me/drive/root' % g_url
    params = {'select': g_drivefields}
    with session.get(url, params=params, timeout=g_timeout) as r:
        print("drivetools.getDrives():\n%s\n%s\n%s" % (r.status_code, r.json(), r.headers))
        if r.status_code == session.codes.ok:
            return r.json()
    return None

def getItem(session, id):
    url = '%s/me/drive/items/%s' % (g_url, id)
    params = {'select': g_itemfields}
    with session.get(url, params=params, timeout=g_timeout) as r:
        print("drivetools.getItem():\n%s\n%s\n%s" % (r.status_code, r.json(), r.headers))
        if r.status_code == session.codes.ok:
            return r.json()
    return None

def getUploadLocation(session, id, parent, name, size, data, new):
    location = None
    if size > g_upload:
        if new:
            url = '%s/me/drive/items/%s:/%s:/createUploadSession' % (g_url, parent, name)
        else:
            #url = '%s/me/drive/items/%s/createUploadSession' % (g_url, id)
            url = '%s/me/drive/items/%s:/%s:/createUploadSession' % (g_url, parent, name)
        print("drivetools.getUploadLocation()1: %s - %s" % (url, id))
        with session.post(url, json=data, timeout=g_timeout) as r:
            print("drivetools.getUploadLocation()2 %s - %s - %s" % (r.url, r.status_code, r.headers))
            print("drivetools.getUploadLocation()3 %s" % (r.content, ))
            if r.status_code == session.codes.ok:
                location = r.json().get('uploadUrl', None)
    elif new:
        location = '%s/me/drive/items/%s:/%s:/content' % (g_url, parent, name)
    else:
        location = '%s/me/drive/items/%s/content' % (g_url, id)
    return location

def updateItem(session, id, parent, data, new):
    url = '%s/me/drive/items/%s/children' % (g_url, parent) if new else '%s/me/drive/items/%s' % (g_url, id)
    method = 'POST' if new else 'DELETE' if data is None else 'PATCH'
    with session.request(method, url, json=data, timeout=g_timeout) as r:
        print("drivetools.updateItem()1 %s - %s" % (r.status_code, r.headers))
        print("drivetools.updateItem()2 %s - %s" % (r.content, data))
        if r.status_code == session.codes.ok or r.status_code == session.codes.created:
            return r.json().get('id')
        elif r.status_code == session.codes.no_content:
            return id
    return False

def selectChildId(connection, userid, parent, title):
    id = None
    call = connection.prepareCall('CALL "selectChildId"(?, ?, ?)')
    call.setString(1, userid)
    call.setString(2, parent)
    call.setString(3, title)
    result = call.executeQuery()
    if result.next():
        id = result.getString(1)
    call.close()
    return id

def isIdentifier(connection, userid, id):
    retreived = False
    call = connection.prepareCall('CALL "isIdentifier"(?, ?)')
    call.setString(1, userid)
    call.setString(2, id)
    result = call.executeQuery()
    if result.next():
        retreived = result.getBoolean(1)
    call.close()
    return retreived

def setJsonData(call, data, parser, timestamp, index=1):
    call.setString(index, data.get('id'))
    index += 1
    call.setString(index, data.get('name'))
    index += 1
    call.setTimestamp(index, parser(data.get('createdDateTime', timestamp)))
    index += 1
    call.setTimestamp(index, parser(data.get('lastModifiedDateTime', timestamp)))
    index += 1
    call.setString(index, data.get('file', {}).get('mimeType', g_folder))
    index += 1
    call.setLong(index, int(data.get('size', 0)))
    index += 1
    call.setBoolean(index, data.get('trashed', False))
    index += 1
    return index

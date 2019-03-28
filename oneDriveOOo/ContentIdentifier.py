#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.lang import XServiceInfo
from com.sun.star.ucb import IllegalIdentifierException

from onedrive import ChildGenerator
from onedrive import InputStream
from onedrive import OutputStream

from onedrive import getItem
from onedrive import isIdentifier
from onedrive import selectChildId
from onedrive import updateItem
from onedrive import setJsonData

from onedrive import g_doc_map
from onedrive import g_folder
from onedrive import g_link
from onedrive import g_plugin

# clouducp is only available after CloudUcpOOo as been loaded...
try:
    from clouducp import ContentIdentifierBase
except ImportError:
    class ContentIdentifierBase():
        pass
# requests is only available after OAuth2OOo as been loaded...
try:
    from oauth2.requests.compat import unquote_plus
except ImportError:
    def unquote_plus():
        pass

import binascii
import traceback

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = '%s.ContentIdentifier' % g_plugin


class ContentIdentifier(ContentIdentifierBase,
                        XServiceInfo):
    def __init__(self, ctx, *namedvalues):
        ContentIdentifierBase.__init__(self, ctx, namedvalues)
    @property
    def Properties(self):
        print("oneDriveOOo.ContentIdentifier.Properties")
        return ('Name', 'DateCreated', 'DateModified', 'MimeType',
                'Size', 'Trashed', 'Loaded')

    def getPlugin(self):
        return g_plugin
    def getFolder(self):
        return g_folder
    def getLink(self):
        return g_link
    def getDocument(self):
        return g_doc_map
    def doSync(self, session):
        return doSync(self.ctx, self.User.Connection, session, self.SourceURL, self.User.Id)
    def updateChildren(self, session):
        merge, index = self.mergeJsonItemCall()
        update = all(self.mergeJsonItem(merge, item, index) for item in ChildGenerator(session, self.Id))
        merge.close()
        return update
    def getNewIdentifier(self):
        return binascii.hexlify(uno.generateUuid().value).decode('utf-8')
    def getItem(self, session):
        return getItem(session, self.Id)
    def selectItem(self):
        item = None
        select = self.User.Connection.prepareCall('CALL "selectItem"(?, ?)')
        select.setString(1, self.User.Id)
        select.setString(2, self.Id)
        result = select.executeQuery()
        if result.next():
            item = self.getItemFromResult(result, self.Properties)
        select.close()
        return item
    def insertJsonItem(self, item):
        item = None
        insert = self.User.Connection.prepareCall('CALL "insertJsonItem"(?, ?, ?, ?, ?, ?, ?, ?, ?)')
        insert.setString(1, self.User.Id)
        index = setJsonData(insert, item, self.getDateTimeParser(), self.unparseDateTime(), 2)
        insert.setString(index, item.get('parentReference', {}).get('id', self.User.RootId))
        result = insert.executeQuery()
        if result.next():
            item = self.getItemFromResult(result, self.Properties)
        insert.close()
        return item
    def isIdentifier(self, title):
        return isIdentifier(self.User.Connection, self.User.Id, title)
    def selectChildId(self, parent, title):
        return selectChildId(self.User.Connection, self.User.Id, parent, title)
    def unquote(self, text):
        return unquote_plus(text)
    def mergeJsonItemCall(self):
        merge = self.User.Connection.prepareCall('CALL "mergeJsonItem"(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
        merge.setString(1, self.User.Id)
        return merge, 2
    def mergeJsonItem(self, merge, item, index):
        index = setJsonData(merge, item, self.getDateTimeParser(), self.unparseDateTime(), index)
        merge.setString(index, item.get('parentReference', {}).get('id', self.User.RootId))
        merge.execute()
        return merge.getLong(index +1)
    def getItemToSync(self, mode):
        items = []
        select = self.User.Connection.prepareCall('CALL "selectSync"(?, ?)')
        select.setString(1, self.User.Id)
        select.setLong(2, mode)
        result = select.executeQuery()
        while result.next():
            items.append(self.getItemFromResult(result, None, None))
        select.close()
        return items
    def syncItem(self, session, path, item):
        result = False
        id = item.get('id')
        mode = item.get('mode')
        parent = item.get('parents')
        name = item.get('name')
        data = None
        if mode & self.CREATED:
            data = {'item': {'@microsoft.graph.conflictBehavior': 'replace'}}
            if mode & self.FOLDER:
                update = self.getUpdateItemId(id)
                newid = updateItem(session, id, parent, data, True)
                self.updateItemId(update, newid)
            if mode & self.FILE:
                update = self.getUpdateItemId(id)
                self.uploadItem(session, path, id, parent, name, data, True, update)
        else:
            if mode & self.REWRITED:
                data = {'item': {'@microsoft.graph.conflictBehavior': 'replace',
                                 'name': name}}
                result = self.uploadItem(session, path, id, parent, name, data, False, None)
            if mode & self.RENAMED:
                data = {'name': name}
                result = updateItem(session, id, parent, data, False)
        if mode & self.TRASHED:
            result = updateItem(session, id, parent, data, False)
        return result
    def uploadItem(self, session, path, id, parent, name, data, new, update):
        size, stream = self.getInputStream(path, id)
        if size:
            location = getUploadLocation(session, id, parent, name, size, data, new)
            if location is not None:
                pump = self.ctx.ServiceManager.createInstance('com.sun.star.io.Pump')
                pump.setInputStream(stream)
                pump.setOutputStream(OutputStream(session, location, size, update))
                pump.start()
                return id
        return False
    def getUpdateItemId(self, id):
        update = self.User.Connection.prepareCall('CALL "updateItemId"(?, ?, ?, ?, ?)')
        update.setString(1, self.User.Id)
        update.setString(2, id)
        update.setString(3, self.RETRIEVED)
        return update
    def updateItemId(self, update, id):
        result = False
        update.setString(4, id)
        update.execute()
        result = update.getString(5)
        update.close()
        return result

    # XInputStreamProvider
    def createInputStream(self):
        return InputStream(self.Session, self.Id, self.Size)

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(ContentIdentifier,                                                  # UNO object class
                                         g_ImplementationName,                                               # Implementation name
                                        (g_ImplementationName, ))                                            # List of implemented services

#!
# -*- coding: utf_8 -*-

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

from com.sun.star.lang import XServiceInfo

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb.ConnectionMode import OFFLINE
from com.sun.star.ucb.ConnectionMode import ONLINE

from com.sun.star.ucb import XRestProvider
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_RETRIEVED
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_CREATED
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_FOLDER
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_FILE
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_RENAMED
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_REWRITED
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_TRASHED

from .unolib import KeyMap

from .unotool import parseDateTime
from .unotool import getResourceLocation
from .unotool import getConnectionMode

import datetime
import traceback


class ProviderObject(object):
    pass


class ProviderBase(ProviderObject,
                   unohelper.Base,
                   XServiceInfo,
                   XRestProvider):

    # Base properties
    @property
    def Error(self):
        return self._Error

    # Must be implemented properties
    @property
    def Name(self):
        raise NotImplementedError
    @property
    def Host(self):
        raise NotImplementedError
    @property
    def BaseUrl(self):
        raise NotImplementedError
    @property
    def UploadUrl(self):
        raise NotImplementedError
    @property
    def Office(self):
        raise NotImplementedError
    @property
    def Document(self):
        raise NotImplementedError
    @property
    def Chunk(self):
        raise NotImplementedError
    @property
    def Buffer(self):
        raise NotImplementedError

    # Can be rewrited properties
    @property
    def IdentifierRange(self):
        return (0, 0)
    @property
    def GenerateIds(self):
        return all(self.IdentifierRange)
    @property
    def FileSyncModes(self):
        return (SYNC_FILE, )
    @property
    def FolderSyncModes(self):
        return (SYNC_FOLDER, )

    # Must be implemented method
    def getRequestParameter(self, method, data):
        raise NotImplementedError

    def getUserId(self, item):
        raise NotImplementedError
    def getUserName(self, item):
        raise NotImplementedError
    def getUserDisplayName(self, item):
        raise NotImplementedError
    def getUserToken(self, item):
        raise NotImplementedError

    def getItemId(self, item):
        raise NotImplementedError
    def getItemTitle(self, item):
        raise NotImplementedError
    def getItemCreated(self, item, timestamp=None):
        raise NotImplementedError
    def getItemModified(self, item, timestamp=None):
        raise NotImplementedError
    def getItemMediaType(self, item):
        raise NotImplementedError
    def getItemSize(self, item):
        raise NotImplementedError
    def getItemTrashed(self, item):
        raise NotImplementedError
    def getItemCanAddChild(self, item):
        raise NotImplementedError
    def getItemCanRename(self, item):
        raise NotImplementedError
    def getItemIsReadOnly(self, item):
        raise NotImplementedError
    def getItemIsVersionable(self, item):
        raise NotImplementedError

    def getItemParent(self, item, rootid):
        raise NotImplementedError

    # Base method
    def parseDateTime(self, timestamp, format='%Y-%m-%dT%H:%M:%S.%fZ'):
        return parseDateTime(timestamp, format)
    def isOnLine(self):
        self.SessionMode = getConnectionMode(self.ctx, self.Host)
        return  self.SessionMode != OFFLINE
    def isOffLine(self):
        self.SessionMode = getConnectionMode(self.ctx, self.Host)
        return  self.SessionMode != ONLINE

    def initialize(self, scheme, plugin, folder, link):
        self.Scheme = scheme
        self.Plugin = plugin
        self.Folder = folder
        self.Link = link
        self.SourceURL = getResourceLocation(self.ctx, plugin, scheme)
        self.SessionMode = getConnectionMode(self.ctx, self.Host)

    def initializeUser(self, user, name):
        if self.isOnLine():
            return user.Request.initializeUser(name)
        return True

    # Can be rewrited method
    def initUser(self, request, database, user):
        pass
    def initFirstPull(self, rootid):
        self._folders = [rootid]
    def hasFirstPull(self):
        return len(self._folders) > 0
    def getFirstPull(self):
        if self.hasFirstPull():
            return self._folders.pop(0)
    def setFirstPull(self, item):
        pass
    def updateDrive(self, database, user, token):
        pass
    def isFolder(self, contenttype):
        return contenttype == self.Folder
    def isLink(self, contenttype):
        return contenttype == self.Link
    def isDocument(self, contenttype):
        return not (self.isFolder(contenttype) or self.isLink(contenttype))

    def getRootId(self, item):
        return self.getItemId(item)
    def getRootTitle(self, item):
        return self.getItemTitle(item)
    def getRootCreated(self, item, timestamp=None):
        return self.getItemCreated(item, timestamp)
    def getRootModified(self, item, timestamp=None):
        return self.getItemModified(item, timestamp)
    def getRootMediaType(self, item):
        return self.getItemMediaType(item)
    def getRootSize(self, item):
        return self.getItemSize(item)
    def getRootTrashed(self, item):
        return self.getItemTrashed(item)
    def getRootCanAddChild(self, item):
        return self.getItemCanAddChild(item)
    def getRootCanRename(self, item):
        return self.getItemCanRename(item)
    def getRootIsReadOnly(self, item):
        return self.getItemIsReadOnly(item)
    def getRootIsVersionable(self, item):
        return self.getItemIsVersionable(item)

    def getResponseId(self, response, default):
        id = self.getItemId(response)
        if not id:
            id = default
        return id
    def getResponseTitle(self, response, default):
        title = self.getItemTitle(response)
        if not title:
            title = default
        return title
    def transform(self, name, value):
        return value

    def getIdentifier(self, request, user):
        parameter = self.getRequestParameter('getNewIdentifier', user)
        return request.getIterator(parameter, None)
    def getUser(self, request, name):
        data = KeyMap()
        data.insertValue('Id', name)
        parameter = self.getRequestParameter('getUser', data)
        return request.execute(parameter)
    def getRoot(self, request, user):
        parameter = self.getRequestParameter('getRoot', user)
        return request.execute(parameter)
    def getToken(self, request, user):
        parameter = self.getRequestParameter('getToken', user)
        return request.execute(parameter)
    def getItem(self, request, identifier):
        parameter = self.getRequestParameter('getItem', identifier)
        return request.execute(parameter)

    def getDocumentContent(self, request, content):
        parameter = self.getRequestParameter('getDocumentContent', content)
        return request.getInputStream(parameter, self.Chunk, self.Buffer)

    def getFolderContent(self, request, content):
        parameter = self.getRequestParameter('getFolderContent', content)
        return request.getIterator(parameter, None)

    def createFolder(self, request, item):
        parameter = self.getRequestParameter('createNewFolder', item)
        return request.execute(parameter)

    def createFile(self, request, uploader, item):
        return True

    def uploadFile(self, uploader, user, item, new=False):
        method = 'getNewUploadLocation' if new else 'getUploadLocation'
        parameter = self.getRequestParameter(method, item)
        response = user.Request.execute(parameter)
        if response.IsPresent:
            parameter = self.getRequestParameter('getUploadStream', response.Value)
            return uploader.start(user.Name, item.getValue('Id'), parameter)
        return False

    def updateTitle(self, request, item):
        parameter = self.getRequestParameter('updateTitle', item)
        response = request.execute(parameter)
        return response.IsPresent

    def updateTrashed(self, request, item):
        parameter = self.getRequestParameter('updateTrashed', item)
        response = request.execute(parameter)
        return response.IsPresent

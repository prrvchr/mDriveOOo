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

from com.sun.star.lang import XServiceInfo

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb.ConnectionMode import OFFLINE
from com.sun.star.ucb.ConnectionMode import ONLINE

from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_RETRIEVED
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_CREATED
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_FOLDER
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_FILE
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_RENAMED
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_REWRITED
from com.sun.star.ucb.RestDataSourceSyncMode import SYNC_TRASHED

from com.sun.star.ucb import IllegalIdentifierException

from .unolib import KeyMap

from .unotool import getConnectionMode

from .dbtool import currentDateTimeInTZ
from .dbtool import getDateTimeFromString

from .logger import getLogger

from .configuration import g_identifier
from .configuration import g_scheme
from .configuration import g_separator
from .configuration import g_chunk

from collections import OrderedDict
import traceback


class ProviderBase(object):

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
    @property
    def DateTimeFormat(self):
        raise NotImplementedError
    @property
    def Folder(self):
        raise NotImplementedError
    @property
    def Link(self):
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
    @property
    def SupportDuplicate(self):
        return False

    # Method called by Content
    def updateFolderContent(self, content):
        timestamp = currentDateTimeInTZ()
        parameter = self.getRequestParameter(content.User.Request, 'getFolderContent', content)
        iterator = self.parseRootFolder(parameter, content)
        count = content.User.DataBase.pullItems(iterator, content.User.Id, timestamp)
        return count

    def getDocumentContent(self, content, url):
        print('ProviderBase.getDocumentContent() Url: %s' % url)
        data = self.getDocumentLocation(content)
        if data is None:
            return False
        print('ProviderBase.getDocumentContent() Data: %s' % data)
        parameter = self.getRequestParameter(content.User.Request, 'getDocumentContent', data)
        return content.User.Request.download(parameter, url, g_chunk, 3, 10)

    # Method called by Replicator
    def pullNewIdentifiers(self, user):
        parameter = self.getRequestParameter(user.Request, 'getNewIdentifier', user)
        response = user.Request.execute(parameter)
        if response.Ok:
            iterator = self.parseNewIdentifiers(response)
        else:
            # TODO: raise exception with the right message...
            self._logger.logprb(SEVERE, 'Replicator', '_checkNewIdentifier', 403, user.Name)
        user.DataBase.insertIdentifier(iterator, user.Id)
        response.close()

    def firstPull(self, user):
        timestamp = currentDateTimeInTZ()
        page = count = 0
        for root in self.getFirstPullRoots(user):
            parameter = self.getRequestParameter(user.Request, 'getFirstPull', root)
            iterator = self.parseItems(user.Request, parameter)
            count +=  user.DataBase.pullItems(iterator, user.Id, timestamp)
            page += parameter.PageCount
        return page, count, parameter.SyncToken

    def pullUser(self, user):
        timestamp = currentDateTimeInTZ()
        parameter = self.getRequestParameter(user.Request, 'getPull', user)
        iterator = self.parseItems(user.Request, parameter)
        count = user.DataBase.pullItems(iterator, user.Id, timestamp)
        return parameter.PageCount, count, parameter.SyncToken

    def getUserToken(self, user):
        parameter = self.getRequestParameter(user.Request, 'getToken', user)
        response = user.Request.execute(parameter)
        if not response.Ok:
            pass
        token = self.parseUserToken(response)
        response.close()
        return token

    def _getRejectedItems(self, items):
        rejected = []
        for item in items:
            itemid = self._getItemId(item)
            title = self._getItemTitle(item)
            parents = self._getItemParents(item)
            rejected.append((title, itemid, ','.join(parents)))
        return rejected

    def _isValidItem(self, item, roots, orphans):
        itemid = self._getItemId(item)
        parents = self._getItemParents(item)
        if not all(parent in roots for parent in parents):
            orphans[itemid] = item
            return False
        roots.append(itemid)
        return True

    def _validItem(self, item, roots, orphans):
        return True

    def _getItemId(self, item):
        return item[0]
    def _getItemTitle(self, item):
        return item[1]
    def _getItemParents(self, item):
        return item[11]

    # Must be implemented method
    def getRequestParameter(self, request, method, data):
        raise NotImplementedError

    def getUser(self, source, request, name):
        raise NotImplementedError

    def parseNewIdentifiers(self, response):
        raise NotImplementedError

    def parseItems(self, request, parameter):
        raise NotImplementedError

    def parseChanges(self, user, parameter):
        raise NotImplementedError

    def parseUserToken(self, user):
        raise NotImplementedError

    def getFirstPullRoots(self, user):
        raise NotImplementedError

    def parseUploadLocation(self, user):
        raise NotImplementedError

    def getDocumentLocation(self, user):
        raise NotImplementedError

    def mergeNewFolder(self, response, user, item):
        raise NotImplementedError

    def createNewFile(self, user, data):
        raise NotImplementedError

    def parseRootFolder(self, parameter, content):
        raise NotImplementedError

    def initUser(self, database, user, token):
        pass

    # Base method
    def parseDateTime(self, timestamp):
        return getDateTimeFromString(timestamp, self.DateTimeFormat)
    def isOnLine(self):
        return OFFLINE != getConnectionMode(self._ctx, self.Host)
    def isOffLine(self):
        return ONLINE != getConnectionMode(self._ctx, self.Host)

    # Can be rewrited method
    def isFolder(self, contenttype):
        return contenttype == self.Folder
    def isLink(self, contenttype):
        return contenttype == self.Link
    def isDocument(self, contenttype):
        return not (self.isFolder(contenttype) or self.isLink(contenttype))

    def getItem(self, request, identifier):
        parameter = self.getRequestParameter(request, 'getItem', identifier)
        return request.execute(parameter)

    def createFolder(self, user, item):
        parameter = self.getRequestParameter(user.Request, 'createNewFolder', item)
        response = user.Request.execute(parameter)
        return self.mergeNewFolder(response, user, item)

    def uploadFile(self, user, data, new=False):
        method = 'getNewUploadLocation' if new else 'getUploadLocation'
        parameter = self.getRequestParameter(user.Request, method, data)
        response = user.Request.execute(parameter)
        location = self.parseUploadLocation(response)
        if location is None:
            return False
        parameter = self.getRequestParameter(user.Request, 'getUploadStream', location)
        url = self.SourceURL + g_separator + data.get('Id')
        return user.Request.upload(parameter, url, g_chunk, 3, 10)

    def updateTitle(self, request, item):
        parameter = self.getRequestParameter(request, 'updateTitle', item)
        response = request.execute(parameter)
        return response.IsPresent

    def updateTrashed(self, request, item):
        parameter = self.getRequestParameter(request, 'updateTrashed', item)
        response = request.execute(parameter)
        return response.IsPresent

    def updateParents(self, request, item):
        parameter = self.getRequestParameter(request, 'updateParents', item)
        response = request.execute(parameter)
        return response.IsPresent


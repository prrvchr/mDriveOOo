#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-25 https://prrvchr.github.io                                  ║
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

from ..unotool import getConnectionMode
from ..unotool import getConfiguration
from ..unotool import getResourceLocation
from ..unotool import getSimpleFile

from ..dbtool import currentDateTimeInTZ

from ..logger import getLogger

from ..configuration import g_identifier
from ..configuration import g_scheme
from ..configuration import g_chunk

from .configuration import g_ucbseparator

from dateutil import parser, tz
import traceback


class Provider():
    def __init__(self, ctx, logger):
        self._ctx = ctx
        self._logger = logger
        self._sf = getSimpleFile(ctx)
        self._url = getResourceLocation(ctx, g_identifier, g_scheme)
        self._folders = []
        self._config = getConfiguration(ctx, g_identifier, False)
        self._logger.logprb(INFO, 'Provider', '__init__', 551)

    @property
    def Scheme(self):
        return g_scheme

    # Must be implemented properties
    @property
    def BaseUrl(self):
        raise NotImplementedError
    @property
    def Host(self):
        raise NotImplementedError
    @property
    def Name(self):
        raise NotImplementedError
    @property
    def UploadUrl(self):
        raise NotImplementedError

    # Must be implemented method
    def getDocumentLocation(self, user, item):
        raise NotImplementedError

    def getFirstPullRoots(self, user):
        raise NotImplementedError

    def getRequestParameter(self, request, method, data):
        raise NotImplementedError

    def getUser(self, source, request, name):
        raise NotImplementedError

    def mergeNewFolder(self, user, itemid, response):
        raise NotImplementedError

    def parseFolder(self, user, data, parameter):
        raise NotImplementedError

    def parseItems(self, request, parameter, parentid):
        raise NotImplementedError

    def parseNewIdentifiers(self, response):
        raise NotImplementedError

    def parseUploadLocation(self, user):
        raise NotImplementedError

    def parseUserToken(self, user):
        raise NotImplementedError

    def updateItemId(self, user, item, response):
        raise NotImplementedError

    # Can be rewrited properties
    @property
    def IdentifierRange(self):
        return (0, 0)
    @property
    def GenerateIds(self):
        return all(self.IdentifierRange)
    @property
    def SupportSharedDocuments(self):
        return self._config.getByName('SupportShare') and self._config.getByName('SharedDocuments')
    @property
    def SharedFolderName(self):
        return self._config.getByName('SharedFolderName')

    # Can be rewrited method
    def initUser(self, user, token):
        user.Token = token

    def initSharedDocuments(self, user, reset, datetime):
        # You must implement this method in Provider to be able to handle Shared Documents
        pass

    def pullUser(self, user):
        count = download = 0
        datetime = currentDateTimeInTZ()
        parameter = self.getRequestParameter(user.Request, 'getPull', user)
        for item in self.parseItems(user.Request, parameter, user.RootId):
            count += user.DataBase.mergeItem(user.Id, user.RootId, datetime, item)
            download += self.pullFileContent(user, item)
        return count, download, parameter.PageCount, parameter.SyncToken

    # Method called by Content
    def updateFolderContent(self, user, data):
        count = 0
        datetime = currentDateTimeInTZ()
        mode = 1 if data.get('ConnectionMode') > 0 else -1
        parameter = self.getRequestParameter(user.Request, 'getFolderContent', data)
        items = self.parseFolder(user, data, parameter)
        for item in user.DataBase.mergeItems(user.Id, user.RootId, datetime, items, mode):
            count += 1
        return count

    def downloadFile(self, user, item, url):
        data = self.getDocumentLocation(user, item)
        if data is not None:
            parameter = self.getRequestParameter(user.Request, 'downloadFile', data)
            return user.Request.download(parameter, url, *self._getDownloadSetting())
        return False

    # Method called by Replicator
    def createFolder(self, user, itemid, item):
        parameter = self.getRequestParameter(user.Request, 'createNewFolder', item)
        response = user.Request.execute(parameter)
        return self.mergeNewFolder(user, itemid, response)

    def firstPull(self, user, reset):
        datetime = currentDateTimeInTZ()
        count = download = page = count2 = download2 = page2 = 0
        if self.SupportSharedDocuments:
            count, download, page = self.initSharedDocuments(user, reset, datetime)
        for root in self.getFirstPullRoots(user):
            parameter = self.getRequestParameter(user.Request, 'getFirstPull', root)
            items = self.parseItems(user.Request, parameter, user.RootId)
            for item in user.DataBase.mergeItems(user.Id, user.RootId, datetime, items):
                count2 += 1
                if reset:
                    download2 += self.pullFileContent(user, item)
            page2 += parameter.PageCount
        return count, download, page, count2, download2, page2, parameter.SyncToken

    def pullNewIdentifiers(self, user):
        count, msg = 0, ''
        parameter = self.getRequestParameter(user.Request, 'getNewIdentifier', user)
        response = user.Request.execute(parameter)
        if not response.Ok:
            msg = response.Text
        else:
            iterator = self.parseNewIdentifiers(response)
            count = user.DataBase.insertIdentifier(iterator, user.Id)
        response.close()
        return count, msg

    def updateName(self, request, itemid, item):
        parameter = self.getRequestParameter(request, 'updateName', item)
        response = request.execute(parameter)
        response.close()
        return itemid

    def updateParents(self, request, itemid, item):
        parameter = self.getRequestParameter(request, 'updateParents', item)
        response = request.execute(parameter)
        response.close()
        return itemid

    def updateTrashed(self, request, itemid, item):
        parameter = self.getRequestParameter(request, 'updateTrashed', item)
        response = request.execute(parameter)
        response.close()
        return itemid

    # Base method
    def getSimpleFile(self):
        return self._sf

    def getTargetUrl(self, itemid):
        return self._url + g_ucbseparator + itemid

    def getUserToken(self, user):
        token = ''
        parameter = self.getRequestParameter(user.Request, 'getToken', user)
        response = user.Request.execute(parameter)
        if response.Ok:
            token = self.parseUserToken(response)
        response.close()
        return token

    def isOffLine(self):
        return ONLINE != getConnectionMode(self._ctx, self.Host)

    def isOnLine(self):
        return OFFLINE != getConnectionMode(self._ctx, self.Host)

    def parseDateTime(self, timestamp):
        datetime = uno.createUnoStruct('com.sun.star.util.DateTime')
        try:
            dt = parser.parse(timestamp)
        except parser.ParserError:
            pass
        else:
            datetime.Year = dt.year
            datetime.Month = dt.month
            datetime.Day = dt.day
            datetime.Hours = dt.hour
            datetime.Minutes = dt.minute
            datetime.Seconds = dt.second
            datetime.NanoSeconds = dt.microsecond * 1000
            datetime.IsUTC = dt.tzinfo == tz.tzutc()
        return datetime

    def pullFileContent(self, user, item):
        url = self.getTargetUrl(item.get('Id'))
        if self.getSimpleFile().exists(url):
            return self.downloadFile(user, item, url)
        return False

    def raiseIllegalIdentifierException(self, source, code, parameter, reponse):
        msg = self._logger.resolveString(code, parameter.Name, response.StatusCode, response.Text)
        response.close()
        raise IllegalIdentifierException(msg, source)

    def updateNewItemId(self, oldid, newid):
        source = self.getTargetUrl(oldid)
        target = self.getTargetUrl(newid)
        if self._sf.exists(source) and not self._sf.exists(target):
            self._sf.move(source, target)

    def uploadFile(self, code, user, item, data, created, chunk, retry, delay, new=False):
        newid = None
        method = 'getNewUploadLocation' if new else 'getUploadLocation'
        parameter = self.getRequestParameter(user.Request, method, data)
        response = user.Request.execute(parameter)
        if not response.Ok:
            args = code, parameter.Name, data.get('Name'), response.Text
            response.close()
        else:
            location = self.parseUploadLocation(response)
            if location is None:
                args = code + 1, parameter.Name, data.get('Name')
            else:
                parameter = self.getRequestParameter(user.Request, 'getUploadStream', location)
                url = self.getTargetUrl(item)
                response = user.Request.upload(parameter, url, chunk, retry, delay)
                if not response.Ok:
                    args = code + 2, parameter.Name, data.get('Name'), response.Text
                    response.close()
                elif new:
                    newid = self.updateItemId(user, item, response)
                    args = code + 3, data.get('Name'), created, data.get('Size')
                else:
                    response.close()
                    newid = item
                    args = code + 4, data.get('Name'), created, data.get('Size')
        return newid, args

    # Private method
    def _getDownloadSetting(self):
        config = self._config.getByHierarchicalName('Settings/Download')
        return config.getByName('Chunk'), config.getByName('Retry'), config.getByName('Delay')


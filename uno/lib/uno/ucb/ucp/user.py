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

from com.sun.star.beans.PropertyAttribute import BOUND

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb.ConnectionMode import OFFLINE
from com.sun.star.ucb.ConnectionMode import ONLINE

from com.sun.star.ucb.ContentAction import EXCHANGED
from com.sun.star.ucb.ContentAction import REMOVED

from com.sun.star.ucb.ContentInfoAttribute import KIND_DOCUMENT
from com.sun.star.ucb.ContentInfoAttribute import KIND_FOLDER
from com.sun.star.ucb.ContentInfoAttribute import KIND_LINK

from com.sun.star.ucb import IllegalIdentifierException

from ..oauth2 import getOAuth2UserName
from ..oauth2 import getRequest
from ..oauth2 import g_oauth2

from ..dbtool import currentDateTimeInTZ
from ..dbtool import currentUnoDateTime
from ..dbtool import getDateTimeInTZToString

from ..unotool import createService
from ..unotool import getProperty
from ..unotool import getUriFactory

from ..database import DataBase

from ..logger import getLogger

from .content import Content

from .identifier import Identifier

from .contenthelper import getContentInfo
from .contenthelper import getExceptionMessage

from ..configuration import g_extension
from ..configuration import g_scheme
from ..configuration import g_separator


import binascii
import traceback


class User():
    def __init__(self, ctx, source, logger, database, provider, sync, name, password=''):
        method = '__init__()'
        self._ctx = ctx
        self._name = name
        self._sync = sync
        self._expired = None
        self.Provider = provider
        #self.CanAddChild = not self.Provider.GenerateIds
        self.CanAddChild = True
        self._logger = logger
        self._factory = None
        metadata = database.selectUser(name)
        new = metadata is None
        if not new:
            request = getRequest(ctx, self.Provider.Scheme, name)
            if request is None:
                # If we have a Null value here then it means that the user has abandoned
                # the OAuth2 Wizard, there is nothing more to do except throw an exception
                msg = self._getExceptionMessage(method, 501, name)
                raise IllegalIdentifierException(msg, source)
        else:
            if not self.Provider.isOnLine():
                msg = self._getExceptionMessage(method, 503, name)
                raise IllegalIdentifierException(msg, source)
            request = getRequest(ctx, self.Provider.Scheme, name)
            if request is None:
                # If we have a Null value here then it means that the user has abandoned
                # the OAuth2 Wizard, there is nothing more to do except throw an exception
                msg = self._getExceptionMessage(method, 501, g_oauth2)
                raise IllegalIdentifierException(msg, source)
            print("User.__init__() Request: %s" % (request, ))
            user, root = self.Provider.getUser(source, request, name)
            metadata = database.insertUser(user, root)
            if metadata is None:
                msg = self._getExceptionMessage(method, 505, name)
                raise IllegalIdentifierException(msg, source)
            if not database.createUser(name, password):
                msg = self._getExceptionMessage(method, 507, name)
                raise IllegalIdentifierException(msg, source)
        self.Request = request
        self.MetaData = metadata
        self.DataBase = DataBase(ctx, logger, database.Url, name, password)
        rootid = metadata.get('RootId')
        self._ids = {'': rootid, '/': rootid}
        self._paths = {}
        self._contents = {}
        if new:
            # Start Replicator for pushing changes…
            self._sync.set()
        self._logger.logprb(INFO, 'User', method, 509)
        print("User.__init__()")

    @property
    def Name(self):
        return self._name
    @property
    def Id(self):
        return self.MetaData.get('UserId')
    @property
    def RootId(self):
        return self.MetaData.get('RootId')
    @property
    def RootName(self):
        return self.MetaData.get('RootName')
    @property
    def Token(self):
        return self.MetaData.get('Token')
    @property
    def SyncMode(self):
        return self.MetaData.get('SyncMode')
    @SyncMode.setter
    def SyncMode(self, mode):
        self.MetaData['SyncMode'] = mode
        self.DataBase.updateUserSyncMode(self.Id, mode)
    @property
    def SessionMode(self):
        return self.Request.getSessionMode(self.Provider.Host)
    @property
    def TimeStamp(self):
        return self.MetaData.get('TimeStamp')
    @TimeStamp.setter
    def TimeStamp(self, timestamp):
        self.MetaData['TimeStamp'] = timestamp

    def setToken(self, token):
        self.MetaData['Token'] = token

    # method called from ContentResultSet.queryContent()
    def getItemByUrl(self, url):
        uri = self._getUriFactory().parse(url)
        return self.getItemByUri(uri)

    # method called from DataSource.queryContent()
    def getItemByUri(self, uri):
        path = uri.getPath()
        if path in self._ids:
            itemid = self._ids[path]
        else:
            itemid = self.DataBase.getItemId(self.Id, path)
            if itemid is not None:
                self._ids[path] = itemid
                self._paths[itemid] = path
        return itemid

    # method called from DataSource.queryContent(), Content.getParent() and ContentResultSet.queryContent()
    def getContent(self, authority, itemid):
        content = None
        if itemid in self._contents:
            data = self._contents[itemid]
        else:
            data = self.DataBase.getItem(self.Id, self.RootId, itemid)
            if data is not None:
                self._contents[itemid] = data
        if data is not None:
            content = Content(self._ctx, self, authority, data)
        return content

    # method called from Content._identifier
    def getContentIdentifier(self, authority, itemid, path, title):
        identifier = self._getContentScheme(authority)
        if itemid != self.RootId:
            identifier += path + title
        else:
            identifier += g_separator
        return identifier

    def createNewContent(self, authority, parentid, path, title, link, contentype):
        data = self._getNewContent(parentid, path, title, link, contentype)
        content = Content(self._ctx, self, authority, data, True)
        return content

    def getTargetUrl(self, itemid):
        return self.Provider.SourceURL + g_separator + itemid

    def getCreatableContentsInfo(self, canaddchild):
        content = []
        if self.CanAddChild and canaddchild:
            properties = (getProperty('Title', 'string', BOUND), )
            content.append(getContentInfo(self.Provider.Folder, KIND_FOLDER, properties))
            content.append(getContentInfo(self.Provider.Office, KIND_DOCUMENT, properties))
            #if self.Provider.hasProprietaryFormat:
            #    content.append(getContentInfo(self.Provider.ProprietaryFormat, KIND_DOCUMENT, properties))
        return tuple(content)

    def getDocumentContent(self, sf, content, size):
        size = 0
        itemid = content.getValue('Id')
        url = self.getTargetUrl()
        if content.getValue('ConnectionMode') == OFFLINE and sf.exists(url):
            size = sf.getSize(url)
            return url, size
        stream = self.Provider.getDocumentContent(self.Request, content)
        if stream:
            try:
                sf.writeFile(url, stream)
            except Exception as e:
                self._logger.logprb(SEVERE, 'User', 'getDocumentContent()', 511, e, traceback.format_exc())
            else:
                size = sf.getSize(url)
                loaded = self.updateConnectionMode(itemid, OFFLINE)
                content.setConnectionMode(loaded)
            finally:
                stream.closeInput()
        return url, size

    def updateContent(self, itemid, property, value):
        updated, clear = self.DataBase.updateContent(self.Id, itemid, property, value)
        if updated:
            # Start Replicator for pushing changes…
            self._sync.set()
        if clear:
            # if Title as been changed then we need to clear identifier cache
            self._ids = {'': self.RootId, '/': self.RootId}
            self._paths = {}

    def insertNewContent(self, authority, content):
        timestamp = currentDateTimeInTZ()
        status = self.DataBase.insertNewContent(self.Id, content, timestamp)
        if status :
            # Start Replicator for pushing changes…
            self._sync.set()
        return status

    def deleteNewIdentifier(self, itemid):
        if self.Provider.GenerateIds:
            self.DataBase.deleteNewIdentifier(self.Id, itemid)

    def getChildren(self, authority, itemid, properties):
        scheme = self._getContentScheme(authority)
        return self.DataBase.getChildren(itemid, properties, self.SessionMode, scheme)

    def updateConnectionMode(self, itemid, mode):
        return self.DataBase.updateConnectionMode(self.Id, itemid, mode)

    # Private methods
    def _getContentScheme(self, authority):
        name = self.Name if authority else ''
        return '%s://%s' % (g_scheme, name)

    def _getUriFactory(self):
        if self._factory is None:
            self._factory = getUriFactory(self._ctx)
        return self._factory

    def _getNewContent(self, parentid, path, title, link, contentype):
        timestamp = currentUnoDateTime()
        isfolder = self.Provider.isFolder(contentype)
        isdocument = self.Provider.isDocument(contentype)
        itemid = self._getNewIdentifier()
        data = {'ConnectionMode':        1,
                'ContentType':           contentype,
                'DateCreated':           timestamp,
                'DateModified':          timestamp,
                'IsCompactDisc':         False,
                'IsDocument':            isdocument,
                'IsFloppy':              False,
                'IsFolder':              isfolder,
                'IsHidden':              False,
                'IsReadOnly':            False,
                'IsRemote':              False,
                'IsRemoveable':          False,
                'IsVersionable':         isdocument,
                'IsVolume':              False,
                'MediaType':             '' if isdocument else contentype,
                'ObjectId':              itemid,
                'ParentId':              parentid,
                'Size':                  0,
                'Title':                 '',
                'TitleOnServer':         '',
                'Id':                    itemid,
                'Path':                  self._getPath(parentid, path, title),
                'Link':                  link,
                'Trashed':               False,
                'IsRoot':                False,
                'IsLink':                False,
                'CanAddChild':           isfolder,
                'CanRename':             True}
        return data

    def _getNewIdentifier(self):
        if self.Provider.GenerateIds:
            identifier = self.DataBase.getNewIdentifier(self.Id)
        else:
            identifier = binascii.hexlify(uno.generateUuid().value).decode('utf-8')
        return identifier

    def _getPath(self, itemid, path, title):
        if itemid != self.RootId:
            path += title + g_separator
        else:
            path = g_separator
        return path

    def _getExceptionMessage(self, method, code, *args):
        return getExceptionMessage(self._ctx, self._logger, 'User', method, code, g_extension, *args)


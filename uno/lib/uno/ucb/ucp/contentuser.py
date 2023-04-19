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


from ..unolib import KeyMap

from ..oauth2 import getOAuth2UserName
from ..oauth2 import getRequest
from ..oauth2 import g_oauth2

from ..dbtool import currentDateTimeInTZ
from ..dbtool import currentUnoDateTime
from ..dbtool import getDateTimeInTZToString

from ..unotool import createService
from ..unotool import getProperty

from ..database import DataBase

from ..logger import getLogger

from .content import Content

from .contentidentifier import ContentIdentifier

from .contenthelper import getContentInfo

from ..configuration import g_scheme
from ..configuration import g_separator


import binascii
import traceback


class ContentUser():
    def __init__(self, ctx, logger, source, database, provider, name, sync, lock, password=''):
        try:
            self._ctx = ctx
            self._name = name
            self._sync = sync
            self._lock = lock
            self._expired = None
            self.Provider = provider
            #self.CanAddChild = not self.Provider.GenerateIds
            self.CanAddChild = True
            self.Request = getRequest(ctx, self.Provider.Scheme, name)
            self._logger = logger
            metadata = database.selectUser(name)
            new = metadata is None
            if new:
                if self.Request is None:
                    msg = self._logger.resolveString(401, g_oauth2)
                    raise IllegalIdentifierException(msg, source)
                elif not self.Provider.isOnLine():
                    msg = self._logger.resolveString(402, name)
                    raise IllegalIdentifierException(msg, source)
                user, root = self.Provider.getUser(source, self.Request, name)
                metadata = database.insertUser(user, root)
                if metadata is None:
                    msg = self._logger.resolveString(403, name)
                    raise IllegalIdentifierException(msg, source)
                if not database.createUser(name, password):
                    msg = self._logger.resolveString(404, name)
                    raise IllegalIdentifierException(msg, source)
            self.MetaData = metadata
            self.DataBase = DataBase(ctx, database.getDataSource(), name, password, sync)
            self._identifiers = {}
            self._contents = {}
            self._contents[self.RootId] = Content(ctx, self)
            if new:
                self._sync.set()
            self._logger.logprb(INFO, 'ContentUser', '__init__()', 405)
        except Exception as e:
            msg = "ContentUser.__init__() Error: %s" % traceback.format_exc()
            print(msg)

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

    # method called from DataSource.queryContent(), Content.getParent() and ContentResultSet.queryContent()
    def getContent(self, path, authority):
        if self._expired is not None and path.startswith(self._expired):
            self._removeIdentifiers()
        if self.isRootPath(path):
            itemid = self.RootId
        else:
            itemid = self._identifiers.get(path)
        content = None if itemid is None else self._contents.get(itemid)
        if content is None:
            content = Content(self._ctx, self, authority, path)
            self._identifiers[path] = content.Id
            self._contents[content.Id] = content
        else:
            content.setAuthority(authority)
        return content

    def isRootPath(self, path):
        return path in ('', g_separator)

    def getContentIdentifier(self, authority, path, title, isroot):
        url = self.getContentScheme(authority) + self.getContentPath(path, title, isroot, g_separator)
        return ContentIdentifier(url)

    def getContentPath(self, path, title, isroot=False, rootpath=''):
        return rootpath if isroot else path + g_separator + title

    def getTargetUrl(self, itemid):
        return self.Provider.SourceURL + g_separator + itemid

    def expireIdentifier(self, identifier):
        # FIXME: We need to remove all the child of a resource (if it's a folder)
         self._expired = identifier.getContentIdentifier()

    def createNewContent(self, id, path, authority, contentype):
        data = self._getNewContent(id, path, contentype)
        content = Content(self._ctx, self, authority, path, data)
        return content

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
        url = self.Provider.SourceURL + g_separator + itemid
        if content.getValue('ConnectionMode') == OFFLINE and sf.exists(url):
            size = sf.getSize(url)
            return url, size
        stream = self.Provider.getDocumentContent(self.Request, content)
        if stream:
            try:
                sf.writeFile(url, stream)
            except Exception as e:
                self._logger.logprb(SEVERE, 'ContentUser', 'getDocumentContent()', 421, e, traceback.format_exc())
            else:
                size = sf.getSize(url)
                loaded = self.DataBase.updateConnectionMode(self.Id, itemid, OFFLINE, ONLINE)
                content.insertValue('ConnectionMode', loaded)
            finally:
                stream.closeInput()
        return url, size

    def insertNewContent(self, content):
        timestamp = currentDateTimeInTZ()
        self.DataBase.insertNewContent(self.Id, content, timestamp)
        return True

    def deleteNewIdentifier(self, itemid):
        if self.Provider.GenerateIds:
            self.DataBase.deleteNewIdentifier(self.Id, itemid)

    def getContentScheme(self, authority):
        name = self.Name if authority else ''
        return '%s://%s' % (g_scheme, name)

    def _getNewContent(self, parentid, path, contentype):
        timestamp = currentUnoDateTime()
        isfolder = self.Provider.isFolder(contentype)
        isdocument = self.Provider.isDocument(contentype)
        itemid = self._getNewIdentifier()
        data = KeyMap()
        data.insertValue('Id', itemid)
        data.insertValue('ParentId', parentid)
        data.insertValue('Path', path)
        data.insertValue('ObjectId', itemid)
        data.insertValue('Title', '')
        data.insertValue('TitleOnServer', '')
        data.insertValue('DateCreated', timestamp)
        data.insertValue('DateModified', timestamp)
        data.insertValue('ContentType', contentype)
        mediatype = '' if isdocument else contentype
        data.insertValue('MediaType', mediatype)
        data.insertValue('Size', 0)
        data.insertValue('Trashed', False)
        data.insertValue('IsRoot', False)
        data.insertValue('IsFolder', isfolder)
        data.insertValue('IsDocument', isdocument)
        data.insertValue('CanAddChild', isfolder)
        data.insertValue('CanRename', True)
        data.insertValue('IsReadOnly', False)
        data.insertValue('IsVersionable', isdocument)
        data.insertValue('ConnectionMode', True)
        data.insertValue('BaseURI', path)
        return data

    def _getNewIdentifier(self):
        if self.Provider.GenerateIds:
            identifier = self.DataBase.getNewIdentifier(self.Id)
        else:
            identifier = binascii.hexlify(uno.generateUuid().value).decode('utf-8')
        return identifier

    def _removeIdentifiers(self):
        for url in tuple(self._identifiers.keys()):
            if url.startswith(self._expired):
                with self._lock:
                    if url in self._identifiers:
                        del self._identifiers[url]
        self._expired = None


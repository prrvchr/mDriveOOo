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

from ..oauth2lib import getOAuth2UserName
from ..oauth2lib import getRequest
from ..oauth2lib import g_oauth2

from ..dbtool import currentUnoDateTime

from ..unotool import createService
from ..unotool import getProperty

from ..database import DataBase

from ..logger import getLogger

from ..configuration import g_defaultlog
from ..configuration import g_scheme

from .content import Content
from .contentidentifier import ContentIdentifier
from .contenttools import getContentInfo

g_basename = 'user'

import binascii
import traceback


class ContentUser():
    def __init__(self, ctx, source, database, provider, name, sync, lock, password=''):
        print("ContentUser.__init__() 1")
        self._ctx = ctx
        self._name = name
        self._sync = sync
        self._lock = lock
        self._expired = None
        self._authority = True
        self.Provider = provider
        #self.CanAddChild = not self.Provider.GenerateIds
        self.CanAddChild = True
        self.Request = getRequest(ctx, self.Provider.Scheme, name)
        self._logger = getLogger(ctx, g_defaultlog, g_basename)
        data = database.selectUser(name)
        new = data is None
        print("ContentUser.__init__() 2")
        if new:
            if not self.Provider.isOnLine():
                msg = self._logger.resolveString(112, name)
                raise IllegalIdentifierException(msg, source)
            user = self.Provider.getUser(self.Request, name)
            if not user.IsPresent:
                msg = self._logger.resolveString(113, name)
                raise IllegalIdentifierException(msg, source)
            root = self.Provider.getRoot(self.Request, user.Value)
            if not root.IsPresent:
                msg = self._logger.resolveString(113, name)
                raise IllegalIdentifierException(msg, source)
            data = database.insertUser(self.Provider, user.Value, root.Value)
            if not database.createUser(name, password):
                msg = self._logger.resolveString(114, name)
                raise IllegalIdentifierException(msg, source)
        self.MetaData = data
        self.DataBase = DataBase(ctx, database.getDataSource(), name, password, sync)
        self._contents = {}
        self._logger.logprb(INFO, 'User', '__init__()', 101)
        if new:
            self._sync.set()
        print("ContentUser.__init__() 3")

    @property
    def Name(self):
        return self._name
    @property
    def Id(self):
        return self.MetaData.getDefaultValue('UserId', None)
    @property
    def RootId(self):
        return self.MetaData.getDefaultValue('RootId', None)
    @property
    def RootName(self):
        return self.MetaData.getDefaultValue('RootName', None)
    @property
    def Token(self):
        return self.MetaData.getDefaultValue('Token', '')

    def getContent(self, identifier, uri, authority=None):
        #if authority is not None:
        #    self._authority = authority
        url = self._getContentKey(uri)
        if self._expired is not None and url.startswith(self._expired):
            self._removeContents()
        else:
            content = self._contents.get(url)
        if content is None:
            content = Content(self._ctx, self, identifier, uri)
            self._contents[url] = content
        else:
            content.setIdentifier(identifier)
        return content

    def getContentUrl(self, path):
        name = self.Name if self._authority else ''
        return '%s://%s%s' % (g_scheme, name, path)

    def addContent(self, identifier):
        key = identifier.getContentIdentifier()
        print("User.addIdentifier() Uri: %s - Id: %s" % (key, identifier.Id))
        if key not in self._identifiers:
            with self._lock:
                self._identifiers[key] = identifier

    def expireContent(self, uri):
        # FIXME: We need to remove all the child of a resource (if it's a folder)
         self._expired = self._getContentKey(uri)

    def createNewContent(self, id, uri, contentype):
        print("ContentUser.createNewContent() 1")
        data = self._getNewContent(id, uri, contentype)
        print("ContentUser.createNewContent() 2")
        identifier = ContentIdentitifier(self.getContentUrl(uri))
        content = Content(self._ctx, self, identifier, uri, data)
        print("ContentUser.createNewContent() 3")
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
        url = '%s/%s' % (self.Provider.SourceURL, itemid)
        if content.getValue('Loaded') == OFFLINE and sf.exists(url):
            size = sf.getSize(url)
            return url, size
        stream = self.Provider.getDocumentContent(self.Request, content)
        if stream:
            try:
                sf.writeFile(url, stream)
            except Exception as e:
                self._logger.logprb(SEVERE, 'ContentUser', 'getDocumentContent()', 131, e, traceback.print_exc())
            else:
                size = sf.getSize(url)
                loaded = self.DataBase.updateLoaded(self.Id, itemid, OFFLINE, ONLINE)
                content.insertValue('Loaded', loaded)
            finally:
                stream.closeInput()
        return url, size

    def getFolderContent(self, content, properties):
        try:
            select, updated = self._getFolderContent(content, properties, False)
            if updated:
                itemid = content.getValue('Id')
                loaded = self.DataBase.updateLoaded(self.Id, itemid, OFFLINE, ONLINE)
                content.insertValue('Loaded', loaded)
            return select
        except Exception as e:
            msg = "Error: %s" % traceback.print_exc()
            print(msg)
            raise e

    def insertNewContent(self, content):
        timestamp = currentDateTimeInTZ()
        print("Identifier.insertNewContent() 1")
        uri, title = self.DataBase.insertNewContent(self.Id, content, timestamp)
        print("Identifier.insertNewContent() 2 Path: %s - BaseName: %s" % (uri, title))
        content.setValue('Title', title)
        content.setValue('TitleOnServer', title)
        content.setValue('BaseURI', uri)
        return True

    def deleteNewIdentifier(self, itemid):
        if self.Provider.GenerateIds:
            self.DataBase.deleteNewIdentifier(self.Id, itemid)

    def _getNewContent(self, id, uri, contentype):
        timestamp = currentUnoDateTime()
        isfolder = self.Provider.isFolder(contentype)
        isdocument = self.Provider.isDocument(contentype)
        itemid = self._getNewIdentifier()
        print("ContentUser._getNewContent() New Uri: %s - NewID: %s" % (uri, itemid))
        data = KeyMap()
        data.insertValue('Uri', uri)
        data.insertValue('Id', itemid)
        data.insertValue('ParentId', id)
        data.insertValue('ParentUri', uri)
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
        data.insertValue('Loaded', True)
        data.insertValue('BaseURI', uri)
        return data

    def _getNewIdentifier(self):
        if self.Provider.GenerateIds:
            identifier = self.DataBase.getNewIdentifier(self.Id)
        else:
            identifier = binascii.hexlify(uno.generateUuid().value).decode('utf-8')
        return identifier

    def _getFolderContent(self, content, properties, updated):
        itemid = content.getValue('Id')
        if ONLINE == content.getValue('Loaded') == self.Provider.SessionMode:
            self._logger.logprb(INFO, 'ContentUser', '_getFolderContent()', 141, content.getValue('Uri'))
            updated = self.DataBase.updateFolderContent(self, content)
        mode = self.Provider.SessionMode
        select = self.DataBase.getChildren(self.Name, itemid, properties, mode, self._authority)
        print("ContentUser._getFolderContent()")
        return select, updated

    def _removeContents(self):
        for url in tuple(self._contents.keys()):
            if url.startswith(self._expired):
                with self._lock:
                    if url in self._contents:
                        del self._contents[url]
        self._expired = None

    def _getContentKey(self, uri):
        return self.Name + uri













    # XRestUser
    def isValid(self):
        return self.Id is not None
    def setDataBase(self, datasource, sync, password=''):
        self.DataBase = DataBase(self._ctx, datasource, self.Name, password, sync)
    def getCredential(self, password):
        return self.Name, password

    def isInitialized(self):
        return self._initialized

    def initialize(self, datasource, url, password=''):
        print("User.initialize() 1")
        if self.Name is None:
            self._setUserName(datasource, url)
        if self.Request is None:
            msg = self._logger.resolveString(111, g_oauth2)
            raise IllegalIdentifierException(msg, self)
        print("User.initialize() 2")
        self.MetaData = datasource.DataBase.selectUser(self._name)
        print("User.initialize() 3")
        if self.MetaData is None:
            if not self.Provider.isOnLine():
                msg = self._logger.resolveString(112, self._name)
                raise IllegalIdentifierException(msg, self)
            data = self.Provider.getUser(self.Request, self._name)
            if not data.IsPresent:
                msg = self._logger.resolveString(113, self._name)
                raise IllegalIdentifierException(msg, self)
            root = self.Provider.getRoot(self.Request, data.Value)
            if not root.IsPresent:
                msg = self._logger.resolveString(113, self._name)
                raise IllegalIdentifierException(msg, self)
            self.MetaData = datasource.DataBase.insertUser(self.Provider, data.Value, root.Value)
            if not datasource.DataBase.createUser(self._name, password):
                msg = self._logger.resolveString(114, self._name)
                raise IllegalIdentifierException(msg, self)
        self.DataBase = DataBase(self._ctx, datasource.DataBase.getDataSource(), self._name, password, self._sync)
        print("User.initialize() 4")
        datasource.addUser(self)
        print("User.initialize() 5")
        self._initialized = True
        self._sync.set()
        print("User.initialize() 6")

    def getIdentifier(self, url):
        identifier = None
        if self._expired is not None and url.startswith(self._expired):
            self._removeIdentifiers()
        else:
            identifier = self._identifiers.get(url)
        if identifier is None:
            identifier = Identifier(self._ctx, self, url)
        return identifier

    def updateIdentifier(self, event):
        pass

    def addIdentifier(self, identifier):
        key = identifier.getContentIdentifier()
        print("User.addIdentifier() Uri: %s - Id: %s" % (key, identifier.Id))
        if key not in self._identifiers:
            with self._lock:
                self._identifiers[key] = identifier

    def expireIdentifier(self, url):
        # FIXME: We need to remove all the child of a resource (if it's a folder)
        self._expired = url

    def _removeIdentifiers(self):
        for url in tuple(self._identifiers.keys()):
            if url.startswith(self._expired):
                with self._lock:
                    if url in self._identifiers:
                        del self._identifiers[url]
        self._expired = None

# Internal use of method
    def _setUserName(self, datasource, url):
        name = getOAuth2UserName(self._ctx, self, self.Provider.Scheme)
        if not name:
            msg = self._logger.resolveString(121, url)
            raise IllegalIdentifierException(msg, self)
        self.Request = getRequest(self._ctx, self.Provider.Scheme, name)
        self._name = name


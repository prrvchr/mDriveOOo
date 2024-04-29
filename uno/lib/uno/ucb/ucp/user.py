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

from com.sun.star.ucb.ContentInfoAttribute import KIND_DOCUMENT
from com.sun.star.ucb.ContentInfoAttribute import KIND_FOLDER

from com.sun.star.ucb import IllegalIdentifierException

from ..oauth2 import getRequest
from ..oauth2 import g_oauth2

from ..dbtool import currentDateTimeInTZ
from ..dbtool import currentUnoDateTime

from ..unotool import getProperty
from ..unotool import getUriFactory

from ..database import DataBase

from .content import Content

from .contenthelper import getContentInfo
from .contenthelper import getExceptionMessage

from .configuration import g_ucbfolder
from .configuration import g_ucbfile
from .configuration import g_ucbseparator

from ..configuration import g_extension
from ..configuration import g_ucpfolder
from ..configuration import g_scheme

from threading import Event
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
        self._paths = {}
        self._contents = {}
        self._lock = None
        if new:
            # Start Replicator for pushing changes…
            self._lock = Event()
            self._sync.set()
        self._logger.logprb(INFO, 'User', method, 509)

    @property
    def Name(self):
        return self.MetaData.get('UserName')
    @property
    def Id(self):
        return self.MetaData.get('UserId')
    @property
    def RootId(self):
        return self.MetaData.get('RootId')
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
    def DateCreated(self):
        return self.MetaData.get('DateCreated')
    @property
    def DateModified(self):
        return self.MetaData.get('DateModified')
    @property
    def TimeStamp(self):
        return self.MetaData.get('TimeStamp')
    @TimeStamp.setter
    def TimeStamp(self, timestamp):
        self.MetaData['TimeStamp'] = timestamp

    def setToken(self, token):
        self.MetaData['Token'] = token

    # method called from Replicator
    def releaseLock(self):
        self.SyncMode = 1
        if self._lock is not None and not self._lock.is_set():
            self._lock.set()

    # method called from ContentResultSet.queryContent()
    def getContentByUrl(self, authority, url):
        uri = self._getUriFactory().parse(url)
        return self.getContent(authority, uri)

    # method called from Content.getParent()
    def getContentByParent(self, authority, itemid, path):
        isroot = itemid == self.RootId
        return self._getContent(authority, self._getPath(path, isroot), isroot)

    # method called from DataSource.queryContent()
    def getContent(self, authority, uri):
        isroot = uri.getPathSegmentCount() == 0
        return self._getContent(authority, uri.getPath(), isroot)

    def setLock(self):
        if self._lock is not None and not self.SyncMode:
            self._lock.wait()

    # method called from Content._identifier
    def getContentIdentifier(self, authority, path, title):
        return self._getScheme(authority) + path + title

    def createNewContent(self, authority, parentid, path, title, contentype):
        data = self._getNewContent(parentid, path, title, contentype)
        content = Content(self._ctx, self, authority, data, True)
        return content

    def getCreatableContentsInfo(self, canaddchild):
        content = []
        if self.CanAddChild and canaddchild:
            properties = (getProperty('Title', 'string', BOUND), )
            content.append(getContentInfo(g_ucbfolder, KIND_FOLDER, properties))
            content.append(getContentInfo(g_ucbfile, KIND_DOCUMENT, properties))
            #if self.Provider.hasProprietaryFormat:
            #    content.append(getContentInfo(self.Provider.ProprietaryFormat, KIND_DOCUMENT, properties))
        return tuple(content)

    def updateContent(self, itemid, property, value):
        updated, clear = self.DataBase.updateContent(self.Id, itemid, property, value)
        if clear:
            # if Title as been changed then we need to clear paths cache
            self._paths = {}
        if updated:
            # Start Replicator for pushing changes…
            self._sync.set()

    def insertNewContent(self, authority, content):
        timestamp = currentDateTimeInTZ()
        inserted = self.DataBase.insertNewContent(self.Id, content, timestamp)
        if inserted :
            # Start Replicator for pushing changes…
            self._sync.set()
        return inserted

    def deleteNewIdentifier(self, itemid):
        if self.Provider.GenerateIds:
            self.DataBase.deleteNewIdentifier(self.Id, itemid)

    def getChildren(self, authority, path, title, properties):
        scheme = self._getScheme(authority)
        return self.DataBase.getChildren(self.Id, scheme, self._composePath(path, title), properties, self.SessionMode)

    def getChildId(self, parentid, path, title, newtitle):
        return self.DataBase.getChildId(parentid, self._composePath(path, title), newtitle)

    def updateConnectionMode(self, itemid, mode):
        return self.DataBase.updateConnectionMode(self.Id, itemid, mode)

    def getRootMetaData(self):
        return self._getContentMetaData(self.RootId, g_ucbseparator, '', None, True, True,
                                        g_ucbfolder, self.DateCreated, self.DateModified)

    # Private methods
    def _getContent(self, authority, path, isroot):
        # XXX: Calls can be made with identifiers that do not exist,
        # XXX: in this case we must return None.
        data = None
        if isroot:
            data = self.getRootMetaData()
        else:
            data = self.DataBase.getItem(self.Id, path)
        content = None
        if data is not None:
            content = Content(self._ctx, self, authority, data)
        return content

    def _getScheme(self, authority):
        scheme = g_scheme + '://'
        if authority:
            scheme += self.Name
        return scheme

    def _getPath(self, path, isroot):
        # XXX: Only the root has a slash as its identifier,
        # XXX: all others have an identifier that ends with its name
        if not isroot:
            path = path.rstrip(g_ucbseparator)
        return path

    def _composePath(self, path, title):
        path += title
        # XXX: If the path doesn't end with a slash, we need to add one
        if not path.endswith(g_ucbseparator):
            path += g_ucbseparator
        return path

    def _getNewContent(self, parentid, path, title, contentype):
        timestamp = currentUnoDateTime()
        isfolder = contentype == g_ucbfolder
        itemid = self._getNewIdentifier()
        path = self._composePath(path, title)
        return self._getContentMetaData(itemid, path, '', parentid, False,
                                        isfolder, contentype, timestamp, timestamp)

    def _getContentMetaData(self, itemid, path, title, parentid, isroot, isfolder, contentype, created, modified):
        return {'Id':                   itemid,
                'ObjectId':             itemid,
                'Path':                 path,
                'Name':                 title,
                'Title':                title,
                'ParentId':             parentid,
                'DateCreated':          created,
                'DateModified':         modified,
                'ContentType':          contentype,
                'MediaType':            g_ucpfolder if isfolder else '',
                'Size':                 0,
                'Link':                 '',
                'Trashed':              False,
                'IsRoot':               isroot,
                'IsFolder':             isfolder,
                'IsDocument':           not isfolder,
                'CanAddChild':          isfolder,
                'CanRename':            not isroot,
                'IsReadOnly':           False,
                'IsVersionable':        not isfolder,
                'ConnectionMode':       1,
                'IsHidden':             False,
                'IsVolume':             False,
                'IsRemote':             False,
                'IsRemoveable':         False,
                'IsFloppy':             False,
                'IsCompactDisc':        False}

    def _getUriFactory(self):
        if self._factory is None:
            self._factory = getUriFactory(self._ctx)
        return self._factory

    def _getNewIdentifier(self):
        if self.Provider.GenerateIds:
            identifier = self.DataBase.getNewIdentifier(self.Id)
        else:
            identifier = binascii.hexlify(uno.generateUuid().value).decode('utf-8')
        return identifier

    def _getExceptionMessage(self, method, code, *args):
        return getExceptionMessage(self._ctx, self._logger, 'User', method, code, g_extension, *args)


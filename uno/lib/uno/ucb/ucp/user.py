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
from ..configuration import g_folder
from ..configuration import g_content

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
        self._ids = {'/': rootid}
        self._paths = {}
        self._contents = {}
        if new:
            # Start Replicator for pushing changes…
            self._sync.set()
        self._logger.logprb(INFO, 'User', method, 509)
        print("User.__init__()")

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

    # method called from ContentResultSet.queryContent()
    def getContentByUrl(self, authority, url):
        uri = self._getUriFactory().parse(url)
        return self.getContent(authority, uri)

    # method called from Content.getParent()
    def getContentByParent(self, authority, itemid, path):
        isroot = itemid == self.RootId
        if not isroot:
            # XXX: If this is not the root then we need to remove any trailing slash
            path = path.rstrip(g_separator)
        return self._getContent(authority, path, isroot)

    # method called from DataSource.queryContent()
    def getContent(self, authority, uri):
        isroot = uri.getPathSegmentCount() == 0
        return self._getContent(authority, uri.getPath(), isroot)

    def _getContent(self, authority, path, isroot):
        data = None
        itemid = None
        content = None
        if isroot:
            itemid = self.RootId
            data = self.getRootMetaData()
        else:
            if path in self._paths:
                itemid = self._paths[path]
            else:
                print("User._getContent() 2 Path: '%s'" % path)
                data, itemid = self._getMetaData(path)
        if itemid is not None:
            if itemid in self._contents:
                content = self._contents[itemid]
            else:
                if data is None:
                    data, itemid = self._getMetaData(path)
                print("User._getContent() 3")
                content = Content(self._ctx, self, authority, data)
                self._contents[itemid] = content
        print("User._getContent() 4")
        return content

    def _getMetaData(self, path):
        data = self.DataBase.getItem(self.Id, path)
        itemid = data.get('Id')
        self._paths[path] = itemid
        return data, itemid

    # method called from Content._identifier
    def getContentIdentifier(self, authority, path, title):
        identifier = self._getContentScheme(authority) + path + title
        print("User.getContentIdentifier() : %s" % identifier)
        return identifier

    def createNewContent(self, authority, parentid, path, title, link, contentype):
        data = self._getNewContent(parentid, path, title, link, contentype)
        content = Content(self._ctx, self, authority, data, True)
        return content

    def getTargetUrl(self, itemid):
        return self.Provider.SourceURL + g_separator + itemid

    def getCreatableContentsInfo(self, canaddchild):
        print("Content.getCreatableContentsInfo() 1")
        content = []
        if self.CanAddChild and canaddchild:
            properties = (getProperty('Title', 'string', BOUND), )
            content.append(getContentInfo(self.Provider.Folder, KIND_FOLDER, properties))
            content.append(getContentInfo(self.Provider.Office, KIND_DOCUMENT, properties))
            print("Content.getCreatableContentsInfo() 2")
            #if self.Provider.hasProprietaryFormat:
            #    content.append(getContentInfo(self.Provider.ProprietaryFormat, KIND_DOCUMENT, properties))
        print("Content.getCreatableContentsInfo() 3")
        return tuple(content)

    def getDocumentContent(self, sf, content, size):
        size = 0
        itemid = content.getValue('Id')
        url = self.getTargetUrl(itemid)
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
            self._ids = {'/': self.RootId}
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

    def getChildren(self, authority, path, properties):
        scheme = self._getContentScheme(authority)
        if not path.endswith(g_separator):
            # XXX: If the path doesn't end with a slash, we need to add one
            path += g_separator
        print("User.getChildren() 1 scheme: %s - path: %s" % (scheme, path))
        return self.DataBase.getChildren(path, properties, self.SessionMode, scheme)

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
        path = path + title + g_separator if parentid != self.RootId else path
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
                'MediaType':             '' if isdocument else g_folder,
                'ObjectId':              itemid,
                'ParentId':              parentid,
                'Size':                  0,
                'Path':                  path,
                'Title':                 'New File',
                'TitleOnServer':         'New File',
                'Id':                    itemid,
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

    def _getExceptionMessage(self, method, code, *args):
        return getExceptionMessage(self._ctx, self._logger, 'User', method, code, g_extension, *args)

    def getRootMetaData(self):
        return {'Id': self.RootId,
                'ObjectId': self.RootId,
                'Path': g_separator,
                'Title': '',
                'ParentId': None,
                'TitleOnServer': self.Name,
                'DateCreated': self.DateCreated,
                'DateModified': self.DateModified,
                'ContentType': g_content[g_folder],
                'MediaType': g_folder,
                'Size': 0,
                'Link': '',
                'Trashed': False,
                'IsRoot': True,
                'IsFolder': True,
                'IsLink': False,
                'IsDocument': False,
                'CanAddChild': True,
                'CanRename': True,
                'IsReadOnly': False,
                'IsVersionable': False,
                'ConnectionMode': 1,
                'IsHidden': False,
                'IsVolume': False,
                'IsRemote': True,
                'IsRemoveable': False,
                'IsFloppy': False,
                'IsCompactDisc': False}


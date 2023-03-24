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

from com.sun.star.container import XChild
from com.sun.star.lang import NoSupportException
from com.sun.star.ucb import XContentIdentifier
from com.sun.star.ucb import XRestIdentifier

from com.sun.star.ucb import IllegalIdentifierException

from com.sun.star.ucb.ContentInfoAttribute import KIND_DOCUMENT
from com.sun.star.ucb.ContentInfoAttribute import KIND_FOLDER
from com.sun.star.ucb.ContentInfoAttribute import KIND_LINK

from com.sun.star.beans.PropertyAttribute import BOUND
from com.sun.star.beans.PropertyAttribute import CONSTRAINED
from com.sun.star.beans.PropertyAttribute import READONLY
from com.sun.star.beans.PropertyAttribute import TRANSIENT

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb.ConnectionMode import OFFLINE
from com.sun.star.ucb.ConnectionMode import ONLINE

from .unolib import KeyMap

from .oauth2lib import getOAuth2UserName

from .unotool import getProperty

from .dbtool import currentUnoDateTime
from .dbtool import currentDateTimeInTZ

from .content import Content
from .contenttools import getContentInfo

from .logger import getLogger

from .configuration import g_defaultlog

g_basename = 'identifier'

import binascii
import traceback


class Identifier(unohelper.Base,
                 XContentIdentifier,
                 XRestIdentifier,
                 XChild):
    def __init__(self, ctx, user, url, data=None):
        self._ctx = ctx
        self._url = url
        self.User = user
        self._oldtitle = None
        self.IsNew = data is not None
        self.MetaData = KeyMap() if data is None else data
        self._propertySetInfo = self._getPropertySetInfo()
        self._content = Content(ctx, self) if self.IsNew else None
        self._logger = getLogger(ctx, g_defaultlog, g_basename)
        self._logger.logprb(INFO, 'Identifier', '__init__()', 101)

    @property
    def Url(self):
        return self._url
    @property
    def Id(self):
        return self.MetaData.getDefaultValue('Id', None)
    @property
    def ParentId(self):
        return self.MetaData.getDefaultValue('ParentId', None)
    @property
    def ParentURI(self):
        return self.MetaData.getDefaultValue('ParentURI', None)

    def isRoot(self):
        return self.Id == self.User.RootId
    def isFolder(self):
        return self.MetaData.getDefaultValue('IsFolder', True)
    def isValid(self):
        return all((self.User.isValid(), self.Id, self.MetaData.hasValue('ObjectId')))

    # XContentIdentifier
    def getContentIdentifier(self):
        return self._url
    def getContentProviderScheme(self):
        return self.User.Provider.Scheme

    # XChild
    def getParent(self):
        print("Identifier.getParent() 1")
        parent = None
        if not self.isRoot():
            print("Identifier.getParent() 2")
            parent = self.User.getIdentifier(self.ParentURI)
        print("Identifier.getParent() 3")
        return parent
    def setParent(self, parent):
        msg = self._logger.resolveString(111)
        raise NoSupportException(msg, self)

    # XRestIdentifier
    def createNewContent(self, contentype):
        print("Identifier.createNewContent() 1")
        data = self._getNewContent(contentype)
        print("Identifier.createNewContent() 2")
        content = Identifier(self._ctx, self.User, self._url, data).getInnerContent()
        print("Identifier.createNewContent() 3")
        return content

    # FIXME: Get called from Content.createNewContent() -> Identifier.createNewContent()
    def getInnerContent(self):
        return self._content

    # FIXME: Get called from Content.getParent(), ContentResultSet.queryContent() and User.removeIdentifiers()
    def getContent(self):
        try:
            print("Identifier.getContent() 1")
            if self._content is None:
                # When getContent is called, the user must already exist
                self._content = self._getContent()
            print("Identifier.getContent() 2")
            return self._content
        except Exception as e:
            msg = "Identifier.getContent() Error: %s" % traceback.print_exc()
            print(msg)
            raise e

    # FIXME: Get called from ContentProvider.queryContent()
    def queryContent(self, datasource):
        try:
            print("Identifier.queryContent() 1")
            if self._content is not None:
                return self._content
            if self._url is None:
                msg = self._logger.resolveString(121)
                raise IllegalIdentifierException(msg, self)
            if not self._isUrlValid():
                msg = self._logger.resolveString(122, self.getContentIdentifier())
                raise IllegalIdentifierException(msg, self)
            print("Identifier.queryContent() 2")
            if not self.User.isInitialized():
                self.User.initialize(datasource, self._url)
            print("Identifier.queryContent() 3")
            self._content = self._getContent()
            return self._content
        except Exception as e:
            msg = "Identifier.queryContent() Error: %s" % traceback.print_exc()
            print(msg)
            raise e

    def _getContent(self):
        try:
            print("Identifier._getContent() 1")
            self.MetaData = self._getMetaData()
            print("Identifier._getContent() 2")
            content = Content(self._ctx, self)
            self.User.addIdentifier(self)
            return content
        except Exception as e:
            msg = "Identifier._getContent() Error: %s" % traceback.print_exc()
            print(msg)
            raise e

    def getFolderContent(self, content):
        try:
            select, updated = self._getFolderContent(content, False)
            if updated:
                loaded = self.User.DataBase.updateLoaded(self.User.Id, self.Id, OFFLINE, ONLINE)
                content.insertValue('Loaded', loaded)
            return select
        except Exception as e:
            msg = "Error: %s" % traceback.print_exc()
            print(msg)
            raise e

    def getDocumentContent(self, sf, content, size):
        size = 0
        url = '%s/%s' % (self.User.Provider.SourceURL, self.Id)
        if content.getValue('Loaded') == OFFLINE and sf.exists(url):
            size = sf.getSize(url)
            return url, size
        stream = self.User.Provider.getDocumentContent(self.User.Request, content)
        if stream:
            try:
                sf.writeFile(url, stream)
            except Exception as e:
                self._logger.logprb(SEVERE, 'Identifier', 'getDocumentContent()', 131, e, traceback.print_exc())
            else:
                size = sf.getSize(url)
                loaded = self.User.DataBase.updateLoaded(self.User.Id, self.Id, OFFLINE, ONLINE)
                content.insertValue('Loaded', loaded)
            finally:
                stream.closeInput()
        return url, size

    def insertNewContent(self, content):
        timestamp = currentDateTimeInTZ()
        print("Identifier.insertNewContent() 1")
        path, basename = self.User.DataBase.insertNewContent(self.User.Id, self.Id, self.ParentId, content, timestamp)
        print("Identifier.insertNewContent() 2 Path: %s - BaseName: %s" % (path, basename))
        return self._setNewTitle(path, basename)

    def setTitle(self, title):
        try:
            # If Title change we need to change Identifier.getContentIdentifier()
            print("Identifier.setTitle() 1 New Title: %s - IsNew: %s" % (title, self.IsNew))
            if not self.IsNew:
                # And as the uri changes we also have to clear this Identifier from the cache.
                # New Identifier bypass the cache: they are created by the folder's Identifier
                # (ie: createNewIdentifier()) and have same uri as this folder.
                self.User.expireIdentifier(self._url)
            if self.User.Provider.SupportDuplicate:
                newtitle = self.User.DataBase.getNewTitle(title, self.ParentId, self.isFolder())
            else:
                newtitle = title
            print("Identifier.setTitle() 2 Title: %s - New Title: %s" % (title, newtitle))
            self._url = '%s/%s' % (self.ParentURI, newtitle)
            self.MetaData.setValue('Title', newtitle)
            self.MetaData.setValue('TitleOnServer', newtitle)
            # If the identifier is new then the content is not yet in the database.
            # It will be inserted by the insert command of the XCommandProcessor2.execute()
            if not self.IsNew:
                self.User.DataBase.updateContent(self.User.Id, self.Id, 'Title', title)
            #if newtitle != title:
            #    action = uno.Enum('com.sun.star.ucb.ContentAction', 'EXCHANGED')
            #    self._content.notifyContentListener(action, self)
            print("Identifier.setTitle() 3 Title")
        except Exception as e:
            msg = "Identifier.setTitle() Error: %s" % traceback.print_exc()
            print(msg)

    def deleteNewIdentifier(self):
        if self.User.Provider.GenerateIds:
            self.User.DataBase.deleteNewIdentifier(self.User.Id, self.Id)

    def getCreatableContentsInfo(self):
        content = []
        if self.User.CanAddChild and self.MetaData.getValue('CanAddChild'):
            provider = self.User.Provider
            properties = (getProperty('Title', 'string', BOUND), )
            content.append(getContentInfo(provider.Folder, KIND_FOLDER, properties))
            content.append(getContentInfo(provider.Office, KIND_DOCUMENT, properties))
            #if provider.hasProprietaryFormat:
            #    content.append(getContentInfo(provider.ProprietaryFormat, KIND_DOCUMENT, properties))
        return tuple(content)

    # Private methods
    def _getMetaData(self):
        metadata = KeyMap()
        if self.IsNew:
            # FIXME: New Identifier are created by the parent folder...
            data = self._getNewContent()
        else:
            itemid, isroot = self.User.DataBase.getIdentifier(self._url, self.User.RootId)
            if itemid is None:
                msg = self._logger.resolveString(151, self.getContentIdentifier())
                raise IllegalIdentifierException(msg, self)
            data = self.User.DataBase.getItem(self.User.Id, itemid, isroot)
        if data is not None:
            metadata += data
        return metadata

    def _getNewIdentifier(self):
        if self.User.Provider.GenerateIds:
            identifier = self.User.DataBase.getNewIdentifier(self.User.Id)
        else:
            identifier = binascii.hexlify(uno.generateUuid().value).decode('utf-8')
        return identifier

    def _getNewContent(self, contentype):
        timestamp = currentUnoDateTime()
        isfolder = self.User.Provider.isFolder(contentype)
        isdocument = self.User.Provider.isDocument(contentype)
        itemid = self._getNewIdentifier()
        print("Identifier._getNewContent() New Uri: %s - NewID: %s" % (self._url, itemid))
        isroot = itemid == self.User.RootId
        data = KeyMap()
        data.insertValue('Id', itemid)
        data.insertValue('ParentId', self.Id)
        data.insertValue('ParentURI', self._url)
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
        data.insertValue('IsRoot', isroot)
        data.insertValue('IsFolder', isfolder)
        data.insertValue('IsDocument', isdocument)
        data.insertValue('CanAddChild', isfolder)
        data.insertValue('CanRename', True)
        data.insertValue('IsReadOnly', False)
        data.insertValue('IsVersionable', isdocument)
        data.insertValue('Loaded', True)
        data.insertValue('BaseURI', self._url)
        return data

    def _setNewTitle(self, url, title):
        self.MetaData.setValue('Title', title)
        self.MetaData.setValue('TitleOnServer', title)
        self.MetaData.setValue('BaseURI', url)
        self._url = url
        return True

    def _getFolderContent(self, content, updated):
        if ONLINE == content.getValue('Loaded') == self.User.Provider.SessionMode:
            self._logger.logprb(INFO, 'Identifier', '_getFolderContent()', 141, self.getContentIdentifier())
            updated = self.User.DataBase.updateFolderContent(self.User, content)
        mode = self.User.Provider.SessionMode
        select = self.User.DataBase.getChildren(self.Id, mode)
        print("Identifier._getFolderContent()")
        return select, updated

    def _getPropertySetInfo(self):
        RO = 0 if self.IsNew else READONLY
        properties = {}
        properties['ContentType'] = getProperty('ContentType', 'string', BOUND | RO)
        properties['MediaType'] = getProperty('MediaType', 'string', BOUND | READONLY)
        properties['IsDocument'] = getProperty('IsDocument', 'boolean', BOUND | RO)
        properties['IsFolder'] = getProperty('IsFolder', 'boolean', BOUND | RO)
        properties['Title'] = getProperty('Title', 'string', BOUND | CONSTRAINED)
        properties['Size'] = getProperty('Size', 'long', BOUND | RO)
        created = getProperty('DateCreated', 'com.sun.star.util.DateTime', BOUND | READONLY)
        properties['DateCreated'] = created
        modified = getProperty('DateModified', 'com.sun.star.util.DateTime', BOUND | RO)
        properties['DateModified'] = modified
        properties['IsReadOnly'] = getProperty('IsReadOnly', 'boolean', BOUND | RO)
        info = getProperty('CreatableContentsInfo','[]com.sun.star.ucb.ContentInfo', BOUND | RO)
        properties['CreatableContentsInfo'] = info
        properties['CasePreservingURL'] = getProperty('CasePreservingURL', 'string', BOUND | RO)
        properties['BaseURI'] = getProperty('BaseURI', 'string', BOUND | READONLY)
        properties['TitleOnServer'] = getProperty('TitleOnServer', 'string', BOUND)
        properties['IsHidden'] = getProperty('IsHidden', 'boolean', BOUND | RO)
        properties['IsVolume'] = getProperty('IsVolume', 'boolean', BOUND | RO)
        properties['IsRemote'] = getProperty('IsRemote', 'boolean', BOUND | RO)
        properties['IsRemoveable'] = getProperty('IsRemoveable', 'boolean', BOUND | RO)
        properties['IsFloppy'] = getProperty('IsFloppy', 'boolean', BOUND | RO)
        properties['IsCompactDisc'] = getProperty('IsCompactDisc', 'boolean', BOUND | RO)
        return properties

    def _getContentScheme(self):
        scheme = '%s://%s' % (self.User.Provider.Scheme, self.User.Name)
        print("Identifier._getContentScheme() : %s" % scheme)
        return scheme

    def _isUrlValid(self):
        # FIXME: LibreOffice seems to do a lot of UCB calls with an incomplete identifier like: 'vnd-google:' 
        # FIXME: for performance reasons we should not process these calls
        return self._url.startswith(self.User.Provider.Scheme + '://')

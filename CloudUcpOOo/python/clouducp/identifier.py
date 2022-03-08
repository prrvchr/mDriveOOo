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

from .unotool import getProperty
from .unotool import parseDateTime

from .content import Content
from .contenttools import getUcb
from .contenttools import getUri
from .contenttools import getUrl
from .contenttools import getContentInfo

from .logger import logMessage
from .logger import getMessage
g_message = 'identifier'

import binascii
import traceback


class Identifier(unohelper.Base,
                 XContentIdentifier,
                 XRestIdentifier,
                 XChild):
    def __init__(self, ctx, user, uri, contenttype=''):
        self.ctx = ctx
        self.User = user
        self._uri = uri
        self.IsNew = contenttype != ''
        self._propertySetInfo = {}
        self.MetaData = self._getMetaData(contenttype)
        msg = getMessage(self.ctx, g_message, 101)
        logMessage(self.ctx, INFO, msg, "Identifier", "__init__()")

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
        return self.MetaData.getValue('IsFolder')
    def isValid(self):
        return all((self.User.isValid(), self.Id, self.MetaData.hasValue('ObjectId')))
    def getUri(self):
        return self._uri

    # XContentIdentifier
    def getContentIdentifier(self):
        return self._uri.getUriReference()
    def getContentProviderScheme(self):
        return self._uri.getScheme()

    # XChild
    def getParent(self):
        parent = None
        if not self.isRoot():
            parent = getUcb(self.ctx).createContentIdentifier(self.ParentURI)
        return parent
    def setParent(self, parent):
        msg = getMessage(self.ctx, g_message, 111)
        raise NoSupportException(msg, self)

    # XRestIdentifier
    def createNewIdentifier(self, contenttype):
        return Identifier(self.ctx, self.User, self._uri, contenttype)

    def getContent(self):
        if not self.isValid():
            msg = getMessage(self.ctx, g_message, 121, self.getContentIdentifier())
            raise IllegalIdentifierException(msg, self)
        content = Content(self.ctx, self)
        return content

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
                msg = getMessage(self.ctx, g_message, 131, (e, traceback.print_exc()))
                logMessage(self.ctx, SEVERE, msg, "Identifier", "getDocumentContent()")
            else:
                size = sf.getSize(url)
                loaded = self.User.DataBase.updateLoaded(self.User.Id, self.Id, OFFLINE, ONLINE)
                content.insertValue('Loaded', loaded)
            finally:
                stream.closeInput()
        return url, size

    def insertNewContent(self, content):
        timestamp = parseDateTime()
        return self.User.DataBase.insertNewContent(self.User.Id, self.Id, self.ParentId, content, timestamp)

    def setTitle(self, title):
        # If Title change we need to change Identifier.getContentIdentifier()
        if not self.IsNew:
            # And as the uri changes we also have to clear this Identifier from the cache.
            # New Identifier bypass the cache: they are created by the folder's Identifier
            # (ie: createNewIdentifier()) and have same uri as this folder.
            url = '%s://%s/#%s' % (self._uri.getScheme(), self.User.Name, self.Id)
            getUcb(self.ctx).createContentIdentifier(url)
        url = self.ParentURI
        if not url.endswith('/'):
            url += '/'
        url += title
        self._uri = getUri(self.ctx, getUrl(self.ctx, url))
        self.MetaData.setValue('Title', title)
        # If the identifier is new then the content is not yet in the database.
        # It will be inserted by the insert command of the XCommandProcessor2.execute()
        if not self.IsNew:
            self.User.DataBase.updateContent(self.User.Id, self.Id, 'Title', title)

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
    def _getMetaData(self, contenttype):
        metadata = KeyMap()
        if not self.User.isValid():
            # Uri with Scheme but without a Path generate invalid user but we need
            # to return an Identifier, and raise an 'IllegalIdentifierException'
            # when ContentProvider try to get the Content...
            # (ie: ContentProvider.queryContent() -> Identifier.getContent())
            return metadata
        uripath = self._uri.getPath().strip('/.')
        itemid, parentid, path = self.User.DataBase.getIdentifier(self.User.Id, self.User.RootId, uripath)
        if itemid is not None:
            if self.IsNew:
                # New Identifier are created by the parent folder...
                metadata.setValue('ParentId', itemid)
                itemid = self._getNewIdentifier()
                parenturi = self._uri.getUriReference()
                data = self._getNewContent(itemid, contenttype)
            else:
                metadata.setValue('ParentId', parentid)
                parenturi = '%s://%s/%s' % (self._uri.getScheme(), self._uri.getAuthority(), path)
                data = self.User.DataBase.getItem(self.User.Id, itemid, parentid)
            metadata.setValue('Id', itemid)
            metadata.setValue('ParentURI', parenturi)
            if data is not None:
                metadata += data
                self._propertySetInfo = self._getPropertySetInfo()
        return metadata

    def _getNewIdentifier(self):
        if self.User.Provider.GenerateIds:
            identifier = self.User.DataBase.getNewIdentifier(self.User.Id)
        else:
            identifier = binascii.hexlify(uno.generateUuid().value).decode('utf-8')
        return identifier

    def _getNewContent(self, itemid, contenttype):
        timestamp = parseDateTime()
        isfolder = self.User.Provider.isFolder(contenttype)
        isdocument = self.User.Provider.isDocument(contenttype)
        isroot = itemid == self.User.RootId
        data = KeyMap()
        data.insertValue('Id', itemid)
        data.insertValue('ObjectId', itemid)
        data.insertValue('Title', '')
        data.insertValue('TitleOnServer', '')
        data.insertValue('DateCreated', timestamp)
        data.insertValue('DateModified', timestamp)
        data.insertValue('ContentType', contenttype)
        mediatype = '' if isdocument else contenttype
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
        data.insertValue('BaseURI', self.getContentIdentifier())
        return data

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

    def _getFolderContent(self, content, updated):
        if ONLINE == content.getValue('Loaded') == self.User.Provider.SessionMode:
            msg = getMessage(self.ctx, g_message, 141, self.getContentIdentifier())
            logMessage(self.ctx, INFO, msg, "Identifier", "_getFolderContent()")
            updated = self.User.DataBase.updateFolderContent(self.User, content)
        url = self.getContentIdentifier()
        if not url.endswith('/'):
            url += '/'
        mode = self.User.Provider.SessionMode
        select = self.User.DataBase.getChildren(self.User.Id, self.Id, url, mode)
        print("Identifier._getFolderContent()")
        return select, updated

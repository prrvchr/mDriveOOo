#!
# -*- coding: utf_8 -*-

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

from unolib import KeyMap
from unolib import getProperty
from unolib import parseDateTime

from .content import Content
from .contenttools import getUcb
from .contenttools import getUri
from .contenttools import getUrl
from .contenttools import getContentInfo
from .logger import logMessage

import binascii
import traceback


class Identifier(unohelper.Base,
                 XContentIdentifier,
                 XRestIdentifier,
                 XChild):
    def __init__(self, ctx, user, uri, callBack, contenttype=''):
        msg = "Identifier loading"
        self.ctx = ctx
        self.User = user
        self._uri = uri
        self.callBack = callBack
        self.IsNew = contenttype != ''
        self._propertySetInfo = {}
        self.MetaData = self._getIdentifier(contenttype)
        msg += " ... Done"
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
        raise NoSupportException('Parent can not be set', self)

    # XRestIdentifier
    def createNewIdentifier(self, contenttype):
        identifier = Identifier(self.ctx, self.User, self._uri, self.callBack, contenttype)
        return identifier

    def getContent(self):
        if not self.isValid():
            msg = "Error: can't retreive Identifier"
            print("Identifier.getContent() 1")
            raise IllegalIdentifierException(msg, self)
        content = Content(self.ctx, self)
        return content

    def getFolderContent(self, content):
        select, updated = self._getFolderContent(content, False)
        if updated:
            loaded = self.User.DataBase.updateLoaded(self.User.Id, self.Id, OFFLINE, ONLINE)
            content.insertValue('Loaded', loaded)
        return select

    def _getFolderContent(self, content, updated):
        if ONLINE == content.getValue('Loaded') == self.User.Provider.SessionMode:
            print("DataBase.getFolderContent() whith request *********************************")
            updated = self.User.DataBase.updateFolderContent(self.User, content)
        url = self.getContentIdentifier()
        if not url.endswith('/'):
            url += '/'
        mode = self.User.Provider.SessionMode
        select = self.User.DataBase.getChildren(self.User.Id, self.Id, url, mode)
        return select, updated

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
                msg = "ERROR: %s - %s" % (e, traceback.print_exc())
                logMessage(self.ctx, SEVERE, msg, "Identifier", "getDocumentContent()")
            else:
                size = sf.getSize(url)
                loaded = self.User.DataBase.updateLoaded(self.User.Id, self.Id, OFFLINE, ONLINE)
                content.insertValue('Loaded', loaded)
            finally:
                stream.closeInput()
        return url, size

    def insertNewContent(self, content):
        print("Identifier.insertNewContent() %s - %s" % (content.getValue('Title'), self.ParentId))
        timestamp = parseDateTime()
        return self.User.DataBase.insertNewContent(self.User.Id, self.Id, self.ParentId, content, timestamp)

    def setTitle(self, title):
        # If Title change we need to change Identifier.getContentIdentifier()
        print("Identifier.setTitle() 1")
        if not self.IsNew:
            print("Identifier.setTitle() 2")
            self.callBack(self.User, self._uri, self.isFolder())
        url = self.ParentURI
        if not url.endswith('/'):
            url += '/'
        url += title
        print("Identifier.setTitle() %s" % url)
        self._uri = getUri(self.ctx, getUrl(self.ctx, url))
        print("Identifier.setTitle() %s" % self.getContentIdentifier())
        return title

    def _getIdentifier(self, contenttype):
        identifier = KeyMap()
        if not self.User.isValid():
            # Uri with Scheme but without a Path generate invalid user but we need
            # to return an Identifier, and raise an 'IllegalIdentifierException'
            # when ContentProvider try to get the Content...
            # (ie: ContentProvider.queryContent() -> Identifier.getContent())
            return identifier
        userid = self.User.Id
        rootid = self.User.RootId
        uripath = self._uri.getPath().strip('/.')
        itemid, parentid, path = self.User.DataBase.getIdentifier(userid, rootid, uripath)
        if self.IsNew:
            # New Identifier are created by the parent folder...
            identifier.setValue('ParentId', itemid)
            itemid = self._getNewIdentifier()
            parenturi = self._uri.getUriReference()
        else:
            identifier.setValue('ParentId', parentid)
            parenturi = '%s://%s/%s' % (self._uri.getScheme(), self._uri.getAuthority(), path)
        identifier.setValue('Id', itemid)
        identifier.setValue('ParentURI', parenturi)
        if itemid is not None:
            if self.IsNew:
                data = self._getNewContent(itemid, contenttype)
            else:
                data = self.User.DataBase.getItem(self.User.Id, itemid, parentid)
            if data is not None:
                self._setCreatableContentsInfo(data)
                identifier += data
                self._propertySetInfo = self._getPropertySetInfo()
        return identifier

    def _getNewIdentifier(self):
        if self.User.Provider.GenerateIds:
            identifier = self.User.DataBase.getNewIdentifier(self.User.Id)
        else:
            identifier = binascii.hexlify(uno.generateUuid().value).decode('utf-8')
        return identifier

    def deleteNewIdentifier(self):
        if self.User.Provider.GenerateIds:
            self.User.DataBase.deleteNewIdentifier(self.User.Id, self.Id)

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
        mediatype = contenttype if isfolder else ''
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

    def _setCreatableContentsInfo(self, data):
        content = []
        if self.User.CanAddChild and data.getValue('CanAddChild'):
            provider = self.User.Provider
            properties = (getProperty('Title', 'string', BOUND), )
            content.append(getContentInfo(provider.Folder, KIND_FOLDER, properties))
            content.append(getContentInfo(provider.Office, KIND_DOCUMENT, properties))
            #if provider.hasProprietaryFormat:
            #    content.append(getContentInfo(provider.ProprietaryFormat, KIND_DOCUMENT, properties))
        data.insertValue('CreatableContentsInfo', tuple(content))

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

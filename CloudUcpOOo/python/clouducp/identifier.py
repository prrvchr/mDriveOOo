#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.container import XChild
from com.sun.star.lang import NoSupportException
from com.sun.star.ucb import XContentIdentifier
from com.sun.star.ucb import XRestIdentifier

from com.sun.star.ucb import IllegalIdentifierException

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb.ConnectionMode import OFFLINE
from com.sun.star.ucb.ConnectionMode import ONLINE

from unolib import KeyMap
from unolib import parseDateTime

from .content import Content
from .contenttools import getUri
from .contenttools import getUrl
from .logger import logMessage

import binascii
import traceback


class Identifier(unohelper.Base,
                 XContentIdentifier,
                 XRestIdentifier,
                 XChild):
    def __init__(self, ctx, user, uri, contenttype=''):
        msg = "Identifier loading"
        self.ctx = ctx
        self.User = user
        self._uri = uri
        self._contenttype = contenttype
        self.MetaData = self._getIdentifier()
        msg += " ... Done"
        print("Identifier.__init__() OK")
        logMessage(self.ctx, INFO, msg, "Identifier", "__init__()")

    @property
    def Id(self):
        return self.MetaData.getDefaultValue('Id', None)
    @property
    def ParentId(self):
        return self.MetaData.getDefaultValue('ParentId', None)
    @property
    def BaseURI(self):
        return self.MetaData.getDefaultValue('BaseURI', None)

    def isNew(self):
        return self._contenttype != ''
    def isRoot(self):
        return self.Id == self.User.RootId
    def isValid(self):
        return self.User.isValid() and self.Id is not None

    # XContentIdentifier
    def getContentIdentifier(self):
        return self._uri.getUriReference()
    def getContentProviderScheme(self):
        return self._uri.getScheme()

    # XChild
    def getParent(self):
        parent = None
        if not self.isRoot():
            uri = getUri(self.ctx, self.BaseURI)
            parent = Identifier(self.ctx, self.User, uri)
        return parent
    def setParent(self, parent):
        raise NoSupportException('Parent can not be set', self)

    # XRestIdentifier
    def createNewIdentifier(self, contenttype):
        print("Identifier.createNewIdentifier() %s" % (contenttype, ))
        identifier = Identifier(self.ctx, self.User, self._uri, contenttype)
        return identifier

    def getContent(self):
        print("Identifier.getContent() 1")
        if self.isNew():
            data = self._getNewContent()
        else:
            data = self.User.DataBase.getItem(self.User.Id, self.Id)
            print("Identifier.getContent()  2 %s" % data)
            #if data is None and self.User.Provider.isOnLine():
            #    data = self.User.Provider.getItem(self.User.Request, self.MetaData)
            #    if data.IsPresent:
            #        data = self.User.DataBase.insertAndSelectItem(self.User, data.Value)
        if data is None:
            msg = "Error: can't retreive Identifier"
            raise IllegalIdentifierException(msg, self)
        content = Content(self.ctx, self, data)
        print("Identifier.getContent() 3 OK")
        return content

    def getFolderContent(self, content):
        select, updated = self._getFolderContent(content, False)
        if updated:
            loaded = self.User.DataBase.updateLoaded(self.User.Id, self.Id, OFFLINE, ONLINE)
            content.insertValue('Loaded', loaded)
        return select

    def _getFolderContent(self, content, updated):
        try:
            if ONLINE == content.getValue('Loaded') == self.User.Provider.SessionMode:
                print("DataBase.getFolderContent() whith request")
                updated = self.User.DataBase.updateFolderContent(self.User, content)
            else:
                print("DataBase.getFolderContent() no request")
            url = self.getContentIdentifier().lstrip('/')
            mode = self.User.Provider.SessionMode
            select = self.User.DataBase.getChildren(self.User.Id, self.Id, url, mode)
            return select, updated
        except Exception as e:
            print("Identifier._getFolderContent().Error: %s - %s" % (e, traceback.print_exc()))

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
        url = self.BaseURI
        if not url.endswith('/'):
            url += '/'
        url += title
        print("Identifier.setTitle() %s" % url)
        self._uri = getUri(self.ctx, getUrl(self.ctx, url))
        print("Identifier.setTitle() %s" % self.getContentIdentifier())
        return title

    def _getIdentifier(self):
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
        if self.isNew():
            # New Identifier are created by the parent folder...
            identifier.setValue('Id', self._getNewIdentifier())
            identifier.setValue('ParentId', itemid)
            baseuri = self._uri.getUriReference()
        else:
            identifier.setValue('Id', itemid)
            identifier.setValue('ParentId', parentid)
            baseuri = '%s://%s/%s' % (self._uri.getScheme(), self._uri.getAuthority(), path)
        identifier.setValue('BaseURI', baseuri)
        print("Identifier._getIdentifier() %s - %s - %s" % (identifier.getValue('Id'),
                                                            identifier.getValue('ParentId'),
                                                            identifier.getValue('BaseURI')))
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

    def _getNewContent(self):
        try:
            print("Identifier._getNewContent() 1")
            timestamp = parseDateTime()
            isfolder = self.User.Provider.isFolder(self._contenttype)
            isdocument = self.User.Provider.isDocument(self._contenttype)
            data = KeyMap()
            data.insertValue('Id', self.Id)
            data.insertValue('ObjectId', self.Id)
            data.insertValue('Title', '')
            data.insertValue('TitleOnServer', '')
            data.insertValue('DateCreated', timestamp)
            data.insertValue('DateModified', timestamp)
            data.insertValue('ContentType',self._contenttype)
            mediatype = self._contenttype if isfolder else ''
            data.insertValue('MediaType', mediatype)
            data.insertValue('Size', 0)
            data.insertValue('Trashed', False)
            data.insertValue('IsRoot', self.isRoot())
            data.insertValue('IsFolder', isfolder)
            data.insertValue('IsDocument', isdocument)
            data.insertValue('CanAddChild', isfolder)
            data.insertValue('CanRename', True)
            data.insertValue('IsReadOnly', False)
            data.insertValue('IsVersionable', isdocument)
            data.insertValue('Loaded', True)
            data.insertValue('BaseURI', self.getContentIdentifier())
            print("Identifier._getNewContent() 2 %s - %s" % (self.Id, self.getContentIdentifier()))
            return data
        except Exception as e:
            print("Identifier._getNewContent() ERROR: %s - %s" % (e, traceback.print_exc()))

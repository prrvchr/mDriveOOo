#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.lang import XServiceInfo
from com.sun.star.ucb import IllegalIdentifierException

from onedrive import InputStream
from onedrive import doSync
from onedrive import updateChildren

from onedrive import getItem
from onedrive import selectItem
from onedrive import insertJsonItem
from onedrive import isIdentifier
from onedrive import selectChildId

from onedrive import g_doc_map
from onedrive import g_folder
from onedrive import g_link
from onedrive import g_plugin

# clouducp is only available after CloudUcpOOo as been loaded...
try:
    from clouducp import ContentIdentifierBase
except ImportError:
    class ContentIdentifierBase():
        pass
# requests is only available after OAuth2OOo as been loaded...
try:
    from oauth2.requests.compat import unquote_plus
except ImportError:
    def unquote_plus():
        pass

import binascii
import traceback

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = '%s.ContentIdentifier' % g_plugin


class ContentIdentifier(ContentIdentifierBase,
                        XServiceInfo):
    def __init__(self, ctx, *namedvalues):
        ContentIdentifierBase.__init__(self, ctx, namedvalues)
    @property
    def Properties(self):
        print("oneDriveOOo.ContentIdentifier.Properties")
        return ('Name', 'DateCreated', 'DateModified', 'MimeType',
                'Size', 'Trashed', 'Loaded')

    def getPlugin(self):
        return g_plugin
    def getFolder(self):
        return g_folder
    def getLink(self):
        return g_link
    def getDocument(self):
        return g_doc_map
    def getInputStream(self):
        return InputStream(self.Session, self.Id, self.Size)
    def doSync(self, session):
        return doSync(self.ctx, self.getContentProviderScheme(), self.User.Connection, session, self.User.Id)
    def updateChildren(self, session):
        return updateChildren(session, self.User.Connection, self.User.Id, self.Id, self.User.RootId)
    def getNewIdentifier(self):
        return binascii.hexlify(uno.generateUuid().value).decode('utf-8')
    def getItem(self, session):
        return getItem(session, self.Id)
    def selectItem(self):
        return selectItem(self.User.Connection, self.User.Id, self.Id)
    def insertJsonItem(self, data):
        return insertJsonItem(self.User.Connection, self.User.Id, self.User.RootId, data)
    def isIdentifier(self, title):
        return isIdentifier(self.User.Connection, self.User.Id, title)
    def selectChildId(self, parent, title):
        return selectChildId(self.User.Connection, self.User.Id, parent, title)
    def unquote(self, text):
        return unquote_plus(text)

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(ContentIdentifier,                                                  # UNO object class
                                         g_ImplementationName,                                               # Implementation name
                                        (g_ImplementationName, ))                                            # List of implemented services

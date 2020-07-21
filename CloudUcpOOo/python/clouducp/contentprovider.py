#!
# -*- coding: utf_8 -*-
import traceback

try:
    import uno
    import unohelper

    from com.sun.star.logging.LogLevel import INFO
    from com.sun.star.logging.LogLevel import SEVERE

    from com.sun.star.ucb import XContentIdentifierFactory
    from com.sun.star.ucb import XContentProvider
    from com.sun.star.ucb import XParameterizedContentProvider
    from com.sun.star.ucb import IllegalIdentifierException

    from com.sun.star.ucb import XRestContentProvider

    from unolib import getUserNameFromHandler

    from .contenttools import getUrl
    from .contenttools import getUri

    from .datasource import DataSource
    from .user import User
    from .identifier import Identifier

    from .logger import logMessage
    from .logger import getMessage

except Exception as e:
    print("clouducp.__init__() ERROR: %s - %s" % (e, traceback.print_exc()))

from threading import Event

class ContentProvider(unohelper.Base,
                      XContentIdentifierFactory,
                      XContentProvider,
                      XParameterizedContentProvider,
                      XRestContentProvider):
    def __init__(self, ctx, plugin):
        self.ctx = ctx
        self.Scheme = ''
        self.Plugin = plugin
        self.DataSource = None
        self.event = Event()
        self._currentUserName = None
        self._error = None
        msg = "ContentProvider: %s loading ... Done" % self.Plugin
        logMessage(self.ctx, INFO, msg, 'ContentProvider', '__init__()')

    def __del__(self):
       msg = "ContentProvider: %s unloading ... Done" % self.Plugin
       logMessage(self.ctx, INFO, msg, 'ContentProvider', '__del__()')

    # XParameterizedContentProvider
    def registerInstance(self, scheme, plugin, replace):
        msg = "ContentProvider registerInstance: Scheme/Plugin: %s/%s ... Started" % (scheme, plugin)
        print(msg)
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'registerInstance()')
        print("ContentProvider.registerInstance() 1")
        datasource = DataSource(self.ctx, self.event, scheme, plugin)
        print("ContentProvider.registerInstance() 2")
        if not datasource.isValid():
            logMessage(self.ctx, SEVERE, datasource.Error, 'ContentProvider', 'registerInstance()')
            print("ContentProvider.registerInstance() 3")
            return None
        self.Scheme = scheme
        self.Plugin = plugin
        self.DataSource = datasource
        print("ContentProvider.registerInstance() 4")
        msg = "ContentProvider registerInstance: Scheme/Plugin: %s/%s ... Done" % (scheme, plugin)
        print(msg)
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'registerInstance()')
        return self
    def deregisterInstance(self, scheme, argument):
        msg = "ContentProvider deregisterInstance: Scheme: %s ... Done" % scheme
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'deregisterInstance()')

    # XContentIdentifierFactory
    def createContentIdentifier(self, url):
        try:
            print("ContentProvider.createContentIdentifier() 1 %s" % url)
            msg = "Identifier: %s ... " % url
            uri = getUri(self.ctx, getUrl(self.ctx, url))
            user = self._getUser(uri, url)
            identifier = Identifier(self.ctx, user, uri)
            msg += "Done"
            logMessage(self.ctx, INFO, msg, 'ContentProvider', 'createContentIdentifier()')
            print("ContentProvider.createContentIdentifier() 2")
            return identifier
        except Exception as e:
            msg += "Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, 'ContentProvider', 'createContentIdentifier()')

    # XContentProvider
    def queryContent(self, identifier):
        url = identifier.getContentIdentifier()
        print("ContentProvider.queryContent() 1 %s" % url)
        if not identifier.isValid():
            msg = "Identitifer: %s ... cannot be found: %s" % (url, self._error)
            logMessage(self.ctx, SEVERE, msg, 'ContentProvider', 'queryContent()')
            raise IllegalIdentifierException(self._error, identifier)
        print("ContentProvider.queryContent() 3")
        content = identifier.getContent()
        self._currentUserName = identifier.User.Name
        msg = "Identitifer: %s ... Done" % url
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'queryContent()')
        print("ContentProvider.queryContent() 4")
        return content

    def compareContentIds(self, id1, id2):
        ids = (id1.getContentIdentifier(), id2.getContentIdentifier())
        print("ContentProvider.compareContentIds() 1 %s - %s" % ids)
        msg = "Identifiers: %s - %s ..." % ids
        if id1.Id == id2.Id and id1.User.Id == id2.User.Id:
            msg += " seem to be the same..."
            compare = 0
        else:
            msg += " doesn't seem to be the same..."
            compare = -1
        msg += " ... Done"
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'compareContentIds()')
        print(msg)
        return compare

    def _getUser(self, uri, url):
        if uri is None:
            self._error = getMessage(self.ctx, 1201, url)
            print("ContentProvider._getUser() 1 ERROR: %s" % self._error)
            return User(self.ctx)
        if not uri.hasAuthority() or not uri.getPathSegmentCount():
            self._error = getMessage(self.ctx, 1202, url)
            print("ContentProvider._getUser() 2 ERROR: %s" % self._error)
            return User(self.ctx)
        name = self._getUserName(uri, url)
        if not name:
            self._error = getMessage(self.ctx, 1203, url)
            print("ContentProvider._getUser() 3 ERROR: %s" % self._error)
            return User(self.ctx)
        user = self.DataSource.getUser(name)
        if user is None:
            self._error = self.DataSource.Error
            print("ContentProvider._getUser() 4 ERROR: %s" % self._error)
            return User(self.ctx)
        return user

    def _getUserName(self, uri, url):
        if uri.hasAuthority() and uri.getAuthority() != '':
            name = uri.getAuthority()
        elif self._currentUserName is not None:
            name = self._currentUserName
        else:
            name = getUserNameFromHandler(self.ctx, uri.getScheme(), self)
        return name

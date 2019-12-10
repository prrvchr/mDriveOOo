#!
# -*- coding: utf_8 -*-
import traceback

try:
    import uno
    import unohelper

    from com.sun.star.util import XCloseListener
    from com.sun.star.logging.LogLevel import INFO
    from com.sun.star.logging.LogLevel import SEVERE
    from com.sun.star.ucb import XContentIdentifierFactory
    from com.sun.star.ucb import XContentProvider
    from com.sun.star.ucb import XParameterizedContentProvider
    from com.sun.star.ucb import IllegalIdentifierException

    from com.sun.star.ucb import XRestContentProvider

    from oauth2 import logMessage

    from .datasource import DataSource
    from .user import User
    from .identifier import Identifier

except Exception as e:
    print("clouducp.__init__() ERROR: %s - %s" % (e, traceback.print_exc()))


class ContentProvider(unohelper.Base,
                      XContentIdentifierFactory,
                      XContentProvider,
                      XCloseListener,
                      XParameterizedContentProvider,
                      XRestContentProvider):
    def __init__(self, ctx, plugin):
        self.ctx = ctx
        self.Scheme = ''
        self.Plugin = plugin
        self.DataSource = None
        self._defaultUser = ''
        msg = "ContentProvider: %s loading ... Done" % self.Plugin
        logMessage(self.ctx, INFO, msg, 'ContentProvider', '__init__()')

    def __del__(self):
       msg = "ContentProvider: %s unloading ... Done" % self.Plugin
       logMessage(self.ctx, INFO, msg, 'ContentProvider', '__del__()')

    # XParameterizedContentProvider
    def registerInstance(self, scheme, plugin, replace):
        msg = "ContentProvider registerInstance: Scheme/Plugin: %s/%s ... Started" % (scheme, plugin)
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'registerInstance()')
        try:
            datasource = DataSource(self.ctx, scheme, plugin)
        except Exception as e:
            msg = "ContentProvider registerInstance: Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, 'ContentProvider', 'registerInstance()')
            return None
        if not datasource.IsValid:
            logMessage(self.ctx, SEVERE, datasource.Error, 'ContentProvider', 'registerInstance()')
            return None
        self.Scheme = scheme
        self.Plugin = plugin
        msg = "ContentProvider registerInstance: addCloseListener ... Done"
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'registerInstance()')
        datasource.Connection.Parent.DatabaseDocument.addCloseListener(self)
        self.DataSource = datasource
        msg = "ContentProvider registerInstance: Scheme/Plugin: %s/%s ... Done" % (scheme, plugin)
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'registerInstance()')
        return self
    def deregisterInstance(self, scheme, argument):
        msg = "ContentProvider deregisterInstance: Scheme: %s ... Done" % scheme
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'deregisterInstance()')

    # XCloseListener
    def queryClosing(self, source, ownership):
        self.deregisterInstance(self.Scheme, self.Plugin)
        query = 'SHUTDOWN COMPACT;'
        statement = self.DataSource.Connection.createStatement()
        statement.execute(query)
        msg = "ContentProvider queryClosing: Scheme: %s ... Done" % self.Scheme
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'queryClosing()')
    def notifyClosing(self, source):
        pass

    # XContentIdentifierFactory
    def createContentIdentifier(self, url):
        try:
            msg = "Identifier: %s ... " % url
            identifier = Identifier(self.ctx, self.DataSource, url)
            msg += "Done"
            logMessage(self.ctx, INFO, msg, 'ContentProvider', 'createContentIdentifier()')
            return identifier
        except Exception as e:
            msg += "Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, 'ContentProvider', 'createContentIdentifier()')

    # XContentProvider
    def queryContent(self, identifier):
        url = identifier.getContentIdentifier()
        print("ContentProvider.queryContent() %s" % url)
        if not identifier.IsInitialized:
            if not identifier.initialize(self._defaultUser):
                msg = "Identifier: %s ... Error: %s" % (url, identifier.Error)
                print("ContentProvider.queryContent() %s" % msg)
                logMessage(self.ctx, INFO, msg, 'ContentProvider', 'queryContent()')
                raise IllegalIdentifierException(identifier.Error, self)
        self._defaultUser = identifier.User.Name
        content = identifier.getContent()
        msg = "Identitifer: %s ... Done" % url
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'queryContent()')
        return content

    def compareContentIds(self, id1, id2):
        print("ContentProvider.compareContentIds() 1")
        try:
            init1 = True
            init2 = True
            compare = -1
            identifier1 = id1.getContentIdentifier()
            identifier2 = id2.getContentIdentifier()
            msg = "Identifiers: %s - %s ..." % (identifier1, identifier2)
            if not id1.IsInitialized:
                init1 = id1.initialize(self._defaultUser)
            if not id2.IsInitialized:
                init2 = id2.initialize(self._defaultUser)
            if not init1:
                compare = -10
            elif not init2:
                compare = 10
            elif identifier1 == identifier2 and id1.User.Name == id2.User.Name:
                msg += " seem to be the same..."
                compare = 0
            msg += " ... Done"
            logMessage(self.ctx, INFO, msg, 'ContentProvider', 'compareContentIds()')
            return compare
        except Exception as e:
            print("ContentProvider.compareContentIds() Error: %s - %s" % (e, traceback.print_exc()))

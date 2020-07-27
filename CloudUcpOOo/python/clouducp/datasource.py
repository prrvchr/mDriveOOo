#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.util import XCloseListener

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb import XRestDataSource

from unolib import g_oauth2
from unolib import createService

from .configuration import g_cache
from .dbtools import getDataSource

from .user import User
from .identifier import Identifier
from .replicator import Replicator
from .database import DataBase

from .logger import logMessage
from .logger import getMessage

from collections import OrderedDict
import traceback


class DataSource(unohelper.Base,
                 XRestDataSource,
                 XCloseListener):
    def __init__(self, ctx, event, scheme, plugin):
        msg = "DataSource for Scheme: %s loading ... " % scheme
        self.ctx = ctx
        self.scheme = scheme
        self.plugin = plugin
        self._Users = {}
        self._Identifiers = OrderedDict()
        self.Error = None
        self.sync = event
        self.Provider = createService(self.ctx, '%s.Provider' % plugin)
        self.datasource, url, created = getDataSource(self.ctx, scheme, plugin, True)
        self.DataBase = DataBase(self.ctx, self.datasource)
        if created:
            self.Error = self.DataBase.createDataBase()
            if self.Error is None:
                self.DataBase.storeDataBase(url)
        self.DataBase.addCloseListener(self)
        folder, link = self.DataBase.getContentType()
        self.Provider.initialize(scheme, plugin, folder, link)
        self.replicator = Replicator(ctx, self.datasource, self.Provider, self._Users, self.sync)
        msg += "Done"
        logMessage(self.ctx, INFO, msg, 'DataSource', '__init__()')

    # XCloseListener
    def queryClosing(self, source, ownership):
        compact= self.replicator.fullPull
        if self.replicator.is_alive():
            self.replicator.cancel()
            self.replicator.join()
        #self.deregisterInstance(self.Scheme, self.Plugin)
        self.DataBase.shutdownDataBase(compact)
        msg = "DataSource queryClosing: Scheme: %s ... Done" % self.scheme
        logMessage(self.ctx, INFO, msg, 'DataSource', 'queryClosing()')
        print("DataSource.queryClosing() OK")
    def notifyClosing(self, source):
        pass

    # XRestDataSource
    def isValid(self):
        return self.Error is None

    def getUser(self, name, password=''):
        # User never change... we can cache it...
        if name in self._Users:
            user = self._Users[name]
        else:
            user = User(self.ctx, self, name)
            if not self._initializeUser(user, name, password):
                return None
            self._Users[name] = user
            self.sync.set()
        return user

    def getIdentifier(self, user, uri):
        # Identifier never change... we can cache it... if it's valid.
        key = self._getIdentifierKey(user, uri)
        if key in self._Identifiers:
            identifier = self._Identifiers[key]
            if identifier.IsNew:
                print("DataSource.getIdentifier() ISNEW ***************************************")
        else:
            identifier = Identifier(self.ctx, user, uri, self.callBack)
            if identifier.isValid() and user.CanAddChild:
                self._Identifiers[key] = identifier
        if len(self._Identifiers) > g_cache:
            k, i = self._Identifiers.popitem(False)
            print("DataSource.getIdentifier() DELETE Cache %s - %s - %s" % (len(self._Identifiers), k, i.getContentIdentifier()))
        return identifier

    def callBack(self, user, uri, isfolder):
        # If the title of the identifier changes, we must remove
        # from the cache this identifier and its children if it's a folder.
        key = self._getIdentifierKey(user, uri)
        child = key + '/'
        for identifier in list(self._Identifiers):
            if identifier == key or (isfolder and identifier.startswith(child)):
                print("DataSource.callBack() %s - %s" % (identifier, key))
                del self._Identifiers[identifier]

    def _getIdentifierKey(self, user, uri):
        return '%s/%s' % (user.Name, uri.getPath().strip('/.'))

    def _initializeUser(self, user, name, password):
        if user.Request is not None:
            if user.MetaData is not None:
                user.setDataBase(self.datasource, password, self.sync)
                return True
            if self.Provider.isOnLine():
                data = self.Provider.getUser(user.Request, name)
                if data.IsPresent:
                    root = self.Provider.getRoot(user.Request, data.Value)
                    if root.IsPresent:
                        user.MetaData = self.DataBase.insertUser(user.Provider, data.Value, root.Value)
                        if self.DataBase.createUser(user, password):
                            user.setDataBase(self.datasource, password, self.sync)
                            return True
                        else:
                            self.Error = getMessage(self.ctx, 1106, name)
                    else:
                        self.Error = getMessage(self.ctx, 1107, name)
                else:
                    self.Error = getMessage(self.ctx, 1107, name)
            else:
                self.Error = getMessage(self.ctx, 1108, name)
        else:
            self.Error = getMessage(self.ctx, 1105, g_oauth2)
        return False

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
        self._Users = {}
        self._Uris = {}
        self._Identifiers = OrderedDict()
        self.Error = None
        self.sync = event
        self.Provider = createService(self.ctx, '%s.Provider' % plugin)
        datasource, url, created = getDataSource(self.ctx, scheme, plugin, True)
        self.DataBase = DataBase(self.ctx, datasource)
        if created:
            self.Error = self.DataBase.createDataBase()
            if self.Error is None:
                self.DataBase.storeDataBase(url)
        self.DataBase.addCloseListener(self)
        folder, link = self.DataBase.getContentType()
        self.Provider.initialize(scheme, plugin, folder, link)
        self.Replicator = Replicator(ctx, datasource, self.Provider, self._Users, self.sync)
        msg += "Done"
        logMessage(self.ctx, INFO, msg, 'DataSource', '__init__()')

    # XCloseListener
    def queryClosing(self, source, ownership):
        if self.Replicator.is_alive():
            self.Replicator.cancel()
            self.Replicator.join()
        #self.deregisterInstance(self.Scheme, self.Plugin)
        self.DataBase.shutdownDataBase(self.Replicator.fullPull)
        msg = "DataSource queryClosing: Scheme: %s ... Done" % self.Provider.Scheme
        logMessage(self.ctx, INFO, msg, 'DataSource', 'queryClosing()')
        print(msg)
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
        # For performance, we have to cache it... if it's valid.
        if uri.getPath() == '/' and uri.hasFragment():
            # A Uri with fragment is supposed to be removed from the cache,
            # usually after the title or Id has been changed
            identifier = self._removeFromCache(user, uri)
        else:
            key = self._getUriKey(user, uri)
            itemid = self._Uris.get(key, None)
            if itemid is not None:
                identifier = self._Identifiers.get(itemid, None)
            if identifier is None:
                identifier = Identifier(self.ctx, user, uri)
                if identifier.isValid() and user.CanAddChild:
                    self._Uris[key] = identifier.Id
                    self._Identifiers[identifier.Id] = identifier
            # To optimize memory usage, the cache size is limited
            if len(self._Identifiers) > g_cache:
                k, i = self._Identifiers.popitem(False)
                self._removeUriFromCache(i)
        return identifier

    # Private methods
    def _removeIdentifierFromCache(self, user, uri):
        # If the title or the Id of the Identifier changes, we must remove
        # from cache this Identifier, it's Uri and its children if it's a folder.
        itemid = uri.getFragment()
        if itemid in self._Identifiers:
            identifier = self._Identifiers[itemid]
            self._removeUriFromCache(identifier, True)
            del self._Identifiers[itemid]
        else:
            # We must return an identifier although it is not used
            identifier = Identifier(self.ctx, user, uri)
        return identifier

    def _removeUriFromCache(self, identifier, child=False):
        isfolder = identifier.isFolder()
        children = '%s/' % self._getUriKey(identifier.User, identifier.getUri())
        for uri in list(self._Uris):
            if self._Uris[uri] == identifier.Id or all((child, isfolder, uri.startswith(children))):
                del self._Uris[uri]

    def _getUriKey(self, user, uri):
        return '%s/%s' % (user.Name, uri.getPath().strip('/.'))

    def _initializeUser(self, user, name, password):
        if user.Request is not None:
            if user.MetaData is not None:
                user.setDataBase(self.DataBase.getDataSource(), password, self.sync)
                return True
            if self.Provider.isOnLine():
                data = self.Provider.getUser(user.Request, name)
                if data.IsPresent:
                    root = self.Provider.getRoot(user.Request, data.Value)
                    if root.IsPresent:
                        user.MetaData = self.DataBase.insertUser(user.Provider, data.Value, root.Value)
                        if self.DataBase.createUser(user, password):
                            user.setDataBase(self.DataBase.getDataSource(), password, self.sync)
                            return True
                        else:
                            self.Error = getMessage(self.ctx, 602, name)
                    else:
                        self.Error = getMessage(self.ctx, 603, name)
                else:
                    self.Error = getMessage(self.ctx, 603, name)
            else:
                self.Error = getMessage(self.ctx, 604, name)
        else:
            self.Error = getMessage(self.ctx, 601, g_oauth2)
        return False

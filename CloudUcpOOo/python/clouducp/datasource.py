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

from com.sun.star.util import XCloseListener

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb import XRestDataSource

from .oauth2lib import g_oauth2

from .unotool import createService
from .unotool import getResourceLocation
from .unotool import getSimpleFile
from .unotool import getUrlPresentation

from .configuration import g_cache

from .dbconfig import g_folder

from .dbtool import getDataSourceLocation
from .dbtool import getDataSourceInfo
from .dbtool import getDataSourceJavaInfo
from .dbtool import registerDataSource

from .user import User
from .identifier import Identifier
from .replicator import Replicator
from .database import DataBase

from .logger import logMessage
from .logger import getMessage
g_message = 'datasource'

from collections import OrderedDict
import traceback


class DataSource(unohelper.Base,
                 XRestDataSource,
                 XCloseListener):
    def __init__(self, ctx, event, scheme, plugin):
        msg = "DataSource for Scheme: %s loading ... " % scheme
        print("DataSource.__init__() 1")
        self.ctx = ctx
        self._Users = {}
        self._Uris = {}
        self._Identifiers = OrderedDict()
        self.Error = None
        self.sync = event
        self.Provider = createService(self.ctx, '%s.Provider' % plugin)
        datasource, url, created = self._getDataSource(scheme, plugin, True)
        self.DataBase = DataBase(self.ctx, datasource)
        if created:
            print("DataSource.__init__() 2")
            self.Error = self.DataBase.createDataBase()
            if self.Error is None:
                self.DataBase.storeDataBase(url)
                print("DataSource.__init__() 3")
        self.DataBase.addCloseListener(self)
        folder, link = self.DataBase.getContentType()
        self.Provider.initialize(scheme, plugin, folder, link)
        self.Replicator = Replicator(ctx, datasource, self.Provider, self._Users, self.sync)
        msg += "Done"
        logMessage(self.ctx, INFO, msg, 'DataSource', '__init__()')
        print("DataSource.__init__() 4")

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
            identifier = self._removeIdentifierFromCache(user, uri)
        else:
            key = self._getUriKey(user, uri)
            itemid = self._Uris.get(key, None)
            if itemid is None:
                identifier = Identifier(self.ctx, user, uri)
                if identifier.isValid():
                    self._Uris[key] = identifier.Id
                    self._Identifiers[identifier.Id] = identifier
            else:
                identifier = self._Identifiers[itemid]
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
            print('DataSource._initializeUser() 1')
            if user.MetaData is not None:
                user.setDataBase(self.DataBase.getDataSource(), password, self.sync)
                print('DataSource._initializeUser() 2')
                return True
            if self.Provider.isOnLine():
                data = self.Provider.getUser(user.Request, name)
                if data.IsPresent:
                    root = self.Provider.getRoot(user.Request, data.Value)
                    if root.IsPresent:
                        user.MetaData = self.DataBase.insertUser(user.Provider, data.Value, root.Value)
                        if self.DataBase.createUser(user, password):
                            user.setDataBase(self.DataBase.getDataSource(), password, self.sync)
                            print('DataSource._initializeUser() 3')
                            return True
                        else:
                            self.Error = getMessage(self.ctx, g_message, 102, name)
                    else:
                        self.Error = getMessage(self.ctx, g_message, 103, name)
                else:
                    self.Error = getMessage(self.ctx, g_message, 103, name)
            else:
                self.Error = getMessage(self.ctx, g_message, 104, name)
        else:
            self.Error = getMessage(self.ctx, g_message, 101, g_oauth2)
        return False

    def _getDataSource(self, dbname, plugin, register):
        location = getResourceLocation(self.ctx, plugin, g_folder)
        location = getUrlPresentation(self.ctx, location)
        url = '%s/%s.odb' % (location, dbname)
        dbcontext = createService(self.ctx, 'com.sun.star.sdb.DatabaseContext')
        if getSimpleFile(self.ctx).exists(url):
            odb = dbname if dbcontext.hasByName(dbname) else url
            datasource = dbcontext.getByName(odb)
            created = False
        else:
            datasource = dbcontext.createInstance()
            datasource.URL = getDataSourceLocation(location, dbname, False)
            datasource.Info = getDataSourceInfo() + getDataSourceJavaInfo(location)
            created = True
        if register:
            registerDataSource(dbcontext, dbname, url)
        return datasource, url, created

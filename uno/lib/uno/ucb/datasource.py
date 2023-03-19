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

from com.sun.star.util import XCloseListener

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb import XRestDataSource

from .oauth2lib import g_oauth2
from .oauth2lib import getOAuth2UserName

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

from .logger import getLogger

g_message = 'datasource'

import traceback


class DataSource(unohelper.Base,
                 XRestDataSource,
                 XCloseListener):
    def __init__(self, ctx, event, scheme, plugin):
        msg = "DataSource for Scheme: %s loading ... " % scheme
        print("DataSource.__init__() 1")
        self._ctx = ctx
        self._users = {}
        self.Error = None
        self._sync = event
        self.Provider = createService(self._ctx, '%s.Provider' % plugin)
        datasource, url, created = self._getDataSource(scheme, plugin, True)
        self.DataBase = DataBase(self._ctx, datasource)
        if created:
            print("DataSource.__init__() 2")
            self.Error = self.DataBase.createDataBase()
            if self.Error is None:
                self.DataBase.storeDataBase(url)
                print("DataSource.__init__() 3")
        self.DataBase.addCloseListener(self)
        folder, link = self.DataBase.getContentType()
        self.Provider.initialize(scheme, plugin, folder, link)
        self.Replicator = Replicator(ctx, datasource, self.Provider, self._users, self._sync)
        msg += "Done"
        self._logger = getLogger(ctx)
        self._logger.logp(INFO, 'DataSource', '__init__()', msg)
        print("DataSource.__init__() 4")

    # XCloseListener
    def queryClosing(self, source, ownership):
        if self.Replicator.is_alive():
            self.Replicator.cancel()
            self.Replicator.join()
        #self.deregisterInstance(self.Scheme, self.Plugin)
        self.DataBase.shutdownDataBase(self.Replicator.fullPull())
        msg = "DataSource queryClosing: Scheme: %s ... Done" % self.Provider.Scheme
        self._logger.logp(INFO, 'DataSource', 'queryClosing()', msg)
        print(msg)
    def notifyClosing(self, source):
        pass

    # XRestDataSource
    def isValid(self):
        return self.Error is None

    def getIdentifier(self, factory, url, default=None):
        print("DataSource.getIdentifier() 1 Url: %s" % url)
        user, name, uri = self._getIdentifiers(factory, url, default)
        if user is not None:
            url = '%s://%s%s' % (uri.getScheme(), name, uri.getPath())
            print("DataSource.getIdentifier() 2 Url: %s" % url)
            identifier = user.getIdentifier(factory, url)
        else:
            identifier = Identifier(self._ctx, factory, user, url)
        return identifier

    # Private methods
    def _getIdentifiers(self, factory, url, default):
        uri = factory.parse(url)
        if uri is None:
            name = None
        elif uri.hasAuthority() and uri.getAuthority() != '':
            name = uri.getAuthority()
        elif default is not None:
            name = default
        else:
            name = getOAuth2UserName(self._ctx, self, uri.getScheme())
        # User never change... we can cache it...
        if name is None:
            print("DataSource._getIdentifiers() Error **************************************************")
            user = None
        elif name in self._users:
            user = self._users[name]
        else:
            user = User(self._ctx, self, name, self._sync)
            self._users[name] = user
        return user, name, uri

    def _getDataSource(self, dbname, plugin, register):
        location = getResourceLocation(self._ctx, plugin, g_folder)
        location = getUrlPresentation(self._ctx, location)
        url = '%s/%s.odb' % (location, dbname)
        dbcontext = createService(self._ctx, 'com.sun.star.sdb.DatabaseContext')
        if getSimpleFile(self._ctx).exists(url):
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


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
from .unotool import parseUrl

from .configuration import g_cache

from .dbconfig import g_folder

from .dbtool import getDataSourceLocation
from .dbtool import getDataSourceInfo
from .dbtool import getDataSourceJavaInfo
from .dbtool import registerDataSource

from .ucb import ContentUser

from .replicator import Replicator
from .database import DataBase

from .logger import getLogger

g_message = 'datasource'

import traceback


class DataSource(unohelper.Base,
                 XCloseListener):
    def __init__(self, ctx, sync, lock, scheme, plugin):
        msg = "DataSource for Scheme: %s loading ... " % scheme
        print("DataSource.__init__() 1")
        self._ctx = ctx
        self._default = ''
        self._users = {}
        self.Error = None
        self._sync = sync
        self._lock = lock
        self._factory = createService(ctx, 'com.sun.star.uri.UriReferenceFactory')
        self._provider = createService(self._ctx, '%s.Provider' % plugin)
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
        self._provider.initialize(scheme, plugin, folder, link)
        self.Replicator = Replicator(ctx, datasource, self._provider, self._users, self._sync, self._lock)
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
        msg = "DataSource queryClosing: Scheme: %s ... Done" % self._provider.Scheme
        self._logger.logp(INFO, 'DataSource', 'queryClosing()', msg)
        print(msg)
    def notifyClosing(self, source):
        pass

    # DataSource
    def getDefaultUser(self):
        return self._default

    # FIXME: Get called from ContentProvider.queryContent()
    def queryContent(self, provider, identifier):
        try:
            print("DataSource.queryContent() 1")
            user, uri, authority = self._getUser(provider, identifier.getContentIdentifier())
            print("DataSource.queryContent() 2")
            return user.getContent(identifier, uri, authority)
        except Exception as e:
            msg = "DataSource.queryContent() Error: %s" % traceback.print_exc()
            print(msg)
            raise e

    def _getUser(self, source, url):
        try:
            print("DataSource._getUser() 1 Url: %s" % url)
            authority = False
            uri = self._factory.parse(url)
            print("DataSource._getUser() 2 Path: '%s'" % uri.getPath())
            if uri is None:
                msg = self._logger.resolveString(121, url)
                raise IllegalIdentifierException(msg, source)
            elif uri.hasAuthority() and uri.getAuthority() != '':
                name = uri.getAuthority()
                authority = True
            elif self._default:
                name = self._default
                #url = self._rewriteContentIdentifierUrl(uri, name)
            else:
                name = self._getUserName(source, url)
                #url = self._rewriteContentIdentifierUrl(uri, name)
            # User never change... we can cache it...
            if name in self._users:
                user = self._users[name]
            else:
                user = ContentUser(self._ctx, source, self.DataBase, self._provider, name, self._sync, self._lock)
                self._users[name] = user
            self._default = name
            return user, uri.getPath(), authority
        except Exception as e:
            msg = "DataSource._getUser() Error: %s" % traceback.print_exc()
            print(msg)
            raise e

    def _getUserName(self, source, url):
        name = getOAuth2UserName(self._ctx, self, self._provider.Scheme)
        if not name:
            msg = self._logger.resolveString(121, url)
            raise IllegalIdentifierException(msg, source)
        return name

    def _rewriteContentIdentifierUrl(self, uri, name):
        url = '%s://%s' % (uri.getScheme(), name)
        if uri.getPathSegmentCount() > 0:
            url += uri.getPath()
        print("DataSource._rewriteContentIdentifierUrl() Url: %s" % url)
        return url




























    # XRestDataSource
    def isValid(self):
        return self.Error is None

    def getIdentifier(self, url):
        try:
            print("DataSource.getIdentifier() 1 Url: %s" % url)
            uri = self._factory.parse(url)
            msg = None
            if uri is None:
                name = None
                url = None
            elif uri.hasAuthority() and uri.getAuthority() != '':
                name = uri.getAuthority()
            elif self._default is not None:
                name = self._default
            else:
                name = None
                #name = getOAuth2UserName(self._ctx, self, uri.getScheme())
            # User never change... we can cache it...
            if name in self._users:
                user = self._users[name]
            else:
                user = User(self._ctx, self, name, self._sync, self._lock)
            return user.getIdentifier(url)
        except Exception as e:
            msg = "DataSource.getIdentifier() Error: %s" % traceback.print_exc()
            print(msg)


    def addUser(self, user):
        self._users[user.Name] = user
        self._default = user.Name

    # Private methods
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


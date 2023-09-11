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
from com.sun.star.util import CloseVetoException

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb import IllegalIdentifierException

from .oauth2 import g_oauth2
from .oauth2 import getOAuth2UserName

from .unotool import createService
from .unotool import getResourceLocation
from .unotool import getSimpleFile
from .unotool import getUrlPresentation
from .unotool import parseUrl

from .configuration import g_cache

from .dbconfig import g_folder
from .dbconfig import g_protocol
from .dbconfig import g_options
from .dbconfig import g_shutdown

from .dbtool import getDataSourceLocation
from .dbtool import getDataSourceInfo
from .dbtool import getDataSourceJavaInfo
from .dbtool import registerDataSource

from .ucp import ContentUser

from .provider import Provider

from .replicator import Replicator

from .database import DataBase

from .logger import getLogger

from .configuration import g_identifier
from .configuration import g_scheme

g_message = 'datasource'

import traceback


class DataSource(unohelper.Base,
                 XCloseListener):
    def __init__(self, ctx, logger, sync, lock):
        self._ctx = ctx
        self._default = ''
        self._users = {}
        self._logger = logger
        self.Error = None
        self._sync = sync
        self._lock = lock
        self._factory = createService(ctx, 'com.sun.star.uri.UriReferenceFactory')
        datasource, url, new = self._getDataSource(False)
        self.DataBase = DataBase(self._ctx, logger, datasource)
        if new and self.DataBase.createDataBase():
            self.DataBase.storeDataBase(url)
        self.DataBase.addCloseListener(self)
        folder, link = self.DataBase.getContentType()
        self._provider = Provider(ctx, logger, folder, link)
        self.Replicator = Replicator(ctx, datasource, self._provider, self._users, self._sync, self._lock)
        self._logger.logprb(INFO, 'DataSource', '__init__()', 301)

    # DataSource
    def getDefaultUser(self):
        return self._default

    # FIXME: Get called from ParameterizedProvider.queryContent()
    def queryContent(self, source, authority, identifier):
        user, path = self._getUser(source, identifier.getContentIdentifier(), authority)
        content = user.getContent(path, authority)
        return content

    # XCloseListener
    def queryClosing(self, source, ownership):
        if ownership:
            raise CloseVetoException('cant close', self)
        print("DataSource.queryClosing() ownership: %s" % ownership)
        if self.Replicator.is_alive():
            self.Replicator.cancel()
            self.Replicator.join()
        self.DataBase.shutdownDataBase(self.Replicator.fullPull())
        self._logger.logprb(INFO, 'DataSource', 'queryClosing()', 341, self._provider.Scheme)
    def notifyClosing(self, source):
        pass

    # Private methods
    def _getUser(self, source, url, authority):
        default = False
        uri = self._factory.parse(url)
        if uri is None:
            msg = self._logger.resolveString(321, url)
            raise IllegalIdentifierException(msg, source)
        if authority:
            if uri.hasAuthority() and uri.getAuthority() != '':
                name = uri.getAuthority()
            else:
                msg = self._logger.resolveString(322, url)
                raise IllegalIdentifierException(msg, source)
        elif self._default:
            name = self._default
        else:
            name = self._getUserName(source, url)
            default = True
        # User never change... we can cache it...
        if name in self._users:
            user = self._users[name]
        else:
            user = ContentUser(self._ctx, self._logger, source, self.DataBase,
                               self._provider, name, self._sync, self._lock)
            self._users[name] = user
        # FIXME: if the user has been instantiated then we can consider it as the default user
        if default:
            self._default = name
        return user, uri.getPath()

    def _getUserName(self, source, url):
        name = getOAuth2UserName(self._ctx, self, self._provider.Scheme)
        if not name:
            msg = self._logger.resolveString(331, url)
            raise IllegalIdentifierException(msg, source)
        return name

    def _getDataSource(self, register):
        path = '%s/%s.odb' % (g_folder, g_scheme)
        location = getResourceLocation(self._ctx, g_identifier, path)
        url = getUrlPresentation(self._ctx, location)
        dbcontext = createService(self._ctx, 'com.sun.star.sdb.DatabaseContext')
        if getSimpleFile(self._ctx).exists(url):
            self._logger.logprb(INFO, 'DataSource', '_getDataSource()', 311, url)
            if register and dbcontext.hasByName(g_scheme):
                datasource = dbcontext.getByName(g_scheme)
                self._logger.logprb(INFO, 'DataSource', '_getDataSource()', 312, g_scheme)
            else:
                datasource = dbcontext.getByName(url)
                self._logger.logprb(INFO, 'DataSource', '_getDataSource()', 313, url)
            new = False
        else:
            self._logger.logprb(INFO, 'DataSource', '_getDataSource()', 314, url)
            datasource = dbcontext.createInstance()
            datasource.URL = self._getDataSourceLocation(url, True)
            datasource.Info = getDataSourceInfo()
            new = True
            self._logger.logprb(INFO, 'DataSource', '_getDataSource()', 315, url)
        if register and new:
            registerDataSource(dbcontext, g_scheme, url)
            self._logger.logprb(INFO, 'DataSource', '_getDataSource()', 316, url, g_scheme)
        return datasource, url, new

    def _getDataSourceLocation(self, url, shutdown):
        url = g_protocol + url + g_options
        if shutdown:
            url += g_shutdown
        return url


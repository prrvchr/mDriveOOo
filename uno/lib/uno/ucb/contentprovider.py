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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.lang import XServiceInfo

from com.sun.star.sdbc import SQLException

from com.sun.star.ucb import XContentIdentifierFactory
from com.sun.star.ucb import XContentProvider
from com.sun.star.ucb import XParameterizedContentProvider
from com.sun.star.ucb import IllegalIdentifierException

from .ucp import Identifier
from .ucp import getExceptionMessage

from .database import DataBase

from .datasource import DataSource

from .unotool import checkVersion
from .unotool import getExtensionVersion

from .dbtool import getConnectionUrl

from .logger import getLogger

from .oauth2 import getOAuth2Version
from .oauth2 import g_extension as g_oauth2ext
from .oauth2 import g_version as g_oauth2ver

from .jdbcdriver import g_extension as g_jdbcext
from .jdbcdriver import g_identifier as g_jdbcid
from .jdbcdriver import g_version as g_jdbcver

from .dbconfig import g_folder
from .dbconfig import g_version

from .configuration import g_extension
from .configuration import g_identifier
from .configuration import g_defaultlog
from .configuration import g_scheme
from .configuration import g_separator

import traceback


class ContentProvider(unohelper.Base,
                      XServiceInfo,
                      XContentIdentifierFactory,
                      XContentProvider):
    def __init__(self, ctx, logger, authority, arguments):
        self._ctx = ctx
        self._authority = authority
        self._cls = f'{arguments}ContentProvider'
        self._services = ('com.sun.star.ucb.ContentProvider', f'{g_identifier}.ContentProvider')
        self._logger = logger
        self._logger.logprb(INFO, self._cls, '__init__()', 201, arguments)

    __datasource = None

    @property
    def _datasource(self):
        if ContentProvider.__datasource is None:
            ContentProvider.__datasource = self._getDataSource()
        return ContentProvider.__datasource

    # XContentIdentifierFactory
    def createContentIdentifier(self, url):
        identifier = Identifier(url)
        self._logger.logprb(INFO, self._cls, 'createContentIdentifier()', 211, url, identifier.getContentIdentifier())
        return identifier

    # XContentProvider
    def queryContent(self, identifier):
        try:
            print("ContentProvider.queryContent() 1")
            url = identifier.getContentIdentifier()
            content = self._datasource.queryContent(self, self._authority, url)
            self._logger.logprb(INFO, self._cls, 'queryContent()', 231, url)
            print("ContentProvider.queryContent() 2")
            return content
        except IllegalIdentifierException as e:
            self._logger.logprb(INFO, self._cls, 'queryContent()', 232, e.Message)
            raise e
        except Exception as e:
            msg = self._logger.resolveString(233, traceback.format_exc())
            self._logger.logp(SEVERE, self._cls, 'queryContent()', msg)
            print(msg)

    def compareContentIds(self, id1, id2):
        print("ContentProvider.compareContentIds() 1")
        uri1 = self._datasource.parseIdentifier(id1)
        uri2 = self._datasource.parseIdentifier(id2)
        auth1 = uri1.getAuthority() if uri1.hasAuthority() else self._datasource.getDefaultUser()
        auth2 = uri2.getAuthority() if uri2.hasAuthority() else self._datasource.getDefaultUser()
        if (auth1 != auth2 or uri1.getPath() != uri2.getPath()):
            self._logger.logprb(INFO, self._cls, 'compareContentIds()', 242, uri1.getUriReference(), uri2.getUriReference())
            compare = -1
        else:
            self._logger.logprb(INFO, self._cls, 'compareContentIds()', 241, uri1.getUriReference(), uri2.getUriReference())
            compare = 0
        return compare

    # XServiceInfo
    def supportsService(self, service):
        return service in self._services
    def getImplementationName(self):
        return self._services[1]
    def getSupportedServiceNames(self):
        return self._services

    # Private methods
    def _getDataSource(self):
        method = '_getDataSource()'
        oauth2 = getOAuth2Version(self._ctx)
        driver = getExtensionVersion(self._ctx, g_jdbcid)
        if oauth2 is None:
            msg = self._getExceptionMessage(method, 221, g_oauth2ext, g_oauth2ext, g_extension)
            raise IllegalIdentifierException(msg, self)
        elif not checkVersion(oauth2, g_oauth2ver):
            msg = self._getExceptionMessage(method, 223, g_oauth2ext, oauth2, g_oauth2ext, g_oauth2ver)
            raise IllegalIdentifierException(msg, self)
        elif driver is None:
            msg = self._getExceptionMessage(method, 221, g_jdbcext, g_jdbcext, g_extension)
            raise IllegalIdentifierException(msg, self)
        elif not checkVersion(driver, g_jdbcver):
            msg = self._getExceptionMessage(method, 223, g_jdbcext, driver, g_jdbcext, g_jdbcver)
            raise IllegalIdentifierException(msg, self)
        else:
            path = g_folder + g_separator + g_scheme
            url = getConnectionUrl(self._ctx, path)
            try:
                database = DataBase(self._ctx, self._logger, url)
            except SQLException as e:
                msg = self._getExceptionMessage(method, 225, g_extension, url, e.Message)
                raise IllegalIdentifierException(msg, self)
            else:
                if not database.isUptoDate():
                    msg = self._getExceptionMessage(method, 227, g_jdbcext, database.Version, g_version)
                    raise IllegalIdentifierException(msg, self)
                else:
                    return DataSource(self._ctx, self._logger, database)
        return None

    def _getExceptionMessage(self, method, code, extension, *args):
        return getExceptionMessage(self._ctx, self._logger, self._cls, method, code, extension, *args)


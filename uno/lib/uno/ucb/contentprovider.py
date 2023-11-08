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

from com.sun.star.ucb import XContentIdentifierFactory
from com.sun.star.ucb import XContentProvider
from com.sun.star.ucb import XParameterizedContentProvider
from com.sun.star.ucb import IllegalIdentifierException

from .ucp import Identifier

from .database import DataBase

from .datasource import DataSource

from .unotool import checkVersion
from .unotool import createService
from .unotool import getExtensionVersion
from .unotool import parseUrl

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

import traceback


class ContentProvider(unohelper.Base,
                      XServiceInfo,
                      XContentIdentifierFactory,
                      XContentProvider):
    def __init__(self, ctx, logger, authority,  arguments):
        self._ctx = ctx
        self._authority = authority
        self._cls = '%sContentProvider' % arguments
        self._services = ('com.sun.star.ucb.ContentProvider', g_identifier + '.ContentProvider')
        self._transformer = createService(ctx, 'com.sun.star.util.URLTransformer')
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
        identifier = Identifier(self._getContentIdentifierUrl(url))
        self._logger.logprb(INFO, self._cls, 'createContentIdentifier()', 211, url, identifier.getContentIdentifier())
        return identifier

    # XContentProvider
    def queryContent(self, identifier):
        try:
            print("ContentProvider.queryContent() 1 ******************************************")
            content = self._datasource.queryContent(self, self._authority, identifier)
            print("ContentProvider.queryContent() 2 ******************************************")
            self._logger.logprb(INFO, self._cls, 'queryContent()', 231, identifier.getContentIdentifier())
            return content
        except IllegalIdentifierException as e:
            self._logger.logprb(INFO, self._cls, 'queryContent()', 232, e.Message)
            raise e
        except Exception as e:
            msg = self._logger.resolveString(233, traceback.format_exc())
            self._logger.logp(SEVERE, self._cls, 'queryContent()', msg)
            print(msg)

    def compareContentIds(self, id1, id2):
        url1, url2 = id1.getContentIdentifier(), id2.getContentIdentifier()
        if url1 == url2:
            self._logger.logprb(INFO, self._cls, 'compareContentIds()', 241, url1, url2)
            compare = 0
        else:
            self._logger.logprb(INFO, self._cls, 'compareContentIds()', 242, url1, url2)
            compare = -1
        return compare

    # XServiceInfo
    def supportsService(self, service):
        return service in self._services
    def getImplementationName(self):
        return self._services[1]
    def getSupportedServiceNames(self):
        return self._services

    # Private methods
    def _getContentIdentifierUrl(self, url):
        # FIXME: Sometimes the url can end with a dot, it must be deleted
        url = url.rstrip('.')
        uri = parseUrl(self._transformer, url)
        if uri is not None:
            uri = self._transformer.getPresentation(uri, True)
        return uri if uri else url

    def _getDataSource(self):
        oauth2 = getOAuth2Version(self._ctx)
        driver = getExtensionVersion(self._ctx, g_jdbcid)
        if oauth2 is None:
            self._logException(221, g_oauth2ext, ' ', g_extension)
            raise self._getException(221, g_oauth2ext, '\n', g_extension)
        elif not checkVersion(oauth2, g_oauth2ver):
            self._logException(222, oauth2, g_oauth2ext, ' ', g_oauth2ver)
            raise self._getException(222, oauth2, g_oauth2ext, '\n', g_oauth2ver)
        elif driver is None:
            self._logException(221, g_jdbcext, ' ', g_extension)
            raise self._getException(221, g_jdbcext, '\n', g_extension)
        elif not checkVersion(driver, g_jdbcver):
            self._logException(222, driver, g_jdbcext, ' ', g_jdbcver)
            raise self._getException(222, driver, g_jdbcext, '\n', g_jdbcver)
        else:
            path = g_folder + '/' + g_scheme
            url = getConnectionUrl(self._ctx, path)
            try:
                database = DataBase(self._ctx, self._logger, url)
            except SQLException as e:
                self._logException(223, url, ' ', e.Message)
                raise self._getException(223, url, '\n', e.Message)
            else:
                if not database.isUptoDate():
                    self._logException(224, database.Version, ' ', g_version)
                    raise self._getException(224, database.Version, '\n', g_version)
                else:
                    return DataSource(self._ctx, self._logger, database)
        return None

    def _logException(self, code, *args):
        self._logger.logprb(SEVERE, 'ContentProvider', 'queryContent()', code, *args)

    def _getException(self, code, *args):
        msg = self._logger.resolveString(code, *args)
        return IllegalIdentifierException(msg, self)


#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-24 https://prrvchr.github.io                                  ║
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
from .ucp import getDataSourceUrl
from .ucp import getExceptionMessage

from .datasource import DataSource

from .unotool import getUrlTransformer
from .unotool import parseUrl

from .logger import getLogger

from .jdbcdriver import g_extension as g_jdbcext

from .dbconfig import g_version

from .configuration import g_extension
from .configuration import g_identifier
from .configuration import g_defaultlog

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
        self._transformer = getUrlTransformer(ctx)
        self._logger = logger
        self._logger.logprb(INFO, self._cls, '__init__', 201, arguments)

    __datasource = None

    @property
    def _datasource(self):
        if ContentProvider.__datasource is None:
            ContentProvider.__datasource = self._getDataSource()
        return ContentProvider.__datasource

    # XContentIdentifierFactory
    def createContentIdentifier(self, url):
        identifier = Identifier(self._getPresentationUrl(url))
        self._logger.logprb(INFO, self._cls, 'createContentIdentifier', 211, url, identifier.getContentIdentifier())
        return identifier

    # XContentProvider
    def queryContent(self, identifier):
        try:
            print("ContentProvider.queryContent() 1")
            url = self._getPresentationUrl(identifier.getContentIdentifier())
            print("ContentProvider.queryContent() 2")
            content = self._datasource.queryContent(self, self._authority, url)
            print("ContentProvider.queryContent() 3")
            self._logger.logprb(INFO, self._cls, 'queryContent', 231, url)
            return content
        except IllegalIdentifierException as e:
            self._logger.logprb(SEVERE, self._cls, 'queryContent', 232, e.Message)
            raise e
        except Exception as e:
            msg = self._logger.resolveString(233, traceback.format_exc())
            self._logger.logp(SEVERE, self._cls, 'queryContent', msg)
            print(msg)

    def compareContentIds(self, id1, id2):
        uri1 = self._datasource.parseUrl(self._getPresentationUrl(id1.getContentIdentifier()))
        uri2 = self._datasource.parseUrl(self._getPresentationUrl(id2.getContentIdentifier()))
        auth1 = uri1.getAuthority() if uri1.hasAuthority() else self._datasource.getDefaultUser()
        auth2 = uri2.getAuthority() if uri2.hasAuthority() else self._datasource.getDefaultUser()
        if (auth1 != auth2 or uri1.getPath() != uri2.getPath()):
            self._logger.logprb(INFO, self._cls, 'compareContentIds', 242, uri1.getUriReference(), uri2.getUriReference())
            compare = -1
        else:
            self._logger.logprb(INFO, self._cls, 'compareContentIds', 241, uri1.getUriReference(), uri2.getUriReference())
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
        mtd = '_getDataSource'
        url = getDataSourceUrl(self._ctx, self, self._logger, self._cls, mtd)
        try:
            datasource = DataSource(self._ctx, self._logger, url)
        except SQLException as e:
            msg = self._getExceptionMessage(mtd, 225, g_extension, url, e.Message)
            raise IllegalIdentifierException(msg, self)
        if not datasource.isUptoDate():
            msg = self._getExceptionMessage(mtd, 227, g_jdbcext, datasource.getDataBaseVersion(), g_version)
            raise IllegalIdentifierException(msg, self)
        return datasource

    def _getPresentationUrl(self, url):
        # FIXME: Sometimes the url can end with a dot, it must be removed
        url = url.rstrip('.')
        uri = parseUrl(self._transformer, url)
        if uri is not None:
            url = self._transformer.getPresentation(uri, True)
        print("ContentProvider._getPresentationUrl() url: %s" % url)
        return url

    def _getExceptionMessage(self, mtd, code, extension, *args):
        return getExceptionMessage(self._ctx, self._logger, self._cls, mtd, code, extension, *args)


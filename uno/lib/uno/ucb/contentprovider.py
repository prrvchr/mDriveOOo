#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-25 https://prrvchr.github.io                                  ║
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

import unohelper

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.lang import XServiceInfo

from com.sun.star.uno import Exception as UnoException

from com.sun.star.sdbc import SQLException

from com.sun.star.ucb import XContentIdentifierFactory
from com.sun.star.ucb import XContentProvider
from com.sun.star.ucb import XParameterizedContentProvider
from com.sun.star.ucb import IllegalIdentifierException

from .ucp import Identifier

from .datasource import DataSource

from .unotool import getUrlTransformer
from .unotool import parseUrl

from .helper import getDataBaseConnection
from .helper import getDataBaseUrl
from .helper import getExceptionMessage
from .helper import getPresentationUrl

import traceback


class ContentProvider(unohelper.Base,
                      XServiceInfo,
                      XContentIdentifierFactory,
                      XContentProvider):
    def __init__(self, ctx, logger, implementation, authority, arguments):
        self._cls = '%sContentProvider' % arguments
        self._ctx = ctx
        self._implementation = implementation
        self._authority = authority
        self._services = ('com.sun.star.ucb.ContentProvider', implementation)
        self._transformer = getUrlTransformer(ctx)
        self._logger = logger
        self._logger.logprb(INFO, self._cls, '__init__', 201, arguments)

    __datasource = None

    @property
    def _datasource(self):
        if ContentProvider.__datasource is None:
            url = getDataBaseUrl(self._ctx)
            connection = getDataBaseConnection(self._ctx, self, self._logger, url)
            datasource = DataSource(self._ctx, self._logger, connection, url)
            ContentProvider.__datasource = datasource
        return ContentProvider.__datasource

    # XContentIdentifierFactory
    def createContentIdentifier(self, url):
        identifier = Identifier(self._getPresentationUrl(url))
        self._logger.logprb(INFO, self._cls, 'createContentIdentifier', 211, url, identifier.getContentIdentifier())
        return identifier

    # XContentProvider
    def queryContent(self, identifier):
        try:
            content = None
            url = self._getPresentationUrl(identifier.getContentIdentifier())
            content = self._datasource.queryContent(self, self._authority, url)
            self._logger.logprb(INFO, self._cls, 'queryContent', 221, url)
            return content
        except IllegalIdentifierException as e:
            self._logger.logprb(SEVERE, self._cls, 'queryContent', 222, e.Message)
            raise e
        except UnoException as e:
            self._logger.logprb(SEVERE, self._cls, 'queryContent', 223, type(e).__name__, e.Message)
            raise IllegalIdentifierException(e.Message, e.Context)
        except Exception as e:
            msg = self._logger.resolveString(224, type(e).__name__, traceback.format_exc())
            self._logger.logp(SEVERE, self._cls, 'queryContent', msg)
            raise IllegalIdentifierException(msg, self)

    def compareContentIds(self, id1, id2):
        uri1 = self._datasource.parseUrl(self._getPresentationUrl(id1.getContentIdentifier()))
        uri2 = self._datasource.parseUrl(self._getPresentationUrl(id2.getContentIdentifier()))
        auth1 = uri1.getAuthority() if uri1.hasAuthority() else self._datasource.getDefaultUser()
        auth2 = uri2.getAuthority() if uri2.hasAuthority() else self._datasource.getDefaultUser()
        if (auth1 != auth2 or uri1.getPath() != uri2.getPath()):
            self._logger.logprb(INFO, self._cls, 'compareContentIds', 231, uri1.getUriReference(), uri2.getUriReference())
            compare = -1
        else:
            self._logger.logprb(INFO, self._cls, 'compareContentIds', 232, uri1.getUriReference(), uri2.getUriReference())
            compare = 0
        return compare

    # XServiceInfo
    def supportsService(self, service):
        return service in self._services
    def getImplementationName(self):
        return self._implementation
    def getSupportedServiceNames(self):
        return self._services

    # Private methods
    def _getPresentationUrl(self, url):
        return getPresentationUrl(self._transformer, url)

    def _getExceptionMessage(self, extension, *args):
        return getExceptionMessage(self._logger, code, extension, *args)


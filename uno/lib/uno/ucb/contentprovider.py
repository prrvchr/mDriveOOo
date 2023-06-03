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

from .ucp import ContentIdentifier

from .unotool import createService
from .unotool import parseUrl

from .datasource import DataSource

from .logger import getLogger

from .configuration import g_identifier
from .configuration import g_defaultlog
from .configuration import g_scheme

import traceback
from threading import Event
from threading import Lock


class ContentProvider(unohelper.Base,
                            XServiceInfo,
                            XContentIdentifierFactory,
                            XContentProvider):
    def __init__(self, ctx, logger, authority,  arguments):
        print("ContentProvider.__init__() 1 Scheme: %s" % g_scheme)
        self._ctx = ctx
        self._authority = authority
        self._cls = '%sContentProvider' % arguments
        self._services = ('com.sun.star.ucb.ContentProvider', g_identifier + '.ContentProvider')
        self._sync = Event()
        self._lock = Lock()
        self._transformer = createService(ctx, 'com.sun.star.util.URLTransformer')
        if self._datasource is None:
            print("ContentProvider.__init__() 2 Scheme: %s" % g_scheme)
            ContentProvider.__datasource = DataSource(ctx, logger, self._sync, self._lock)
        self._logger = logger
        self._logger.logprb(INFO, self._cls, '__init__()', 201, arguments)

    __datasource = None

    @property
    def _datasource(self):
        return ContentProvider.__datasource

    # XContentIdentifierFactory
    def createContentIdentifier(self, url):
        identifier = ContentIdentifier(self._getContentIdentifierUrl(url))
        self._logger.logprb(INFO, self._cls, 'createContentIdentifier()', 211, url, identifier.getContentIdentifier())
        return identifier

    # XContentProvider
    def queryContent(self, identifier):
        try:
            content = self._datasource.queryContent(self, self._authority, identifier)
            self._logger.logprb(INFO, self._cls, 'queryContent()', 221, identifier.getContentIdentifier())
            return content
        except IllegalIdentifierException as e:
            self._logger.logprb(INFO, self._cls, 'queryContent()', 222, e.Message)
            raise e
        except Exception as e:
            msg = self._logger.resolveString(223, traceback.format_exc())
            self._logger.logp(SEVERE, self._cls, 'queryContent()', msg)
            print(msg)

    def compareContentIds(self, id1, id2):
        url1, url2 = id1.getContentIdentifier(), id2.getContentIdentifier()
        if url1 == url2:
            self._logger.logprb(INFO, self._cls, 'compareContentIds()', 231, url1, url2)
            compare = 0
        else:
            self._logger.logprb(INFO, self._cls, 'compareContentIds()', 232, url1, url2)
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

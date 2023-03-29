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

from com.sun.star.ucb import XContentIdentifierFactory
from com.sun.star.ucb import XContentProvider
from com.sun.star.ucb import XParameterizedContentProvider
from com.sun.star.ucb import IllegalIdentifierException

from .contentidentifier import ContentIdentifier

from ..unotool import createService
from ..unotool import parseUrl

from ..datasource import DataSource

from ..logger import getLogger

from ..configuration import g_defaultlog
from ..configuration import g_scheme

import traceback
from threading import Event
from threading import Lock


class ParameterizedProvider(unohelper.Base,
                            XContentIdentifierFactory,
                            XContentProvider):
    def __init__(self, ctx, logger, arguments):
        self._ctx = ctx
        self._authority = True if arguments == 'WithAuthority' else False
        self._clazz = 'ParameterizedProvider%s' % arguments
        self._sync = Event()
        self._lock = Lock()
        self._transformer = createService(ctx, 'com.sun.star.util.URLTransformer')
        if self._datasource is None:
            ParameterizedProvider.__datasource = DataSource(ctx, logger, self._sync, self._lock)
        self._logger = logger
        self._logger.logprb(INFO, self._clazz, '__init__()', 201, arguments)

    __datasource = None

    @property
    def _datasource(self):
        return ParameterizedProvider.__datasource

    # XContentIdentifierFactory
    def createContentIdentifier(self, url):
        identifier = ContentIdentifier(self._getContentIdentifierUrl(url))
        self._logger.logprb(INFO, self._clazz, 'createContentIdentifier()', 211, url, identifier.getContentIdentifier())
        return identifier

    # XContentProvider
    def queryContent(self, identifier):
        try:
            content = self._datasource.queryContent(self, self._authority, identifier)
            self._logger.logprb(INFO, self._clazz, 'queryContent()', 221, identifier.getContentIdentifier())
            return content
        except IllegalIdentifierException as e:
            self._logger.logprb(INFO, self._clazz, 'queryContent()', 222, e.Message)
            raise e
        except Exception as e:
            msg = self._logger.resolveString(223, traceback.format_exc())
            self._logger.logp(SEVERE, self._clazz, 'queryContent()', msg)
            print(msg)

    def compareContentIds(self, id1, id2):
        url1, url2 = id1.getContentIdentifier(), id2.getContentIdentifier()
        if url1 == url2:
            self._logger.logprb(INFO, self._clazz, 'compareContentIds()', 231, url1, url2)
            compare = 0
        else:
            self._logger.logprb(INFO, self._clazz, 'compareContentIds()', 232, url1, url2)
            compare = -1
        return compare

    # Private methods
    def _getContentIdentifierUrl(self, url):
        # FIXME: Sometimes the url can end with a dot, it must be deleted
        url = url.rstrip('.')
        uri = parseUrl(self._transformer, url)
        if uri is not None:
            uri = self._transformer.getPresentation(uri, True)
        return uri if uri else url

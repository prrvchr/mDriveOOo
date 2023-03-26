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

from com.sun.star.ucb import XRestContentProvider

from .contentidentifier import ContentIdentifier

from ..unotool import createService
from ..unotool import parseUrl

from ..datasource import DataSource

from ..logger import getLogger

from ..configuration import g_defaultlog

import traceback
from threading import Event
from threading import Lock


class ContentProvider(unohelper.Base,
                      XContentIdentifierFactory,
                      XContentProvider,
                      XParameterizedContentProvider):
    def __init__(self, ctx, plugin):
        self._ctx = ctx
        self.Scheme = ''
        self.Plugin = plugin
        self._datasource = None
        self._sync = Event()
        self._lock = Lock()
        self._transformer = createService(ctx, 'com.sun.star.util.URLTransformer')
        self._logger = getLogger(ctx)
        self._logger.logprb(INFO, 'ContentProvider', '__init__()', 101, self.Plugin)

    # XParameterizedContentProvider
    def registerInstance(self, scheme, plugin, replace):
        self._logger.logprb(INFO, 'ContentProvider', 'registerInstance()', 111, scheme, plugin)
        datasource = DataSource(self._ctx, self._sync, self._lock, scheme, plugin)
        if not datasource.isValid():
            self._logger.logp(SEVERE, 'ContentProvider', 'registerInstance()', datasource.Error)
            return None
        self.Scheme = scheme
        self.Plugin = plugin
        self._datasource = datasource
        self._logger.logprb(INFO, 'ContentProvider', 'registerInstance()', 112, scheme, plugin)
        return self
    def deregisterInstance(self, scheme, argument):
        self._logger.logprb(INFO, 'ContentProvider', 'deregisterInstance()', 161, scheme)

    # XContentIdentifierFactory
    def createContentIdentifier(self, url):
        print("ContentProvider.createContentIdentifier() 1")
        identifier = ContentIdentifier(self._getContentIdentifierUrl(url))
        self._logger.logprb(INFO, 'ContentProvider', 'createContentIdentifier()', 131, url)
        print("ContentProvider.createContentIdentifier() 2")
        return identifier

    # XContentProvider
    def queryContent(self, identifier):
        try:
            print("ContentProvider.queryContent() 1 Url: %s" % identifier.getContentIdentifier())
            # FIXME: We are forced to perform lazy loading on Identifier (and User) in order to be able
            # FIXME: to trigger an exception when delivering the content ie: XContentProvider.queryContent().
            content = self._datasource.queryContent(self, identifier)
            self._logger.logprb(INFO, 'ContentProvider', 'queryContent()', 141, identifier.getContentIdentifier())
            print("ContentProvider.queryContent() 2")
            return content
        except IllegalIdentifierException as e:
            self._logger.logprb(SEVERE, 'ContentProvider', 'queryContent()', 142, e.Message)
            raise e

    def compareContentIds(self, id1, id2):
        ids = (id1.getContentIdentifier(), id2.getContentIdentifier())
        if id1.Id == id2.Id and id1.User.Id == id2.User.Id:
            msg = self._logger.resolveString(151, ids)
            compare = 0
        else:
            msg = self._logger.resolveString(152, ids)
            compare = -1
        self._logger.logp(INFO, 'ContentProvider', 'compareContentIds()', msg)
        return compare

    # Private methods
    def _getContentIdentifierUrl(self, url):
        print("ContentProvider._getContentIdentifierUrl() Url: %s" % url)
        if not url.endswith('//'):
            url = url.rstrip('/.')
        print("ContentProvider._getContentIdentifierUrl() Url: %s" % url)
        uri = parseUrl(self._transformer, url)
        if uri is not None:
            uri = self._transformer.getPresentation(uri, True)
        print("ContentProvider._getContentIdentifierUrl() Url: %s" % uri)
        return uri if uri else url

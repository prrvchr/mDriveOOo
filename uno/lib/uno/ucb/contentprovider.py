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

from .unotool import createService
from .unotool import parseUrl

from .datasource import DataSource

from .logger import getLogger

from .configuration import g_defaultlog

import traceback
from threading import Event


class ContentProvider(unohelper.Base,
                      XContentIdentifierFactory,
                      XContentProvider,
                      XParameterizedContentProvider,
                      XRestContentProvider):
    def __init__(self, ctx, plugin):
        self._ctx = ctx
        self.Scheme = ''
        self.Plugin = plugin
        self.DataSource = None
        self.event = Event()
        self._user = None
        self._error = ''
        self._factory = createService(ctx, 'com.sun.star.uri.UriReferenceFactory')
        self._transformer = createService(ctx, 'com.sun.star.util.URLTransformer')
        self._logger = getLogger(ctx)
        self._logger.logprb(INFO, 'ContentProvider', '__init__()', 101, self.Plugin)

    def __del__(self):
        self._logger.logprb(INFO, 'ContentProvider', '__del__()', 171, self.Plugin)

    # XParameterizedContentProvider
    def registerInstance(self, scheme, plugin, replace):
        self._logger.logprb(INFO, 'ContentProvider', 'registerInstance()', 111, scheme, plugin)
        datasource = DataSource(self._ctx, self.event, scheme, plugin)
        if not datasource.isValid():
            self._logger.logp(SEVERE, 'ContentProvider', 'registerInstance()', datasource.Error)
            return None
        self.Scheme = scheme
        self.Plugin = plugin
        self.DataSource = datasource
        self._logger.logprb(INFO, 'ContentProvider', 'registerInstance()', 112, scheme, plugin)
        return self
    def deregisterInstance(self, scheme, argument):
        self._logger.logprb(INFO, 'ContentProvider', 'deregisterInstance()', 161, scheme)

    # XContentIdentifierFactory
    def createContentIdentifier(self, url):
        print("ContentProvider.createContentIdentifier() 1")
        # FIXME: We are forced to perform lazy loading on Identifier (and User) in order to be able
        # FIXME: to trigger an exception when delivering the content ie: XContentProvider.queryContent().
        identifier = self.DataSource.getIdentifier(self._factory, self._getContentIdentifier(url), self._user)
        self._logger.logprb(INFO, 'ContentProvider', 'createContentIdentifier()', 131, url)
        print("ContentProvider.createContentIdentifier() 2")
        return identifier

    # XContentProvider
    def queryContent(self, identifier):
        try:
            print("ContentProvider.queryContent() 1")
            # FIXME: We are forced to perform lazy loading on Identifier (and User) in order to be able
            # FIXME: to trigger an exception when delivering the content ie: XContentProvider.queryContent().
            if not identifier.isInitialized():
                identifier.initialize(self.DataSource.DataBase)
            self._user = identifier.User.Name
            content = identifier.getContent()
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
    def _getContentIdentifier(self, identifier):
        url = parseUrl(self._transformer, identifier)
        if url is not None:
            url = self._transformer.getPresentation(url, True)
        return url if url else identifier


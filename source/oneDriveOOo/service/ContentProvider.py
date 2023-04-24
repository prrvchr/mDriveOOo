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

from com.sun.star.lang import XServiceInfo

from com.sun.star.ucb import XContentProvider
from com.sun.star.ucb import XContentIdentifierFactory
from com.sun.star.ucb import XParameterizedContentProvider

from com.sun.star.logging.LogLevel import INFO

from onedrive import ParameterizedProvider

from onedrive import getLogger

from onedrive import g_identifier
from onedrive import g_basename
from onedrive import g_defaultlog

import traceback

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = '%s.ContentProvider' % g_identifier


class ContentProvider(unohelper.Base,
                      XServiceInfo,
                      XContentProvider,
                      XContentIdentifierFactory,
                      XParameterizedContentProvider):
    def __init__(self, ctx):
        print('ContentProvider.__init__()')
        self._ctx = ctx
        self._logger = getLogger(ctx, g_defaultlog, g_basename)
        self._logger.logprb(INFO, 'ContentProvider', '__init__()', 101, g_ImplementationName)

    # XParameterizedContentProvider
    def registerInstance(self, template, arguments, replace):
        print('ContentProvider.registerInstance() 1')
        try:
            provider = ParameterizedProvider(self._ctx, self._logger, arguments)
            print('ContentProvider.registerInstance() 2')
            self._logger.logprb(INFO, 'ContentProvider', 'registerInstance()', 111, arguments)
            return provider
        except Exception as e:
            msg = "ContentProvider.registerInstance() Error: %s" % traceback.print_exc()
            print(msg)

    def deregisterInstance(self, scheme, authority):
        print('ContentProvider.deregisterInstance()')

    # XContentIdentifierFactory
    def createContentIdentifier(self, identifier):
        print('ContentProvider.createContentIdentifier()')
        return None

    # XContentProvider
    def queryContent(self, identifier):
        print('ContentProvider.queryContent()')
        return None
    def compareContentIds(self, identifier1, identifier2):
        print('ContentProvider.compareContentIds()')
        return None

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(ContentProvider,
                                         g_ImplementationName,
                                         (g_ImplementationName,
                                         'com.sun.star.ucb.ContentProvider'))


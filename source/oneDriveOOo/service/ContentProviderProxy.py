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
from com.sun.star.uno import XInterface
from com.sun.star.ucb import XContentIdentifierFactory
from com.sun.star.ucb import XContentProvider
from com.sun.star.ucb import XContentProviderFactory
from com.sun.star.ucb import XContentProviderSupplier
from com.sun.star.ucb import XParameterizedContentProvider

from com.sun.star.beans.PropertyAttribute import BOUND
from com.sun.star.beans.PropertyAttribute import READONLY

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from onedrive import PropertySet
from onedrive import getProperty

from onedrive import ContentProvider

from onedrive import getLogger

from onedrive import g_scheme
from onedrive import g_identifier
from onedrive import g_basename
from onedrive import g_driverlog

g_proxy = 'com.sun.star.ucb.ContentProviderProxy'

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = '%s.ContentProviderProxy' % g_identifier


class ContentProviderProxy(unohelper.Base,
                           XServiceInfo,
                           XContentIdentifierFactory,
                           XContentProvider,
                           XParameterizedContentProvider,
                           XContentProviderSupplier,
                           PropertySet):
    def __init__(self, ctx):
        msg = "ContentProviderProxy for plugin: %s loading ..." % g_identifier
        self.ctx = ctx
        self.scheme = ''
        self.plugin = ''
        self.replace = True
        msg += " Done"
        self._logger = getLogger(ctx, g_driverlog, g_basename)
        self._logger.logp(INFO, 'ContentProviderProxy', '__init__()', msg)
        print('ContentProviderProxy.__init__()')

    _Provider = None

    @property
    def IsLoaded(self):
        return ContentProviderProxy._Provider is not None
    @property
    def Provider(self):
        if not self.IsLoaded:
            ContentProviderProxy._Provider = self._getContentProvider()
        return ContentProviderProxy._Provider

    # XContentProviderFactory
    def createContentProvider(self, service):
        print('ContentProviderProxy.createContentProvider()')
        provider = None
        level = INFO
        msg = "Service: %s loading ..." % service
        ucp = ContentProvider(self.ctx, service)
        if not ucp:
            level = SEVERE
            msg += " ERROR: requested service is not available..."
        else:
            msg += " Done"
            provider = ucp.registerInstance(g_scheme, g_identifier, True)
        self._logger.logp(level, 'ContentProviderProxy', 'createContentProvider()', msg)
        return provider

    # XInterface
    def queryInterface(self, itype):
        print("ContentProviderProxy.queryInterface()")
        return self
    def acquire(self):
        pass
    def release(self):
        pass

    # XContentProviderSupplier
    def getContentProvider(self):
        print('ContentProviderProxy.getContentProvider()')
        return self

    # XContentProviderSupplier
    def getContentProvider1(self):
        print('ContentProviderProxy.getContentProvider()')
        level = INFO
        msg = "Need to get UCP: %s ..." % g_identifier
        if not self.IsLoaded:
            service = '%s.ContentProvider' % g_identifier
            provider = self.createContentProvider(service)
            if not provider:
                level = SEVERE
                msg += " ERROR: requested service is not available..."
            else:
               ContentProviderProxy._Provider = provider
               msg += " Done"
        else:
            msg += " Done"
        self._logger.logp(level, 'ContentProviderProxy', 'getContentProvider()', msg)
        return ContentProviderProxy._Provider

    def _getContentProvider(self):
        print('ContentProviderProxy._getContentProvider()')
        service = '%s.ContentProvider' % g_identifier
        provider = self.createContentProvider(service)
        return provider

    # XParameterizedContentProvider
    def registerInstance(self, scheme, plugin, replace):
        msg = "Register Scheme/Plugin/Replace: %s/%s/%s ..." % (scheme, plugin, replace)
        print('ContentProviderProxy.registerInstance() %s' % msg)
        self.scheme = scheme
        self.plugin = plugin
        self.replace = replace
        msg += " Done"
        self._logger.logp(INFO, 'ContentProviderProxy', 'registerInstance()', msg)
        return self
    def deregisterInstance(self, scheme, plugin):
        print('ContentProviderProxy.deregisterInstance()')
        #self.Provider.deregisterInstance(scheme, plugin)
        msg = "ContentProviderProxy.deregisterInstance(): %s - %s ... Done" % (scheme, plugin)
        self._logger.logp(INFO, 'ContentProviderProxy', 'deregisterInstance()', msg)

    # XContentIdentifierFactory
    def createContentIdentifier(self, identifier):
        print('ContentProviderProxy.createContentIdentifier()')
        return self.Provider.createContentIdentifier(identifier)

    # XContentProvider
    def queryContent(self, identifier):
        print('ContentProviderProxy.queryContent()')
        return self.Provider.queryContent(identifier)
    def compareContentIds(self, identifier1, identifier2):
        return self.Provider.compareContentIds(identifier1, identifier2)

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)

    def _getPropertySetInfo(self):
        properties = {}
        properties['IsLoaded'] = getProperty('IsLoaded', 'boolean', BOUND | READONLY)
        return properties

g_ImplementationHelper.addImplementation(ContentProviderProxy,
                                         g_ImplementationName,
                                        (g_ImplementationName, g_proxy))

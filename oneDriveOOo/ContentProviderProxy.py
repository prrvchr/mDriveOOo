#!
# -*- coding: utf_8 -*-

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

from unolib import PropertySet
from unolib import getProperty

from onedrive import ContentProvider

from onedrive import logMessage
from onedrive import getUcp
from onedrive import g_scheme
from onedrive import g_identifier

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

    _Provider = None

    @property
    def IsLoaded(self):
        return ContentProviderProxy._Provider is not None
    @property
    def Provider(self):
        if not self.IsLoaded:
            ContentProviderProxy._Provider = self._getContentProvider()
        return ContentProviderProxy._Provider

    def __init__(self, ctx):
        msg = "ContentProviderProxy for plugin: %s loading ..." % g_identifier
        self.ctx = ctx
        self.scheme = ''
        self.plugin = ''
        self.replace = True
        msg += " Done"
        logMessage(self.ctx, INFO, msg, 'ContentProviderProxy', '__init__()')
        print('ContentProviderProxy.__init__()')

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
        logMessage(self.ctx, level, msg, 'ContentProviderProxy', 'createContentProvider()')
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
        logMessage(self.ctx, level, msg, 'ContentProviderProxy', 'getContentProvider()')
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
        logMessage(self.ctx, INFO, msg, 'ContentProviderProxy', 'registerInstance()')
        return self
    def deregisterInstance(self, scheme, plugin):
        print('ContentProviderProxy.deregisterInstance()')
        #self.Provider.deregisterInstance(scheme, plugin)
        msg = "ContentProviderProxy.deregisterInstance(): %s - %s ... Done" % (scheme, plugin)
        logMessage(self.ctx, INFO, msg, 'ContentProviderProxy', 'deregisterInstance()')

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

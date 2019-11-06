#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.lang import XServiceInfo
from com.sun.star.ucb import XContentIdentifierFactory
from com.sun.star.ucb import XContentProvider
from com.sun.star.ucb import XContentProviderFactory
from com.sun.star.ucb import XContentProviderSupplier
from com.sun.star.ucb import XParameterizedContentProvider
from com.sun.star.beans.PropertyAttribute import BOUND
from com.sun.star.beans.PropertyAttribute import READONLY
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from clouducp import g_scheme
from clouducp import g_plugin
from clouducp import getLogger
from clouducp import getUcp
from clouducp import PropertySet
from clouducp import getProperty

g_proxy = 'com.sun.star.ucb.ContentProviderProxy'

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = '%s.ContentProviderProxy' % g_plugin


class ContentProviderProxy(unohelper.Base,
                           XServiceInfo,
                           XContentIdentifierFactory,
                           XContentProvider,
                           XContentProviderFactory,
                           XContentProviderSupplier,
                           PropertySet):

    _Provider = None

    @property
    def IsLoaded(self):
        return ContentProviderProxy._Provider is not None

    def __init__(self, ctx):
        msg = "ContentProviderProxy for plugin: %s loading ..." % g_plugin
        self.ctx = ctx
        self.scheme = ''
        self.plugin = ''
        self.replace = True
        self.Logger = getLogger(self.ctx)
        msg += " Done"
        self.Logger.logp(INFO, 'ContentProviderProxy', '__init__()', msg)

    # XContentProviderFactory
    def createContentProvider(self, service):
        print('ContentProviderProxy.createContentProvider()')
        provider = None
        level = INFO
        msg = "Service: %s loading ..." % service
        ucp = self.ctx.ServiceManager.createInstanceWithContext(service, self.ctx)
        if not ucp:
            level = SEVERE
            msg += " ERROR: requested service is not available..."
        else:
            msg += " Done"
            provider = ucp.registerInstance(g_scheme, g_plugin, True)
        self.Logger.logp(level, 'ContentProviderProxy', 'createContentProvider()', msg)
        return provider

    # XContentProviderSupplier
    def getContentProvider(self):
        print('ContentProviderProxy.getContentProvider()')
        level = INFO
        msg = "Need to get UCP: %s ..." % g_plugin
        if not self.IsLoaded:
            service = '%s.ContentProvider' % g_plugin
            provider = self.createContentProvider(service)
            if not provider:
                level = SEVERE
                msg += " ERROR: requested service is not available..."
            else:
               ContentProviderProxy._Provider = provider
               msg += " Done"
        else:
            msg += " Done"
        self.Logger.logp(level, 'ContentProviderProxy', 'getContentProvider()', msg)
        return ContentProviderProxy._Provider

    # XParameterizedContentProvider
    def registerInstance1(self, scheme, plugin, replace):
        msg = "Register Scheme/Plugin/Replace: %s/%s/%s ..." % (scheme, plugin, replace)
        self.scheme = scheme
        self.plugin = plugin
        self.replace = replace
        msg += " Done"
        self.Logger.logp(INFO, 'ContentProviderProxy', 'registerInstance()', msg)
        return self
    def deregisterInstance1(self, scheme, plugin):
        self.getContentProvider().deregisterInstance(scheme, plugin)
        msg = "ContentProviderProxy.deregisterInstance(): %s - %s ... Done" % (scheme, plugin)
        self.Logger.logp(INFO, 'ContentProviderProxy', 'deregisterInstance()', msg)

    # XContentIdentifierFactory
    def createContentIdentifier(self, identifier):
        return self.getContentProvider().createContentIdentifier(identifier)

    # XContentProvider
    def queryContent(self, identifier):
        return self.getContentProvider().queryContent(identifier)
    def compareContentIds(self, identifier1, identifier2):
        return self.getContentProvider().compareContentIds(identifier1, identifier2)

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

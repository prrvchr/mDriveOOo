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
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from onedrive import g_plugin
from onedrive import g_provider
from onedrive import g_oauth2


# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = '%s.ContentProviderProxy' % g_plugin


class ContentProviderProxy(unohelper.Base,
                           XServiceInfo,
                           XContentIdentifierFactory,
                           XContentProvider,
                           XContentProviderFactory,
                           XContentProviderSupplier,
                           XParameterizedContentProvider):
    def __init__(self, ctx):
        self.ctx = ctx
        self.template = ''
        self.arguments = ''
        self.replace = True
        self.Logger = self._getLogger()
        msg = "ContentProviderProxy for plugin: %s loading ... Done" % g_plugin
        self.Logger.logp(INFO, 'ContentProviderProxy', '__init__()', msg)

    def __del__(self):
        msg = "ContentProviderProxy for plugin: %s unloading ... Done" % g_plugin
        self.Logger.logp(INFO, 'ContentProviderProxy', '__del__()', msg)

    # XContentProviderFactory
    def createContentProvider(self, service):
        ucp = self.ctx.ServiceManager.createInstanceWithContext(g_provider, self.ctx)
        provider = ucp.registerInstance(self.template, self.arguments, self.replace)
        msg = "ContentProviderProxy createContentProvider: %s ... Done" % service
        self.Logger.logp(INFO, 'ContentProviderProxy', 'createContentProvider()', msg)
        return provider

    # XContentProviderSupplier
    def getContentProvider(self):
        provider = self._getUcp()
        if provider.supportsService('com.sun.star.ucb.ContentProviderProxy'):
            provider = self.createContentProvider(g_provider)
        msg = "ContentProviderProxy getContentProvider: %s ... Done" % g_provider
        self.Logger.logp(INFO, 'ContentProviderProxy', 'getContentProvider()', msg)
        return provider

    # XParameterizedContentProvider
    def registerInstance(self, template, arguments, replace):
        self.template = template
        self.arguments = arguments
        self.replace = replace
        msg = "ContentProviderProxy.registerInstance(): %s - %s ... Done" % (template, arguments)
        self.Logger.logp(INFO, 'ContentProviderProxy', 'registerInstance()', msg)
        return self
    def deregisterInstance(self, template, argument):
        self.getContentProvider().deregisterInstance(template, argument)
        msg = "ContentProviderProxy.deregisterInstance(): %s - %s ... Done" % (template, argument)
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

    def _getUcb(self, arguments=('Local', 'Office')):
        name = 'com.sun.star.ucb.UniversalContentBroker'
        return self.ctx.ServiceManager.createInstanceWithArguments(name, (arguments, ))

    def _getUcp(self):
        return self._getUcb().queryContentProvider('%s://' % self.template)

    def _getLogger(self, logger='org.openoffice.logging.DefaultLogger'):
        singleton = '/singletons/com.sun.star.logging.LoggerPool'
        return self.ctx.getValueByName(singleton).getNamedLogger(logger)


g_ImplementationHelper.addImplementation(ContentProviderProxy,
                                         g_ImplementationName,
                                        (g_ImplementationName, 'com.sun.star.ucb.ContentProviderProxy'))

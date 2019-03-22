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

from onedrive import g_plugin
from onedrive import g_provider

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
        print("ContentProviderProxy.__init__()")

    def __del__(self):
         print("ContentProviderProxy.__del__(): %s - %s" % (g_plugin, g_provider))

    # XContentProviderFactory
    def createContentProvider(self, service):
        print("ContentProviderProxy.createContentProvider() %s" % service)
        ucp = self.ctx.ServiceManager.createInstanceWithContext(service, self.ctx)
        provider = ucp.registerInstance(self.template, self.arguments, self.replace)
        return provider

    # XContentProviderSupplier
    def getContentProvider(self):
        provider = self._getUcp()
        print("ContentProviderProxy.getContentProvider() 1")
        if provider.supportsService('com.sun.star.ucb.ContentProviderProxy'):
            print("ContentProviderProxy.getContentProvider() 2")
            provider = self.createContentProvider('%s.ContentProvider' % g_provider)
            print("ContentProviderProxy.getContentProvider() 3")
        return provider

    # XParameterizedContentProvider
    def registerInstance(self, template, arguments, replace):
        print("ContentProviderProxy.registerInstance(): %s - %s" % (template, arguments))
        self.template = template
        self.arguments = arguments
        self.replace = replace
        return self
    def deregisterInstance(self, template, argument):
        self.getContentProvider().deregisterInstance(template, argument)

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


g_ImplementationHelper.addImplementation(ContentProviderProxy,                                               # UNO object class
                                         g_ImplementationName,                                               # Implementation name
                                        (g_ImplementationName, 'com.sun.star.ucb.ContentProviderProxy'))     # List of implemented services

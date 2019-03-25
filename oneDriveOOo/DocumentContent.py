#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.lang import XServiceInfo


from onedrive import g_doc_map
from onedrive import g_plugin

# clouducp is only available after CloudUcpOOo as been loaded...
try:
    from clouducp import DocumentContentBase
except ImportError:
    class DocumentContentBase():
        pass

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = '%s.DocumentContent' % g_plugin


class DocumentContent(DocumentContentBase,
                      XServiceInfo):
    def __init__(self, ctx, *namedvalues):
        super(DocumentContent, self).__init__(ctx, namedvalues)
        self.ContentType = 'application/vnd.microsoft-apps.document'

    def getDocumentMap(self):
        return g_doc_map

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(DocumentContent,                                                    # UNO object class
                                         g_ImplementationName,                                               # Implementation name
                                        (g_ImplementationName, 'com.sun.star.ucb.Content'))                  # List of implemented services

#!
# -*- coding: utf_8 -*-

import unohelper

from com.sun.star.lang import XServiceInfo

from onedrive import getUser
from onedrive import setJsonData
from onedrive import g_host
from onedrive import g_plugin

# clouducp is only available after CloudUcpOOo as been loaded...
try:
    from clouducp import ContentUserBase
except ImportError:
    class ContentUserBase():
        pass

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = '%s.ContentUser' % g_plugin


class ContentUser(ContentUserBase,
                  XServiceInfo):
    def __init__(self, ctx, *namedvalues):
        ContentUserBase.__init__(self, ctx, namedvalues)

    def getHost(self):
        return g_host
    def selectUser(self):
        user = None
        select = self.Connection.prepareCall('CALL "selectUser"(?)')
        select.setString(1, self.Name)
        result = select.executeQuery()
        if result.next():
            user = self.getItemFromResult(result)
        select.close()
        return user
    def getUser(self, session):
        return getUser(session)
    def checkIdentifiers(self, session):
        pass
    def mergeJsonUser(self, user, data):
        root = None
        merge = self.Connection.prepareCall('CALL "mergeJsonUser"(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
        merge.setString(1, user.get('id'))
        merge.setString(2, user.get('userPrincipalName'))
        merge.setString(3, user.get('displayName'))
        index = setJsonData(merge, data, self.getDateTimeParser(), self.unparseDateTime(), 4)
        result = merge.executeQuery()
        if result.next():
            root = self.getItemFromResult(result)
        merge.close()
        return root

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(ContentUser,                                                        # UNO object class
                                         g_ImplementationName,                                               # Implementation name
                                        (g_ImplementationName, ))                                            # List of implemented services

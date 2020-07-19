#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.lang import XServiceInfo
from com.sun.star.lang import XComponent
from com.sun.star.sdb import XCompletedConnection
from com.sun.star.sdbc import XIsolatedConnection
from com.sun.star.util import XFlushable
from com.sun.star.sdb import XQueryDefinitionsSupplier
from com.sun.star.sdbc import XDataSource
from com.sun.star.sdb import XBookmarksSupplier
from com.sun.star.sdb import XDocumentDataSource
from com.sun.star.uno import XWeak

from com.sun.star.beans.PropertyAttribute import BOUND
from com.sun.star.beans.PropertyAttribute import READONLY

from unolib import PropertySet
from unolib import getProperty

import traceback


class DocumentDataSource(unohelper.Base,
                         XServiceInfo,
                         XComponent,
                         XCompletedConnection,
                         XIsolatedConnection,
                         XFlushable,
                         XQueryDefinitionsSupplier,
                         XDataSource,
                         XBookmarksSupplier,
                         XDocumentDataSource,
                         XWeak,
                         PropertySet):
    def __init__(self, datasource, protocols, username):
        self._datasource = datasource
        self._protocols = protocols
        self._username = username

    @property
    def Name(self):
        return self._datasource.Name
    @property
    def URL(self):
        return ':'.join(self._protocols)
    @URL.setter
    def URL(self, url):
        self._datasource.URL = url
    @property
    def Info(self):
        return self._datasource.Info
    @Info.setter
    def Info(self, info):
        self._datasource.Info = info
    @property
    def Settings(self):
        return self._datasource.Settings
    @property
    def User(self):
        return self._username
    @User.setter
    def User(self, user):
        pass
    @property
    def Password(self):
        return self._datasource.Password
    @Password.setter
    def Password(self, password):
        self._datasource.Password = password
    @property
    def IsPasswordRequired(self):
        return self._datasource.IsPasswordRequired
    @IsPasswordRequired.setter
    def IsPasswordRequired(self, state):
        self._datasource.IsPasswordRequired = state
    @property
    def SuppressVersionColumns(self):
        return self._datasource.SuppressVersionColumns
    @SuppressVersionColumns.setter
    def SuppressVersionColumns(self, state):
        self._datasource.SuppressVersionColumns = state
    @property
    def IsReadOnly(self):
        return self._datasource.IsReadOnly
    @property
    def NumberFormatsSupplier(self):
        return self._datasource.NumberFormatsSupplier
    @property
    def TableFilter(self):
        return self._datasource.TableFilter
    @TableFilter.setter
    def TableFilter(self, filter):
        self._datasource.TableFilter = filter
    @property
    def TableTypeFilter(self):
        return self._datasource.TableTypeFilter
    @TableTypeFilter.setter
    def TableTypeFilter(self, filter):
        self._datasource.TableTypeFilter = filter
    @property
    def DatabaseDocument(self):
        return self._datasource.DatabaseDocument

    # XComponent
    def dispose(self):
        print("DataSource.dispose()")
        self._datasource.dispose()
    def addEventListener(self, listener):
        print("DataSource.addEventListener()")
        self._datasource.addEventListener(listener)
    def removeEventListener(self, listener):
        print("DataSource.removeEventListener()")
        self._datasource.removeEventListener(listener)

    # XWeak
    def queryAdapter(self):
        print("DataSource.queryAdapter()")
        return self._datasource.queryAdapter()

    # XCompletedConnection
    def connectWithCompletion(self, handler):
        print("DataSource.connectWithCompletion()")
        return self._datasource.connectWithCompletion(handler)

    # XIsolatedConnection
    def getIsolatedConnectionWithCompletion(self, handler):
        print("DataSource.getIsolatedConnectionWithCompletion()")
        return self._datasource.getIsolatedConnectionWithCompletion(handler)
    def getIsolatedConnection(self, user, password):
        print("DataSource.getIsolatedConnection()")
        return self._datasource.getIsolatedConnection(user, password)

    # XFlushable
    def flush(self):
        print("DataSource.flush()")
        self._datasource.flush()
    def addFlushListener(self, listener):
        print("DataSource.addFlushListener()")
        self._datasource.addFlushListener(listener)
    def removeFlushListener(self):
        print("DataSource.removeFlushListener()")
        self._datasource.removeFlushListener(listener)

    # XQueryDefinitionsSupplier
    def getQueryDefinitions(self):
        print("DataSource.getQueryDefinitions()")
        return self._datasource.getQueryDefinitions()

    # XDataSource
    def getConnection(self, user, password):
        print("DataSource.getConnection()")
        return self._datasource.getConnection(user, password)
    def setLoginTimeout(self, seconds):
        print("DataSource.setLoginTimeout()")
        self._datasource.setLoginTimeout(seconds)
    def getLoginTimeout(self):
        print("DataSource.getLoginTimeout()")
        return self._datasource.getLoginTimeout()

    # XBookmarksSupplier
    def getBookmarks(self):
        print("DataSource.getBookmarks()")
        return self._datasource.getBookmarks()

    # XServiceInfo
    def supportsService(self, service):
        return self._datasource.supportsService(service)
    def getImplementationName(self):
        return self._datasource.getImplementationName()
    def getSupportedServiceNames(self):
        return self._datasource.getSupportedServiceNames()

    # XPropertySet
    def _getPropertySetInfo(self):
        properties = {}
        properties['Name'] = getProperty('Name', 'string', READONLY)
        properties['URL'] = getProperty('URL', 'string', BOUND)
        infotype = '[]com.sun.star.beans.PropertyValue'
        properties['Info'] = getProperty('Info', infotype, BOUND)
        settingtype = '[]com.sun.star.beans.XPropertySet'
        properties['Settings'] = getProperty('Settings', settingtype, READONLY)
        properties['User'] = getProperty('User', 'string', BOUND)
        properties['Password'] = getProperty('Password', 'string', BOUND)
        properties['IsPasswordRequired'] = getProperty('IsPasswordRequired', 'boolean', BOUND)
        properties['SuppressVersionColumns'] = getProperty('SuppressVersionColumns', 'boolean', BOUND)
        properties['IsReadOnly'] = getProperty('IsReadOnly', 'boolean', READONLY)
        numbertype = 'com.sun.star.util.XNumberFormatsSupplier'
        properties['NumberFormatsSupplier'] = getProperty('NumberFormatsSupplier', numbertype, READONLY)
        properties['TableFilter'] = getProperty('TableFilter', '[]string', BOUND)
        properties['TableTypeFilter'] = getProperty('TableTypeFilter', '[]string', BOUND)
        databasedocument = 'com.sun.star.sdb.XOfficeDatabaseDocument'
        properties['DatabaseDocument'] = getProperty('DatabaseDocument', databasedocument, READONLY)
        return properties

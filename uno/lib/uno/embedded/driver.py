#!
# -*- coding: utf_8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-25 https://prrvchr.github.io                                  ║
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

import unohelper

from com.sun.star.lang import XServiceInfo

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.sdbc import XDriver
from com.sun.star.sdbc import SQLException

from .documenthandler import DocumentHandler

from .unotool import checkVersion
from .unotool import createService
from .unotool import getConfiguration
from .unotool import getExtensionVersion
from .unotool import getLibreOfficeInfo
from .unotool import getPropertyValueSet
from .unotool import getResourceLocation

from .helper import getException

from .logger import getLogger

from .jdbcdriver import g_extension as g_jdbcext
from .jdbcdriver import g_identifier as g_jdbcid
from .jdbcdriver import g_version as g_jdbcver

from .configuration import g_dbname
from .configuration import g_extension
from .configuration import g_identifier
from .configuration import g_defaultlog
from .configuration import g_basename
from .configuration import g_protocol
from .configuration import g_url
from .configuration import g_user
from .configuration import g_lover
from .configuration import g_driver

import traceback


class Driver(unohelper.Base,
             XServiceInfo,
             XDriver):

    def __init__(self, ctx, lock, logger, service, implementation, services):
        self._ctx = ctx
        self._lock = lock
        self._driver = createService(ctx, service)
        self._implementation = implementation
        self._services = services
        self._logger = logger
        # FIXME: If we want to add the StorageChangeListener only once,
        # FIXME: we need to be able to retrieve the DocumentHandler (keep a reference)
        self._handlers = []

    # XDriver
    def connect(self, url, infos):
        # XXX: We need to test first if configuration is OK...
        newinfos, document, storage, location = self._getConnectionInfo(infos)
        if storage is None or location is None:
            self._logException(112, url, ' ')
            raise self._getException(1001, None, 111, 112, url, '\n')
        handler = self._getDocumentHandler(location)
        # XXX: Getting path from handler unpacks the database files
        path = handler.getConnectionUrl(storage)
        self._logger.logprb(INFO, 'Driver', 'connect()', 113, location)
        try:
            connection = self._driver.connect(path, newinfos)
        except Exception as e:
            self._logger.logprb(SEVERE, 'Driver', 'connect()', 115, str(e), traceback.format_exc())
            # XXX: Database files will only be deleted if they have been unpacked
            handler.removeFolder()
            raise e
        # XXX: Connection has been done we can add close and change listener to document
        self._setDocumentHandler(document, handler)
        version = connection.getMetaData().getDriverVersion()
        self._logger.logprb(INFO, 'Driver', 'connect()', 114, g_dbname, version, g_user)
        return connection

    def acceptsURL(self, url):
        accept = url.startswith(g_url)
        self._logger.logprb(INFO, 'Driver', 'acceptsURL()', 131, url, accept)
        return accept

    def getPropertyInfo(self, url, infos):
        try:
            # XXX: We need to test first if configuration is OK...
            self._logger.logprb(INFO, 'Driver', 'getPropertyInfo()', 141, url)
            drvinfo = self._driver.getPropertyInfo(g_protocol, infos)
            for info in drvinfo:
                self._logger.logprb(INFO, 'Driver', 'getPropertyInfo()', 142, info.Name, info.Value)
            return drvinfo
        except SQLException as e:
            self._logger.logp(SEVERE, 'Driver', 'getPropertyInfo()', e.Message)
            raise e
        except Exception as e:
            self._logger.logprb(SEVERE, 'Driver', 'getPropertyInfo()', 143, e, traceback.format_exc())
            raise e

    def getMajorVersion(self):
        return 1
    def getMinorVersion(self):
        return 0

    # XServiceInfo
    def supportsService(self, service):
        return service in self._services
    def getImplementationName(self):
        return self._implementation
    def getSupportedServiceNames(self):
        return self._services

    # Driver private getter methods
    def _getConnectionInfo(self, infos):
        document = storage = url = None
        config = getConfiguration(self._ctx, g_identifier)
        level = config.getByName('ApiLevel')
        system = config.getByName('ShowSystemTable')
        bookmark = config.getByName('UseBookmark')
        mode = config.getByName('SQLMode')
        newinfos = {'Url': g_url,
                    'ApiLevel': level,
                    'ShowSystemTable': system,
                    'UseBookmark': bookmark,
                    'SQLMode': mode}
        if g_user:
            newinfos['user'] = g_user
        if g_driver:
            path = getResourceLocation(self._ctx, g_identifier, g_driver)
            newinfos['JavaDriverClassPath'] = path
        for info in infos:
            if info.Name == 'URL':
                url = info.Value
            elif info.Name == 'Storage':
                storage = info.Value
            elif info.Name == 'Document':
                document = info.Value
            else:
                newinfos[info.Name] = info.Value
        return getPropertyValueSet(newinfos), document, storage, url

    def _getHandler(self, location):
        document = None
        # XXX: If we want to be able to remove dead handler we need to do copy
        for handler in self._handlers[:]:
            url = handler.URL
            # XXX: The URL is None for a closed connection and can be cleared.
            if url is None:
                self._handlers.remove(handler)
            elif url == location:
                document = handler
        return document

    def _getDocumentHandler(self, location):
        with self._lock:
            handler = self._getHandler(location)
            if handler is None:
                handler = DocumentHandler(self._ctx, self._lock, self._logger, self._driver, location)
            return handler

    def _setDocumentHandler(self, document, handler):
        with self._lock:
            # FIXME: We only add handler if connection is successful
            if handler not in self._handlers:
                if self._setListener(document, handler):
                    self._handlers.append(handler)

    def _setListener(self, document, handler):
        # FIXME: With OpenOffice there is no Document in the info
        # FIXME: parameter provided during the connection
        if document is None:
            document = handler.getDocument()
        if document is not None:
            document.addStorageChangeListener(handler)
            document.addCloseListener(handler)
            return True
        return False

    def _logException(self, resource, *args):
        self._logger.logprb(SEVERE, 'Driver', 'connect()', resource, *args)

    def _getException(self, code, exc, state, resource, *args):
        return getException(self._logger, self, code, exc, state, resource, *args)


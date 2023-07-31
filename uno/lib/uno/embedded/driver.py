#!
# -*- coding: utf_8 -*-

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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.sdbc import XDriver
from com.sun.star.sdbc import SQLException

from .documenthandler import DocumentHandler

from .unotool import createService
from .unotool import getConfiguration
from .unotool import getPropertyValueSet

from .logger import getLogger

from .configuration import g_identifier
from .configuration import g_defaultlog
from .configuration import g_basename
from .configuration import g_protocol
from .configuration import g_url
from .configuration import g_user

import traceback


class Driver(unohelper.Base,
             XServiceInfo,
             XDriver):

    def __init__(self, ctx, lock, service, name):
        self._ctx = ctx
        self._lock = lock
        self._service = service
        self._name = name
        self._logger = getLogger(ctx, g_defaultlog, g_basename)
        # FIXME: Driver is lazy loaded in connect() driver method to be able to throw
        # FIXME: an exception if jdbcDriverOOo extension is not installed.
        self._driver = None
        # FIXME: If we want to add the StorageChangeListener only once,
        # FIXME: we need to be able to retrieve the DocumentHandler (keep a reference)
        self._handlers = []

    # XDriver
    def connect(self, url, infos):
        try:
            newinfos, document, storage, location = self._getConnectionInfo(infos)
            if storage is None or location is None:
                code = self._logger.resolveString(111)
                msg = self._logger.resolveString(112, url)
                raise self._getException(code, 1001, msg, self)
            driver = self._getDriver()
            handler = self._getDocumentHandler(location)
            path = handler.getConnectionUrl(document, storage, location)
            print("driver.connect() Path: %s" % path)
            self._logger.logprb(INFO, 'Driver', 'connect()', 113, location)
            connection = driver.connect(path, newinfos)
            version = connection.getMetaData().getDriverVersion()
            self._logger.logprb(INFO, 'Driver', 'connect()', 114, version, g_user)
            return connection
        except SQLException as e:
            self._logger.logp(SEVERE, 'Driver', 'connect()', e.Message)
            raise e
        except Exception as e:
            self._logger.logprb(SEVERE, 'Driver', 'connect()', 117, e, traceback.format_exc())
            raise e

    def acceptsURL(self, url):
        accept = url.startswith(g_url)
        self._logger.logprb(INFO, 'Driver', 'acceptsURL()', 121, url, accept)
        return accept

    def getPropertyInfo(self, url, infos):
        try:
            self._logger.logprb(INFO, 'Driver', 'getPropertyInfo()', 131, url)
            driver = self._getDriver()
            drvinfo = driver.getPropertyInfo(g_protocol, infos)
            for info in drvinfo:
                self._logger.logprb(INFO, 'Driver', 'getPropertyInfo()', 132, info.Name, info.Value)
            return drvinfo
        except SQLException as e:
            self._logger.logp(SEVERE, 'Driver', 'getPropertyInfo()', e.Message)
            raise e
        except Exception as e:
            self._logger.logprb(SEVERE, 'Driver', 'getPropertyInfo()', 133, e, traceback.format_exc())
            raise e

    def getMajorVersion(self):
        return 1
    def getMinorVersion(self):
        return 0

    # XServiceInfo
    def supportsService(self, service):
        return service in self._services
    def getImplementationName(self):
        return self._name
    def getSupportedServiceNames(self):
        return self._services

    # Driver private getter methods
    def _getDriver(self):
        # FIXME: If jdbcDriverOOo is not installed,
        # FIXME: we need to throw SQLException
        if self._driver is None:
            driver = createService(self._ctx, self._service)
            if driver is None:
                code = self._logger.resolveString(181)
                msg = self._logger.resolveString(182, self._service)
                raise self._getException(code, 1001, msg, self)
            self._driver = driver
        return self._driver

    def _getConnectionInfo(self, infos):
        document = storage = url = None
        service = getConfiguration(self._ctx, g_identifier).getByName('ConnectionService')
        newinfos = {'Url': g_url, 'ConnectionService': service}
        for info in infos:
            if info.Name == 'URL':
                url = info.Value
            elif info.Name == 'Storage':
                storage = info.Value
            elif info.Name == 'Document':
                document = info.Value
            else:
                newinfos[info.Name] = info.Value
                print("Driver._getConnectionInfo() Name: %s - Value: %s" % (info.Name, info.Value))
        return getPropertyValueSet(newinfos), document, storage, url

    def _getHandler(self, location):
        document = None
        for handler in self._handlers:
            url = handler.URL
            if url is None:
                self._handlers.remove(handler)
            elif url == location:
                document = handler
        return document

    def _getDocumentHandler(self, location):
        with self._lock:
            handler = self._getHandler(location)
            if handler is None:
                handler = DocumentHandler(self._ctx, self._lock, self._logger, location)
                self._handlers.append(handler)
            return handler

    def _getException(self, state, code, message, context=None, exception=None):
        error = SQLException()
        error.SQLState = state
        error.ErrorCode = code
        error.NextException = exception
        error.Message = message
        error.Context = context
        return error


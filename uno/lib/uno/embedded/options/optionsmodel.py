#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-24 https://prrvchr.github.io                                  ║
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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.uno import Exception as UnoException

from ..unotool import createService
from ..unotool import getConfiguration

from ..configuration import g_identifier
from ..configuration import g_defaultlog

from ..logger import getLogger
g_basename = 'OptionsDialog'

import traceback


class OptionsModel():
    def __init__(self, ctx, url=None):
        self._ctx = ctx
        self._url = url
        self._services = {'Driver': ('io.github.prrvchr.jdbcdriver.sdbc.Driver',
                                     'io.github.prrvchr.jdbcdriver.sdbcx.Driver'),
                          'Connection': ('com.sun.star.sdbc.Connection',
                                         'com.sun.star.sdbcx.Connection',
                                         'com.sun.star.sdb.Connection')}
        self._config = getConfiguration(ctx, g_identifier, True)
        self._service = self._getDriverService()

# OptionsModel getter methods
    def getViewData(self):
        driver = self._services.get('Driver').index(self._getDriverService())
        connection = self._services.get('Connection').index(self._getConnectionService())
        enabled = self._isConnectionEnabled(driver)
        version = self._getDriverVersion()
        system = self._config.getByName('ShowSystemTable')
        bookmark = self._config.getByName('UseBookmark')
        mode = self._config.getByName('SQLMode')
        return driver, connection, enabled, version, system, bookmark, mode

    def loadSetting(self):
        self._config = getConfiguration(self._ctx, g_identifier, True)
        return self.getViewData()

    def getServicesLevel(self):
        driver = self._services.get('Driver').index(self._getDriverService())
        connection = self._services.get('Connection').index(self._getConnectionService())
        return driver, connection, self._isConnectionEnabled(driver)

# OptionsModel setter methods
    def setDriverService(self, driver):
        self._config.replaceByName('DriverService', self._services.get('Driver')[driver])
        connection = self._services.get('Connection').index(self._getConnectionService())
        if driver and not connection:
            connection = 1
            self.setConnectionService(connection)
        return connection, self._isConnectionEnabled(driver)

    def setConnectionService(self, level):
        self._config.replaceByName('ConnectionService', self._services.get('Connection')[level])

    def setSystemTable(self, state):
        self._config.replaceByName('ShowSystemTable', bool(state))

    def setBookmark(self, state):
        self._config.replaceByName('UseBookmark', bool(state))

    def setSQLMode(self, state):
        self._config.replaceByName('SQLMode', bool(state))

    def saveSetting(self):
        config = self._config.hasPendingChanges()
        if config:
            self._config.commitChanges()
            if self._service != self._getDriverService():
                return True
        return False

# OptionsModel private methods
    def _getDriverService(self):
        return self._config.getByName('DriverService')

    def _getConnectionService(self):
        return self._config.getByName('ConnectionService')

    def _isConnectionEnabled(self, driver):
        return driver == 0

    def _getLevelValue(self, level):
        return '%d' % level

    def _getDriverVersion(self):
        version = 'N/A'
        if self._url is None:
            return version
        try:
            service = self._getDriverService()
            driver = createService(self._ctx, service)
            # FIXME: If jdbcDriverOOo extension has not been installed then driver is None
            if driver is not None:
                connection = driver.connect(self._url, ())
                version = connection.getMetaData().getDriverVersion()
                connection.close()
                driver.dispose()
        except UnoException as e:
            self._getLogger().logprb(SEVERE, 'OptionsModel', '_getDriverVersion()', 141, e.Message)
        except Exception as e:
            self._getLogger().logprb(SEVERE, 'OptionsModel', '_getDriverVersion()', 142, str(e), traceback.format_exc())
        return version

    def _getLogger(self):
        return getLogger(self._ctx, g_defaultlog, g_basename)

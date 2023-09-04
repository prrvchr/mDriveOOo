#!
# -*- coding: utf-8 -*-

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

import unohelper

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


class OptionsModel(unohelper.Base):

    _level = False
    _reboot = False

    def __init__(self, ctx):
        self._ctx = ctx
        self._url = 'xdbc:hsqldb:mem:dbversion'
        self._services = {'Driver': ('io.github.prrvchr.jdbcdriver.sdbc.Driver',
                                     'io.github.prrvchr.jdbcdriver.sdbcx.Driver'),
                          'Connection': ('com.sun.star.sdbc.Connection',
                                         'com.sun.star.sdbcx.Connection',
                                         'com.sun.star.sdb.Connection')}
        self._config = getConfiguration(ctx, g_identifier, True)

# OptionsModel getter methods
    def getViewData(self):
        driver = self._services.get('Driver').index(self._getDriverService())
        connection = self._services.get('Connection').index(self._getConnectionService())
        return driver, connection, self.isUpdated(), self._isConnectionEnabled(driver), self._getDriverVersion(), OptionsModel._reboot

    def loadSetting(self):
        self._config = getConfiguration(self._ctx, g_identifier, True)
        return self.getViewData()

    def needReboot(self):
        return OptionsModel._reboot

    def getServicesLevel(self):
        driver = self._services.get('Driver').index(self._getDriverService())
        connection = self._services.get('Connection').index(self._getConnectionService())
        return driver, connection, self.isUpdated(), self._isConnectionEnabled(driver)

    def isUpdated(self):
        return OptionsModel._level

    def _getDriverService(self):
        return self._config.getByName('DriverService')

    def _getConnectionService(self):
        return self._config.getByName('ConnectionService')

# OptionsModel setter methods
    def setDriverService(self, driver):
        OptionsModel._level = True
        self._config.replaceByName('DriverService', self._services.get('Driver')[driver])
        connection = self._services.get('Connection').index(self._getConnectionService())
        if driver and not connection:
            connection = 1
            self._config.replaceByName('ConnectionService', self._services.get('Connection')[connection])
        return connection, self._isConnectionEnabled(driver)

    def setConnectionService(self, level):
        self._config.replaceByName('ConnectionService', self._services.get('Connection')[level])

    def saveSetting(self):
        if self._config.hasPendingChanges():
            self._config.commitChanges()
            if OptionsModel._level:
                OptionsModel._reboot = True
            return True
        return False

# OptionsModel private methods
    def _isConnectionEnabled(self, driver):
        return driver == 0

    def _getLevelValue(self, level):
        return '%d' % level

    def _getDriverVersion(self):
        version = 'N/A'
        try:
            service = self._config.getByName('DriverService')
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

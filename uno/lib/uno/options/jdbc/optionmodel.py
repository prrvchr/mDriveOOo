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

from ..unotool import getConfiguration

from ..logger import getLogger
g_basename = 'OptionsDialog'

from ..configuration import g_identifier

import traceback


class OptionModel():
    def __init__(self, ctx, logger):
        self._keys = ('DriverService', 'ApiLevel', 'ShowSystemTable', 'UseBookmark', 'SQLMode')
        self._keysmap = {'DriverService': ('io.github.prrvchr.jdbcdriver.sdbc.Driver',
                                           'io.github.prrvchr.jdbcdriver.sdbcx.Driver'),
                         'ApiLevel':      ('com.sun.star.sdbc',
                                           'com.sun.star.sdbcx',
                                           'com.sun.star.sdb')}
        self._config = getConfiguration(ctx, g_identifier, True)
        self._service = self.getDriverService()
        self._settings = None
        self._logger = getLogger(ctx, logger, g_basename)
        self._logger.logprb(INFO, 'JdbcDialog', '__init__()', 101)

# OptionModel getter methods
    def getDriverService(self):
        return self._config.getByName('DriverService')

    def getViewData(self):
        self._settings = self._getSettings()
        driver = self._keysmap.get('DriverService').index(self._settings.get('DriverService'))
        level = self._keysmap.get('ApiLevel').index(self._settings.get('ApiLevel'))
        system = self._settings.get('ShowSystemTable')
        bookmark = self._settings.get('UseBookmark')
        mode = self._settings.get('SQLMode')
        return driver, level, self._isApiLevelEnabled(driver), system, bookmark, mode

# OptionModel setter methods
    def setDriverService(self, driver, level):
        self._settings['DriverService'] = self._keysmap.get('DriverService')[driver]
        if driver and not level:
            level = 1
            self.setApiLevel(level)
        system = self._settings.get('ShowSystemTable')
        bookmark = self._settings.get('UseBookmark')
        mode = self._settings.get('SQLMode')
        return level, self._isApiLevelEnabled(driver), system, bookmark, mode

    def setApiLevel(self, level):
        self._settings['ApiLevel'] = self._keysmap.get('ApiLevel')[level]
        bookmark = self._settings.get('UseBookmark')
        mode = self._settings.get('SQLMode')
        return level, bookmark, mode

    def setSystemTable(self, state):
        self._settings['ShowSystemTable'] = bool(state)

    def setBookmark(self, state):
        self._settings['UseBookmark'] = bool(state)
        return state, self._settings.get('SQLMode')

    def setSQLMode(self, state):
        self._settings['SQLMode'] = bool(state)

    def saveSetting(self, system, bookmark, mode):
        self.setSystemTable(system)
        self.setBookmark(bookmark)
        self.setSQLMode(mode)
        for key in self._keys:
            value = self._settings.get(key)
            if value != self._config.getByName(key):
                self._config.replaceByName(key, value)
        if self._config.hasPendingChanges():
            self._config.commitChanges()
        return self._service != self.getDriverService()

# OptionModel private methods
    def _getSettings(self):
        settings = {}
        for key in self._keys:
            settings[key] = self._config.getByName(key)
        return settings

    def _isApiLevelEnabled(self, driver):
        return driver == 0


#!
# -*- coding: utf-8 -*-

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

from ...unotool import getConfiguration

from ...configuration import g_identifier


class OptionModel():
    def __init__(self, ctx):
        self._rebootkeys = ('ApiLevel', )
        configkeys = ('ResultSetType', 'ShowSystemTable', 'UseCachedRowSet')
        self._keys = self._rebootkeys + configkeys
        self._config = getConfiguration(ctx, g_identifier, True)
        self._settings = self._getSettings()
        self._java = False

# OptionModel getter methods
    def getInitData(self, state):
        self._settings = self._getSettings()
        level = self._settings.get('ApiLevel')
        crs = self._settings.get('UseCachedRowSet')
        system = self._settings.get('ShowSystemTable')
        rst = self._settings.get('ResultSetType')
        enabled = self._isRowSetEnabled(level)
        self._java = state.java
        return level, crs, system, rst, enabled, state

    def getRefreshData(self, state):
        level = self._settings.get('ApiLevel')
        rst = self._settings.get('ResultSetType')
        enabled = self._isRowSetEnabled(level)
        self._java = state.java
        return rst, enabled, state

    def getConfigApiLevel(self):
        return self._config.getByName('ApiLevel')

# OptionModel setter methods
    def setApiLevel(self, level):
        self._settings['ApiLevel'] = level
        return self._java and self._isRowSetEnabled(level)

    def setResultSetType(self, level):
        self._settings['ResultSetType'] = level
        return level != 0

    def setCachedRowSet(self, state):
        self._settings['UseCachedRowSet'] = bool(state)

    def setSystemTable(self, state):
        self._settings['ShowSystemTable'] = bool(state)

    def saveSetting(self):
        reboot = False
        for key in self._keys:
            if key != 'ResultSetType' or self._java:
                value = self._settings.get(key)
                if value != self._config.getByName(key):
                    self._config.replaceByName(key, value)
                    if key in self._rebootkeys:
                        reboot = True
        if self._config.hasPendingChanges():
            self._config.commitChanges()
        return reboot

# OptionModel private methods
    def _getSettings(self):
        settings = {}
        for key in self._keys:
            settings[key] = self._config.getByName(key)
        return settings

    def _isRowSetEnabled(self, level):
        return level != 0

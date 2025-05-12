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

from com.sun.star.logging.LogLevel import INFO

from ..unotool import getConfiguration

from ..logger import getLogger

from ..jdbcdriver import g_services

from ..configuration import g_identifier
from ..configuration import g_basename

import traceback


class OptionModel():
    def __init__(self, ctx):
        self._keys = ('ApiLevel', 'ShowSystemTable', 'UseBookmark', 'SQLMode')
        self._levels = ('com.sun.star.sdbc',
                        'com.sun.star.sdbcx',
                        'com.sun.star.sdb')
        self._config = getConfiguration(ctx, g_identifier, True)
        self._settings = self._getSettings()

# OptionModel getter methods
    def getConfigApiLevel(self):
        return self._config.getByName('ApiLevel')

    def getApiLevel(self):
        return self._settings['ApiLevel']

    def getViewData(self):
        level = self._levels.index(self._settings.get('ApiLevel'))
        system = self._settings.get('ShowSystemTable')
        bookmark = self._settings.get('UseBookmark')
        mode = self._settings.get('SQLMode')
        return level, system, bookmark, mode

# OptionModel setter methods
    def setApiLevel(self, level):
        self._settings['ApiLevel'] = self._levels[level]
        system = self._settings.get('ShowSystemTable')
        bookmark = self._settings.get('UseBookmark')
        mode = self._settings.get('SQLMode')
        return level, system, bookmark, mode

    def setSystemTable(self, state):
        self._settings['ShowSystemTable'] = bool(state)

    def setBookmark(self, state):
        self._settings['UseBookmark'] = bool(state)
        return state, self._settings.get('SQLMode')

    def setSQLMode(self, state):
        self._settings['SQLMode'] = bool(state)

    def saveSetting(self, system, bookmark, mode):
        changed = False
        self.setSystemTable(system)
        self.setBookmark(bookmark)
        self.setSQLMode(mode)
        for key in self._keys:
            value = self._settings.get(key)
            if value != self._config.getByName(key):
                self._config.replaceByName(key, value)
        if self._config.hasPendingChanges():
            self._config.commitChanges()
            changed = True
        return changed

# OptionModel private methods
    def _getSettings(self):
        settings = {}
        for key in self._keys:
            settings[key] = self._config.getByName(key)
        return settings


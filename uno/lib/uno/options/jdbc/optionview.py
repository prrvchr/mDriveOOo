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

from ..unotool import getContainerWindow

from ..configuration import g_identifier

import traceback


class OptionWindow():
    def __init__(self, ctx, window, handler, restart, offset):
        self._window = getContainerWindow(ctx, window.getPeer(), handler, g_identifier, 'OptionDialog')
        self._window.setVisible(True)
        self.setRestart(restart)
        self._getRestart().Model.PositionY += offset

# OptionWindow getter methods
    def getApiLevel(self):
        for level in range(3):
            if self._getApiLevel(level).State == 1:
                return level

    def getOptions(self):
        system = self._getSytemTable().State
        bookmark = self._getBookmark().State
        mode = self._getSQLMode().State
        return system, bookmark, mode

# OptionWindow setter methods
    def dispose(self):
        self._window.dispose()

    def setDriverLevel(self, level):
        self._getDriverService(level).State = 1

    def setApiLevel(self, level, enabled, bookmark, mode):
        self._getApiLevel(level).State = 1
        self._getApiLevel(0).Model.Enabled = enabled
        self.enableOptions(level, bookmark, mode)

    def setSystemTable(self, driver, state):
        self._getSytemTable().Model.Enabled = bool(driver)
        if driver:
            self._getSytemTable().State = int(state)
        else:
            self._getSytemTable().State = 0

    def setRestart(self, enabled):
        self._getRestart().setVisible(enabled)

    def enableOptions(self, level, bookmark, mode):
        self._getBookmark().Model.Enabled = bool(level)
        if level:
            self._getBookmark().State = int(bookmark)
            self.enableSQLMode(bookmark, mode)
        else:
            self._getBookmark().State = 0
            self._getSQLMode().Model.Enabled = False
            self._getSQLMode().State = 0

    def enableSQLMode(self, state, mode):
        self._getSQLMode().Model.Enabled = bool(state)
        self._getSQLMode().State = int(mode) if state else 0

# OptionWindow private control methods
    def _getDriverService(self, index):
        return self._window.getControl('OptionButton%s' % (index + 1))

    def _getApiLevel(self, index):
        return self._window.getControl('OptionButton%s' % (index + 3))

    def _getSytemTable(self):
        return self._window.getControl('CheckBox1')

    def _getBookmark(self):
        return self._window.getControl('CheckBox2')

    def _getSQLMode(self):
        return self._window.getControl('CheckBox3')

    def _getRestart(self):
        return self._window.getControl('Label3')


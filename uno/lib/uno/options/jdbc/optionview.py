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

    def setApiLevel(self, level, system, bookmark, mode):
        self._getApiLevel(level).State = 1
        self.enableOptions(level, system, bookmark, mode)

    def setRestart(self, enabled):
        self._getRestart().setVisible(enabled)

    def enableOptions(self, level, system, bookmark, mode):
        if level == 0:
            self._enableSytemTable(False)
            self._enableBookmark(False)
        elif level == 1:
            self._enableSytemTable(True, system)
            self._enableBookmark(True, bookmark, mode)

    def enableSQLMode(self, enable, state=0):
        self._getSQLMode().Model.Enabled = enable
        self._getSQLMode().State = int(enable and state)

# OptionWindow private control methods
    def _enableBookmark(self, enable, state=0, mode=0):
        self._getBookmark().Model.Enabled = enable
        self._getBookmark().State = int(enable and state)
        self.enableSQLMode(enable, mode)

    def _enableSytemTable(self, enable, state=0):
        self._getSytemTable().Model.Enabled = enable
        self._getSytemTable().State = int(enable and state)

    def _getApiLevel(self, index):
        return self._window.getControl('OptionButton%s' % (index + 1))

    def _getSytemTable(self):
        return self._window.getControl('CheckBox1')

    def _getBookmark(self):
        return self._window.getControl('CheckBox2')

    def _getSQLMode(self):
        return self._window.getControl('CheckBox3')

    def _getRestart(self):
        return self._window.getControl('Label2')


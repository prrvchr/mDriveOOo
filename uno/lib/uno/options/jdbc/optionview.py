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
    def __init__(self, ctx, window, handler, options, restart, offset):
        self._window = getContainerWindow(ctx, window.getPeer(), handler, g_identifier, 'OptionDialog')
        self._window.setVisible(True)
        for crs in options:
            self._getCachedRowSet(crs).Model.Enabled = False
        self.setRestart(restart)
        self._getRestart().Model.PositionY += offset

# OptionWindow setter methods
    def dispose(self):
        self._window.dispose()

    def initView(self, level, crs, system, enabled):
        self._getApiLevel(level).State = 1
        self._getCachedRowSet(crs).State = 1
        self.enableCachedRowSet(enabled)
        self._getSytemTable().State = int(system)

    def enableCachedRowSet(self, enabled):
        for crs in range(3):
            self._getCachedRowSet(crs).Model.Enabled = enabled

    def setRestart(self, enabled):
        self._getRestart().setVisible(enabled)

# OptionWindow private control methods
    def _getApiLevel(self, index):
        return self._window.getControl('OptionButton%s' % (index + 1))

    def _getCachedRowSet(self, index):
        return self._window.getControl('OptionButton%s' % (index + 4))

    def _getSytemTable(self):
        return self._window.getControl('CheckBox1')

    def _getRestart(self):
        return self._window.getControl('Label3')


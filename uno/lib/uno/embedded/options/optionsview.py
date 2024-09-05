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

import traceback


class OptionsView():
    def __init__(self, window, restart):
        self._window = window
        self.setRestart(restart)

# OptionsView setter methods
    def initView(self, driver, connection, enabled, version, system, bookmark, mode):
        self._getVersion().Text = version
        self._getDriverService(driver).State = 1
        self._getConnectionService(connection).State = 1
        self._getConnectionService(0).Model.Enabled = enabled
        self._getSytemTable().State = int(system)
        self._getBookmark().State = int(bookmark)
        self.enableSQLMode(bookmark)
        self._getSQLMode().State = int(mode)

    def setDriverVersion(self, version):
        self._getVersion().Text = version

    def setDriverLevel(self, level, updated):
        self._getDriverService(level).State = 1

    def setConnectionLevel(self, level, enabled):
        self._getConnectionService(level).State = 1
        self._getConnectionService(0).Model.Enabled = enabled

    def setRestart(self, enabled):
        self._getRestart().setVisible(enabled)

    def enableSQLMode(self, state):
        self._getSQLMode().Model.Enabled = bool(state)

# OptionsView private control methods
    def _getDriverService(self, index):
        return self._window.getControl('OptionButton%s' % (index + 1))

    def _getConnectionService(self, index):
        return self._window.getControl('OptionButton%s' % (index + 3))

    def _getSytemTable(self):
        return self._window.getControl('CheckBox1')

    def _getBookmark(self):
        return self._window.getControl('CheckBox2')

    def _getSQLMode(self):
        return self._window.getControl('CheckBox3')

    def _getVersion(self):
        return self._window.getControl('Label2')

    def _getRestart(self):
        return self._window.getControl('Label5')


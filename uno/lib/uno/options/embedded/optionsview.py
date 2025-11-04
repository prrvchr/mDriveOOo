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

import traceback


class OptionsView():
    def __init__(self, window, restart, url, instrumented):
        self._window = window
        control = self._getWarning()
        control.URL = url
        self._setWarning(control, restart, instrumented)

# OptionsView setter methods
    def setWarning(self, restart, instrumented):
        self._setWarning(self._getWarning(), restart, instrumented)

    def setDriverVersion(self, version):
        self._getVersion().Text = version

# OptionsView private methods
    def _setWarning(self, control, restart, instrumented):
        if restart:
            control.setVisible(False)
            self._getRestart().setVisible(True)
        else:
            self._getRestart().setVisible(False)
            control.setVisible(not instrumented)

# OptionsView private control methods
    def _getVersion(self):
        return self._window.getControl('Label2')

    def _getRestart(self):
        return self._window.getControl('Label3')

    def _getWarning(self):
        return self._window.getControl('Hyperlink1')


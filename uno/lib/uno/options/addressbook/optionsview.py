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

import traceback


class OptionsView(unohelper.Base):
    def __init__(self, window, timeout, view, enabled):
        self._window = window
        self._getTimeout().Value = timeout
        self._getDatasource().Model.Enabled = enabled
        self._setViewName(view, not enabled)

# OptionsView getter methods
    def getViewData(self):
        return int(self._getTimeout().Value), self._getViewName().Text

# OptionsView setter methods
    def setTimeout(self, timeout):
        self._getTimeout().Value = timeout

    def setViewName(self, view):
        self._getViewName().Text = view

# OptionsView private setter methods
    def _setViewName(self, view, disabled):
        self._getViewLabel().Model.Enabled = disabled
        control = self._getViewName()
        control.Model.Enabled = disabled
        control.Text = view

# OptionsView private control methods
    def _getTimeout(self):
        return self._window.getControl('NumericField1')

    def _getDatasource(self):
        return self._window.getControl('CommandButton1')

    def _getViewLabel(self):
        return self._window.getControl('Label3')

    def _getViewName(self):
        return self._window.getControl('TextField1')

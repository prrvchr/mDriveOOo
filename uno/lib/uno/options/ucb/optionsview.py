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
    def __init__(self, window, update, links):
        self._window = window
        self._getSetup().Model.Enabled = update
        for i, link in enumerate(links, start=1):
            self._getLink(i).URL = link

# OptionsView getter methods
    def getViewData(self):
        return self.getSetup()

    def getSetup(self):
        return self._getSetup().getSelectedItemPos()

# OptionView setter methods
    def initView(self, setup, state):
        self._setSetup(setup)
        self.refreshView(state)

    def refreshView(self, state):
        self._window.Model.Step = state.step

# OptionsView private setter methods
    def _setSetup(self, setup):
        control = self._getSetup()
        if control.Model.Enabled:
            control.selectItemPos(setup, True)

# OptionsView private control methods
    def _getSetup(self):
        return self._window.getControl('ListBox1')

    def _getLink(self, index):
        return self._window.getControl(f'Hyperlink{index}')


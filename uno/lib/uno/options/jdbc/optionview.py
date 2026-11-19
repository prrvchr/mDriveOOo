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

from ...unotool import Layout
from ...unotool import SubLayout

from ...unotool import getContainerWindow

from ...configuration import g_identifier


class OptionView():
    def __init__(self, ctx, window, handler):
        self._window = getContainerWindow(ctx, window.getPeer(), handler, g_identifier, 'OptionDialog')
        self._layout = SubLayout(Layout(self._window, **self._getLayouts()))
        self._window.setVisible(True)

# OptionsView getter methods
    def getLayout(self):
        return self._layout

    def getFrame(self):
        return self._getFrame()

# OptionView setter methods
    def dispose(self):
        self._window.dispose()

    def initView(self, level, crs, system, rst, enabled, state):
        self._getApiLevel(level).State = 1
        self._getCachedRowSet().State = int(crs)
        self._getSytemTable().State = int(system)
        self.refreshView(rst, enabled, state)

    def refreshView(self, rst, enabled, state):
        if state.java:
            self._getResultSetType(rst).State = 1
        else:
            self._getResultSetType(0).State = 1
        self.enableResultSetType(state.java and enabled)
        self.enableCachedRowSet(state.java and enabled and rst != 0)

    def enableResultSetType(self, enabled, options=(0, 1, 2)):
        for index in options:
            self._getResultSetType(index).Model.Enabled = enabled

    def enableCachedRowSet(self, enabled):
        self._getCachedRowSet().Model.Enabled = enabled

    def _getLayouts(self):
        return {'horizontals': self._getHorizontals(),
                'tops': self._getTops()}

    def _getHorizontals(self):
        yield self._getFrame()
        yield self._getFixedLine()

    def _getTops(self):
        for index in range(1, 7):
            yield self._getOptionButton(index)
        yield self._getSytemTable()

# OptionView private control methods
    def _getFrame(self):
        return self._window.getControl('FrameControl1')

    def _getFixedLine(self):
        return self._window.getControl('FixedLine1')

    def _getOptionButton(self, index):
        return self._window.getControl(f'OptionButton{index}')

    def _getApiLevel(self, index):
        return self._window.getControl('OptionButton%s' % (index + 1))

    def _getResultSetType(self, index):
        return self._window.getControl('OptionButton%s' % (index + 4))

    def _getCachedRowSet(self):
        return self._window.getControl('CheckBox1')

    def _getSytemTable(self):
        return self._window.getControl('CheckBox2')

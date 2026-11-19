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
    def __init__(self, ctx, window, handler, title):
        self._window = getContainerWindow(ctx, window.getPeer(), handler, g_identifier, 'OptionDialog')
        self._getTitle().Model.Label = title
        self._layout = SubLayout(Layout(self._window, **self._getLayouts()))
        self._window.setVisible(True)

# OptionView getter methods
    def getLayout(self):
        return self._layout

    def getWindow(self):
        return self._window

    def getFrame(self):
        return self._getFrame()

    def getViewData(self):
        return int(self._getTimeout().Value), self._getViewName().Text

# OptionView setter methods
    def initView(self, timeout, view, state):
        self._getTimeout().Value = timeout
        self._getViewName().Text = view
        self.refreshView(state)

    def refreshView(self, state):
        self._getDatasource().Model.Enabled = state.database
        self._getViewName().Model.Enabled = not state.database

    def _getLayouts(self):
        return {'horizontals': (self._getFrame(), self._getTitle(), self._getViewName()),
                'tops': (self._getTimeout(), self._getDatasource())}

# OptionView private control methods
    def _getFrame(self):
        return self._window.getControl('FrameControl1')

    def _getTitle(self):
        return self._window.getControl('FixedLine1')

    def _getTimeout(self):
        return self._window.getControl('NumericField1')

    def _getDatasource(self):
        return self._window.getControl('CommandButton1')

    def _getViewLabel(self):
        return self._window.getControl('Label3')

    def _getViewName(self):
        return self._window.getControl('TextField1')

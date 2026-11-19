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

from com.sun.star.awt import Size

from ..unotool import Layout
from ..unotool import LinkListener
from ..unotool import SubLayout


class OptionsView():
    def __init__(self, ctx, window, title, setup, update):
        self._window = window
        self._setSetup(setup, update)
        self._getTitle().Model.Label = title
        self._link = LinkListener(ctx, self._getLabel())
        self._layout = SubLayout(Layout(window, size=Size(279, 225), **self._getLayouts()))
        window.addWindowListener(self._layout)

# OptionView getter methods
    def getLayout(self):
        return self._layout

    def getFrame(self):
        return self._getFrame()

    def getSetupMode(self):
        return self._getSetupMode().getSelectedItemPos()

# OptionView setter methods
    def refreshView(self, label, url):
        self._setLabel(label, url)

# OptionsView private methods
    def _getLayouts(self):
        return {'horizontals': self._getHorizontals(),
                'tops': (self._getSetup(), )}

    def _getHorizontals(self):
        yield self._getFrame()
        yield self._getTitle()
        yield self._getSetupMode()
        yield self._getLabel()

    def _setSetup(self, setup, update):
        if update:
            control = self._getSetupMode()
            control.Model.Enabled = True
            control.selectItemPos(setup, True)

    def _setLabel(self, label, url):
        self._getLabel().Model.Label = label
        self._link.setUrl(url)

# OptionsView private control methods
    def _getFrame(self):
        return self._window.getControl('FrameControl1')

    def _getTitle(self):
        return self._window.getControl('FixedLine1')

    def _getSetupMode(self):
        return self._window.getControl('ListBox1')

    def _getSetup(self):
        return self._window.getControl('CommandButton1')

    def _getLabel(self):
        return self._window.getControl('Label2')

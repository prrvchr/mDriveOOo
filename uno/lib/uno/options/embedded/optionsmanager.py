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

from .optionsmodel import OptionsModel
from .optionsview import OptionsView
from .optionshandler import OptionsListener

from ..option import OptionManager

from ..configuration import g_defaultlog

import traceback


class OptionsManager():
    def __init__(self, ctx, window, url=None):
        self._model = OptionsModel(ctx, url)
        window.addEventListener(OptionsListener(self))
        self._view = OptionsView(window)
        self._manager = OptionManager(ctx, window, 21, g_defaultlog)
        version = self._model.getDriverVersion(self._service())
        self._view.setDriverVersion(version)

    def dispose(self):
        self._manager.dispose()

# OptionsManager setter methods
    def saveSetting(self):
        self._manager.saveSetting() 

    def loadSetting(self):
        self._manager.loadSetting()
        version = self._model.getDriverVersion(self._service())
        self._view.setDriverVersion(version)

# OptionsManager private methods
    def _service(self):
        return self._manager.getDriverService()


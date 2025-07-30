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

from .optionsmodel import OptionsModel
from .optionsview import OptionsView
from .optionshandler import OptionsListener

from ..option import OptionManager

from ..configuration import g_defaultlog

import traceback


class OptionsManager():
    def __init__(self, ctx, logger, window, options, url=None):
        self._model = OptionsModel(ctx, logger, url)
        self._manager = OptionManager(ctx, window, options, OptionsManager._restart, 20, g_defaultlog)
        self._view = OptionsView(window)
        window.addEventListener(OptionsListener(self))
        self._manager.initView()
        self._initView()

    _restart = False

    def dispose(self):
        self._manager.dispose()

# OptionsManager setter methods
    def saveSetting(self):
        if self._manager.saveSetting():
            OptionsManager._restart = True
            self._manager.setRestart(True)


    def loadSetting(self):
        self._manager.loadSetting()
        version = self._model.getDriverVersion(self._getConfigApiLevel())
        self._view.setDriverVersion(version)

# OptionsManager private getter methods
    def _getConfigApiLevel(self):
        return self._manager.getConfigApiLevel()

# OptionsManager private setter methods
    def _initView(self):
        version = self._model.getDriverVersion(self._getConfigApiLevel())
        self._view.setDriverVersion(version)

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

from .optionmodel import OptionModel

from .optionview import OptionView

from .optionhandler import OptionHandler

from ...runner import DispatchListener

from ...setup import SetupCheck

from ..logger import LogManager

from ...setup import showSetup

from ...configuration import g_identifier

import traceback


class OptionManager():
    def __init__(self, ctx, window, dispatch, logger, *loggers):
        self._ctx = ctx
        self._dispatch = dispatch
        self._model = OptionModel(ctx)
        self._logmanager = LogManager(ctx, window, 'requirements.txt', logger, *loggers)
        self._logmanager.initView()
        self._view = OptionView(ctx, window, OptionHandler(self), *self._model.getViewData())

    def init(self, state):
        self._view.initView(*self._model.getInitData(state))

    def refresh(self, state):
        self._view.refreshView(*self._model.getRefreshData(state))

# OptionManager setter methods
    def dispose(self):
        self._logmanager.dispose()
        self._view.dispose()

# OptionManager getter methods
    def getConfigApiLevel(self):
        return self._model.getConfigApiLevel()

    def getSetupMode(self):
        return self._view.getSetup()

# OptionManager setter methods
    def saveSetting(self):
        saved = self._logmanager.saveSetting()
        saved |= self._model.saveSetting(self._view.getSetup())
        return saved

    def loadSetting(self):
        self._logmanager.loadSetting()

    def setApiLevel(self, level):
        enabled = self._model.setApiLevel(level)
        self._view.enableResultSetType(enabled)
        self._view.enableCachedRowSet(enabled)

    def setResultSetType(self, level):
        enabled = self._model.setResultSetType(level)
        self._view.enableCachedRowSet(enabled)

    def setCachedRowSet(self, state):
        self._model.setCachedRowSet(state)

    def setSystemTable(self, state):
        self._model.setSystemTable(state)

    def showSetup(self):
        mode = self.getSetupMode()
        showSetup(self._ctx, g_identifier, Dispatch=self._dispatch, Mode=mode)


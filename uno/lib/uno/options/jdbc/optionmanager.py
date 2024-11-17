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

from .optionmodel import OptionModel
from .optionview import OptionWindow
from .optionhandler import WindowHandler

from ..logger import LogManager

import traceback


class OptionManager():
    def __init__(self, ctx, window, offset, logger, *loggers):
        self._logmanager = LogManager(ctx, window, 'requirements.txt', logger, *loggers)
        self._model = OptionModel(ctx, logger)
        self._view = OptionWindow(ctx, window, WindowHandler(self), OptionManager._restart, offset)
        self._initView()

    _restart = False

    def dispose(self):
        self._logmanager.dispose()
        self._view.dispose()

# OptionManager getter methods
    def getDriverService(self):
        return self._model.getDriverService()

# OptionManager setter methods
    def saveSetting(self):
        saved = self._logmanager.saveSetting()
        saved |= self._model.saveSetting(*self._view.getOptions())
        if saved:
            OptionManager._restart = True
            self._view.setRestart(True)
        return saved

    def loadSetting(self):
        self._logmanager.loadSetting()
        self._initView()

    def setDriverService(self, driver):
        level = self._view.getApiLevel()
        level, enabled, system, bookmark, mode = self._model.setDriverService(driver, level)
        self._view.setApiLevel(level, enabled, bookmark, mode)
        self._view.setSystemTable(driver, system)

    def setApiLevel(self, level):
        self._view.enableOptions(*self._model.setApiLevel(level))

    def setSystemTable(self, state):
        self._model.setSystemTable(state)

    def setBookmark(self, state):
        self._view.enableSQLMode(*self._model.setBookmark(state))

    def setSQLMode(self, state):
        self._model.setSQLMode(state)

# OptionManager private methods
    def _initView(self):
        driver, level, enabled, system, bookmark, mode = self._model.getViewData()
        self._view.setDriverLevel(driver)
        self._view.setApiLevel(level, enabled, bookmark, mode)
        self._view.setSystemTable(driver, system)


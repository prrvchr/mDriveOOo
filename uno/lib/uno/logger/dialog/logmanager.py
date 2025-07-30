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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from .logmodel import LogModel

from .logview import LogWindow
from .logview import LogDialog

from .loghandler import WindowHandler
from .loghandler import DialogHandler
from .loghandler import LoggerListener
from .loghandler import PoolListener

from ..loghelper import getLoggerName


class LogManager():
    def __init__(self, ctx, window, requirements, *loggers):
        self._ctx = ctx
        self._model = LogModel(ctx, loggers)
        self._view = LogWindow(ctx, window, WindowHandler(self))
        self._requirements = requirements
        self._dialog = None
        self._model.addPoolListener(PoolListener(self))
        self._update = True

# LogManager setter methods
    def initView(self):
        # FIXME: If we want to load data using handlers,
        # FIXME: it is necessary to devalidate all resulting updates
        self._update = False
        self._view.initView(self._model.getLoggerNames())
        self._update = True

    def dispose(self):
        self._model.dispose()
        self._view.dispose()

    # LogManager setter methods called by OptionsManager
    def saveSetting(self):
        return self._model.saveSetting()

    # LogManager setter methods called by OptionsHandler
    def loadSetting(self):
        self._update = False
        self._view.setLogSetting(*self._model.loadSetting())
        self._update = True

    # LogManager setter methods called by LoggerListener
    def updateLoggers(self):
        logger = self._view.getLogger()
        loggers = self._model.getLoggerNames()
        self._view.updateLoggers(loggers)
        if logger in loggers:
            self._update = False
            self._view.setLogger(logger)
            self._update = True

    # LogManager setter methods called by WindowHandler
    def setLogger(self, name):
        logger = getLoggerName(name)
        self._view.setLogSetting(*self._model.getLoggerSetting(logger))

    def enableLogger(self, enabled):
        if self._update:
            self._model.enableLogger(enabled, self._view.getLogLevel())
        self._view.enableLogger(enabled)

    def toggleHandler(self, index):
        if self._update:
            self._model.toggleHandler(index)
        self._view.enableViewer(index == 2)

    def setLevel(self, level):
        if self._update:
            self._model.setLevel(level)

    def viewLog(self):
        handler = DialogHandler(self)
        parent = self._view.getParent()
        data = self._model.getLoggerData()
        self._dialog = LogDialog(self._ctx, handler, parent, *data)
        listener = LoggerListener(self)
        self._model.addLoggerListener(listener)
        self._dialog.execute()
        self._model.removeLoggerListener(listener)
        self._dialog.dispose()
        self._dialog = None

    # LogManager setter methods called by DialogHandler
    def logInfos(self):
        self._model.logInfos(INFO, 'LogManager', 'logInfos', self._requirements)

    # LogManager setter methods called by LoggerListener
    def updateLogger(self):
        text, length = self._model.getLogContent()
        self._dialog.updateLogger(text, length)

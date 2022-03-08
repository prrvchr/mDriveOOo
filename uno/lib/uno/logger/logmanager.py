#!
# -*- coding: utf_8 -*-

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

import uno
import unohelper

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from .logger import Pool
from .logview import LogWindow
from .logview import LogDialog
from .loghandler import WindowHandler
from .loghandler import DialogHandler

from ..unotool import getDialog

import traceback


class LogManager(unohelper.Base):
    def __init__(self, ctx, parent, extension, loggers, infos):
        self._ctx = ctx
        self._extention = extension
        self._logger = 'Logger'
        self._infos = infos
        self._model = None
        self._dialog = None
        handler = WindowHandler(self)
        self._view = LogWindow(ctx, handler, parent, extension)
        self._view.initLogger(loggers)

# LogManager setter methods
    def setLoggerSetting(self):
        settings = self._model.getLoggerSetting()
        self._view.setLoggerSetting(*settings)

    def saveLoggerSetting(self):
        settings = self._view.getLoggerSetting()
        self._model.setLoggerSetting(*settings)

    def changeLogger(self, logger):
        self._model = Pool(self._ctx).getLogger(logger)
        self.setLoggerSetting()

    def toggleLogger(self, enabled):
        self._view.toggleLogger(enabled)

    def toggleViewer(self, enabled):
        self._view.toggleViewer(enabled)

    def viewLog(self):
        handler = DialogHandler(self)
        parent = self._view.getParent()
        url = self._model.getLoggerUrl()
        text = self._model.getLoggerText()
        self._dialog = LogDialog(self._ctx, handler, parent, self._extention, url, text)
        self._model.addListener(self)
        dialog = self._dialog.getDialog()
        dialog.execute()
        dialog.dispose()
        self._model.removeListener(self)
        self._dialog = None

    def clearLog(self):
        msg = Pool(self._ctx).getLogger(self._logger).getMessage(101)
        self._model.clearLogger(msg, "LogManager", "clearLog()")

    def logInfo(self):
        logger = Pool(self._ctx).getLogger(self._logger)
        for code, info in self._infos.items():
            msg = logger.getMessage(code, info)
            self._model.logMessage(INFO, msg, "LogManager", "logInfo()")

    def refreshLog(self):
        text = self._model.getLoggerText()
        self._dialog.setLogger(text)

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

from .loghandler import getRollerHandlerUrl

from ..unotool import createService
from ..unotool import getConfiguration
from ..unotool import getFileSequence

import traceback

# XXX: LogConfig allows access to the Logger configuration
# XXX: it is used by ./dialog/LogModel and ./LogController
class LogConfig():
    def __init__(self, ctx):
        self._ctx = ctx
        self._setting = '/org.openoffice.Office.Logging/Settings'
        self.loadSetting()

    def loadSetting(self):
        self._config = getConfiguration(self._ctx, self._setting, True)

    def getLoggerUrl(self, name):
        url = '$(userurl)/$(loggername).log'
        settings = self.getSetting(name).getByName('HandlerSettings')
        if settings.hasByName('FileURL'):
            url = settings.getByName('FileURL')
        path = createService(self._ctx, 'com.sun.star.util.PathSubstitution')
        url = url.replace('$(loggername)', name)
        return path.substituteVariables(url, True)

    def getLoggerContent(self, name, roller=False):
        url, text, length = self.getLoggerData(name, roller)
        return text, length

    def getLoggerData(self, name, roller=False):
        url = self._getLoggerUrl(name, roller)
        length, sequence = getFileSequence(self._ctx, url)
        text = sequence.value.decode('utf-8')
        return url, text, length

    def saveSetting(self):
        if self._config.hasPendingChanges():
            self._config.commitChanges()
            return True
        return False

    def getSetting(self, name):
        if not self._config.hasByName(name):
            self._config.insertByName(name, self._config.createInstance())
        return self._config.getByName(name)

    def _getLoggerUrl(self, name, roller=False):
        return getRollerHandlerUrl(self._ctx, name) if roller else self.getLoggerUrl(name)


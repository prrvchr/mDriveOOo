#!
# -*- coding: utf-8 -*-

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

import unohelper

from com.sun.star.logging.LogLevel import ALL
from com.sun.star.logging.LogLevel import OFF

from ..unotool import getConfiguration
from ..unotool import getFileSequence
from ..unotool import getResourceLocation
from ..unotool import getStringResourceWithLocation

from .loghelper import LogWrapper
from .loghelper import LogController
from .loghelper import LogConfig
from .loghelper import getPool

from ..configuration import g_identifier
from ..configuration import g_resource
from ..configuration import g_basename


class LogModel(LogController):
    def __init__(self, ctx, name, listener):
        self._ctx = ctx
        self._basename = g_basename
        self._pool, self._localized = getPool(ctx)
        self._url = getResourceLocation(ctx, g_identifier, g_resource)
        self._logger = None
        self._listener = listener
        self._resolver = getStringResourceWithLocation(ctx, self._url, 'Logger')
        self._setting = None
        self._default = name
        self._config = getConfiguration(ctx, '/org.openoffice.Office.Logging/Settings', True)
        if self._localized:
            self._pool.addModifyListener(listener)

    # Public getter method
    def getLoggerNames(self, filter=None):
        if self._localized:
            names = self._pool.getLoggerNames() if filter is None else self._pool.getFilteredLoggerNames(filter)
            if self._default not in names:
                names = list(names)
                names.insert(0, self._default)
                names = tuple(names)
        else:
            names = (self._default, )
        return names

    def getLoggerSetting(self, name):
        if self._localized:
            self._logger = self._pool.getLocalizedLogger(name, self._url, g_basename)
        else:
            self._logger = self._pool.getNamedLogger(name)
        return self._getLoggerSetting()

    def loadSetting(self):
        self._config = getConfiguration(self._ctx, '/org.openoffice.Office.Logging/Settings', True)
        return self._getLoggerSetting()

    def getLoggerData(self):
        url = self._getLoggerUrl()
        length, sequence = getFileSequence(self._ctx, url)
        text = sequence.value.decode('utf-8')
        return url, text, length

# Public setter method
    def dispose(self):
        if self._localized:
            self._pool.removeModifyListener(self._listener)

    def setLogSetting(self, setting):
        config = self._getLogConfig()
        config.LogLevel = setting.LogLevel
        config.DefaultHandler = setting.DefaultHandler

    def saveSetting(self):
        if self._config.hasPendingChanges():
            self._config.commitChanges()


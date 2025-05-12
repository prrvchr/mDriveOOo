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

from com.sun.star.logging.LogLevel import SEVERE

from .logwrapper import LogWrapper

from .logconfig import LogConfig

from .loghandler import RollerHandler
from .loghandler import getRollerHandlerUrl

from ..unotool import getSimpleFile
from ..unotool import getStringResourceWithLocation

from ..configuration import g_basename

import traceback

# XXX: This LogController allows to use a deletable log file as used in eMailerOOo
class LogController(LogWrapper):
    def __init__(self, ctx, name, basename=g_basename, listener=None):
        super().__init__(ctx, name, basename)
        self._listener = listener
        self._setting = None
        self._config = LogConfig(ctx)
        if listener is not None:
            self._logger.addModifyListener(listener)

    # Public getter method
    def getLogContent(self, roller=False):
        return self._config.getLoggerContent(self.Name, roller)

    # Public setter method
    def dispose(self):
        if self._listener is not None:
            self._logger.removeModifyListener(self._listener)

    def clearLogger(self):
        url = getRollerHandlerUrl(self._ctx, self.Name)
        sf = getSimpleFile(self._ctx)
        if sf.exists(url):
            sf.kill(url)
            resolver = getStringResourceWithLocation(self._ctx, self._url, 'Logger')
            msg = resolver.resolveString(111)
            handler = RollerHandler(self._ctx, self.Name)
            self.addRollerHandler(handler)
            self._logger.logp(SEVERE, 'Logger', 'clearLogger', msg)
            self.removeRollerHandler(handler)

    def addModifyListener(self, listener):
        self._logger.addModifyListener(listener)

    def removeModifyListener(self, listener):
        self._logger.removeModifyListener(listener)


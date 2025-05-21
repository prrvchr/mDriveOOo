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

from com.sun.star.uno import Exception as UnoException

from ..unotool import createService

from ..jdbcdriver import g_service as jdbc

from ..configuration import g_service as embedded

import traceback


class OptionsModel():
    def __init__(self, ctx, logger, url=None):
        self._ctx = ctx
        self._url = url
        self._logger = logger
        self._logger.logprb(INFO, 'OptionsModel', '__init__', 401)

# OptionsModel getter methods
    def getDriverVersion(self, apilevel):
        driver = None
        version = 'N/A'
        try:
            # We must try all the required services 
            driver = createService(self._ctx, embedded)
            driver = createService(self._ctx, jdbc)
            if driver and self._url:
                connection = driver.connect(self._url, ())
                version = connection.getMetaData().getDriverVersion()
                connection.close()
        except UnoException as e:
            # If the driver is None, the error is already logged
            if driver is not None:
                self._logger.logprb(SEVERE, 'OptionsModel', 'getDriverVersion', 102, g_service, apilevel, e.Message)
        return version


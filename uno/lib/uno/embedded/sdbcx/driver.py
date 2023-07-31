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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.sdbcx import XDataDefinitionSupplier
from com.sun.star.sdbcx import XCreateCatalog
from com.sun.star.sdbcx import XDropCatalog

from ..driver import Driver as DriverBase

import traceback


class Driver(DriverBase,
             XDataDefinitionSupplier,
             XCreateCatalog,
             XDropCatalog):

    def __init__(self, ctx, lock, service, name):
        DriverBase.__init__(self, ctx, lock, service, name)
        self._services = ('com.sun.star.sdbc.Driver', 'com.sun.star.sdbcx.Driver')
        self._logger.logprb(INFO, 'Driver', '__init__()', 101)

    # XDataDefinitionSupplier
    def getDataDefinitionByConnection(self, connection):
        try:
            self._logger.logprb(INFO, 'Driver', 'getDataDefinitionByConnection()', 141)
            driver = self._getDriver()
            return driver.getDataDefinitionByConnection(connection)
        except SQLException as e:
            raise e
        except Exception as e:
            self._logger.logprb(SEVERE, 'Driver', 'getDataDefinitionByConnection()', 142, e, traceback.format_exc())

    def getDataDefinitionByURL(self, url, infos):
        self._logger.logprb(INFO, 'Driver', 'getDataDefinitionByURL()', 151, url)
        return self.getDataDefinitionByConnection(connect(url, infos))

    # XCreateCatalog
    def createCatalog(self, info):
        self._logger.logprb(INFO, 'Driver', 'createCatalog()', 161)

    # XDropCatalog
    def dropCatalog(self, name, info):
        self._logger.logprb(INFO, 'Driver', 'dropCatalog()', 171, name)


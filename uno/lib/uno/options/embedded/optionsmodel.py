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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.uno import Exception as UnoException

from ..unotool import createService

from ..configuration import g_defaultlog

from ..logger import getLogger
g_basename = 'OptionsDialog'

import traceback


class OptionsModel():
    def __init__(self, ctx, url=None):
        self._ctx = ctx
        self._url = url

# OptionsModel getter methods
    def getDriverVersion(self, service):
        version = 'N/A'
        if self._url is None:
            return version
        try:
            driver = createService(self._ctx, service)
            # FIXME: If jdbcDriverOOo extension has not been installed then driver is None
            if driver is not None:
                connection = driver.connect(self._url, ())
                version = connection.getMetaData().getDriverVersion()
                connection.close()
                driver.dispose()
        except UnoException as e:
            self._getLogger().logprb(SEVERE, 'OptionsModel', '_getDriverVersion()', 141, e.Message)
        except Exception as e:
            self._getLogger().logprb(SEVERE, 'OptionsModel', '_getDriverVersion()', 142, str(e), traceback.format_exc())
        return version

# OptionsModel private methods
    def _getLogger(self):
        return getLogger(self._ctx, g_defaultlog, g_basename)

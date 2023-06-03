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

from ..unotool import getConfiguration
from ..unotool import getResourceLocation
from ..unotool import getSimpleFile

from ..dbconfig  import g_folder

from ..configuration import g_host
from ..configuration import g_identifier

import traceback


class OptionsModel(unohelper.Base):
    def __init__(self, ctx):
        self._ctx = ctx
        self._configuration = getConfiguration(ctx, g_identifier, True)
        folder = g_folder + '/' + g_host
        location = getResourceLocation(ctx, g_identifier, folder)
        self._url = location + '.odb'
        self._factor = 60

# OptionsModel getter methods
    def getViewData(self):
        return self.getTimeout(), self.getViewName(), self._hasDatasource()

    def getTimeout(self):
        timeout = self._configuration.getByName('ReplicateTimeout')
        return timeout / self._factor

    def getViewName(self):
        return self._configuration.getByName('AddressBookName')

    def getDatasourceUrl(self):
        return self._url

# OptionsModel setter methods
    def setViewData(self, timeout, view):
        timeout = timeout * self._factor
        self._configuration.replaceByName('ReplicateTimeout', timeout)
        self._configuration.replaceByName('AddressBookName', view)
        if self._configuration.hasPendingChanges():
            self._configuration.commitChanges()

# OptionsModel private getter methods
    def _hasDatasource(self):
        return getSimpleFile(self._ctx).exists(self._url)


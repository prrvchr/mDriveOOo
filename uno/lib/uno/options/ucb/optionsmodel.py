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

from com.sun.star.ucb.SynchronizePolicy import SERVER_IS_MASTER
from com.sun.star.ucb.SynchronizePolicy import CLIENT_IS_MASTER
from com.sun.star.ucb.SynchronizePolicy import NONE_IS_MASTER

from ..unotool import getConfiguration
from ..unotool import getResourceLocation
from ..unotool import getSimpleFile

from ..dbconfig  import g_folder

from ..configuration import g_identifier
from ..configuration import g_scheme
from ..configuration import g_separator

import traceback


class OptionsModel(unohelper.Base):
    def __init__(self, ctx):
        self._ctx = ctx
        self._config = getConfiguration(ctx, g_identifier, True)
        folder = g_folder + g_separator + g_scheme
        location = getResourceLocation(ctx, g_identifier, folder)
        self._policies = {'SERVER_IS_MASTER': 1, 'CLIENT_IS_MASTER': 2, 'NONE_IS_MASTER': 3}
        self._url = location + '.odb'
        self._factor = 60

# OptionsModel getter methods
    def getViewData(self):
        return self.getSynchronizePolicy(), self.getTimeout(), self.hasDatasource()

    def getSynchronizePolicy(self):
        policy = self._config.getByName('SynchronizePolicy')
        return self._policies.get(policy)

    def getTimeout(self):
        timeout = self._config.getByName('ReplicateTimeout')
        return timeout / self._factor

    def hasDatasource(self):
        return getSimpleFile(self._ctx).exists(self._url)

    def getDatasourceUrl(self):
        return self._url

# OptionsModel setter methods
    def setSynchronizePolicy(self, index):
        policy = self._getSynchronizePolicy(index)
        self._config.replaceByName('SynchronizePolicy', policy)
        if self._config.hasPendingChanges():
            self._config.commitChanges()

    def setTimeout(self, timeout):
        timeout = timeout * self._factor
        self._config.replaceByName('ReplicateTimeout', timeout)
        if self._config.hasPendingChanges():
            self._config.commitChanges()

# OptionsModel private methods
    def _getSynchronizePolicy(self, index):
        for policy, value in self._policies.items():
            if value == index:
                return policy


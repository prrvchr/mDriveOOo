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

from ...unotool import createService
from ...unotool import getStringResource

from ...dbinit import getDataSourceUrl

from ...configuration import g_extension
from ...configuration import g_identifier
from ...configuration import g_implementation


class OptionModel():
    def __init__(self, ctx, config):
        self._ctx = ctx
        self._config = config
        self._url = getDataSourceUrl(ctx)
        self._factor = 60
        self._resolver = getStringResource(ctx, g_identifier, 'dialogs', 'OptionDialog')
        self._resources = {'Title': 'OptionDialog.FixedLine1.Label'}

    @property
    def _Timeout(self):
        timeout = self._config.getByName('ReplicatorTimeout')
        return timeout // self._factor

    @property
    def _ViewName(self):
        return self._config.getByName('AddressBookName')

# OptionModel getter methods
    def getViewData(self):
        return self._getTitle()

    def getInitData(self, state):
        return self._Timeout, self._ViewName, state

    def getDataSourceUrl(self):
        return self._url

# OptionModel setter methods
    def loadDriver(self):
        try:
            _ = createService(self._ctx, g_implementation)
        except Exception:
            # Nothing to do the error is already logged
            pass

# OptionModel getter methods
    def setViewData(self, timeout, view):
        if timeout != self._Timeout:
            self._config.replaceByName('ReplicatorTimeout', timeout * self._factor)
        if view != self._ViewName:
            self._config.replaceByName('AddressBookName', view)
        if self._config.hasPendingChanges():
            self._config.commitChanges()
            return True
        return False

# OptionModel private methods
    def _getTitle(self):
        resource = self._resources.get('Title')
        return self._resolver.resolveString(resource).format(extension=g_extension)

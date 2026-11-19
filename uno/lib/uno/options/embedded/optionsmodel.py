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

from ..unotool import canUpdatePackages
from ..unotool import createService
from ..unotool import getConfiguration
from ..unotool import getStringResource

from ..jdbcdriver import g_service as jdbc

from ..configuration import g_extension
from ..configuration import g_identifier
from ..configuration import g_service as embedded


class OptionsModel():
    def __init__(self, ctx, logger, url=None):
        self._ctx = ctx
        self._url = url
        self._logger = logger
        self._update = canUpdatePackages()
        self._config = getConfiguration(ctx, g_identifier, True)
        self._resolver = getStringResource(ctx, g_identifier, 'dialogs', 'OptionsDialog')
        self._logger.logprb(INFO, 'OptionsModel', '__init__', 401)
        self._resources = {'Title': 'OptionsDialog.FixedLine1.Label',
                           'Link':  'OptionsDialog.Label4.Url.%s'}

# OptionsModel getter methods
    def getViewData(self):
        return self._getTitle()

    def getInitData(self, state):
        return self._getSetupMode(), self._update, *self.getRefreshData(state)

    def getRefreshData(self, state):
        return state.getMessage(self._ctx), self._getLink(state.code)

    def saveSetting(self, mode):
        if self._update and mode != self._getSetupMode():
            self._config.replaceByName('SetupUpdate', mode)
            self._config.commitChanges()

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
                self._logger.logprb(SEVERE, 'OptionsModel', 'getDriverVersion', 102, embedded, apilevel, e.Message)
        except Exception as ex:
            # If the driver is None, the error is already logged
            if driver is not None:
                self._logger.logprb(SEVERE, 'OptionsModel', 'getDriverVersion', 102, embedded, apilevel, str(ex))
        return version

    def _getSetupMode(self):
        return self._config.getByName('SetupUpdate')

    def _getTitle(self):
        resource = self._resources.get('Title')
        return self._resolver.resolveString(resource).format(extension=g_extension)

    def _getLink(self, code):
        resource = self._resources.get('Link') % code
        return self._resolver.resolveString(resource)

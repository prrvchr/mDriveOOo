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

import uno
import unohelper

from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.lang import XServiceInfo
from com.sun.star.awt import XContainerWindowEventHandler

from mdrive import OptionsManager

from mdrive import getLogger

from mdrive import g_identifier
from mdrive import g_defaultlog

import traceback

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = f'{g_identifier}.OptionsHandler'


class OptionsHandler(unohelper.Base,
                     XServiceInfo,
                     XContainerWindowEventHandler):
    def __init__(self, ctx):
        self._ctx = ctx
        self._manager = None
        self._logger = getLogger(ctx, g_defaultlog)

    # XContainerWindowEventHandler
    def callHandlerMethod(self, window, event, method):
        try:
            handled = False
            if method == 'external_event':
                if event == 'initialize':
                    self._manager = OptionsManager(self._ctx, window, self._logger)
                    handled = True
                elif event == 'ok':
                    self._manager.saveSetting()
                    handled = True
                elif event == 'back':
                    self._manager.loadSetting()
                    handled = True
            elif method == 'EnableShare':
                self._manager.enableShare(bool(event.Source.State))
                handled = True
            elif method == 'EnableSync':
                self._manager.enableTimeout(True)
                handled = True
            elif method == 'DisableSync':
                self._manager.enableTimeout(False)
                handled = True
            elif method == 'ViewData':
                self._manager.viewData()
                handled = True
            elif method == 'Download':
                self._manager.download()
                handled = True
            elif method == 'Upload':
                self._manager.upload()
                handled = True
            return handled
        except Exception as e:
            self._logger.logprb(SEVERE, 'OptionsHandler', 'callHandlerMethod()', 141, e, traceback.format_exc())

    def getSupportedMethodNames(self):
        return ('external_event',
                'EnableShare',
                'EnableSync',
                'DisableSync',
                'ViewData',
                'Download',
                'Upload')

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(OptionsHandler,                            # UNO object class
                                         g_ImplementationName,                      # Implementation name
                                        (g_ImplementationName,))                    # List of implemented services

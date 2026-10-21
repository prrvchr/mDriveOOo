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

import unohelper

from com.sun.star.awt import XContainerWindowEventHandler

import traceback


class OptionHandler(unohelper.Base,
                    XContainerWindowEventHandler):
    def __init__(self, manager):
        self._manager = manager

    # XContainerWindowEventHandler
    def callHandlerMethod(self, window, event, method):
        try:
            handled = False
            if method == 'EnableShare':
                self._manager.enableShare(bool(event.Source.State))
                handled = True
            elif method == 'EnableSync':
                self._manager.enableSync(True)
                handled = True
            elif method == 'DisableSync':
                self._manager.enableSync(False)
                handled = True
            elif method == 'Reset':
                self._manager.setReset(bool(event.Source.State))
                handled = True
            elif method == 'ViewData':
                self._manager.viewData()
                handled = True
            elif method == 'ViewFile':
                self._manager.viewFile()
                handled = True
            elif method == 'Download':
                self._manager.download()
                handled = True
            elif method == 'Upload':
                self._manager.upload()
                handled = True
            elif method == 'SpinUp1':
                self._manager.spinUp(0)
                handled = True
            elif method == 'SpinDown1':
                self._manager.spinDown(0)
                handled = True
            elif method == 'SpinUp2':
                self._manager.spinUp(1)
                handled = True
            elif method == 'SpinDown2':
                self._manager.spinDown(1)
                handled = True
            elif method == 'EnableMacro':
                self._manager.enableMacro(bool(event.Source.State))
                handled = True
            elif method == 'Customize':
                self._manager.customizeMenu()
                handled = True
            return handled
        except:
            print("OptionHandler.callHandlerMethod() ERROR: %s" % traceback.format_exc())

    def getSupportedMethodNames(self):
        return ('EnableShare',
                'EnableSync',
                'DisableSync',
                'Reset',
                'ViewData',
                'ViewFile',
                'Download',
                'Upload',
                'SpinUp1',
                'SpinDown1',
                'SpinUp2',
                'SpinDown2',
                'EnableMacro',
                'Customize')


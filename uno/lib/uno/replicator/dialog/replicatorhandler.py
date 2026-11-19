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

from com.sun.star.frame import XTerminateListener2

from com.sun.star.util import XCloseListener

import traceback


class WindowHandler(unohelper.Base,
                    XContainerWindowEventHandler):
    def __init__(self, manager):
        self._manager = manager

    # XContainerWindowEventHandler
    def callHandlerMethod(self, _dialog, event, method):
        try:
            handled = False
            if method == 'ClearLog':
                self._manager.clearLog()
                handled = True
            elif method == 'ShowLog':
                self._manager.showLog(event.Source.Model.State)
                handled = True
            elif method == 'CloseReplicator':
                self._manager.closeReplicator()
                handled = True
            return handled
        except Exception:
            print("WindowHandler.callHandlerMethod() ERROR: %s" % traceback.format_exc())

    def getSupportedMethodNames(self):
        return ('ClearLog',
                'ShowLog',
                'CloseReplicator')


class CloseListener(unohelper.Base,
                    XCloseListener):
    def __init__(self, manager):
        self._manager = manager

    # XCloseListener
    def queryClosing(self, event, ownership):
        self._manager.queryClosing(event.Source, ownership)

    def notifyClosing(self, event):
        self._manager.notifyClosing(event.Source)

    def disposing(self, event):
        pass


class TerminateListener(unohelper.Base,
                        XTerminateListener2):
    def __init__(self, manager):
        self._manager = manager
        print("TerminateListener.__init__() 1")

    def cancelTermination(self, _event):
        print("TerminateListener.cancelTermination() 1")
        pass

    def queryTermination(self, event):
        print("TerminateListener.queryTermination() 1")
        self._manager.queryTermination(event.Source)

    def notifyTermination(self, event):
        print("TerminateListener.notifyTermination() 1")
        self._manager.notifyTermination(event.Source)

    def disposing(self, _event):
        print("TerminateListener.disposing() 1")
        pass

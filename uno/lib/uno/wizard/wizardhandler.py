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
from com.sun.star.awt import XDialogEventHandler
from com.sun.star.awt import XItemListener

from com.sun.star.util import XCloseListener

import traceback


class DialogHandler(unohelper.Base,
                    XDialogEventHandler):
    def __init__(self, manager):
        self._manager = manager

# XDialogEventHandler
    def callHandlerMethod(self, dialog, event, method):
        try:
            handled = False
            if method == 'Help':
                handled = True
            elif method == 'Previous':
                self._manager.travelPrevious()
                handled = True
            elif method == 'Next':
                self._manager.travelNext()
                handled = True
            elif method == 'Finish':
                self._manager.doFinish()
                handled = True
            elif method == 'Cancel':
                self._manager.doCancel()
                handled = True
            return handled
        except:
            print("DialogHandler.callHandlerMethod() ERROR: %s" % traceback.format_exc())

    def getSupportedMethodNames(self):
        return ('Help',
                'Previous',
                'Next',
                'Finish',
                'Cancel')


class WindowHandler(unohelper.Base,
                    XContainerWindowEventHandler):
    def __init__(self, manager):
        self._manager = manager

# XContainerWindowEventHandler
    def callHandlerMethod(self, dialog, event, method):
        try:
            handled = False
            if method == 'Help':
                handled = True
            elif method == 'Previous':
                self._manager.travelPrevious()
                handled = True
            elif method == 'Next':
                self._manager.travelNext()
                handled = True
            elif method == 'Finish':
                self._manager.doFinish()
                handled = True
            elif method == 'Cancel':
                self._manager.doCancel()
                handled = True
            return handled
        except:
            print("WindowHandler.callHandlerMethod() ERROR: %s" % traceback.format_exc())

    def getSupportedMethodNames(self):
        return ('Help',
                'Previous',
                'Next',
                'Finish',
                'Cancel')


class ItemListener(unohelper.Base,
                   XItemListener):
    def __init__(self, manager):
        self._manager = manager

# XItemListener
    def itemStateChanged(self, event):
        try:
            self._manager.changeRoadmapStep(event.ItemId)
        except:
            print("ItemListener.itemStateChanged() ERROR: %s" % traceback.format_exc())

    def disposing(self, event):
        pass


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


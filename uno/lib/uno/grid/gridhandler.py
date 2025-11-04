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
from com.sun.star.awt.grid import XGridDataListener
from com.sun.star.awt.grid import XGridSelectionListener

import traceback


class WindowHandler(unohelper.Base,
                    XContainerWindowEventHandler):
    def __init__(self, manager):
        self._manager = manager

# XContainerWindowEventHandler
    def callHandlerMethod(self, window, event, method):
        try:
            handled = False
            if method == 'ShowColumns':
                self._manager.showColumns(event.Source.Model.State)
                handled = True
            elif method == 'SetColumn':
                self._manager.setColumn(event.Source.getSelectedItemPos())
                handled = True
            return handled
        except:
            print("WindowHandler.callHandlerMethod() ERROR: %s" % traceback.format_exc())

    def getSupportedMethodNames(self):
        return ('ShowColumns',
                'SetColumn')


class GridDataListener(unohelper.Base,
                       XGridDataListener):
    def __init__(self, manager):
        self._manager = manager

    # XGridDataListener
    def rowsInserted(self, event):
        try:
            self._manager.dataGridChanged()
        except:
            print("GridDataListener.rowsInserted() ERROR: %s" % traceback.format_exc())

    def rowsRemoved(self, event):
        try:
            self._manager.dataGridChanged()
        except:
            print("GridDataListener.rowsRemoved() ERROR: %s" % traceback.format_exc())

    def dataChanged(self, event):
        pass

    def rowHeadingChanged(self, event):
        pass

    def disposing(self, event):
        pass


class GridSelectionListener(unohelper.Base,
                            XGridSelectionListener):
    def __init__(self, manager, grid=1):
        self._manager = manager
        self._grid = grid

    # XGridSelectionListener
    def selectionChanged(self, event):
        try:
            control = event.Source
            index = control.getSelectedRows()[-1] if control.hasSelectedRows() else -1
            self._manager.changeGridSelection(index, self._grid)
        except:
            print("GridSelectionListener.selectionChanged() ERROR: %s" % traceback.format_exc())

    def disposing(self, event):
        pass


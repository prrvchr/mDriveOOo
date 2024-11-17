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

import unohelper

from com.sun.star.awt import XContainerWindowEventHandler
from com.sun.star.awt.grid import XGridDataListener
from com.sun.star.awt.grid import XGridSelectionListener
from com.sun.star.sdbc import XRowSetListener

from collections import OrderedDict
import traceback


class WindowHandler(unohelper.Base,
                    XContainerWindowEventHandler):
    def __init__(self, manager):
        self._manager = manager

# XContainerWindowEventHandler
    def callHandlerMethod(self, window, event, method):
        try:
            handled = False
            if method == 'showControls':
                state = event.Source.Model.State
                self._manager.showControls(state)
                handled = True
            elif method == 'ChangeColumn':
                control = event.Source
                index = control.getSelectedItemPos()
                if index != -1:
                    reset = True
                    for i in range(control.Model.ItemCount):
                        image = control.Model.getItemImage(i)
                        if i != index and self._manager.isSelected(image):
                            reset = False
                            break
                    identifier = control.Model.getItemData(index)
                    image = control.Model.getItemImage(index)
                    selected = self._manager.isUnSelected(image)
                    self._manager.setColumn(identifier, selected, reset, index)
                handled = True
            return handled
        except Exception as e:
            msg = "Error: %s" % traceback.format_exc()
            print(msg)

    def getSupportedMethodNames(self):
        return ('showControls',
                'ChangeColumn')


class RowSetListener(unohelper.Base,
                     XRowSetListener):
    def __init__(self, manager):
        self._manager = manager

    # XRowSetListener
    def disposing(self, event):
        pass
    def cursorMoved(self, event):
        pass
    def rowChanged(self, event):
        pass
    def rowSetChanged(self, event):
        try:
            rowset = event.Source
            self._manager.setDataModel(rowset)
        except Exception as e:
            msg = "Error: %s" % traceback.format_exc()
            print(msg)


class GridListener(unohelper.Base,
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
        except Exception as e:
            msg = "Error: %s" % traceback.format_exc()
            print(msg)

    def disposing(self, event):
        pass


class GridDataListener(unohelper.Base,
                       XGridDataListener):
    def __init__(self, manager, grid=1):
        self._manager = manager
        self._grid = grid

    # XGridDataListener
    def rowsInserted(self, event):
        print("GridDataListener.rowsInserted()")

    def rowsRemoved(self, event):
        print("GridDataListener.rowsRemoved()")

    def dataChanged(self, event):
        # FIXME: This method is called when a column header is clicked in order to sort it
        print("GridDataListener.dataChanged() FirstColumn: %s LastColumn: %s FirstRow: %s LastRow: %s" % (event.FirstColumn, event.LastColumn, event.FirstRow, event.LastRow))
        self._manager.setColumnOrder()

    def rowHeadingChanged(self, event):
        print("GridDataListener.rowHeadingChanged()")

    def disposing(self, event):
        pass


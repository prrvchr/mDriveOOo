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

from com.sun.star.uno import XWeak
from com.sun.star.uno import XAdapter

from com.sun.star.awt.grid import XMutableGridDataModel

from ..unotool import hasInterface

import traceback


class GridModelBase(unohelper.Base,
                    XWeak,
                    XAdapter,
                    XMutableGridDataModel):
    def __init__(self, ctx):
        self._ctx = ctx
        self._sortable = None
        self._events = []
        self._listeners = []
        self._row = 0
        self._column = 0

    @property
    def RowCount(self):
        return self._row
    @property
    def ColumnCount(self):
        return self._column

# FIXME: We can't use XMutableGridDataModel without this interface XWeak
# XWeak
    def queryAdapter(self):
        return self

# FIXME: We can't use XMutableGridDataModel without this interface XAdapter
# XAdapter
    def queryAdapted(self):
        return self
    def addReference(self, reference):
        pass
    def removeReference(self, reference):
        pass

# XCloneable
    def createClone(self):
         raise NotImplementedError('Need to be implemented!')

# XGridDataModel
    def getCellData(self, column, row):
        raise NotImplementedError('Need to be implemented!')
    def getCellToolTip(self, column, row):
        raise NotImplementedError('Need to be implemented!')
    # FIXME: This method must not be overloaded: It is necessary to find the RowSet's
    # FIXME: row number from the Grid's selection even if the sort is activated!!!
    def getRowHeading(self, row):
        return row
    def getRowData(self, row):
        raise NotImplementedError('Need to be implemented!')

# FIXME: We need this interface to be able to broadcast the data change to all listener
# XMutableGridDataModel
    def addRow(self, heading, data):
        pass
    def addRows(self, headings, data):
        pass

    def insertRow(self, index, heading, data):
        pass
    def insertRows(self, index, headings, data):
        pass

    def removeRow(self, index):
        pass
    def removeAllRows(self):
        pass

    def updateCellData(self, column, row, value):
        pass
    def updateRowData(self, indexes, rows, values):
        pass
    def updateRowHeading(self, index, heading):
        pass
    def updateCellToolTip(self, column, row, value):
        pass
    def updateRowToolTip(self, row, value):
        pass

    def addGridDataListener(self, listener):
        # FIXME: The service 'com.sun.star.awt.grid.SortableGridDataModel' packaging
        # FIXME: this interface seems to want to register as an XGridDataListener when
        # FIXME: initialized, so it is necessary to filter the listener's interfaces
        if hasInterface(listener, 'com.sun.star.awt.grid.XGridDataListener'):
            self._listeners.append(listener)
        #elif hasInterface(listener, 'com.sun.star.awt.grid.XSortableMutableGridDataModel'):
        #    self._sortable = listener

    def removeGridDataListener(self, listener):
        if listener in self._listeners:
            self._listeners.remove(listener)

# XComponent
    def dispose(self):
        event = uno.createUnoStruct('com.sun.star.lang.EventObject')
        event.Source = self
        for listener in self._events:
            listener.disposing(event)
    def addEventListener(self, listener):
        self._events.append(listener)
    def removeEventListener(self, listener):
        if listener in self._events:
            self._events.remove(listener)

# GridModel getter methods
    def getCurrentSortOrder(self):
        return self._sortable.getCurrentSortOrder()

# GridModel setter methods
    def setSortableModel(self, sortable):
        self._sortable = sortable

    def sortByColumn(self, index, ascending):
        if index != -1:
            self._sortable.sortByColumn(index, ascending)
        else:
            self._sortable.removeColumnSort()

# GridModel private methods
    def _removeRow(self, first, last):
        event = self._getGridDataEvent(first, last)
        for listener in self._listeners:
            listener.rowsRemoved(event)

    def _insertRow(self, first, last):
        event = self._getGridDataEvent(first, last)
        for listener in self._listeners:
            listener.rowsInserted(event)

    def _changeData(self, first, last):
        event = self._getGridDataEvent(first, last)
        for listener in self._listeners:
            listener.dataChanged(event)

    def _getGridDataEvent(self, first, last):
        event = uno.createUnoStruct('com.sun.star.awt.grid.GridDataEvent')
        event.Source = self
        event.FirstColumn = 0
        event.LastColumn = self._column -1
        event.FirstRow = first
        event.LastRow = last
        return event

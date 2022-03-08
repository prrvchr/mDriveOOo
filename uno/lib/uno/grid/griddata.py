#!
# -*- coding: utf_8 -*-

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

from ..dbtool import getValueFromResult

from .gridhandler import RowSetListener

import traceback


class GridData(unohelper.Base,
               XWeak,
               XAdapter,
               XMutableGridDataModel):
    def __init__(self):
        self._events = []
        self._listeners = []
        self._resultset = None
        self.RowCount = 0
        self.ColumnCount = 0

# XWeak
    def queryAdapter(self):
        return self

# XAdapter
    def queryAdapted(self):
        return self
    def addReference(self, reference):
        pass
    def removeReference(self, reference):
        pass

# XCloneable
    def createClone(self):
        return self

# XGridDataModel
    def getCellData(self, column, row):
        self._resultset.absolute(row +1)
        return  getValueFromResult(self._resultset, column +1)
    def getCellToolTip(self, column, row):
        return self.getCellData(column, row)
    def getRowHeading(self, row):
        return row
    def getRowData(self, row):
        data = []
        self._resultset.absolute(row +1)
        for index in range(self.ColumnCount):
            data.append(getValueFromResult(self._resultset, index +1))
        return tuple(data)

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
        self._listeners.append(listener)
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

# GridModel setter methods
    def resetRowSetData(self):
        rowcount = self.RowCount
        self.RowCount = 0
        if self.RowCount < rowcount:
            self._removeRow(self.RowCount, rowcount -1)

    def setRowSetData(self, rowset):
        self._resultset = rowset.createResultSet()
        rowcount = self.RowCount
        self.RowCount = rowset.RowCount
        self.ColumnCount = rowset.getMetaData().getColumnCount()
        if self.RowCount < rowcount:
            self._removeRow(self.RowCount, rowcount -1)
            if self.RowCount > 0:
                self._changeData(0, self.RowCount -1)
        elif self.RowCount > rowcount:
            self._insertRow(rowcount, self.RowCount -1)
            if rowcount > 0:
                self._changeData(0, rowcount -1)
        elif self.RowCount > 0:
            self._changeData(0, rowcount -1)

# GridModel private methods
    def _removeRow(self, firstrow, lastrow):
        event = self._getGridDataEvent(firstrow, lastrow)
        previous = None
        for listener in self._listeners:
            if previous != listener:
                listener.rowsRemoved(event)
                previous = listener

    def _insertRow(self, firstrow, lastrow):
        event = self._getGridDataEvent(firstrow, lastrow)
        previous = None
        for listener in self._listeners:
            if previous != listener:
                listener.rowsInserted(event)
                previous = listener

    def _changeData(self, firstrow, lastrow):
        event = self._getGridDataEvent(firstrow, lastrow)
        previous = None
        for listener in self._listeners:
            if previous != listener:
                listener.dataChanged(event)
                previous = listener

    def _getGridDataEvent(self, firstrow, lastrow):
        event = uno.createUnoStruct('com.sun.star.awt.grid.GridDataEvent')
        event.Source = self
        event.FirstColumn = 0
        event.LastColumn = self.ColumnCount -1
        event.FirstRow = firstrow
        event.LastRow = lastrow
        return event

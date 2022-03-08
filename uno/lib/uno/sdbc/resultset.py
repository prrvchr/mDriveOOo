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

from com.sun.star.beans import XPropertySet

from com.sun.star.lang import XComponent
from com.sun.star.lang import XServiceInfo

from com.sun.star.sdbc import XCloseable
from com.sun.star.sdbc import XColumnLocate
from com.sun.star.sdbc import XResultSet
from com.sun.star.sdbc import XResultSetMetaDataSupplier
from com.sun.star.sdbc import XResultSetUpdate
from com.sun.star.sdbc import XRow
from com.sun.star.sdbc import XRowUpdate
from com.sun.star.sdbc import XWarningsSupplier

from com.sun.star.sdbcx.CompareBookmark import LESS
from com.sun.star.sdbcx.CompareBookmark import EQUAL
from com.sun.star.sdbcx.CompareBookmark import GREATER
from com.sun.star.sdbcx.CompareBookmark import NOT_EQUAL
from com.sun.star.sdbcx.CompareBookmark import NOT_COMPARABLE
from com.sun.star.sdbcx import XColumnsSupplier
from com.sun.star.sdbcx import XDeleteRows
from com.sun.star.sdbcx import XRowLocate

from com.sun.star.util import XCancellable

from ..dbtool import getValueFromResult

import traceback


class ResultSet(unohelper.Base,
                XCancellable,
                XCloseable,
                XColumnLocate,
                XColumnsSupplier,
                XComponent,
                XPropertySet,
                XResultSet,
                XResultSetMetaDataSupplier,
                XResultSetUpdate,
                XRow,
                XRowLocate,
                XRowUpdate,
                XServiceInfo,
                XWarningsSupplier):

    def __init__(self, statement, result):
        print("ResultSet.__init__() 1")
        self._statement = statement
        self._result = result

    @property
    def CursorName(self):
        return self._result.CursorName
    @property
    def FetchDirection(self):
        return self._result.FetchDirection
    @FetchDirection.setter
    def FetchDirection(self, row):
        self._result.FetchDirection = row
    @property
    def FetchSize(self):
        return self._result.FetchSize
    @FetchSize.setter
    def FetchSize(self, size):
        self._result.FetchSize = size
    @property
    def IsBookmarkable(self):
        return self._result.IsBookmarkable
    @property
    def MetaData(self):
        return self.getMetaData()
    @property
    def ResultSetConcurrency(self):
        return self._result.ResultSetConcurrency
    @property
    def ResultSetType(self):
        return self._result.ResultSetType

# XCancellable
    def cancel(self):
        self._result.cancel()

# XCloseable
    def close(self):
        self._result.close()

# XColumnLocate
    def findColumn(self, name):
        return self._result.findColumn(name)

# XColumnsSupplier
    def getColumns(self):
        return self._result.getColumns()

# XComponent
    def dispose(self):
        self._result.dispose()
    def addEventListener(self, listener):
        self._result.addEventListener(listener)
    def removeEventListener(self, listener):
        self._result.removeEventListener(listener)

# XDeleteRows
    def deleteRows(self, rows):
        return self._result.deleteRows(rows)

# XPropertySet
    def getPropertySetInfo(self):
        return self._result.getPropertySetInfo()
    def setPropertyValue(self, name, value):
        self._result.setPropertyValue(name, value)
    def getPropertyValue(self, name):
        return self._result.getPropertyValue(name)
    def addPropertyChangeListener(self, name, listener):
        self._result.addPropertyChangeListener(name, value)
    def removePropertyChangeListener(self, name, listener):
        self._result.removePropertyChangeListener(name, listener)
    def addVetoableChangeListener(self, name, listener):
        self._result.addVetoableChangeListener(name, value)
    def removeVetoableChangeListener(self, name, listener):
        self._result.removeVetoableChangeListener(name, listener)

# XResultSet
    def next(self):
        return self._result.next()
    def isBeforeFirst(self):
        return self._result.isBeforeFirst()
    def isAfterLast(self):
        return self._result.isAfterLast()
    def isFirst(self):
        return self._result.isFirst()
    def isLast(self):
        return self._result.isLast()
    def beforeFirst(self):
        self._result.beforeFirst()
    def afterLast(self):
        self._result.afterLast()
    def first(self):
        return self._result.first()
    def last(self):
        return self._result.last()
    def getRow(self):
        return self._result.getRow()
    def absolute(self, row):
        return self._result.absolute(row)
    def relative(self, row):
        return self._result.relative(row)
    def previous(self):
        return self._result.previous()
    def refreshRow(self):
        self._result.refreshRow()
    def rowUpdated(self):
        return self._result.rowUpdated()
    def rowInserted(self):
        return self._result.rowInserted()
    def rowDeleted(self):
        return self._result.rowDeleted()
    def getStatement(self):
        # TODO: This wrapping is only there for the following lines:
        return self._statement

# XResultSetMetaDataSupplier
    def getMetaData(self):
        return self._result.getMetaData()

# XResultSetUpdate
    def insertRow(self):
        self._result.insertRow()
    def updateRow(self):
        self._result.updateRow()
    def deleteRow(self):
        self._result.deleteRow()
    def cancelRowUpdates(self):
        self._result.cancelRowUpdates()
    def moveToInsertRow(self):
        self._result.moveToInsertRow()
    def moveToCurrentRow(self):
        self._result.moveToCurrentRow()

# XRow
    def wasNull(self):
        return self._result.wasNull()
    def getString(self, index):
        return self._result.getString(index)
    def getBoolean(self, index):
        return self._result.getBoolean(index)
    def getByte(self, index):
        return self._result.getByte(index)
    def getShort(self, index):
        return self._result.getShort(index)
    def getInt(self, index):
        return self._result.getInt(index)
    def getLong(self, index):
        return self._result.getLong(index)
    def getFloat(self, index):
        return self._result.getFloat(index)
    def getDouble(self, index):
        return self._result.getDouble(index)
    def getBytes(self, index):
        return self._result.getBytes(index)
    def getDate(self, index):
        return self._result.getDate(index)
    def getTime(self, index):
        return self._result.getTime(index)
    def getTimestamp(self, index):
        return self._result.getTimestamp(index)
    def getBinaryStream(self, index):
        return self._result.getBinaryStream(index)
    def getCharacterStream(self, index):
        return self._result.getCharacterStream(index)
    def getObject(self, index, typemap):
        return self._result.getObject(index, typemap)
    def getRef(self, index):
        return self._result.getRef(index)
    def getBlob(self, index):
        return self._result.getBlob(index)
    def getClob(self, index):
        return self._result.getClob(index)
    def getArray(self, index):
        return self._result.getArray(index)

# XRowLocate
    def getBookmark(self):
        print("ResultSet.getBookmark() 1")
        bookmark = uno.createUnoStruct('com.sun.star.sdbc.Bookmark')
        index = self._result.getMetaData().getColumnCount()
        bookmark.Identifier = getValueFromResult(self._result, 1)
        bookmark.Value = getValueFromResult(self._result, index)
        print("ResultSet.getBookmark() %s - %s" % (bookmark.Identifier, bookmark.Value))
        return bookmark
    def moveToBookmark(self, bookmark):
        print("ResultSet.moveToBookmark() 1")
        state = False
        if self._result.absolute(bookmark.Value):
            value = getValueFromResult(self._result, 1)
            if value == bookmark.Identifier:
                print("ResultSet.moveToBookmark() %s - %s" % (bookmark.Identifier, value))
                state = True
        if not state:
            self._result.afterLast()
        print("ResultSet.moveToBookmark() %s" % (state, ))
        return state
    def moveRelativeToBookmark(self, bookmark, rows):
        print("ResultSet.moveRelativeToBookmark() 1")
        value = bookmak.Value
        value += rows
        bookmak.Value = value
        print("ResultSet.moveRelativeToBookmark() %s" % (value, ))
        return self.moveToBookmark(bookmark)
    def compareBookmarks(self, first, second):
        print("ResultSet.compareBookmarks() 1")
        equal = first.Identifier == second.Identifier
        if first.Value == second.Value and not equal:
            compare = NOT_EQUAL
        elif first.Value < second.Value and not equal:
            compare = LESS
        elif first.Value > second.Value and not equal:
            compare = GREATER
        elif first.Value == second.Value and equal:
            compare = EQUAL
        else:
            compare = NOT_COMPARABLE
        return compare
    def hasOrderedBookmarks(self):
        print("ResultSet.hasOrderedBookmarks() 1")
        return True
    def hashBookmark(self, bookmark):
        print("ResultSet.hashBookmark() 1")
        hashed = hash(bookmark.Value)
        print("ResultSet.hashBookmark() %s" % (hashed, ))
        return hashed

# XRowUpdate
    def updateNull(self, index):
        self._result.updateNull(index)
    def updateString(self, index):
        self._result.updateString(index)
    def updateBoolean(self, index):
        self._result.updateBoolean(index)
    def updateByte(self, index):
        self._result.updateByte(index)
    def updateShort(self, index):
        self._result.updateShort(index)
    def updateInt(self, index):
        self._result.updateInt(index)
    def updateLong(self, index):
        self._result.updateLong(index)
    def updateFloat(self, index):
        self._result.updateFloat(index)
    def updateDouble(self, index):
        self._result.updateDouble(index)
    def updateBytes(self, index):
        self._result.updateBytes(index)
    def updateDate(self, index):
        self._result.updateDate(index)
    def updateTime(self, index):
        self._result.updateTime(index)
    def updateTimestamp(self, index):
        self._result.updateTimestamp(index)
    def updateBinaryStream(self, index):
        self._result.updateBinaryStream(index)
    def updateCharacterStream(self, index):
        self._result.updateCharacterStream(index)
    def updateObject(self, index, typemap):
        self._result.updateObject(index, typemap)
    def updateNumericObject(self, index):
        self._result.updateNumericObject(index)

# XServiceInfo
    def supportsService(self, service):
        return self._result.supportsService(service)
    def getImplementationName(self):
        return self._result.getImplementationName()
    def getSupportedServiceNames(self):
        return self._result.getSupportedServiceNames()

# XWarningsSupplier
    def getWarnings(self):
        return self._result.getWarnings()
    def clearWarnings(self):
        self._result.clearWarnings()

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

from com.sun.star.sdbc import XBatchExecution
from com.sun.star.sdbc import XCloseable
from com.sun.star.sdbc import XMultipleResults
from com.sun.star.sdbc import XOutParameters
from com.sun.star.sdbc import XParameters
from com.sun.star.sdbc import XPreparedBatchExecution
from com.sun.star.sdbc import XPreparedStatement
from com.sun.star.sdbc import XResultSetMetaDataSupplier
from com.sun.star.sdbc import XRow
from com.sun.star.sdbc import XStatement
from com.sun.star.sdbc import XWarningsSupplier

from com.sun.star.sdbcx import XColumnsSupplier

from com.sun.star.util import XCancellable

from .resultset import ResultSet

import traceback


class BaseStatement(unohelper.Base,
                    XCancellable,
                    XCloseable,
                    XComponent,
                    XMultipleResults,
                    XPropertySet,
                    XServiceInfo,
                    XWarningsSupplier):

    def __init__(self, connection, statement):
        print("BaseStatement.__init__() 1")
        self._connection = connection
        self._statement = statement

    @property
    def CursorName(self):
        return ''
    @CursorName.setter
    def CursorName(self, name):
        pass
    @property
    def EscapeProcessing(self):
        return self._statement.EscapeProcessing
    @EscapeProcessing.setter
    def EscapeProcessing(self, state):
        self._statement.EscapeProcessing = state
    @property
    def FetchDirection(self):
        return self._statement.FetchDirection
    @FetchDirection.setter
    def FetchDirection(self, row):
        self._statement.FetchDirection = row
    @property
    def FetchSize(self):
        return self._statement.FetchSize
    @FetchSize.setter
    def FetchSize(self, size):
        self._statement.FetchSize = size
    @property
    def MaxFieldSize(self):
        return self._statement.MaxFieldSize
    @MaxFieldSize.setter
    def MaxFieldSize(self, size):
        self._statement.MaxFieldSize = size
    @property
    def MaxRows(self):
        return self._statement.MaxRows
    @MaxRows.setter
    def MaxRows(self, row):
        self._statement.MaxRows = row
    @property
    def QueryTimeOut(self):
        return 0
    @QueryTimeOut.setter
    def QueryTimeOut(self, timeout):
        pass
    @property
    def ResultSetConcurrency(self):
        return self._statement.ResultSetConcurrency
    @ResultSetConcurrency.setter
    def ResultSetConcurrency(self, constant):
        self._statement.ResultSetConcurrency = constant
    @property
    def ResultSetType(self):
        return self._statement.ResultSetType
    @ResultSetType.setter
    def ResultSetType(self, constant):
        self._statement.ResultSetType = constant
    @property
    def UseBookmarks(self):
        print("Statement.UseBookmarks getter 1")
        use = self._statement.UseBookmarks
        print("Statement.UseBookmarks getter: %s " % use)
        return use
    @UseBookmarks.setter
    def UseBookmarks(self, state):
        print("Statement.UseBookmarks setter 1")
        self._statement.UseBookmarks = state
        print("Statement.UseBookmarks setter: %s - %s " % (state, self._statement.UseBookmarks))

# XCancellable
    def cancel(self):
        self._statement.cancel()

# XCloseable
    def close(self):
        self._statement.close()

# XComponent
    def dispose(self):
        self._statement.dispose()
    def addEventListener(self, listener):
        self._statement.addEventListener(listener)
    def removeEventListener(self, listener):
        self._statement.removeEventListener(listener)

# XMultipleResults
    def getResultSet(self):
        print("Statement.getResultSet() 1")
        return self._statement.getResultSet()
    def getUpdateCount(self):
        print("Statement.getUpdateCount() 1")
        return self._statement.getUpdateCount()
    def getMoreResults(self):
        print("Statement.getMoreResults() 1")
        return self._statement.getMoreResults()

# XPropertySet
    def getPropertySetInfo(self):
        return self._statement.getPropertySetInfo()
    def setPropertyValue(self, name, value):
        self._statement.setPropertyValue(name, value)
    def getPropertyValue(self, name):
        return self._statement.getPropertyValue(name)
    def addPropertyChangeListener(self, name, listener):
        self._statement.addPropertyChangeListener(name, value)
    def removePropertyChangeListener(self, name, listener):
        self._statement.removePropertyChangeListener(name, listener)
    def addVetoableChangeListener(self, name, listener):
        self._statement.addVetoableChangeListener(name, value)
    def removeVetoableChangeListener(self, name, listener):
        self._statement.removeVetoableChangeListener(name, listener)

# XServiceInfo
    def supportsService(self, service):
        return self._statement.supportsService(service)
    def getImplementationName(self):
        return self._statement.getImplementationName()
    def getSupportedServiceNames(self):
        return self._statement.getSupportedServiceNames()

# XWarningsSupplier
    def getWarnings(self):
        return self._statement.getWarnings()
    def clearWarnings(self):
        self._statement.clearWarnings()


class Statement(BaseStatement,
                XBatchExecution,
                XStatement):

# XBatchExecution
    def addBatch(self, sql):
        self._statement.addBatch(sql)
    def clearBatch(self):
        self._statement.clearBatch()
    def executeBatch(self):
        return self._statement.executeBatch()

# XStatement
    def executeQuery(self, sql):
        print("Statement.executeQuery() 1")
        result = self._statement.executeQuery(sql)
        return ResultSet(self, result)
    def executeUpdate(self, sql):
        return self._statement.executeUpdate(sql)
    def execute(self, sql):
        return self._statement.execute(sql)
    def getConnection(self):
        return self._connection


class PreparedStatement(BaseStatement,
                        XColumnsSupplier,
                        XParameters,
                        XPreparedBatchExecution,
                        XPreparedStatement,
                        XResultSetMetaDataSupplier):

# XColumnsSupplier
    def getColumns(self):
        return self._statement.getColumns()

# XParameters
    def setNull(self, index, sqltype):
        self._statement.setNull(index, sqltype)
    def setObjectNull(self, index, sqltype, typename):
        self._statement.setObjectNull(index, sqltype, typename)
    def setBoolean(self, index, value):
        self._statement.setBoolean(index, value)
    def setByte(self, index, value):
        self._statement.setByte(index, value)
    def setShort(self, index, value):
        self._statement.setShort(index, value)
    def setInt(self, index, value):
        self._statement.setInt(index, value)
    def setLong(self, index, value):
        self._statement.setLong(index, value)
    def setFloat(self, index, value):
        self._statement.setFloat(index, value)
    def setDouble(self, index, value):
        self._statement.setDouble(index, value)
    def setString(self, index, value):
        self._statement.setString(index, value)
    def setBytes(self, index, value):
        self._statement.setBytes(index, value)
    def setDate(self, index, value):
        self._statement.setDate(index, value)
    def setTime(self, index, value):
        self._statement.setTime(index, value)
    def setTimestamp(self, index, value):
        self._statement.setTimestamp(index, value)
    def setBinaryStream(self, index, value, length):
        self._statement.setBinaryStream(index, value, length)
    def setCharacterStream(self, index, value, length):
        self._statement.setCharacterStream(index, value, length)
    def setObject(self, index, value):
        self._statement.setObject(index, value)
    def setObjectWithInfo(self, index, value, sqltype, scale):
        self._statement.setObjectWithInfo(index, value, sqltype, scale)
    def setRef(self, index, value):
        self._statement.setRef(index, value)
    def setBlob(self, index, value):
        self._statement.setBlob(index, value)
    def setClob(self, index, value):
        self._statement.setClob(index, value)
    def setArray(self, index, value):
        self._statement.setArray(index, value)
    def clearParameters(self):
        self._statement.clearParameters()

# XPreparedBatchExecution
    def addBatch(self):
        self._statement.addBatch()
    def clearBatch(self):
        self._statement.clearBatch()
    def executeBatch(self):
        return self._statement.executeBatch()

# XPreparedStatement
    def executeQuery(self):
        result = self._statement.executeQuery()
        return ResultSet(self, result)
    def executeUpdate(self):
        return self._statement.executeUpdate()
    def execute(self):
        return self._statement.execute()
    def getConnection(self):
        return self._connection

# XResultSetMetaDataSupplier
    def getMetaData(self):
        return self._statement.getMetaData()


class CallableStatement(PreparedStatement,
                        XOutParameters,
                        XRow):

# XOutParameters
    def registerOutParameter(self, index, sqltype, typename):
        self._statement.registerOutParameter(index, sqltype, typename)
    def registerNumericOutParameter(self, index, sqltype, scale):
        self._statement.registerNumericOutParameter(index, sqltype, scale)

# XRow
    def wasNull(self):
        return self._statement.wasNull()
    def getString(self, index):
        return self._statement.getString(index)
    def getBoolean(self, index):
        return self._statement.getBoolean(index)
    def getByte(self, index):
        return self._statement.getByte(index)
    def getShort(self, index):
        return self._statement.getShort(index)
    def getInt(self, index):
        return self._statement.getInt(index)
    def getLong(self, index):
        return self._statement.getLong(index)
    def getFloat(self, index):
        return self._statement.getFloat(index)
    def getDouble(self, index):
        return self._statement.getDouble(index)
    def getBytes(self, index):
        return self._statement.getBytes(index)
    def getDate(self, index):
        return self._statement.getDate(index)
    def getTime(self, index):
        return self._statement.getTime(index)
    def getTimestamp(self, index):
        return self._statement.getTimestamp(index)
    def getBinaryStream(self, index):
        return self._statement.getBinaryStream(index)
    def getCharacterStream(self, index):
        return self._statement.getCharacterStream(index)
    def getObject(self, index, typemap):
        return self._statement.getObject(index, typemap)
    def getRef(self, index):
        return self._statement.getRef(index)
    def getBlob(self, index):
        return self._statement.getBlob(index)
    def getClob(self, index):
        return self._statement.getClob(index)
    def getArray(self, index):
        return self._statement.getArray(index)

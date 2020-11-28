#!
# -*- coding: utf_8 -*-

'''
    Copyright (c) 2020 https://prrvchr.github.io

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the Software
    is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
    OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import uno
import unohelper

from com.sun.star.sdbc import XResultSet
from com.sun.star.sdbc import XCloseable
from com.sun.star.sdbc import XWarningsSupplier
from com.sun.star.sdbc import XResultSetMetaDataSupplier
from com.sun.star.sdbc import XColumnLocate
from com.sun.star.sdbc import XRow

from unolib import PropertySet
from unolib import getProperty

import traceback


class ResultSet(unohelper.Base,
                XResultSet,
                XCloseable,
                XWarningsSupplier,
                XResultSetMetaDataSupplier,
                XColumnLocate,
                XRow,
                PropertySet):
    def __init__(self, statement, sql=None):
        try:
            print("ResultSet.__init__() 1")
            self.statement = statement
            if sql:
                self.result = statement.statement.executeQuery(sql)
            else:
                self.result = statement.statement.executeQuery()
            #self.result = statement.statement.executeQuery()
            print("ResultSet.__init__() 2")
        except Exception as e:
            print("ResultSet.__init__() ERROR: %s - %s" % (e, traceback.print_exc()))

    @property
    def CursorName(self):
        return self.result.CursorName
    @property
    def ResultSetConcurrency(self):
        return self.result.ResultSetConcurrency
    @property
    def ResultSetType(self):
        return self.result.ResultSetType

    @property
    def FetchDirection(self):
        return self.result.FetchDirection
    @FetchDirection.setter
    def FetchDirection(self, row):
        self.result.FetchDirection = row

    @property
    def FetchSize(self):
        return self.result.FetchSize
    @FetchSize.setter
    def FetchSize(self, size):
        self.result.FetchSize = size

    # XCloseable
    def close(self):
        print("ResultSet.close()")
        self.result.close()

    # XWarningsSupplier
    def getWarnings(self):
        print("ResultSet.getWarnings() 1")
        warning = self.result.getWarnings()
        print("ResultSet.getWarnings() 2 %s" % warning)
        return warning
    def clearWarnings(self):
        print("ResultSet.clearWarnings()")
        self.result.clearWarnings()

    # XResultSet
    def next(self):
        print("ResultSet.next()")
        return self.result.next()
    def isBeforeFirst(self):
        return self.result.isBeforeFirst()
    def isAfterLast(self):
        return self.result.isAfterLast()
    def isFirst(self):
        return self.result.isFirst()
    def isLast(self):
        return self.result.isLast()
    def beforeFirst(self):
        self.result.beforeFirst()
    def afterLast(self):
        self.result.afterLast()
    def first(self):
        return self.result.first()
    def last(self):
        return self.result.last()
    def getRow(self):
        return self.result.getRow()
    def absolute(self, row):
        return self.result.absolute(row)
    def relative(self, row):
        return self.result.relative(row)
    def previous(self):
        return self.result.previous()
    def refreshRow(self):
        self.result.refreshRow()
    def rowUpdated(self):
        return self.result.rowUpdated()
    def rowInserted(self):
        return self.result.rowInserted()
    def rowDeleted(self):
        return self.result.rowDeleted()
    def getStatement(self):
        print("Connection.ResultSet.getStatement()")
        return self.statement

    # XResultSetMetaDataSupplier
    def getMetaData(self):
        print("Connection.ResultSet.getMetaData()")
        return self.result.getMetaData()

    # XRow
    def wasNull(self):
        return self.result.wasNull()
    def getString(self, index):
        print("ResultSet.getString()")
        return self.result.getString(index)
    def getBoolean(self, index):
        return self.result.getBoolean(index)
    def getByte(self, index):
        return self.result.getByte(index)
    def getShort(self, index):
        return self.result.getShort(index)
    def getInt(self, index):
        return self.result.getInt(index)
    def getLong(self, index):
        return self.result.getLong(index)
    def getFloat(self, index):
        return self.result.getFloat(index)
    def getDouble(self, index):
        return self.result.getDouble(index)
    def getBytes(self, index):
        return self.result.getBytes(index)
    def getDate(self, index):
        return self.result.getDate(index)
    def getTime(self, index):
        return self.result.getTime(index)
    def getTimestamp(self, index):
        return self.result.getTimestamp(index)
    def getBinaryStream(self, index):
        return self.result.getBinaryStream(index)
    def getCharacterStream(self, index):
        return self.result.getCharacterStream(index)
    def getObject(self, index, typemap):
        print("ResultSet.getObject()")
        return self.result.getObject(index, typemap)
    def getRef(self, index):
        return self.result.getRef(index)
    def getBlob(self, index):
        return self.result.getBlob(index)
    def getClob(self, index):
        return self.result.getClob(index)
    def getArray(self, index):
        return self.result.getArray(index)

    # XColumnLocate
    def findColumn(self, name):
        print("ResultSet.findColumn()")
        return self.result.findColumn(name)

    # XPropertySet
    def _getPropertySetInfo(self):
        properties = {}
        properties['CursorName'] = getProperty('CursorName', 'string', BOUND | READONLY)
        properties['ResultSetConcurrency'] = getProperty('ResultSetConcurrency', 'long', BOUND | READONLY)
        properties['ResultSetType'] = getProperty('ResultSetType', 'long', BOUND | READONLY)
        properties['FetchDirection'] = getProperty('FetchDirection', 'long', BOUND)
        properties['FetchSize'] = getProperty('FetchSize', 'long', BOUND)
        return properties

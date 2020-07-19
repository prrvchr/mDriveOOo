#!
# -*- coding: utf_8 -*-

import uno
import unohelper


from com.sun.star.sdbc import XResultSetMetaData

import traceback


class ResultSetMetaData(unohelper.Base,
                        XResultSetMetaData):
    def __init__(self, metadata):
        self._metadata = metadata

    # XResultSetMetaData
    def getColumnCount(self):
        print("ResultSetMetaData.getColumnCount() %s" % self._metadata.getColumnCount())
        return self._metadata.getColumnCount()
    def isAutoIncrement(self, column):
        print("ResultSetMetaData.isAutoIncrement() %s" % self._metadata.isAutoIncrement(column))
        return self._metadata.isAutoIncrement(column)
    def isCaseSensitive(self, column):
        print("ResultSetMetaData.isCaseSensitive() %s" % self._metadata.isCaseSensitive(column))
        return self._metadata.isCaseSensitive(column)
    def isSearchable(self, column):
        print("ResultSetMetaData.isSearchable() %s" % self._metadata.isSearchable(column))
        return self._metadata.isSearchable(column)
    def isCurrency(self, column):
        print("ResultSetMetaData.isCurrency() %s" % self._metadata.isCurrency(column))
        return self._metadata.isCurrency(column)
    def isNullable(self, column):
        print("ResultSetMetaData.isNullable() %s" % self._metadata.isNullable(column))
        return self._metadata.isNullable(column)
    def isSigned(self, column):
        print("ResultSetMetaData.isSigned() %s" % self._metadata.isSigned(column))
        return self._metadata.isSigned(column)
    def getColumnDisplaySize(self, column):
        print("ResultSetMetaData.getColumnDisplaySize() %s" % self._metadata.getColumnDisplaySize(column))
        return self._metadata.getColumnDisplaySize(column)
    def getColumnLabel(self, column):
        #print("ResultSetMetaData.getColumnLabel() %s" % self._metadata.getColumnLabel(column))
        return self._metadata.getColumnLabel(column)
    def getColumnName(self, column):
        #print("ResultSetMetaData.getColumnName() %s" % self._metadata.getColumnName(column))
        return self._metadata.getColumnName(column)
    def getSchemaName(self, column):
        print("ResultSetMetaData.getSchemaName() %s" % self._metadata.getSchemaName(column))
        return self._metadata.getSchemaName(column)
    def getPrecision(self, column):
        print("ResultSetMetaData.getPrecision() %s" % self._metadata.getPrecision(column))
        return self._metadata.getPrecision(column)
    def getScale(self, column):
        print("ResultSetMetaData.getScale() %s" % self._metadata.getScale(column))
        return self._metadata.getScale(column)
    def getTableName(self, column):
        print("ResultSetMetaData.getTableName() %s" % self._metadata.getTableName(column))
        return self._metadata.getTableName(column)
    def getCatalogName(self, column):
        print("ResultSetMetaData.getCatalogName() %s" % self._metadata.getCatalogName(column))
        return self._metadata.getCatalogName(column)
    def getColumnType(self, column):
        print("ResultSetMetaData.getColumnType() %s" % self._metadata.getColumnType(column))
        return self._metadata.getColumnType(column)
    def getColumnTypeName(self, column):
        print("ResultSetMetaData.getColumnTypeName() %s" % self._metadata.getColumnTypeName(column))
        return self._metadata.getColumnTypeName(column)
    def isReadOnly(self, column):
        print("ResultSetMetaData.isReadOnly() %s" % self._metadata.isReadOnly(column))
        return self._metadata.isReadOnly(column)
    def isWritable(self, column):
        print("ResultSetMetaData.isWritable() %s" % self._metadata.isWritable(column))
        return self._metadata.isWritable(column)
    def isDefinitelyWritable(self, column):
        print("ResultSetMetaData.isDefinitelyWritable() %s" % self._metadata.isDefinitelyWritable(column))
        return self._metadata.isDefinitelyWritable(column)
    def getColumnServiceName(self, column):
        print("ResultSetMetaData.getColumnServiceName() %s" % self._metadata.getColumnServiceName(column))
        return self._metadata.getColumnServiceName(column)

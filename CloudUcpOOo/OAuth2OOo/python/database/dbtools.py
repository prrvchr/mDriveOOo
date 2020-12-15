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

from com.sun.star.sdbc import SQLException
from com.sun.star.sdbc import SQLWarning

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from unolib import KeyMap
from unolib import createService
from unolib import getPropertyValue
from unolib import getPropertyValueSet
from unolib import getResourceLocation
from unolib import getSimpleFile

from .dbqueries import getSqlQuery

from .dbconfig import g_protocol
from .dbconfig import g_path
from .dbconfig import g_jar
from .dbconfig import g_class
from .dbconfig import g_options
from .dbconfig import g_shutdown
from .dbconfig import g_version

from .logger import getMessage
g_message = 'dbtools'

import traceback


def getDataSource(ctx, dbname, plugin, register):
    location = getResourceLocation(ctx, plugin, g_path)
    url = '%s/%s.odb' % (location, dbname)
    dbcontext = createService(ctx, 'com.sun.star.sdb.DatabaseContext')
    if getSimpleFile(ctx).exists(url):
        odb = dbname if dbcontext.hasByName(dbname) else url
        datasource = dbcontext.getByName(odb)
        created = False
    else:
        datasource = createDataSource(dbcontext, location, dbname)
        created = True
    if register:
        registerDataSource(dbcontext, dbname, url)
    return datasource, url, created

def getDataSourceConnection(ctx, url, dbname, name='', password=''):
    dbcontext = createService(ctx, 'com.sun.star.sdb.DatabaseContext')
    odb = dbname if dbcontext.hasByName(dbname) else '%s/%s.odb' % (url, dbname)
    datasource = dbcontext.getByName(odb)
    connection, error = None, None
    try:
        connection = datasource.getConnection(name, password)
    except SQLException as e:
        error = e
    return connection, error

def getDataBaseConnection(ctx, url, dbname, name='', password='', shutdown=False):
    info = getDataSourceJavaInfo(url)
    if name != '':
        info += getPropertyValueSet({'user': name})
        if password != '':
            info += getPropertyValueSet({'password': password})
    path = getDataSourceLocation(url, dbname, shutdown)
    manager = ctx.ServiceManager.createInstance('com.sun.star.sdbc.DriverManager')
    connection, error = None, None
    try:
        connection = manager.getConnectionWithInfo(path, info)
    except SQLException as e:
        error = e
    return connection, error

def getDataSourceCall(ctx, connection, name, format=None):
    query = getSqlQuery(ctx, name, format)
    call = connection.prepareCall(query)
    return call

def createDataSource(dbcontext, location, dbname, shutdown=False):
    datasource = dbcontext.createInstance()
    datasource.URL = getDataSourceLocation(location, dbname, shutdown)
    datasource.Info = getDataSourceInfo() + getDataSourceJavaInfo(location)
    return datasource

def checkDataBase(ctx, connection):
    error = None
    version = connection.getMetaData().getDriverVersion()
    if version < g_version:
        state = getMessage(ctx, g_message, 101)
        msg = getMessage(ctx, g_message, 102, (g_jar, g_version, version))
        error = getSqlException(state, 1112, msg)
    return version, error

def executeQueries(ctx, statement, queries):
    for name, format in queries:
        query = getSqlQuery(ctx, name, format)
        statement.executeQuery(query)

def getDataSourceJavaInfo(location):
    info = {}
    info['JavaDriverClass'] = g_class
    info['JavaDriverClassPath'] = '%s/%s' % (location, g_jar)
    return getPropertyValueSet(info)

def getDataSourceInfo():
    info = getDataBaseInfo()
    return getPropertyValueSet(info)

def getDataBaseInfo():
    info = {}
    info['AppendTableAliasName'] = True
    info['AutoIncrementCreation'] = 'GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY'
    info['AutoRetrievingStatement'] = 'CALL IDENTITY()'
    info['IsAutoRetrievingEnabled'] = True
    info['ParameterNameSubstitution'] = True
    # TODO: OpenOffice 4.2.0 dont accept following parameters
    #info['DisplayVersionColumns'] = True
    #info['GeneratedValues'] = True
    #info['UseIndexDirectionKeyword'] = True
    return info

def getDriverInfo():
    info = {}
    info['AddIndexAppendix'] = True
    info['BaseDN'] = ''
    info['BooleanComparisonMode'] = 0
    info['CharSet'] = ''
    info['ColumnAliasInOrderBy'] = True
    info['CommandDefinitions'] = ''
    info['DecimalDelimiter'] = '.'

    info['EnableOuterJoinEscape'] = True
    info['EnableSQL92Check'] = False
    info['EscapeDateTime'] = True
    info['Extension'] = ''
    info['FieldDelimiter'] = ','
    info['Forms'] = ''
    info['FormsCheckRequiredFields'] = True
    info['GenerateASBeforeCorrelationName'] = False

    info['HeaderLine'] = True
    info['HostName'] = ''
    info['IgnoreCurrency'] = False
    info['IgnoreDriverPrivileges'] = True
    info['IndexAlterationServiceName'] = ''
    info['KeyAlterationServiceName'] = ''
    info['LocalSocket'] = ''

    info['MaxRowCount'] = 100
    info['Modified'] = True
    info['NamedPipe'] = ''
    info['NoNameLengthLimit'] = False
    info['PortNumber'] = 389
    info['PreferDosLikeLineEnds'] = False
    info['Reports'] = ''

    info['RespectDriverResultSetType'] = False
    info['ShowColumnDescription'] = False
    info['ShowDeleted'] = False
    info['StringDelimiter'] = '"'
    info['SystemDriverSettings'] = ''
    info['TableAlterationServiceName'] = ''
    info['TableRenameServiceName'] = ''
    info['TableTypeFilterMode'] = 3

    info['ThousandDelimiter'] = ''
    info['UseCatalog'] = False
    info['UseCatalogInSelect'] = True
    info['UseSchemaInSelect'] = True
    info['ViewAccessServiceName'] = ''
    info['ViewAlterationServiceName'] = ''
    return info

def getDataSourceLocation(location, dbname, shutdown=False):
    url = uno.fileUrlToSystemPath('%s/%s' % (location, dbname))
    return '%sfile:%s%s%s' % (g_protocol, url, g_options, g_shutdown if shutdown else '')

def registerDataSource(dbcontext, dbname, url):
    if not dbcontext.hasRegisteredDatabase(dbname):
        dbcontext.registerDatabaseLocation(dbname, url)
    elif dbcontext.getDatabaseLocation(dbname) != url:
        dbcontext.changeDatabaseLocation(dbname, url)

def getKeyMapFromResult(result, keymap=None, provider=None):
    keymap = KeyMap() if keymap is None else keymap
    for i in range(1, result.MetaData.ColumnCount +1):
        name = result.MetaData.getColumnName(i)
        value = getValueFromResult(result, i)
        if value is None:
            continue
        if result.wasNull():
            value = None
        if provider:
            value = provider.transform(name, value)
        keymap.insertValue(name, value)
    return keymap

def getDataFromResult(result, provider=None):
    data = {}
    for i in range(1, result.MetaData.ColumnCount +1):
        name = result.MetaData.getColumnName(i)
        value = getValueFromResult(result, i)
        if value is None:
            continue
        if result.wasNull():
            value = None
        if provider:
            value = provider.transform(name, value)
        data[name] = value
    return data

def getKeyMapSequenceFromResult(result, provider=None):
    sequence = []
    count = result.MetaData.ColumnCount +1
    while result.next():
        keymap = KeyMap()
        for i in range(1, count):
            name = result.MetaData.getColumnName(i)
            value = getValueFromResult(result, i)
            if value is None:
                continue
            if result.wasNull():
                value = None
            if provider:
                value = provider.transform(name, value)
            keymap.insertValue(name, value)
        sequence.append(keymap)
    return sequence

def getKeyMapKeyMapFromResult(result):
    sequence = KeyMap()
    count = result.MetaData.ColumnCount +1
    while result.next():
        keymap = KeyMap()
        name = getValueFromResult(result, 1)
        for i in range(2, count):
            v = getValueFromResult(result, i)
            n = result.MetaData.getColumnName(i)
            keymap.insertValue(n, v)
        sequence.insertValue(name, keymap)
    return sequence

def getSequenceFromResult(result, sequence=None, index=1, provider=None):
    sequence = [] if sequence is None else sequence
    i = result.MetaData.ColumnCount
    if 0 < index < i:
        i = index
    if not i:
        return sequence
    name = result.MetaData.getColumnName(i)
    while result.next():
        value = getValueFromResult(result, i)
        if value is None:
            continue
        if result.wasNull():
            value = None
        if provider:
            value = provider.transform(name, value)
        sequence.append(value)
    return sequence

def getDictFromResult(result):
    values = {}
    index = range(1, result.MetaData.ColumnCount +1)
    while result.next():
        for i in index:
            if i == 1:
                key = getValueFromResult(result, i)
            else:
                value = getValueFromResult(result, i)
            if result.wasNull():
                value = None
        values[key] = value
    return values

def getRowResult(result, index=(0,), separator=' '):
    sequence = []
    if len(index) > 0:
        result.beforeFirst()
        while result.next():
            values = []
            for i in index:
                column = i + 1
                values.append('%s' % getValueFromResult(result, column, ''))
            sequence.append(separator.join(values))
    return tuple(sequence)

def getValueFromResult(result, index, default=None):
    dbtype = result.MetaData.getColumnTypeName(index)
    if dbtype == 'VARCHAR':
        value = result.getString(index)
    elif dbtype == 'BOOLEAN':
        value = result.getBoolean(index)
    elif dbtype == 'TINYINT':
        value = result.getByte(index)
    elif dbtype == 'SMALLINT':
        value = result.getShort(index)
    elif dbtype == 'INTEGER':
        value = result.getInt(index)
    elif dbtype == 'BIGINT':
        value = result.getLong(index)
    elif dbtype == 'FLOAT':
        value = result.getFloat(index)
    elif dbtype == 'DOUBLE':
        value = result.getDouble(index)
    elif dbtype == 'TIMESTAMP':
        value = result.getTimestamp(index)
    elif dbtype == 'TIME':
        value = result.getTime(index)
    elif dbtype == 'DATE':
        value = result.getDate(index)
    else:
        value = default
    return value

def createStaticTable(ctx, statement, tables, readonly=False):
    for table in tables:
        query = getSqlQuery(ctx, 'createTable' + table)
        statement.executeUpdate(query)
    for table in tables:
        statement.executeUpdate(getSqlQuery(ctx, 'setTableSource', table))
        if readonly:
            statement.executeUpdate(getSqlQuery(ctx, 'setTableReadOnly', table))

def executeSqlQueries(statement, queries):
    for query in queries:
        statement.executeQuery(query)

def getWarning(state, code, message, context=None, exception=None):
    return getSQLWarning(state, code, message, context, exception)

def getSqlWarning(state, code, message, context=None, exception=None):
    warning = SQLWarning()
    warning.SQLState = state
    warning.ErrorCode = code
    warning.NextException = exception
    warning.Message = message
    warning.Context = context
    return warning

def getSqlException(state, code, message, context=None, exception=None):
    error = SQLException()
    error.SQLState = state
    error.ErrorCode = code
    error.NextException = exception
    error.Message = message
    error.Context = context
    return error

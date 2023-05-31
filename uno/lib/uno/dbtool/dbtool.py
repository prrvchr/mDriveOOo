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

from com.sun.star.sdbc import SQLException
from com.sun.star.sdbc import SQLWarning

from com.sun.star.sdb.CommandType import TABLE

from com.sun.star.sdbc.DataType2 import BIT
from com.sun.star.sdbc.DataType2 import TINYINT
from com.sun.star.sdbc.DataType2 import SMALLINT
from com.sun.star.sdbc.DataType2 import INTEGER
from com.sun.star.sdbc.DataType2 import BIGINT
from com.sun.star.sdbc.DataType2 import FLOAT
from com.sun.star.sdbc.DataType2 import REAL
from com.sun.star.sdbc.DataType2 import DOUBLE
from com.sun.star.sdbc.DataType2 import NUMERIC
from com.sun.star.sdbc.DataType2 import DECIMAL
from com.sun.star.sdbc.DataType2 import CHAR
from com.sun.star.sdbc.DataType2 import VARCHAR
from com.sun.star.sdbc.DataType2 import LONGVARCHAR
from com.sun.star.sdbc.DataType2 import DATE
from com.sun.star.sdbc.DataType2 import TIME
from com.sun.star.sdbc.DataType2 import TIME_WITH_TIMEZONE
from com.sun.star.sdbc.DataType2 import TIMESTAMP
from com.sun.star.sdbc.DataType2 import TIMESTAMP_WITH_TIMEZONE
from com.sun.star.sdbc.DataType2 import BINARY
from com.sun.star.sdbc.DataType2 import VARBINARY
from com.sun.star.sdbc.DataType2 import LONGVARBINARY
from com.sun.star.sdbc.DataType2 import SQLNULL
from com.sun.star.sdbc.DataType2 import OTHER
from com.sun.star.sdbc.DataType2 import OBJECT
from com.sun.star.sdbc.DataType2 import DISTINCT
from com.sun.star.sdbc.DataType2 import STRUCT
from com.sun.star.sdbc.DataType2 import ARRAY
from com.sun.star.sdbc.DataType2 import BLOB
from com.sun.star.sdbc.DataType2 import CLOB
from com.sun.star.sdbc.DataType2 import REF
from com.sun.star.sdbc.DataType2 import BOOLEAN

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from .object import Object

from ..unotool import createService
from ..unotool import getPropertyValue
from ..unotool import getPropertyValueSet
from ..unotool import getResourceLocation
from ..unotool import getSimpleFile

from ..dbqueries import getSqlQuery

from ..dbconfig import g_protocol
from ..dbconfig import g_folder
from ..dbconfig import g_jar
from ..dbconfig import g_class
from ..dbconfig import g_options
from ..dbconfig import g_version

from ..logger import getLogger

from ..configuration import g_errorlog
g_basename = 'dbtool'

import time
from datetime import datetime
import traceback


def getDataSourceConnection(ctx, url, name='', password='', create=True):
    if create:
        datasource = createDataSource(ctx, url)
    else:
        datasource = getDataSource(ctx, url)
    connection = datasource.getIsolatedConnection(name, password)
    return connection

def createDataSource(ctx, url, path=None):
    service = 'com.sun.star.sdb.DatabaseContext'
    dbcontext = createService(ctx, service)
    datasource = dbcontext.createInstance()
    datasource.URL = getDataBaseUrl(url)
    if path is not None:
        datasource.Settings.JavaDriverClassPath = path
    return datasource

def getDataSource(ctx, url):
    location = '%s.odb' % url
    service = 'com.sun.star.sdb.DatabaseContext'
    dbcontext = createService(ctx, service)
    datasource = dbcontext.getByName(location)
    return datasource

def getDataBaseConnection(ctx, url, info):
    service = 'com.sun.star.sdbc.DriverManager'
    manager = createService(ctx, service)
    url = getDataBaseUrl(url)
    connection = manager.getConnectionWithInfo(url, info)
    return connection

def getDataBaseUrl(url):
    return g_protocol + url + g_options

def getConnectionInfo(user, password, path):
    values = {'user': user,
              'password': password,
              'JavaDriverClassPath': path}
    info = getPropertyValueSet(values)
    return info

def getDataSourceLocation(location, dbname, shutdown):
    url = '%s%s/%s%s' % (g_protocol, location, dbname, g_options)
    if shutdown:
        url += g_shutdown
    return url

def getDataSourceCall(ctx, connection, name, format=None):
    query = getSqlQuery(ctx, name, format)
    call = connection.prepareCall(query)
    return call

def checkDataBase(ctx, connection):
    error = None
    version = connection.getMetaData().getDriverVersion()
    if version < g_version:
        logger = getLogger(ctx, g_errorlog, g_basename)
        state = logger.resolveString(101)
        msg = logger.resolveString(102, g_jar, g_version, version)
        logger.logp(SEVERE, g_basename, 'checkDataBase()', msg)
        error = getSqlException(state, 1112, msg)
    return version, error

def executeQueries(ctx, statement, queries):
    for name, format in queries:
        query = getSqlQuery(ctx, name, format)
        statement.executeQuery(query)

def getDataSourceClassPath(ctx, identifier):
    path = getResourceLocation(ctx, identifier, g_folder)
    return '%s/%s' % (path, g_jar)

def getDataSourceJavaInfo(location):
    info = {}
    info['JavaDriverClass'] = g_class
    info['JavaDriverClassPath'] = '%s/%s' % (location, g_jar)
    return getPropertyValueSet(info)

def getDataSourceInfo():
    info = getDataBaseInfo()
    return getPropertyValueSet(info)

def getDriverPropertyInfos():
    infos = []
    info = getDriverPropertyInfo('AutoIncrementCreation',
                                 'GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY')
    infos.append(info)
    info = getDriverPropertyInfo('AutoRetrievingStatement',
                                 'CALL IDENTITY()')
    infos.append(info)
    info = getDriverPropertyInfo('IsAutoRetrievingEnabled', True)
    infos.append(info)
    return tuple(infos)

def getDriverPropertyInfo(name, value, required=False, choices=()):
    info = uno.createUnoStruct('com.sun.star.sdbc.DriverPropertyInfo')
    info.Name = name
    info.Value = value
    info.IsRequired = required
    info.Choices = choices
    return info

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

def registerDataSource(dbcontext, dbname, url):
    if not dbcontext.hasRegisteredDatabase(dbname):
        dbcontext.registerDatabaseLocation(dbname, url)
    elif dbcontext.getDatabaseLocation(dbname) != url:
        dbcontext.changeDatabaseLocation(dbname, url)

def getDataFromResult(result, provider=None):
    data = {}
    for i in range(1, result.MetaData.ColumnCount +1):
        name = result.MetaData.getColumnLabel(i)
        value = getResultValue(result, i)
        if provider:
            value = provider.transform(name, value)
        data[name] = value
    return data

def getRowDict(result, default=None, count=None):
    row = {}
    if count is None:
        count = result.MetaData.ColumnCount +1
    for i in range(1, count):
        name = result.MetaData.getColumnLabel(i)
        value = getResultValue(result, i, default)
        row[name] = value
    return row

def getObjectFromResult(result, default=None, count=None):
    obj = Object()
    if count is None:
        count = result.MetaData.ColumnCount +1
    for i in range(1, count):
        name = result.MetaData.getColumnLabel(i)
        value = getResultValue(result, i, default)
        setattr(obj, name, value)
    return obj

def getObjectSequenceFromResult(result, default=None):
    sequence = []
    count = result.MetaData.ColumnCount +1
    while result.next():
        obj = getObjectFromResult(result, default, count)
        sequence.append(obj)
    return sequence

def getSequenceFromResult(result, index=1, default=None, transformer=None):
    sequence = []
    #name = result.MetaData.getColumnName(index)
    name = result.MetaData.getColumnLabel(index)
    while result.next():
        value = getResultValue(result, index, default)
        if transformer is not None:
            value = transformer.transform(name, value)
        sequence.append(value)
    return tuple(sequence)

def getDictFromResult(result):
    values = {}
    index = range(1, result.MetaData.ColumnCount +1)
    while result.next():
        for i in index:
            if i == 1:
                key = getResultValue(result, i)
            else:
                value = getResultValue(result, i)
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
                values.append('%s' % getResultValue(result, column, ''))
            sequence.append(separator.join(values))
    return tuple(sequence)

def getValueFromResult(result, index=1, default=None):
    dbtype = result.MetaData.getColumnType(index)
    return getRowValue(result, dbtype, index, default)

def getResultValue(result, index=1, default=None):
    dbtype = result.MetaData.getColumnType(index)
    return getRowValue(result, dbtype, index, default)

def getUnoType(dbtype):
    if dbtype == CHAR:
        value = uno.getTypeByName('char')
    elif dbtype == VARCHAR:
        value = uno.getTypeByName('string')
    elif dbtype == LONGVARCHAR:
        value = uno.getTypeByName('string')
    elif dbtype == BINARY:
        value = uno.getTypeByName('byte')
    elif dbtype == VARBINARY:
        value = uno.getTypeByName('byte')
    elif dbtype == LONGVARBINARY:
        value = uno.getTypeByName('byte')
    elif dbtype == BOOLEAN:
        value = uno.getTypeByName('boolean')
    elif dbtype == TINYINT:
        value = uno.getTypeByName('short')
    elif dbtype == SMALLINT:
        value = uno.getTypeByName('short')
    elif dbtype == INTEGER:
        value = uno.getTypeByName('long')
    elif dbtype == BIGINT:
        value = uno.getTypeByName('hyper')
    elif dbtype == FLOAT:
        value = uno.getTypeByName('float')
    elif dbtype == DOUBLE:
        value = uno.getTypeByName('double')
    else:
        value = uno.getTypeByName('unknown')
    return value

def getRowValue(row, dbtype, index=1, default=None):
    if dbtype == CHAR:
        value = row.getString(index)
    elif dbtype == VARCHAR:
        value = row.getString(index)
    elif dbtype == LONGVARCHAR:
        value = row.getString(index)
    elif dbtype == BOOLEAN:
        value = row.getBoolean(index)
    elif dbtype == TINYINT:
        value = row.getByte(index)
    elif dbtype == SMALLINT:
        value = row.getShort(index)
    elif dbtype == INTEGER:
        value = row.getInt(index)
    elif dbtype == BIGINT:
        value = row.getLong(index)
    elif dbtype == FLOAT:
        value = row.getFloat(index)
    elif dbtype == DOUBLE:
        value = row.getDouble(index)
    elif dbtype == TIMESTAMP:
        value = row.getTimestamp(index)
    elif dbtype == TIMESTAMP_WITH_TIMEZONE:
        value = row.getObject(index, None)
    elif dbtype == TIME:
        value = row.getTime(index)
    elif dbtype == TIME_WITH_TIMEZONE:
        value = row.getObject(index, None)
    elif dbtype == DATE:
        value = row.getDate(index)
    elif dbtype == BINARY:
        value = row.getBytes(index)
        if not row.wasNull():
            value = value.value
    elif dbtype == ARRAY:
        value = row.getArray(index)
        if not row.wasNull():
            value = value.getArray(None)
    else:
        value = default
    if row.wasNull():
        value = default
    return value

def createStaticTable(ctx, statement, tables, csv, readonly=False):
    for table in tables:
        query = getSqlQuery(ctx, 'createTable' + table)
        statement.executeUpdate(query)
    for table in tables:
        statement.executeUpdate(getSqlQuery(ctx, 'setTableSource', (table, csv % table)))
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

def currentDateTimeInTZ(utc=True):
    dtz = uno.createUnoStruct('io.github.prrvchr.css.util.DateTimeWithTimezone')
    dtz.DateTimeInTZ = currentDateTime(utc)
    dtz.Timezone = 0 if utc else _getTimeZone()
    return dtz

def currentDateTime(utc=True):
    now = datetime.utcnow() if utc else datetime.now()
    return _currentDateTime(now, utc)

def currentUnoDateTime(utc=True):
    now = datetime.utcnow() if utc else datetime.now()
    return _getUnoDateTime(now, utc)

def getDateTimeInTZToString(dtz, decimal=6):
    dt = dtz.DateTimeInTZ
    fraction = dt.NanoSeconds // (10 ** (9 - decimal))
    format = '%04d-%02d-%02dT%02d:%02d:%02d.%'
    format += '0%sdZ' % decimal
    format += '%s'
    return format % (dt.Year, dt.Month, dt.Day, dt.Hours, dt.Minutes, dt.Seconds, fraction, dtz.Timezone)

def getDateTimeToString(dt, decimal=6):
    format = '%04d-%02d-%02dT%02d:%02d:%02d.000Z'
    return format % (dt.Year, dt.Month, dt.Day, dt.Hours, dt.Minutes, dt.Seconds)

def toUnoDateTime(dtz):
    dt = dtz.DateTimeInTZ
    udt = uno.createUnoStruct('com.sun.star.util.DateTime')
    udt.Year = dt.Year
    udt.Month = dt.Month
    udt.Day = dt.Day
    udt.Hours = dt.Hours
    udt.Minutes = dt.Minutes
    udt.Seconds = dt.Seconds
    if hasattr(udt, 'HundredthSeconds'):
        udt.HundredthSeconds = dt.NanoSeconds // 10000000
    elif hasattr(udt, 'NanoSeconds'):
        udt.NanoSeconds = dt.NanoSeconds
    if hasattr(udt, 'IsUTC'):
        udt.IsUTC = dt.IsUTC
    return udt

def getDateTimeFromString(dtstr, format, utc=False):
    now = datetime.strptime(dtstr, format)
    return _getUnoDateTime(now, utc)

def _getUnoDateTime(now, utc):
    dt = uno.createUnoStruct('com.sun.star.util.DateTime')
    dt.Year = now.year
    dt.Month = now.month
    dt.Day = now.day
    dt.Hours = now.hour
    dt.Minutes = now.minute
    dt.Seconds = now.second
    if hasattr(dt, 'HundredthSeconds'):
        dt.HundredthSeconds = now.microsecond // 10000
    elif hasattr(dt, 'NanoSeconds'):
        dt.NanoSeconds = now.microsecond * 1000
    if hasattr(dt, 'IsUTC'):
        dt.IsUTC = utc
    return dt

def _currentDateTime(now, utc=True):
    dt = uno.createUnoStruct('io.github.prrvchr.css.util.DateTime')
    dt.Year = now.year
    dt.Month = now.month
    dt.Day = now.day
    dt.Hours = now.hour
    dt.Minutes = now.minute
    dt.Seconds = now.second
    dt.NanoSeconds = now.microsecond * 1000
    dt.IsUTC = utc
    return dt

def _getTimeZone():
    offset = time.timezone if time.localtime().tm_isdst else time.altzone
    return offset / 60 * -1

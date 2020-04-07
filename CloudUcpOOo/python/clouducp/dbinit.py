#!
# -*- coding: utf_8 -*-

from com.sun.star.sdbc import SQLException
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from unolib import getResourceLocation
from unolib import getSimpleFile

from .dbconfig import g_path
from .dbconfig import g_version

from .dbtools import registerDataSource
from .dbtools import executeQueries
from .dbtools import executeSqlQueries
from .dbtools import getDataSourceConnection
from .dbtools import getDataSourceCall
from .dbtools import getSequenceFromResult
from .dbtools import getKeyMapFromResult
from .dbtools import createDataSource
from .dbtools import checkDataBase
from .dbtools import createStaticTable

from .dbqueries import getSqlQuery

import traceback


def getDataSourceUrl(ctx, dbname, plugin, register):
    error = None
    url = getResourceLocation(ctx, plugin, g_path)
    odb = '%s/%s.odb' % (url, dbname)
    if not getSimpleFile(ctx).exists(odb):
        dbcontext = ctx.ServiceManager.createInstance('com.sun.star.sdb.DatabaseContext')
        datasource = createDataSource(dbcontext, url, dbname)
        error = _createDataBase(ctx, datasource, url, dbname)
        if error is None:
            datasource.DatabaseDocument.storeAsURL(odb, ())
            if register:
                registerDataSource(dbcontext, dbname, odb)
    return url, error

def _createDataBase(ctx, datasource, url, dbname):
    error = None
    try:
        connection = datasource.getConnection('', '')
    except SQLException as e:
        error = e
    else:
        version, error = checkDataBase(ctx, connection)
        if error is None:
            statement = connection.createStatement()
            createStaticTable(statement, _getStaticTables(), True)
            tables, statements = _getTablesAndStatements(statement, version)
            executeSqlQueries(statement, tables)
            executeQueries(statement, _getViews())
        connection.close()
        connection.dispose()
    return error

def _getTablesAndStatements(statement, version=g_version):
    tables = []
    statements = []
    call = getDataSourceCall(statement.getConnection(), 'getTables')
    for table in getSequenceFromResult(statement.executeQuery(getSqlQuery('getTableName'))):
        view = False
        versioned = False
        columns = []
        primary = []
        unique = []
        constraint = []
        call.setString(1, table)
        result = call.executeQuery()
        while result.next():
            data = getKeyMapFromResult(result, KeyMap())
            view = data.getValue('View')
            versioned = data.getValue('Versioned')
            column = data.getValue('Column')
            definition = '"%s"' % column
            definition += ' %s' % data.getValue('Type')
            lenght = data.getValue('Lenght')
            definition += '(%s)' % lenght if lenght else ''
            default = data.getValue('Default')
            definition += ' DEFAULT %s' % default if default else ''
            options = data.getValue('Options')
            definition += ' %s' % options if options else ''
            columns.append(definition)
            if data.getValue('Primary'):
                primary.append('"%s"' % column)
            if data.getValue('Unique'):
                unique.append({'Table': table, 'Column': column})
            if data.getValue('ForeignTable') and data.getValue('ForeignColumn'):
                constraint.append({'Table': table,
                                   'Column': column,
                                   'ForeignTable': data.getValue('ForeignTable'),
                                   'ForeignColumn': data.getValue('ForeignColumn')})
        if primary:
            columns.append(getSqlQuery('getPrimayKey', primary))
        for format in unique:
            columns.append(getSqlQuery('getUniqueConstraint', format))
        for format in constraint:
            columns.append(getSqlQuery('getForeignConstraint', format))
        if version >= '2.5.0' and versioned:
            columns.append(getSqlQuery('getPeriodColumns'))
        format = (table, ','.join(columns))
        query = getSqlQuery('createTable', format)
        if version >= '2.5.0' and versioned:
            query += getSqlQuery('getSystemVersioning')
        tables.append(query)
        if view:
            typed = False
            for format in constraint:
                if format['Column'] == 'Type':
                    typed = True
                    break
            format = {'Table': table}
            if typed:
                merge = getSqlQuery('createTypedDataMerge', format)
            else:
                merge = getSqlQuery('createUnTypedDataMerge', format)
            statements.append(merge)
    call.close()
    return tables, statements

def _getStaticTables():
    tables = ('Tables',
              'Columns',
              'TableColumn',
              'Settings')
    return tables

def _getViews():
    return ('createItemView',
            'createChildView',
            'createSyncView')

#!
# -*- coding: utf_8 -*-


from oauth2 import getResourceLocation
from oauth2 import getSimpleFile

from .dbconfig import g_path
from .dbqueries import getSqlQuery
from .dbtools import getTablesAndStatements
from .dbtools import registerDataSource
from .dbtools import executeQueries
from .dbtools import getDataSourceLocation
from .dbtools import getDataSourceInfo
from .dbtools import getDataSourceJavaInfo
from .dbtools import getDataSourceConnection
from .dbtools import checkDataBase

import traceback


def getDataSourceUrl(ctx, dbctx, dbname, plugin, register):
    error = None
    location = getResourceLocation(ctx, plugin, g_path)
    url = '%s/%s.odb' % (location, dbname)
    if not getSimpleFile(ctx).exists(url):
        error = _createDataSource(ctx, dbctx, url, location, dbname)
        if register:
            registerDataSource(dbctx, dbname, url)
    return url, error

def _createDataSource(ctx, dbcontext, url, location, dbname):
    datasource = dbcontext.createInstance()
    datasource.URL = getDataSourceLocation(location, dbname, False)
    datasource.Info = getDataSourceInfo() + getDataSourceJavaInfo(location)
    datasource.DatabaseDocument.storeAsURL(url, ())
    error = _createDataBase(datasource)
    datasource.DatabaseDocument.store()
    return error

def _createDataBase(datasource):
    connection, error = getDataSourceConnection(datasource)
    if error is not None:
        return error
    error = checkDataBase(connection)
    if error is None:
        print("dbinit._createDataBase()")
        statement = connection.createStatement()
        _createStaticTable(statement, _getStaticTables())
        tables, statements = getTablesAndStatements(statement)
        _executeQueries(statement, tables)
        executeQueries(statement, _getViews())
    connection.close()
    connection.dispose()
    return error

def _createStaticTable(statement, tables):
    for table in tables:
        query = getSqlQuery('createTable' + table)
        print("dbtool._createStaticTable(): %s" % query)
        statement.executeQuery(query)
    for table in tables:
        statement.executeQuery(getSqlQuery('setTableSource', table))
        statement.executeQuery(getSqlQuery('setTableReadOnly', table))

def _executeQueries(statement, queries):
    for query in queries:
        statement.executeQuery(query)

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

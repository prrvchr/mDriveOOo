#!
# -*- coding: utf_8 -*-


from .unotools import getResourceLocation
from .unotools import getSimpleFile

from .dbtools import getTablesAndStatements
from .dbtools import registerDataSource
from .dbtools import executeQueries
from .dbtools import getDataSourceLocation
from .dbtools import getDataSourceInfo
from .dbtools import getDataSourceJavaInfo

from .dbqueries import getSqlQuery
from .dbconfig import g_path

import traceback


def getDataSourceUrl(ctx, dbctx, dbname, plugin, register):
    location = getResourceLocation(ctx, plugin, g_path)
    url = '%s/%s.odb' % (location, dbname)
    if not getSimpleFile(ctx).exists(url):
        _createDataSource(ctx, dbctx, url, location, dbname)
        if register:
            registerDataSource(dbctx, dbname, url)
    return url

def _createDataSource(ctx, dbcontext, url, location, dbname):
    datasource = dbcontext.createInstance()
    datasource.URL = getDataSourceLocation(location, dbname, False)
    datasource.Info = getDataSourceInfo() + getDataSourceJavaInfo(location)
    datasource.DatabaseDocument.storeAsURL(url, ())
    _createDataBase(datasource)
    datasource.DatabaseDocument.store()

def _createDataBase(datasource):
    connection = datasource.getConnection('', '')
    statement = connection.createStatement()
    _createStaticTable(statement, _getStaticTables())
    tables, statements = getTablesAndStatements(statement)
    _executeQueries(statement, tables)
    executeQueries(statement, _getViews())
    connection.close()
    connection.dispose()

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

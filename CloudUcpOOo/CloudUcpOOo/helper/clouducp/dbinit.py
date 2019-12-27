#!
# -*- coding: utf_8 -*-

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from unolib import getResourceLocation
from unolib import getSimpleFile

from .dbconfig import g_path
from .dbqueries import getSqlQuery
from .dbtools import getTablesAndStatements
from .dbtools import registerDataSource
from .dbtools import executeQueries
from .dbtools import executeSqlQueries
from .dbtools import getDataSourceConnection
from .dbtools import createDataSource
from .dbtools import checkDataBase
from .dbtools import createStaticTable
from .logger import logMessage

import traceback


def getDataSourceUrl(ctx, dbcontext, dbname, plugin, register):
    try:
        error = None
        location = getResourceLocation(ctx, plugin, g_path)
        url = '%s/%s.odb' % (location, dbname)
        if not getSimpleFile(ctx).exists(url):
            datasource = createDataSource(dbcontext, location, dbname)
            error = _createDataBase(ctx, datasource)
            logMessage(ctx, INFO, "Stage 5", 'dbinit', 'getDataSourceUrl()')
            if error is None:
                datasource.DatabaseDocument.storeAsURL(url, ())
                if register:
                    logMessage(ctx, INFO, "Stage 6", 'dbinit', 'getDataSourceUrl()')
                    registerDataSource(dbcontext, dbname, url)
        logMessage(ctx, INFO, "Stage 7", 'dbinit', 'getDataSourceUrl()')
        return url, error
    except Exception as e:
        msg = "getDataSourceUrl: ERROR: %s - %s" % (e, traceback.print_exc())
        logMessage(ctx, SEVERE, msg, 'dbinit', 'getDataSourceUrl()')

def _createDataBase(ctx, datasource):
    #connection, error = getDataSourceConnection(datasource)
    logMessage(ctx, INFO, "Stage 1", 'dbinit', '_createDataBase()')
    error = None
    try:
        logMessage(ctx, INFO, "Stage 2", 'dbinit', '_createDataBase()')
        connection = datasource.getConnection('', '')
    except Exception as e:
        error = e
        msg = "_createDataBase: ERROR: %s - %s" % (e, traceback.print_exc())
        logMessage(ctx, SEVERE, msg, 'dbinit', '_createDataBase()')
    if error is not None:
        logMessage(ctx, INFO, "Stage 3", 'dbinit', '_createDataBase()')
        return error
    logMessage(ctx, INFO, "Stage 4", 'dbinit', '_createDataBase()')
    error = checkDataBase(connection)
    logMessage(ctx, INFO, "Stage 5", 'dbinit', '_createDataBase()')
    if error is None:
        logMessage(ctx, INFO, "Stage 6", 'dbinit', '_createDataBase()')
        statement = connection.createStatement()
        logMessage(ctx, INFO, "Stage 7", 'dbinit', '_createDataBase()')
        createStaticTable(statement, _getStaticTables(), True)
        tables, statements = getTablesAndStatements(statement)
        executeSqlQueries(statement, tables)
        logMessage(ctx, INFO, "Stage 8", 'dbinit', '_createDataBase()')
        executeQueries(statement, _getViews())
    connection.close()
    connection.dispose()
    logMessage(ctx, INFO, "Stage 9", 'dbinit', '_createDataBase()')
    return error

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

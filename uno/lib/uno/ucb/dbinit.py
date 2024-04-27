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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.sdbc.ColumnValue import NO_NULLS
from com.sun.star.sdbc.ColumnValue import NULLABLE

from com.sun.star.sdbc.DataType import INTEGER
from com.sun.star.sdbc.DataType import VARCHAR

from com.sun.star.sdbc.KeyRule import CASCADE

from .dbtool import createStaticTables
from .dbtool import createStaticIndexes
from .dbtool import createStaticForeignKeys
from .dbtool import setStaticTable
from .dbtool import createTables
from .dbtool import createIndexes
from .dbtool import createForeignKeys
from .dbtool import createRoleAndPrivileges
from .dbtool import executeQueries
from .dbtool import getConnectionInfos
from .dbtool import getDataBaseTables
from .dbtool import getDataBaseIndexes
from .dbtool import getDataBaseForeignKeys
from .dbtool import getDataSourceConnection
from .dbtool import getDriverInfos
from .dbtool import getTableNames
from .dbtool import getTables
from .dbtool import getIndexes
from .dbtool import getForeignKeys
from .dbtool import getPrivileges

from .dbconfig import g_csv
from .dbconfig import g_role
from .dbconfig import g_queries
from .dbconfig import g_drvinfos

from collections import OrderedDict
import traceback


def getDataBaseConnection(ctx, url, user, pwd, new, infos=None):
    if new:
        infos = getDriverInfos(ctx, url, g_drvinfos)
    return getDataSourceConnection(ctx, url, user, pwd, new, infos)

def createDataBase(ctx, logger, connection, odb, version):
    logger.logprb(INFO, 'DataBase', '_createDataBase()', 411, version)
    tables = connection.getTables()
    statement = connection.createStatement()
    statics = createStaticTables(tables, **_getStaticTables())
    createStaticIndexes(tables)
    createStaticForeignKeys(tables, *_getForeignKeys())
    setStaticTable(statement, statics, g_csv, True)
    _createTables(connection, statement, tables)
    _createIndexes(statement, tables)
    _createForeignKeys(statement, tables)
    _createRoleAndPrivileges(statement, tables, connection.getGroups())
    executeQueries(ctx, statement, _getQueries())
    statement.close()
    connection.getParent().DatabaseDocument.storeAsURL(odb, ())
    logger.logprb(INFO, 'DataBase', '_createDataBase()', 412)

def _createTables(connection, statement, tables):
    infos = getConnectionInfos(connection, 'AutoIncrementCreation', 'RowVersionCreation')
    createTables(tables, getDataBaseTables(connection, statement, getTables(), getTableNames(), infos[0], infos[1]))

def _createIndexes(statement, tables):
    createIndexes(tables, getDataBaseIndexes(statement, getIndexes()))

def _createForeignKeys(statement, tables):
    createForeignKeys(tables, getDataBaseForeignKeys(statement, getForeignKeys()))

def _createRoleAndPrivileges(statement, tables, groups):
    createRoleAndPrivileges(statement, tables, groups, getPrivileges())

def _getStaticTables():
    tables = OrderedDict()
    tables['Privileges'] =   {'CatalogName': 'PUBLIC',
                              'SchemaName':  'PUBLIC',
                              'Type':        'TEXT TABLE',
                              'Columns': ({'Name': 'Table',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'Column',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NULLABLE,
                                           'DefaultValue': 'NULL'},
                                          {'Name': 'Role',
                                           'TypeName': 'VARCHAR',
                                           'Type': VARCHAR,
                                           'Scale': 100,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'Privilege',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS})}
    return tables

def _getForeignKeys():
    return (('PUBLIC.PUBLIC.Privileges', 'Table',  'PUBLIC.PUBLIC.Tables',  'Table',  CASCADE, CASCADE),
            ('PUBLIC.PUBLIC.Privileges', 'Column', 'PUBLIC.PUBLIC.Columns', 'Column', CASCADE, CASCADE))

def _getQueries():
    return (('createGetIsFolder', g_queries),
            ('createGetContentType', g_queries),
            ('createGetUniqueName', g_queries),

            ('createChildView', g_queries),
            ('createTwinView', g_queries),
            ('createDuplicateView', g_queries),
            ('createPathView', g_queries),
            ('createChildrenView', g_queries),

            ('createGetItem', g_queries),
            ('createGetNewTitle', g_queries),
            ('createUpdatePushItems', g_queries),
            ('createGetPushItems', g_queries),
            ('createGetPushProperties', g_queries),
            ('createGetItemParentIds', g_queries),
            ('createInsertUser', g_queries),
            ('createInsertSharedFolder', g_queries),
            ('createMergeItem', g_queries),
            ('createMergeParent', g_queries),
            ('createInsertItem', g_queries),
            ('createPullChanges', g_queries),
            ('createUpdateNewItemId', g_queries))


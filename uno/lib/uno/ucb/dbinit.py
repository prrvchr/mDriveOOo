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

from com.sun.star.sdbc import KeyRule

from com.sun.star.sdbcx import CheckOption
from com.sun.star.sdbcx import PrivilegeObject

from .dbtool import createStaticTables
from .dbtool import createStaticIndexes
from .dbtool import createStaticForeignKeys
from .dbtool import setStaticTable
from .dbtool import createTables
from .dbtool import createIndexes
from .dbtool import createForeignKeys
from .dbtool import createRoleAndPrivileges
from .dbtool import createViews
from .dbtool import executeQueries
from .dbtool import getConnectionInfos
from .dbtool import getDataBaseTables
from .dbtool import getDataBaseIndexes
from .dbtool import getDataBaseForeignKeys
from .dbtool import getDataSourceConnection
from .dbtool import getDriverInfos
from .dbtool import getTableNames
from .dbtool import getTables
from .dbtool import getTablePrivileges
from .dbtool import getIndexes
from .dbtool import getForeignKeys
from .dbtool import getPrivileges

from .dbqueries import getSqlQuery

from .dbconfig import g_catalog
from .dbconfig import g_schema
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
    # XXX Creation order are very important here...
    tables = connection.getTables()
    statement = connection.createStatement()
    statics = createStaticTables(g_catalog, g_schema, tables, **_getStaticTables())
    createStaticIndexes(g_catalog, g_schema, tables)
    createStaticForeignKeys(g_catalog, g_schema, tables, *_getForeignKeys())
    setStaticTable(statement, statics, g_csv, True)
    _createTables(connection, statement, tables)
    _createIndexes(statement, tables)
    _createForeignKeys(statement, tables)
    groups = connection.getGroups()
    _createRoleAndPrivileges(statement, tables, groups)
    executeQueries(ctx, statement, _getFunctions(), 'create%s', g_queries)
    createViews(connection.getViews(), _getItemCommands(ctx, _getViews(), 'get%sViewCommand', g_queries, CheckOption.CASCADE))
    createRoleAndPrivileges(tables, groups, _getItemOptions(_getViews(), PrivilegeObject.TABLE, g_role, 1))
    executeQueries(ctx, statement, _getProcedures(), 'create%s', g_queries)
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
    privileges = getTablePrivileges(statement, getPrivileges())
    createRoleAndPrivileges(tables, groups, privileges)

def _getStaticTables():
    tables = OrderedDict()
    tables['Privileges'] =   {'CatalogName': g_catalog,
                              'SchemaName':  g_schema,
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
    return ((f'{g_catalog}.{g_schema}.Privileges', 'Table',  f'{g_catalog}.{g_schema}.Tables',  'Table',  KeyRule.CASCADE, KeyRule.CASCADE),
            (f'{g_catalog}.{g_schema}.Privileges', 'Column', f'{g_catalog}.{g_schema}.Columns', 'Column', KeyRule.CASCADE, KeyRule.CASCADE))

def _getFunctions():
    for name in ('GetIsFolder', 'GetContentType', 'GetUniqueName'):
        yield name

def _getItemCommands(ctx, items, command, format, *option):
    for catalog, schema, name in items:
        yield catalog, schema, name, getSqlQuery(ctx, command % name, format), *option

def _getItemOptions(items, *options):
    for catalog, schema, name in items:
        yield catalog, schema, name, *options

def _getViews(catalog=g_catalog, schema=g_schema):
    for name in ('Child', 'Twin', 'Duplicate', 'Path', 'Children'):
        yield catalog, schema, name

def _getProcedures():
    for name in ('GetItem', 'GetNewTitle', 'UpdatePushItems', 'GetPushItems', 'GetPushProperties',
                 'GetItemParentIds', 'InsertUser', 'InsertSharedFolder', 'MergeItem', 'MergeParent',
                 'InsertItem', 'PullChanges', 'UpdateNewItemId'):
        yield name


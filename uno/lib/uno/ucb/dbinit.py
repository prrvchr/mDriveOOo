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

from .configuration import g_separator

from .dbconfig import g_csv
from .dbconfig import g_role
from .dbconfig import g_drvinfos


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
    return {'Privileges':    {'CatalogName': 'PUBLIC',
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
                                           'IsNullable': NO_NULLS})},
            'Settings':      {'CatalogName': 'PUBLIC',
                              'SchemaName':  'PUBLIC',
                              'Type':        'TEXT TABLE',
                              'Columns': ({'Name': 'Id',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'Name',
                                           'TypeName': 'VARCHAR',
                                           'Type': VARCHAR,
                                           'Scale': 100,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'Value1',
                                           'TypeName': 'VARCHAR',
                                           'Type': VARCHAR,
                                           'Scale': 100,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'Value2',
                                           'TypeName': 'VARCHAR',
                                           'Type': VARCHAR,
                                           'Scale': 100,
                                           'IsNullable': NULLABLE,
                                           'DefaultValue': 'NULL'},
                                          {'Name': 'Value3',
                                           'TypeName': 'VARCHAR',
                                           'Type': VARCHAR,
                                           'Scale': 100,
                                           'IsNullable': NULLABLE,
                                           'DefaultValue': 'NULL'}),
                              'PrimaryKeys': ('Id', )}}

def _getForeignKeys():
    return (('PUBLIC.PUBLIC.Privileges', 'Table',  'PUBLIC.PUBLIC.Tables',  'Table',  CASCADE, CASCADE),
            ('PUBLIC.PUBLIC.Privileges', 'Column', 'PUBLIC.PUBLIC.Columns', 'Column', CASCADE, CASCADE))

def _getQueries():
    return (('createGetTitle',{'Role': g_role}),
            ('createGetUniqueName',{'Role': g_role, 'Prefix': ' ~', 'Suffix': ''}),

            ('createChildView',{'Role': g_role}),
            ('createTwinView',{'Role': g_role}),
            ('createUriView',{'Role': g_role}),
            ('createItemView',{'Role': g_role}),
            ('createTitleView',{'Role': g_role}),
            ('createChildrenView',{'Role': g_role}),
            ('createPathView',{'Role': g_role, 'Separator': g_separator}),

            ('createGetPath',{'Role': g_role}),
            ('createGetItemId',{'Role': g_role, 'Separator': g_separator}),
            ('createGetRoot',{'Role': g_role}),
            ('createGetItem',{'Role': g_role}),
            ('createGetNewTitle',{'Role': g_role}),
            ('createUpdatePushItems',{'Role': g_role}),
            ('createGetPushItems',{'Role': g_role}),
            ('createGetPushProperties',{'Role': g_role}),
            ('createGetItemParentIds',{'Role': g_role}),
            ('createInsertUser',{'Role': g_role}),
            ('createInsertSharedFolder',{'Role': g_role}),
            ('createMergeItem',{'Role': g_role}),
            ('createMergeParent',{'Role': g_role}),
            ('createInsertItem',{'Role': g_role}),
            ('createPullChanges',{'Role': g_role}),
            ('createUpdateNewItemId',{'Role': g_role}))


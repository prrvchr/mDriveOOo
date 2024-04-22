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

from .unotool import getPropertyValueSet

from .dbconfig import g_catalog
from .dbconfig import g_schema
from .dbconfig import g_rowversion
from .dbconfig import g_role
from .dbconfig import g_sep
from .dbconfig import g_typeinfo
from .dbconfig import g_privilege

from .dbtool import addRole
from .dbtool import createDataBaseTables
from .dbtool import createDataBaseIndexes
from .dbtool import createDataBaseForeignKeys
from .dbtool import createRoleAndPrivileges
from .dbtool import executeQueries
from .dbtool import getDataBaseTables
from .dbtool import getDataBaseIndexes
from .dbtool import getDataBaseForeignKeys
from .dbtool import getDataSourceCall
from .dbtool import getDataSourceConnection
from .dbtool import getForeignKeys
from .dbtool import getStaticTables
from .dbtool import getUniqueIndexes
from .dbtool import setStaticTable

from .dbqueries import getSqlQuery

from .configuration import g_separator

from .dbconfig import g_csv

import traceback

def getDataBaseConnection(ctx, url, user, pwd, new):
    infos = _getConnectionInfos() if new else None
    return getDataSourceConnection(ctx, url, user, pwd, new, infos)

def createDataBase(ctx, logger, connection, odb, version):
    logger.logprb(INFO, 'DataBase', '_createDataBase()', 411, version)
    tables = connection.getTables()
    statement = connection.createStatement()
    _createStaticTables(ctx, tables, statement)
    _createTables(ctx, connection, statement, tables)
    _createIndexes(ctx, statement, tables)
    _createForeignKeys(ctx, statement, tables)
    _createRoleAndPrivileges(ctx, statement, tables, connection.getGroups())
    executeQueries(ctx, statement, _getQueries())
    statement.close()
    connection.getParent().DatabaseDocument.storeAsURL(odb, ())
    logger.logprb(INFO, 'DataBase', '_createDataBase()', 412)

def _getConnectionInfos():
    infos = {'TypeInfoSettings': g_typeinfo, 'TablePrivilegesSettings': g_privilege}
    return getPropertyValueSet(infos)

def _createStaticTables(ctx, tables, statement):
    createDataBaseTables(tables, getStaticTables().items())
    createDataBaseIndexes(tables, getUniqueIndexes())
    createDataBaseForeignKeys(tables, getForeignKeys())
    setStaticTable(ctx, statement, getStaticTables().keys(), g_csv, True)

def _createTables(ctx, connection, statement, tables):
    call = getDataSourceCall(ctx, connection, 'getTables')
    query = getSqlQuery(ctx, 'getTableNames')
    createDataBaseTables(tables, getDataBaseTables(statement, query, call, g_rowversion))

def _createIndexes(ctx, statement, tables):
    query = getSqlQuery(ctx, 'getIndexes')
    createDataBaseIndexes(tables, getDataBaseIndexes(statement, query))

def _createForeignKeys(ctx, statement, tables):
    query = getSqlQuery(ctx, 'getForeignKeys')
    createDataBaseForeignKeys(tables, getDataBaseForeignKeys(statement, query))

def _createRoleAndPrivileges(ctx, statement, tables, groups):
    query = getSqlQuery(ctx, 'getPrivileges')
    createRoleAndPrivileges(statement, tables, groups, query)

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

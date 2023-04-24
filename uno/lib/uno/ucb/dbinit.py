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

from com.sun.star.sdbc import SQLException
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from .unolib import KeyMap

from .unotool import createService
from .unotool import getResourceLocation
from .unotool import getSimpleFile

from .dbconfig import g_path
from .dbconfig import g_version
from .dbconfig import g_role

from .dbtool import registerDataSource
from .dbtool import executeQueries
from .dbtool import executeSqlQueries
from .dbtool import getDataSourceConnection
from .dbtool import getDataSourceCall
from .dbtool import getSequenceFromResult
from .dbtool import getKeyMapFromResult
from .dbtool import createDataSource
from .dbtool import checkDataBase
from .dbtool import createStaticTable

from .dbqueries import getSqlQuery

from .configuration import g_scheme
from .configuration import g_separator

import traceback


def getDataSourceUrl(ctx, dbname, plugin, register):
    error = None
    url = getResourceLocation(ctx, plugin, g_path)
    odb = '%s/%s.odb' % (url, dbname)
    dbcontext = createService(ctx, 'com.sun.star.sdb.DatabaseContext')
    if not getSimpleFile(ctx).exists(odb):
        datasource = createDataSource(dbcontext, url, dbname)
        error = createDataBase(ctx, datasource, url, dbname)
        if error is None:
            datasource.DatabaseDocument.storeAsURL(odb, ())
    if error is None and register:
        registerDataSource(dbcontext, dbname, odb)
    return url, error

def createDataBase(ctx, connection):
    version, error = checkDataBase(ctx, connection)
    if error is None:
        statement = connection.createStatement()
        createStaticTable(statement, getStaticTables(), True)
        tables, statements = getTablesAndStatements(statement, version)
        executeSqlQueries(statement, tables)
        executeQueries(statement, getViews())
    return error

def _getTableNames(ctx, statement):
    result = statement.executeQuery(getSqlQuery(ctx, 'getTableNames'))
    names = getSequenceFromResult(result)
    result.close()
    return names

def getTablesAndStatements(ctx, statement, version=g_version):
    tables = []
    statements = []
    call = getDataSourceCall(ctx, statement.getConnection(), 'getTables')
    for table in _getTableNames(ctx, statement):
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
            columns.append(getSqlQuery(ctx, 'getPrimayKey', primary))
        for format in unique:
            columns.append(getSqlQuery(ctx, 'getUniqueConstraint', format))
        for format in constraint:
            columns.append(getSqlQuery(ctx, 'getForeignConstraint', format))
        if version >= '2.5.0' and versioned:
            columns.append(getSqlQuery(ctx, 'getPeriodColumns'))
        format = (table, ','.join(columns))
        query = getSqlQuery(ctx, 'createTable', format)
        if version >= '2.5.0' and versioned:
            query += getSqlQuery(ctx, 'getSystemVersioning')
        tables.append(query)
        if view:
            typed = False
            for format in constraint:
                if format['Column'] == 'Type':
                    typed = True
                    break
            format = {'Table': table}
            if typed:
                merge = getSqlQuery(ctx, 'createTypedDataMerge', format)
            else:
                merge = getSqlQuery(ctx, 'createUnTypedDataMerge', format)
            statements.append(merge)
    call.close()
    return tables, statements

def getStaticTables():
    tables = ('Tables',
              'Columns',
              'TableColumn',
              'Settings')
    return tables

def getQueries():
    return (('createRole',{'Role': g_role}),
            ('grantPrivilege',{'Privilege':'SELECT,UPDATE','Table': 'Users', 'Role': g_role}),
            ('grantPrivilege',{'Privilege':'SELECT,INSERT,DELETE','Table': 'Identifiers', 'Role': g_role}),
            ('grantPrivilege',{'Privilege':'SELECT,INSERT,UPDATE,DELETE','Table': 'Items', 'Role': g_role}),
            ('grantPrivilege',{'Privilege':'SELECT,INSERT,UPDATE,DELETE','Table': 'Parents', 'Role': g_role}),
            ('grantPrivilege',{'Privilege':'SELECT,INSERT,UPDATE,DELETE','Table': 'Capabilities', 'Role': g_role}),

            ('createGetTitle',{'Role': g_role}),
            ('createGetUniqueName',{'Role': g_role, 'Prefix': ' ~', 'Suffix': ''}),

            ('createChildView',{'Role': g_role}),
            ('createTwinView',{'Role': g_role}),
            ('createUriView',{'Role': g_role}),
            ('createItemView',{'Role': g_role}),
            ('createTitleView',{'Role': g_role}),
            ('createChildrenView',{'Role': g_role}),
            ('createPathView',{'Role': g_role, 'Separator': g_separator}),

            ('createGetIdentifier',{'Role': g_role, 'Separator': g_separator}),
            ('createGetRoot',{'Role': g_role}),
            ('createGetItem',{'Role': g_role}),
            ('createGetNewTitle',{'Role': g_role}),
            ('createUpdatePushItems',{'Role': g_role}),
            ('createGetPushItems',{'Role': g_role}),
            ('createGetPushProperties',{'Role': g_role}),
            ('createGetItemParentIds',{'Role': g_role}),
            ('createInsertUser',{'Role': g_role}),
            ('createMergeItem',{'Role': g_role}),
            ('createMergeParent',{'Role': g_role}),
            ('createInsertItem',{'Role': g_role}),
            ('createPullChanges',{'Role': g_role}),
            ('createUpdateNewItemId',{'Role': g_role}))

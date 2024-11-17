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

from .unolib import KeyMap

from .unotool import getResourceLocation
from .unotool import getSimpleFile

from .dbconfig import g_folder
from .dbconfig import g_version

from .dbqueries import getSqlQuery

from .dbtool import getDataSourceCall
from .dbtool import getSequenceFromResult
from .dbtool import getDataFromResult
from .dbtool import getKeyMapFromResult
from .dbtool import registerDataSource
from .dbtool import executeQueries
from .dbtool import executeSqlQueries
from .dbtool import getDataSourceConnection
from .dbtool import createDataSource
from .dbtool import checkDataBase
from .dbtool import createStaticTable

import traceback


def getDataSourceUrl(ctx, dbname, plugin, register):
    error = None
    url = getResourceLocation(ctx, plugin, g_folder)
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
    print("dbinit._createDataBase() 1")
    try:
        connection = datasource.getConnection('', '')
    except SQLException as e:
        error = e
    else:
        version, error = checkDataBase(ctx, connection)
        if error is None:
            statement = connection.createStatement()
            createStaticTable(ctx, statement, _getStaticTables())
            tables, queries = _getTablesAndStatements(ctx, statement, version)
            executeSqlQueries(statement, tables)
            _executeQueries(ctx, statement, _getQueries())
            executeSqlQueries(statement, queries)
            print("dbinit._createDataBase() 2")
            views, triggers = _getViewsAndTriggers(ctx, statement)
            executeSqlQueries(statement, views)
            #executeSqlQueries(statement, triggers)
        connection.close()
        connection.dispose()
    print("dbinit._createDataBase() 3")
    return error

def _executeQueries(ctx, statement, queries):
    for name, format in queries.items():
        query = getSqlQuery(ctx, name, format)
        statement.executeQuery(query)

def _getTableColumns(connection, tables):
    columns = {}
    metadata = connection.MetaData
    for table in tables:
        columns[table] = _getColumns(metadata, table)
    return columns

def _getColumns(metadata, table):
    columns = []
    result = metadata.getColumns("", "", table, "%")
    while result.next():
        column = '"%s"' % result.getString(4)
        columns.append(column)
    return columns

def _createPreparedStatement(ctx, datasource, statements):
    queries = datasource.getQueryDefinitions()
    for name, sql in statements.items():
        if not queries.hasByName(name):
            query = ctx.ServiceManager.createInstance("com.sun.star.sdb.QueryDefinition")
            query.Command = sql
            queries.insertByName(name, query)

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

def getViewsAndTriggers(ctx, statement, name):
    c1 = []
    s1 = []
    f1 = []
    queries = []
    triggers = []
    triggercore = []
    call = getDataSourceCall(ctx, statement.getConnection(), 'getViews')
    tables = getSequenceFromResult(statement.executeQuery(getSqlQuery(ctx, 'getViewNames')))
    for table in tables:
        call.setString(1, table)
        result = call.executeQuery()
        while result.next():
            c2 = []
            s2 = []
            f2 = []
            trigger = {}
            data = getDataFromResult(result)
            view = data['View']
            ptable = data['PrimaryTable']
            pcolumn = data['PrimaryColumn']
            labelid = data['LabelId']
            typeid = data['TypeId']
            c1.append('"%s"' % view)
            c2.append('"%s"' % pcolumn)
            c2.append('"Value"')
            s1.append('"%s"."Value"' % view)
            s2.append('"%s"."%s"' % (table, pcolumn))
            s2.append('"%s"."Value"' % table)
            f = 'LEFT JOIN "%s" ON "%s"."%s"="%s"."%s"' % (view, ptable, pcolumn, view, pcolumn)
            f1.append(f)
            f2.append('"%s"' % table)
            f = 'JOIN "Labels" ON "%s"."Label"="Labels"."Label" AND "Labels"."Label"=%s'
            f2.append(f % (table, labelid))
            if typeid is not None:
                f = 'JOIN "Types" ON "%s"."Type"="Types"."Type" AND "Types"."Type"=%s'
                f2.append(f % (table, typeid))
            format = (view, ','.join(c2), ','.join(s2), ' '.join(f2))
            query = getSqlQuery(ctx, 'createView', format)
            queries.append(query)
            triggercore.append(getSqlQuery(ctx, 'createTriggerUpdateAddressBookCore', data))
    call.close()
    if queries:
        column = getSqlQuery(ctx, 'getPrimaryColumnName')
        c1.insert(0, '"%s"' % column)
        c1.append('"%s"' % getSqlQuery(ctx, 'getBookmarkColumnName'))
        s1.insert(0, '"%s"."%s"' % (ptable, column))
        s1.append(getSqlQuery(ctx, 'getBookmarkColumn'))
        f1.insert(0, getSqlQuery(ctx, 'getAddressBookTable'))
        f1.append(getSqlQuery(ctx, 'getAddressBookPredicate'))
        format = (name, ','.join(c1), ','.join(s1), ' '.join(f1))
        query = getSqlQuery(ctx, 'createView', format)
        queries.append(query)
        trigger = getSqlQuery(ctx, 'createTriggerUpdateAddressBook', ' '.join(triggercore))
        triggers.append(trigger)
    return queries, triggers

def getStaticTables():
    tables = ('Tables',
              'Types',
              'Columns',
              'TableType',
              'TableColumn',
              'Fields',
              'Labels',
              'TableLabel',
              'Settings')
    return tables

def getQueries():
    return (('createInsertUser', None),
            ('createGetPeopleIndex', None),
            ('createGetLabelIndex', None),
            ('createGetTypeIndex', None),
            ('createMergePeople', None),
            ('createMergeGroup', None),
            ('createMergeConnection', None))

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


from ..unolib import KeyMap

from ..dbtool import getDataSourceCall
from ..dbtool import getSequenceFromResult
from ..dbtool import getKeyMapFromResult

from ..dbqueries import getSqlQuery

from ..dbconfig import g_version
from ..dbconfig import g_superuser
from ..dbconfig import g_view
from ..dbconfig import g_cardview
from ..dbconfig import g_bookview
from ..dbconfig import g_dba

import traceback


def getTables(ctx, connection, version=g_version):
    tables = []
    statement = connection.createStatement()
    query = getSqlQuery(ctx, 'getTableNames')
    result = statement.executeQuery(query)
    sequence = getSequenceFromResult(result)
    result.close()
    statement.close()
    call = getDataSourceCall(ctx, connection, 'getTables')
    for table in sequence:
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
            definition = '"%s" %s' % (column, data.getValue('Type'))
            default = data.getValue('Default')
            if default:
                definition += ' DEFAULT %s' % default
            options = data.getValue('Options')
            if options:
                definition += ' %s' % options
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
    call.close()
    return tables

def getViews(ctx, result, name):
    try:
        print("dbinit.getViews() 1")
        sel1 = []
        tab1 = []
        queries = []
        format = g_view
    
        q = 'CREATE VIEW IF NOT EXISTS "%(ViewName)s" AS SELECT %(ViewSelect)s FROM "%(CardTable)s" %(ViewTable)s'
    
        t1 = 'LEFT JOIN "%(ViewName)s" ON "%(CardTable)s"."%(CardColumn)s"="%(ViewName)s"."%(CardColumn)s"'
        t2 = 'LEFT JOIN "%(DataTable)s" AS "%(AliasNum)s" ON "%(CardTable)s"."%(CardColumn)s"="%(AliasNum)s"."%(CardColumn)s" '
        t2 += 'AND "%(AliasNum)s"."%(DataColumn)s"=%(ColumnId)s'
    
        s1 = '"%(ViewName)s"."%(ColumnName)s"'
        s2 = '"%(AliasNum)s"."%(DataValue)s" AS "%(ColumnName)s"'
        s3 = '"%(CardTable)s"."%(CardColumn)s"'
        s4 = '"%(CardTable)s"."Created","%(CardTable)s"."Modified"'
        s5 = '"%(CardTable)s"."%(CardUri)s"'
        print("dbinit.getViews() 2")
    
        for view, columns in result.items():
            i = 0
            col2 = columns.keys()
            sel2 = []
            tab2 = []
            format['ViewName'] = view
            for column, index in columns.items():
                format['ColumnName'] = column
                format['ColumnId'] = index
                format['AliasNum'] = i
                sel1.append(s1 % format)
                tab2.append(t2 % format)
                sel2.append(s2 % format)
                i += 1
            sel2.append(s3 % format)
            format['ViewSelect'] = ','.join(sel2)
            format['ViewTable'] = ' '.join(tab2)
            tab1.append(t1 % format)
            queries.append(q % format)
        print("dbinit.getViews() 3")
        sel1.append(s3 % format)
        sel1.append(s4 % format)
        sel1.append(s5 % format)
        format['ViewName'] = g_cardview
        format['ViewSelect'] = ','.join(sel1)
        format['ViewTable'] = ' '.join(tab1)
        queries.append(q % format)
        #format['Name'] = g_bookview
        #query = getSqlQuery(ctx, 'createBookView', format)
        #print("dbinit.getViews() 4 %s" % query)
        #queries.append(query)
        return queries
    except Exception as e:
        msg = "Error: %s" % traceback.print_exc()
        print(msg)

def getStaticTables():
    tables = ('Tables',
              'Columns',
              'TableColumn',
              'Resources',
              'Properties',
              'Types',
              'PropertyType')
    return tables

def getQueries():
    return (('createSelectUser', None),
            ('createInsertUser', None),
            ('createInsertAddressbook', None),
            ('createUpdateAddressbookName', None),
            ('createMergeCard', None),
            ('createMergeGroup', None),
            ('createMergeGroupMembers', None),
            ('createDeleteCard', None),
            ('createUpdateUser', None),
            ('createGetLastUserSync', None),
            ('createGetLastAddressbookSync', None),
            ('createGetLastGroupSync', None),
            ('createSelectChangedCards', None),
            ('insertSuperUser', g_superuser),
            ('insertSuperAdressbook', None),
            ('insertSuperGroup', None),
            ('createSelectColumns', None),
            ('createSelectColumnIds', None),
            ('createSelectPaths', None),
            ('createSelectTypes', None),
            ('createSelectMaps', None),
            ('createSelectTmps', None),
            ('createSelectFields', None),
            ('createSelectGroups', None),
            ('createSelectCardGroup', None),
            ('createInsertGroup', None),
            ('createMergeCardValue', None),
            ('createMergeCardData', None),
            ('createMergeCardGroup', None),
            ('createSelectChangedAddressbooks', None),
            ('createSelectChangedGroups', None),
            ('createUpdateAddressbook', None),
            ('createUpdateGroup', None),
            ('createSelectCardProperties', None))

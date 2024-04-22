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

from com.sun.star.sdbc.ColumnValue import NO_NULLS
from com.sun.star.sdbc.ColumnValue import NULLABLE

from .dbtool import createTables
from .dbtool import createIndexes
from .dbtool import createForeignKeys

import traceback


def createStaticTables(tables, statement, csv, readonly=False):
    createTables(tables, _getStaticTables().items())
    createIndexes(tables, _getUniqueIndexes())
    createForeignKeys(tables, _getForeignKeys())
    _setStaticTable(statement, _getStaticTables().keys(), csv, readonly)

def getTableNames():
    return 'SELECT "CatalogName", "SchemaName", "Name" FROM "Tables" ORDER BY "Table";'

def getTables():
    c1 = '"C"."Name"'
    c2 = '"TC"."TypeName"'
    c3 = '"TC"."Type"'
    c4 = '"TC"."Scale"'
    c5 = '"TC"."IsNullable"'
    c6 = '"TC"."DefaultValue"'
    c7 = '"TC"."IsRowVersion"'
    c8 = '"TC"."IsAutoIncrement"'
    c9 = '"TC"."Primary"'
    c = (c1, c2, c3, c4, c5, c6, c7, c8, c9)
    f1 = '"Tables" AS "T"'
    f2 = 'JOIN "TableColumn" AS "TC" ON "T"."Table"="TC"."Table"'
    f3 = 'JOIN "Columns" AS "C" ON "TC"."Column"="C"."Column"'
    f = (f1, f2, f3)
    w = '"T"."CatalogName"=? AND "T"."SchemaName"=? AND "T"."Name"=?'
    s = (','.join(c), ' '.join(f), w)
    return 'SELECT %s FROM %s WHERE %s;' % s

def getIndexes():
    c1 = '"T"."CatalogName"'
    c2 = '"T"."SchemaName"'
    c3 = '"T"."Name"'
    c4 = '"I"."Unique"'
    c5 = 'ARRAY_AGG("C"."Name")'
    c = (c1, c2, c3, c4, c5)
    f1 = '"Indexes" AS "I"'
    f2 = 'JOIN "Tables" AS "T" ON "I"."Table"="T"."Table"'
    f3 = 'JOIN "Columns" AS "C" ON "I"."Column"="C"."Column"'
    f = (f1, f2, f3)
    g = '"T"."CatalogName", "T"."SchemaName", "T"."Name", "I"."Unique"'
    s = (','.join(c), ' '.join(f), g)
    return 'SELECT %s FROM %s GROUP BY %s;' % s

def getForeignKeys():
    c1 = '"T"."CatalogName"'
    c2 = '"T"."SchemaName"'
    c3 = '"T"."Name"'
    c4 = '"C"."Name"'
    c5 = '"FT"."CatalogName"'
    c6 = '"FT"."SchemaName"'
    c7 = '"FT"."Name"'
    c8 = '"K"."UpdateRule"'
    c9 = '"K"."DeleteRule"'
    c10 = '"FC"."Name"'
    c = (c1, c2, c3, c4, c5, c6, c7, c8, c9, c10)
    f1 = '"ForeignKeys" AS "K"'
    f2 = 'JOIN "Tables" AS "T" ON "K"."Table"="T"."Table"'
    f3 = 'JOIN "Columns" AS "C" ON "K"."Column"="C"."Column"'
    f4 = 'JOIN "Tables" AS "FT" ON "K"."ReferencedTable"="FT"."Table"'
    f5 = 'JOIN "Columns" AS "FC" ON "K"."RelatedColumn"="FC"."Column"'
    f = (f1, f2, f3, f4, f5)
    s = (','.join(c), ' '.join(f))
    return 'SELECT %s FROM %s;' % s

def getPrivileges():
    c1 = '"T"."CatalogName"'
    c2 = '"T"."SchemaName"'
    c3 = '"T"."Name"'
    c4 = '"C"."Column"'
    c5 = '"P"."Role"'
    c6 = 'SUM("P"."Privilege")'
    c = (c1, c2, c3, c4, c5, c6)
    f1 = '"Privileges" AS "P"'
    f2 = 'JOIN "Tables" AS "T" ON "P"."Table"="T"."Table"'
    f3 = 'LEFT JOIN "Columns" AS "C" ON "P"."Column"="C"."Column"'
    f = (f1, f2, f3)
    g = '"T"."CatalogName", "T"."SchemaName", "T"."Name", "C"."Column", "P"."Role"'
    s = (','.join(c), ' '.join(f), g)
    return 'SELECT %s FROM %s GROUP BY %s;' % s

def _setStaticTable(statement, tables, csv, readonly):
    for table in tables:
        statement.executeUpdate(_getTableSource(table, csv % table))
        if readonly:
            statement.executeUpdate(_getTableReadOnly(table))

def _getStaticTables():
    return {'Tables':      {'CatalogName': 'PUBLIC',
                            'SchemaName':  'PUBLIC',
                            'Type':        'TEXT TABLE',
                            'Columns': ({'Name': 'Table',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'CatalogName',
                                         'TypeName': 'VARCHAR',
                                         'Type': 12,
                                         'Scale': 100,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'SchemaName',
                                         'TypeName': 'VARCHAR',
                                         'Type': 12,
                                         'Scale': 100,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'Name',
                                         'TypeName': 'VARCHAR',
                                         'Type': 12,
                                         'Scale': 100,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'Identity',
                                         'TypeName': 'SMALLINT',
                                         'Type': 5,
                                         'IsNullable': NULLABLE,
                                         'DefaultValue': 'NULL'},
                                        {'Name': 'View',
                                         'TypeName': 'BOOLEAN',
                                         'Type': 16,
                                         'IsNullable': NULLABLE,
                                         'DefaultValue': 'FALSE'}),
                            'PrimaryKeys': ('Table', )},
            'Columns':     {'CatalogName': 'PUBLIC',
                            'SchemaName':  'PUBLIC',
                            'Type':        'TEXT TABLE',
                            'Columns': ({'Name': 'Column',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'Name',
                                         'TypeName': 'VARCHAR',
                                         'Type': 12,
                                         'Scale': 100,
                                         'IsNullable': NO_NULLS}),
                            'PrimaryKeys': ('Column', )},
            'TableColumn': {'CatalogName': 'PUBLIC',
                            'SchemaName':  'PUBLIC',
                            'Type':        'TEXT TABLE',
                            'Columns': ({'Name': 'Table',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'Column',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'TypeName',
                                         'TypeName': 'VARCHAR',
                                         'Type': 12,
                                         'Scale': 100,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'Type',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'Scale',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NULLABLE,
                                         'DefaultValue': 'NULL'},
                                        {'Name': 'IsNullable',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS,
                                         'DefaultValue': '0'},
                                        {'Name': 'DefaultValue',
                                         'TypeName': 'VARCHAR',
                                         'Type': 12,
                                         'Scale': 100,
                                         'IsNullable': NULLABLE,
                                         'DefaultValue': 'NULL'},
                                        {'Name': 'IsRowVersion',
                                         'TypeName': 'BOOLEAN',
                                         'Type': 16,
                                         'IsNullable': NULLABLE,
                                         'DefaultValue': 'NULL'},
                                        {'Name': 'IsAutoIncrement',
                                         'TypeName': 'BOOLEAN',
                                         'Type': 16,
                                         'IsNullable': NULLABLE,
                                         'DefaultValue': 'NULL'},
                                        {'Name': 'Primary',
                                         'TypeName': 'BOOLEAN',
                                         'Type': 16,
                                         'IsNullable': NULLABLE,
                                         'DefaultValue': 'NULL'}),
                            'PrimaryKeys': ('Table', 'Column')},
            'ForeignKeys': {'CatalogName': 'PUBLIC',
                            'SchemaName':  'PUBLIC',
                            'Type':        'TEXT TABLE',
                            'Columns': ({'Name': 'Table',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'Column',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'ReferencedTable',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'RelatedColumn',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'UpdateRule',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'DeleteRule',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS})},
            'Indexes':     {'CatalogName': 'PUBLIC',
                            'SchemaName':  'PUBLIC',
                            'Type':        'TEXT TABLE',
                            'Columns': ({'Name': 'Index',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'Table',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'Column',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'Unique',
                                         'TypeName': 'BOOLEAN',
                                         'Type': 16,
                                         'IsNullable': NO_NULLS,
                                         'DefaultValue': 'TRUE'})},
            'Privileges':  {'CatalogName': 'PUBLIC',
                            'SchemaName':  'PUBLIC',
                            'Type':        'TEXT TABLE',
                            'Columns': ({'Name': 'Table',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'Column',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NULLABLE,
                                         'DefaultValue': 'NULL'},
                                        {'Name': 'Role',
                                         'TypeName': 'VARCHAR',
                                         'Type': 12,
                                         'Scale': 100,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'Privilege',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS})},
            'Settings':    {'CatalogName': 'PUBLIC',
                            'SchemaName':  'PUBLIC',
                            'Type':        'TEXT TABLE',
                            'Columns': ({'Name': 'Id',
                                         'TypeName': 'INTEGER',
                                         'Type': 4,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'Name',
                                         'TypeName': 'VARCHAR',
                                         'Type': 12,
                                         'Scale': 100,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'Value1',
                                         'TypeName': 'VARCHAR',
                                         'Type': 12,
                                         'Scale': 100,
                                         'IsNullable': NO_NULLS},
                                        {'Name': 'Value2',
                                         'TypeName': 'VARCHAR',
                                         'Type': 12,
                                         'Scale': 100,
                                         'IsNullable': NULLABLE,
                                         'DefaultValue': 'NULL'},
                                        {'Name': 'Value3',
                                         'TypeName': 'VARCHAR',
                                         'Type': 12,
                                         'Scale': 100,
                                         'IsNullable': NULLABLE,
                                         'DefaultValue': 'NULL'}),
                            'PrimaryKeys': ('Id', )}}

def _getUniqueIndexes():
    return (('PUBLIC.PUBLIC.Tables',  True, ('CatalogName', 'SchemaName', 'Name')),
            ('PUBLIC.PUBLIC.Columns', True, ('Name', )))

def _getForeignKeys():
    return (('PUBLIC.PUBLIC.TableColumn', 'Table',  'PUBLIC.PUBLIC.Tables',  'Table',  0, 0),
            ('PUBLIC.PUBLIC.TableColumn', 'Column', 'PUBLIC.PUBLIC.Columns', 'Column', 0, 0),
            ('PUBLIC.PUBLIC.ForeignKeys', 'Table',  'PUBLIC.PUBLIC.Tables',  'Table',  0, 0),
            ('PUBLIC.PUBLIC.ForeignKeys', 'Column', 'PUBLIC.PUBLIC.Columns', 'Column', 0, 0),
            ('PUBLIC.PUBLIC.Indexes',     'Table',  'PUBLIC.PUBLIC.Tables',  'Table',  0, 0),
            ('PUBLIC.PUBLIC.Indexes',     'Column', 'PUBLIC.PUBLIC.Columns', 'Column', 0, 0),
            ('PUBLIC.PUBLIC.Privileges',  'Table',  'PUBLIC.PUBLIC.Tables',  'Table',  0, 0),
            ('PUBLIC.PUBLIC.Privileges',  'Column', 'PUBLIC.PUBLIC.Columns', 'Column', 0, 0))

# Set Static Table Queries
def _getTableSource(table, csv):
    return 'SET TABLE "%s" SOURCE "%s"' % (table, csv)

def _getTableHeader(table):
    return 'SET TABLE "%s" SOURCE HEADER "%s"' % table

def _getTableReadOnly(table):
    return 'SET TABLE "%s" READONLY TRUE' % table


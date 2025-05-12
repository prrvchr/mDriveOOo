#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-25 https://prrvchr.github.io                                  ║
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

from com.sun.star.sdbc.DataType import BOOLEAN
from com.sun.star.sdbc.DataType import INTEGER
from com.sun.star.sdbc.DataType import SMALLINT
from com.sun.star.sdbc.DataType import VARCHAR

from com.sun.star.sdbc.KeyRule import CASCADE

from .dbtool import createTables
from .dbtool import createIndexes
from .dbtool import createForeignKeys

from collections import OrderedDict
import traceback


def createStaticTables(catalog, schema, tables, **kwargs):
    items = _getStaticTables(catalog, schema, **kwargs)
    createTables(tables, items.items())
    return items.keys()

def createStaticIndexes(catalog, schema, tables, *args):
    createIndexes(tables, _getUniqueIndexes(catalog, schema, *args))

def createStaticForeignKeys(catalog, schema, tables, *args):
    createForeignKeys(tables, _getForeignKeys(catalog, schema, *args))

def setStaticTable(statement, tables, csv, readonly=False):
    _setStaticTable(statement, tables, csv, readonly)

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

def _getStaticTables(catalog, schema, **kwargs):
    tables = OrderedDict()
    tables['Tables'] =       {'CatalogName': catalog,
                              'SchemaName':  schema,
                              'Type':        'TEXT TABLE',
                              'Columns': ({'Name': 'Table',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'CatalogName',
                                           'TypeName': 'VARCHAR',
                                           'Type': VARCHAR,
                                           'Scale': 100,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'SchemaName',
                                           'TypeName': 'VARCHAR',
                                           'Type': VARCHAR,
                                           'Scale': 100,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'Name',
                                           'TypeName': 'VARCHAR',
                                           'Type': VARCHAR,
                                           'Scale': 100,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'Identity',
                                           'TypeName': 'SMALLINT',
                                           'Type': SMALLINT,
                                           'IsNullable': NULLABLE,
                                           'DefaultValue': 'NULL'},
                                          {'Name': 'View',
                                           'TypeName': 'BOOLEAN',
                                           'Type': BOOLEAN,
                                           'IsNullable': NULLABLE,
                                           'DefaultValue': 'FALSE'}),
                              'PrimaryKeys': ('Table', )}
    tables['Columns'] =      {'CatalogName': catalog,
                              'SchemaName':  schema,
                              'Type':        'TEXT TABLE',
                              'Columns': ({'Name': 'Column',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'Name',
                                           'TypeName': 'VARCHAR',
                                           'Type': VARCHAR,
                                           'Scale': 100,
                                           'IsNullable': NO_NULLS}),
                              'PrimaryKeys': ('Column', )}
    tables['TableColumn'] =  {'CatalogName': catalog,
                              'SchemaName':  schema,
                              'Type':        'TEXT TABLE',
                              'Columns': ({'Name': 'Table',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'Column',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'TypeName',
                                           'TypeName': 'VARCHAR',
                                           'Type': VARCHAR,
                                           'Scale': 100,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'Type',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'Scale',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NULLABLE,
                                           'DefaultValue': 'NULL'},
                                          {'Name': 'IsNullable',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS,
                                           'DefaultValue': '0'},
                                          {'Name': 'DefaultValue',
                                           'TypeName': 'VARCHAR',
                                            'Type': VARCHAR,
                                            'Scale': 100,
                                            'IsNullable': NULLABLE,
                                            'DefaultValue': 'NULL'},
                                          {'Name': 'IsRowVersion',
                                           'TypeName': 'BOOLEAN',
                                           'Type': BOOLEAN,
                                           'IsNullable': NULLABLE,
                                           'DefaultValue': 'NULL'},
                                          {'Name': 'IsAutoIncrement',
                                           'TypeName': 'BOOLEAN',
                                           'Type': BOOLEAN,
                                           'IsNullable': NULLABLE,
                                           'DefaultValue': 'NULL'},
                                          {'Name': 'Primary',
                                           'TypeName': 'BOOLEAN',
                                           'Type': BOOLEAN,
                                           'IsNullable': NULLABLE,
                                           'DefaultValue': 'NULL'}),
                              'PrimaryKeys': ('Table', 'Column')}
    tables['ForeignKeys'] =  {'CatalogName': catalog,
                              'SchemaName':  schema,
                              'Type':        'TEXT TABLE',
                              'Columns': ({'Name': 'Table',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'Column',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'ReferencedTable',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'RelatedColumn',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'UpdateRule',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'DeleteRule',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS})}
    tables['Indexes'] =      {'CatalogName': catalog,
                              'SchemaName':  schema,
                              'Type':        'TEXT TABLE',
                              'Columns': ({'Name': 'Index',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'Table',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'Column',
                                           'TypeName': 'INTEGER',
                                           'Type': INTEGER,
                                           'IsNullable': NO_NULLS},
                                          {'Name': 'Unique',
                                           'TypeName': 'BOOLEAN',
                                           'Type': BOOLEAN,
                                           'IsNullable': NO_NULLS,
                                           'DefaultValue': 'TRUE'})}
    for name, value in kwargs.items():
        tables[name] = value
    return tables

def _getUniqueIndexes(catalog, schema, *args):
    indexes = [(f'{catalog}.{schema}.Tables',  True, ('CatalogName', 'SchemaName', 'Name')),
               (f'{catalog}.{schema}.Columns', True, ('Name', ))]
    for index in args:
        indexes.append(index)
    return tuple(indexes)

def _getForeignKeys(catalog, schema, *args):
    foreignkeys = [(f'{catalog}.{schema}.TableColumn', 'Table',  f'{catalog}.{schema}.Tables',  'Table',  CASCADE, CASCADE),
                   (f'{catalog}.{schema}.TableColumn', 'Column', f'{catalog}.{schema}.Columns', 'Column', CASCADE, CASCADE),
                   (f'{catalog}.{schema}.ForeignKeys', 'Table',  f'{catalog}.{schema}.Tables',  'Table',  CASCADE, CASCADE),
                   (f'{catalog}.{schema}.ForeignKeys', 'Column', f'{catalog}.{schema}.Columns', 'Column', CASCADE, CASCADE),
                   (f'{catalog}.{schema}.Indexes',     'Table',  f'{catalog}.{schema}.Tables',  'Table',  CASCADE, CASCADE),
                   (f'{catalog}.{schema}.Indexes',     'Column', f'{catalog}.{schema}.Columns', 'Column', CASCADE, CASCADE)]
    for foreignkey in args:
        foreignkeys.append(foreignkey)
    return tuple(foreignkeys)

# Set Static Table Queries
def _getTableSource(table, csv):
    return 'SET TABLE "%s" SOURCE "%s"' % (table, csv)

def _getTableHeader(table):
    return 'SET TABLE "%s" SOURCE HEADER "%s"' % table

def _getTableReadOnly(table):
    return 'SET TABLE "%s" READONLY TRUE' % table


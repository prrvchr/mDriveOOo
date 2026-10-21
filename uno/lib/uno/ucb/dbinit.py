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

from com.sun.star.sdbc.DataType import INTEGER
from com.sun.star.sdbc.DataType import VARCHAR

from com.sun.star.sdbc import KeyRule

from com.sun.star.sdbcx import CheckOption
from com.sun.star.sdbcx import PrivilegeObject

from .dbtool import getConnectionUrl
from .dbtool import getTablePrivileges
from .dbtool import getPrivileges

from .dbqueries import getSqlQuery

from .ucp import g_ucbseparator

from .dbconfig import g_catalog
from .dbconfig import g_folder
from .dbconfig import g_schema
from .dbconfig import g_role
from .dbconfig import g_queries

from .configuration import g_scheme

import traceback


def getDataBaseUrl(ctx):
    return getConnectionUrl(ctx, g_folder + g_ucbseparator + g_scheme)

def getDataSourceUrl(ctx):
    return getConnectionUrl(ctx, g_folder + g_ucbseparator + g_scheme + '.odb')

def getStaticTables():
    yield 'Privileges',      {'CatalogName': g_catalog,
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

def getForeignKeys():
    yield (f'{g_catalog}.{g_schema}.Privileges', 'Table',  f'{g_catalog}.{g_schema}.Tables',  'Table',  KeyRule.CASCADE, KeyRule.CASCADE)
    yield (f'{g_catalog}.{g_schema}.Privileges', 'Column', f'{g_catalog}.{g_schema}.Columns', 'Column', KeyRule.CASCADE, KeyRule.CASCADE)

def getFunctions():
    for name in ('GetIsFolder', 'GetContentType', 'GetUniqueName'):
        yield name

def getDefaultPrivileges(statement):
    yield from getTablePrivileges(statement, getPrivileges())

def getViews(ctx, connection):
    yield from _getViews(ctx, _getViewNames(), 'get%sViewCommand', g_queries, CheckOption.CASCADE)

def getViewPrivileges(statement):
    yield from _getViewOptions(_getViewNames(), PrivilegeObject.TABLE, g_role, 1)

def getProcedures():
    for name in ('GetItem',
                 'UpdatePushItems',
                 'GetPushItems',
                 'GetPushProperties',
                 'GetItemParentIds',
                 'InsertUser',
                 'MergeItem',
                 'InsertItem',
                 'UpdateNewItemId'):
        yield name

def _getViews(ctx, items, command, format, *option):
    for catalog, schema, name in items:
        yield catalog, schema, name, getSqlQuery(ctx, command % name, format), *option

def _getViewNames(catalog=g_catalog, schema=g_schema):
    for name in ('Child',
                 'Twin',
                 'Duplicate',
                 'Path',
                 'Children'):
        yield catalog, schema, name

def _getViewOptions(items, *options):
    for catalog, schema, name in items:
        yield catalog, schema, name, *options


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

# DataSource configuration
g_protocol = 'xdbc:hsqldb:'
g_folder = 'hsqldb'
g_jar = 'hsqldb.jar'
g_class = 'org.hsqldb.jdbcDriver'
g_options = ';hsqldb.default_table_type=cached;ifexists=false;shutdown=true'
g_csv = '%s.csv;fs=|;ignore_first=true;encoding=UTF-8;quoted=true'
g_version = '2.5.1'
g_role = 'FrontOffice'
g_dba = 'SA'

g_dotcode = 183

# View parameter
g_catalog = 'PUBLIC'
g_schema  = 'PUBLIC'

g_view = {'CardTable':  f'{g_catalog}.{g_schema}."Cards"',
          'CardColumn': 'Card',
          'CardUri':    'Uri',
          'DataTable':  f'{g_catalog}.{g_schema}."CardValues"',
          'DataColumn': 'Column',
          'DataValue':  'Value'}

# XXX: If we want to be able to create DataBase we need to get some
# XXX: DriverPropertyInfo from the driver. Here is the necessary information
g_drvinfos = {'AutoIncrementCreation':   lambda x: x.Value,
              'RowVersionCreation':      lambda x: x.Choices,
              'TypeInfoSettings':        lambda x: x.Choices,
              'TablePrivilegesSettings': lambda x: x.Choices}


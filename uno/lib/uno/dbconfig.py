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
g_superuser = ('#', 'https://', 'localhost', '/', 'admin')
g_schema = '%i'
g_user = '%i'

g_dotcode = 183

# View parameter
g_cardview = 'CardView'
g_bookview = 'BookView'
g_usercolumn = 'User'
g_view = {'UserTable': 'Users',
          'UserColumn': g_usercolumn,
          'BookCardTable': 'BookCards',
          'CardTable': 'Cards',
          'CardColumn': 'Card',
          'CardUri': 'Uri',
          'BookTable': 'Books',
          'BookColumn': 'Book',
          'DataTable': 'CardValues',
          'DataColumn': 'Column',
          'DataValue': 'Value',
          'Admin': g_dba}


g_bookmark = 'Bookmark'

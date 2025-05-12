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

from .ucp import g_ucbseparator
from .ucp import g_ucbprefix
from .ucp import g_ucbsuffix

from .ucp import g_ucbfolder
from .ucp import g_ucbfile

from .configuration import g_ucpfolder

# DataSource configuration
g_protocol = 'xdbc:hsqldb:'
g_folder = 'hsqldb'
g_path = 'hsqldb'
g_jar = 'hsqldb.jar'
g_class = 'org.hsqldb.jdbcDriver'
g_options = ';hsqldb.default_table_type=cached;ifexists=false'
g_shutdown = ';shutdown=true'
g_csv = '%s.csv;fs=|;ignore_first=true;encoding=UTF-8;quoted=true'
g_version = '2.7.2'
g_role = 'FrontOffice'

g_catalog = 'PUBLIC'
g_schema  = 'PUBLIC'
g_queries = {'Users':     f'{g_catalog}.{g_schema}."Users"',
             'Items':     f'{g_catalog}.{g_schema}."Items"',
             'Parents':   f'{g_catalog}.{g_schema}."Parents"',
             'Child':     f'{g_catalog}.{g_schema}."Child"',
             'Twin':      f'{g_catalog}.{g_schema}."Twin"',
             'Duplicate': f'{g_catalog}.{g_schema}."Duplicate"',
             'Path':      f'{g_catalog}.{g_schema}."Path"',
             'Children':  f'{g_catalog}.{g_schema}."Children"',
             'Role':      g_role,
             'Separator': g_ucbseparator,
             'UcbFolder': g_ucbfolder,
             'UcbFile':   g_ucbfile,
             'UcpFolder': g_ucpfolder,
             'Prefix':    g_ucbprefix,
             'Suffix':    g_ucbsuffix}

# XXX: If we want to be able to create DataBase we need to get some
# XXX: DriverPropertyInfo from the driver. Here is the necessary information
g_drvinfos = {'AutoIncrementCreation':   lambda x: x.Value,
              'RowVersionCreation':      lambda x: x.Choices,
              'TypeInfoSettings':        lambda x: x.Choices,
              'TablePrivilegesSettings': lambda x: x.Choices}


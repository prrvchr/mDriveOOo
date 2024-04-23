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

from .dbtool import checkDataBase
from .dbtool import createDataSource
from .dbtool import createTables
from .dbtool import createIndexes
from .dbtool import createForeignKeys
from .dbtool import createRoleAndPrivileges
from .dbtool import createUser
from .dbtool import currentDateTime
from .dbtool import currentDateTimeInTZ
from .dbtool import currentUnoDateTime
from .dbtool import executeQueries
from .dbtool import executeSqlQueries
from .dbtool import getConnectionInfo
from .dbtool import getConnectionInfos
from .dbtool import getConnectionUrl
from .dbtool import getDataBaseConnection
from .dbtool import getDataBaseInfo
from .dbtool import getDataBaseUrl
from .dbtool import getDataBaseTables
from .dbtool import getDataBaseIndexes
from .dbtool import getDataBaseForeignKeys
from .dbtool import getDataFromResult
from .dbtool import getDataSource
from .dbtool import getDataSourceCall
from .dbtool import getDataSourceClassPath
from .dbtool import getDataSourceConnection
from .dbtool import getDataSourceLocation
from .dbtool import getDataSourceInfo
from .dbtool import getDataSourceJavaInfo
from .dbtool import getDateTimeInTZToString
from .dbtool import getDateTimeFromString
from .dbtool import getDictFromResult
from .dbtool import getDriverInfos
from .dbtool import getDriverPropertyInfo
from .dbtool import getDriverPropertyInfos
from .dbtool import getObjectFromResult
from .dbtool import getObjectSequenceFromResult
from .dbtool import getResultValue
from .dbtool import getRowDict
from .dbtool import getRowValue
from .dbtool import getSequenceFromResult
from .dbtool import getSqlException
from .dbtool import getDateTimeToString
from .dbtool import getUnoType
from .dbtool import getValueFromResult
from .dbtool import registerDataSource
from .dbtool import toUnoDateTime

from .dbinit import createStaticTables
from .dbinit import createStaticIndexes
from .dbinit import createStaticForeignKeys
from .dbinit import setStaticTable
from .dbinit import getTableNames
from .dbinit import getTables
from .dbinit import getIndexes
from .dbinit import getForeignKeys
from .dbinit import getPrivileges

from .array import Array

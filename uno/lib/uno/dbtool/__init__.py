#!
# -*- coding: utf_8 -*-

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
from .dbtool import createStaticTable
from .dbtool import executeQueries
from .dbtool import executeSqlQueries
from .dbtool import getConnectionInfo
from .dbtool import getDataBaseConnection
from .dbtool import getDataBaseInfo
from .dbtool import getDataBaseUrl
from .dbtool import getDataFromResult
from .dbtool import getDataSource
from .dbtool import getDataSourceCall
from .dbtool import getDataSourceClassPath
from .dbtool import getDataSourceConnection
from .dbtool import getDataSourceLocation
from .dbtool import getDataSourceInfo
from .dbtool import getDataSourceJavaInfo
from .dbtool import getDictFromResult
from .dbtool import getDriverPropertyInfo
from .dbtool import getDriverPropertyInfos
from .dbtool import getKeyMapFromResult
from .dbtool import getKeyMapKeyMapFromResult
from .dbtool import getKeyMapSequenceFromResult
from .dbtool import getObjectFromResult
from .dbtool import getObjectSequenceFromResult
from .dbtool import getResultValue
from .dbtool import getRowDict
from .dbtool import getRowValue
from .dbtool import getSequenceFromResult
from .dbtool import getSqlException
from .dbtool import getTableColumns
from .dbtool import getTablesInfos
from .dbtool import getValueFromResult
from .dbtool import isSimilar
from .dbtool import registerDataSource

from .array import Array

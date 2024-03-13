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

from .database import DataBase

from .datasource import DataSource

from .cardtool import getLogException

from .dbtool import getConnectionUrl

from .unotool import checkVersion
from .unotool import getExtensionVersion

from .oauth2 import getOAuth2Version
from .oauth2 import g_extension as g_oauth2ext
from .oauth2 import g_version as g_oauth2ver

from .jdbcdriver import g_extension as g_jdbcext
from .jdbcdriver import g_identifier as g_jdbcid
from .jdbcdriver import g_version as g_jdbcver

from .configuration import g_extension
from .configuration import g_host

from .dbconfig import g_folder
from .dbconfig import g_version

import traceback


def getDataSource(ctx, logger, source, cls, mtd):
    oauth2 = getOAuth2Version(ctx)
    driver = getExtensionVersion(ctx, g_jdbcid)
    if oauth2 is None:
        raise getLogException(logger, source, 1003, 1121, cls, mtd, g_oauth2ext, g_extension)
    elif not checkVersion(oauth2, g_oauth2ver):
        raise getLogException(logger, source, 1003, 1122, cls, mtd, oauth2, g_oauth2ext, g_oauth2ver)
    elif driver is None:
        raise getLogException(logger, source, 1003, 1121, cls, mtd, g_jdbcext, g_extension)
    elif not checkVersion(driver, g_jdbcver):
        raise getLogException(logger, source, 1003, 1122, cls, mtd, driver, g_jdbcext, g_jdbcver)
    else:
        path = g_folder + '/' + g_host
        url = getConnectionUrl(ctx, path)
        try:
            database = DataBase(ctx, url)
        except SQLException as e:
            raise getLogException(logger, source, 1005, 1123, cls, mtd, url, e.Message)
        else:
            if not database.isUptoDate():
                raise getLogException(logger, source, 1005, 1124, cls, mtd, database.Version, g_version)
            else:
                return DataSource(ctx, database)
    return None


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

from com.sun.star.logging import LogLevel

from .dbtool import getSqlException as getException

from .unotool import checkVersion
from .unotool import createService
from .unotool import getExtensionVersion
from .unotool import getResourceLocation
from .unotool import getSimpleFile

from .oauth20 import getOAuth2Version
from .oauth20 import g_extension as g_oauth2ext
from .oauth20 import g_version as g_oauth2ver

from .jdbcdriver import g_extension as g_jdbcext
from .jdbcdriver import g_identifier as g_jdbcid
from .jdbcdriver import g_version as g_jdbcver
from .jdbcdriver import g_service

from .dbconfig import g_dotcode
from .dbconfig  import g_folder

from .logger import getLogger

from .configuration import g_extension
from .configuration import g_identifier
from .configuration import g_basename
from .configuration import g_defaultlog
from .configuration import g_host

g_memdb = 'xdbc:hsqldb:mem:db'

def getUserId(metadata):
    return metadata.get('User')

def getUserSchema(metadata):
    # FIXME: We need to replace the dot for schema name
    # FIXME: g_dotcode is used in database procedure too...
    return metadata.get('Name').replace('.', chr(g_dotcode))

def getDataBaseUrl(ctx):
    folder = g_folder + '/' + g_host
    location = getResourceLocation(ctx, g_identifier, folder)
    return location + '.odb'

def checkConfiguration(ctx, logger):
    oauth2 = getOAuth2Version(ctx)
    driver = getExtensionVersion(ctx, g_jdbcid)
    if oauth2 is None:
        raise _getLogException(logger, 1701, g_oauth2ext, g_extension)
    if not checkVersion(oauth2, g_oauth2ver):
        raise _getLogException(logger, 1702, oauth2, g_oauth2ext, g_oauth2ver)
    if driver is None:
        raise _getLogException(logger, 1701, g_jdbcext, g_extension)
    if not checkVersion(driver, g_jdbcver):
        raise _getLogException(logger, 1702, driver, g_jdbcext, g_jdbcver)
    driver = createService(ctx, g_service)
    if not _isDatabaseCreated(ctx) and not _hasRequiredServices(driver):
        raise _getLogException(logger, 1703, g_jdbcext, g_extension)

def getLogException(logger, source, state, code, cls, mtd, *args):
    status = logger.resolveString(state)
    msg = logger.resolveString(code, *args)
    logger.logp(LogLevel.SEVERE, cls, mtd, msg)
    return getException(status, code, msg, source)

def getSqlException(ctx, source, state, code, cls, mtd, *args):
    logger = getLogger(ctx, g_defaultlog, g_basename)
    return getLogException(logger, source, state, code, cls, mtd, *args)

def _getLogException(logger, code, *args):
    status = logger.resolveString(1003)
    msg = logger.resolveString(code, *args)
    return getException(status, code, msg, None)

def _isDatabaseCreated(ctx):
    return getSimpleFile(ctx).exists(getDataBaseUrl(ctx))

def _hasRequiredServices(driver):
    supports = False
    if driver.supportsService('com.sun.star.sdbcx.Driver'):
        connection = driver.connect(g_memdb, ())
        supports = connection.supportsService('com.sun.star.sdb.Connection')
        connection.close()
    return supports

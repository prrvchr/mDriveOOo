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

from com.sun.star.logging import LogLevel

from .dbtool import getConnectionUrl
from .dbtool import getSqlException as getException

from .unotool import checkVersion
from .unotool import getExtensionVersion

from .oauth20 import getOAuth2Version
from .oauth20 import g_extension as g_oauth2ext
from .oauth20 import g_version as g_oauth2ver

from .jdbcdriver import g_extension as g_jdbcext
from .jdbcdriver import g_identifier as g_jdbcid
from .jdbcdriver import g_version as g_jdbcver

from .configuration import g_extension
from .configuration import g_host

from .dbconfig import g_dotcode
from .dbconfig import g_folder

from .logger import getLogger

from .configuration import g_basename
from .configuration import g_defaultlog


def getUserId(metadata):
    return metadata.get('User')

def getUserSchema(metadata):
    # FIXME: We need to replace the dot for schema name
    # FIXME: g_dotcode is used in database procedure too...
    return metadata.get('Name').replace('.', chr(g_dotcode))

def getDataSourceUrl(ctx, logger, source, state, code, cls, mtd):
    oauth2 = getOAuth2Version(ctx)
    driver = getExtensionVersion(ctx, g_jdbcid)
    if oauth2 is None:
        raise getLogException(logger, source, state, code, cls, mtd, g_oauth2ext, g_extension)
    if not checkVersion(oauth2, g_oauth2ver):
        raise getLogException(logger, source, state, code + 1, cls, mtd, oauth2, g_oauth2ext, g_oauth2ver)
    if driver is None:
        raise getLogException(logger, source, state, code, cls, mtd, g_jdbcext, g_extension)
    if not checkVersion(driver, g_jdbcver):
        raise getLogException(logger, source, state, code + 1, cls, mtd, driver, g_jdbcext, g_jdbcver)
    return getConnectionUrl(ctx, g_folder + '/' + g_host)

def getLogException(logger, source, state, code, cls, mtd, *args):
    status = logger.resolveString(state)
    msg = logger.resolveString(code, *args)
    logger.logp(LogLevel.SEVERE, cls, mtd, msg)
    return getException(status, code, msg, source)

def getSqlException(ctx, source, state, code, cls, mtd, *args):
    logger = getLogger(ctx, g_defaultlog, g_basename)
    return getLogException(logger, source, state, code, cls, mtd, *args)


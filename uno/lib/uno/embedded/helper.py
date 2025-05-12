#!
# -*- coding: utf_8 -*-

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

from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.sdbc import SQLException

from .unotool import checkVersion
from .unotool import getExtensionVersion
from .unotool import getLibreOfficeInfo

from .jdbcdriver import g_extension as g_jdbcext
from .jdbcdriver import g_identifier as g_jdbcid
from .jdbcdriver import g_version as g_jdbcver

from .configuration import g_dbname
from .configuration import g_extension
from .configuration import g_lover

import traceback


def checkConfiguration(ctx, logger):
    name, version = getLibreOfficeInfo(ctx)
    if not checkVersion(version, g_lover):
        raise _getException(logger, 1001, 122, 123, name, version, name, g_lover)
    version = getExtensionVersion(ctx, g_jdbcid)
    if version is None:
        raise _getException(logger, 1001, 121, 124, g_jdbcext, g_extension)
    if not checkVersion(version, g_jdbcver):
        raise _getException(logger, 1001, 122, 125, version, g_jdbcext, g_jdbcver)

def getException(logger, source, code, exc, state, resource, *args):
    error = SQLException()
    error.ErrorCode = code
    error.NextException = exc
    error.SQLState = logger.resolveString(state)
    error.Message = logger.resolveString(resource, *args)
    error.Context = source
    return error

def _getException(logger, code, state, resource, *args):
    return getException(logger, None, code, None, state, resource, *args)


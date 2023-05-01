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

import uno
import unohelper

from com.sun.star.logging.LogLevel import SEVERE

from ..dbtool import getDateTimeFromString
from ..dbtool import getSqlException as getException

from ..logger import getLogger

from ..configuration import g_errorlog
from ..configuration import g_basename

import traceback


class Provider(unohelper.Base):

    @property
    def DateTimeFormat(self):
        return '%Y-%m-%dT%H:%M:%SZ'

    def parseDateTime(self, timestamp):
        return getDateTimeFromString(timestamp, self.DateTimeFormat)

    # Need to be implemented method
    def insertUser(self, database, request, scheme, server, name, pwd):
        raise NotImplementedError

    def initAddressbooks(self, database, user):
        raise NotImplementedError

    def firstPullCard(self, database, user, addressbook, pages, count):
        raise NotImplementedError

    def pullCard(self, database, user, addressbook, pages, count):
        raise NotImplementedError

    def parseCard(self, database):
        raise NotImplementedError

    # Can be overwritten method
    def syncGroups(self, database, user, addressbook, pages, count):
        pass

def getSqlException(ctx, source, state, code, method, *args):
    logger = getLogger(ctx, g_errorlog, g_basename)
    state = logger.resolveString(state)
    msg = logger.resolveString(code, *args)
    logger.logp(SEVERE, g_basename, method, msg)
    error = getException(state, code, msg, source)
    return error


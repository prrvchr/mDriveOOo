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

from com.sun.star.logging.LogLevel import INFO

from com.sun.star.ucb.ConnectionMode import ONLINE

from .base import UserBase

from .helper import getSqlException
from .helper import getUserId
from .helper import getUserSchema

from ..unotool import getConnectionMode

from ..configuration import g_extension


class User(UserBase):
    def __init__(self, ctx, source, logger, database, provider, scheme, url, server, name, token):
        self._cls = 'User'
        print("User.__init__() 1 url: %s" % url)
        mtd = '__init__'
        logger.logprb(INFO, self._cls, mtd, 1501, name)
        self._ctx = ctx
        logger.logprb(INFO, self._cls, mtd, 1502, name)
        metadata, arguments = database.selectUser(server, name)
        if metadata is not None:
            new = False
            logger.logprb(INFO, self._cls, mtd, 1503, name)
            request = provider.getRequest(url, name)
            if request is None:
                raise getSqlException(ctx, source, 1002, 1506, self._cls, mtd, name, g_extension)
        else:
            new = True
            logger.logprb(INFO, self._cls, mtd, 1504, name)
            if getConnectionMode(ctx, server) != ONLINE:
                raise getSqlException(ctx, source, 1004, 1507, self._cls, mtd, server)
            request = provider.getRequest(url, name)
            if request is None:
                raise getSqlException(ctx, source, 1002, 1506, self._cls, mtd, name, g_extension)
            metadata, arguments = provider.insertUser(database, request, scheme, server, name, token)
            if metadata is None:
                raise getSqlException(ctx, source, 1005, 1508, self._cls, mtd, name)
            database.createUser(getUserSchema(metadata), getUserId(metadata), name, '')
        super().__init__(ctx, request, metadata, arguments, token, new)

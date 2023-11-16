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

from com.sun.star.ucb.ConnectionMode import OFFLINE
from com.sun.star.ucb.ConnectionMode import ONLINE

from .book import Books

from ..cardtool import getSqlException

from ..dbconfig import g_user
from ..dbconfig import g_schema
from ..dbconfig import g_dotcode

from ..unotool import getConnectionMode

from ..oauth2 import getRequest
from ..oauth2 import g_service

import traceback


class User(object):
    def __init__(self, ctx, source, database, provider, scheme, server, name, pwd=''):
        self._ctx = ctx
        self._password = pwd
        self._sessions = []
        self._metadata, books = database.selectUser(server, name)
        new = self._metadata is None
        cls, mtd = 'User', '__init__()'
        if not new:
            request = getRequest(ctx, server, name)
            if request is None:
                raise getSqlException(ctx, source, 1002, 1105, cls, mtd, name)
        else:
            if self._isOffLine(server):
                raise getSqlException(ctx, source, 1004, 1108, cls, mtd, name)
            request = getRequest(ctx, server, name)
            if request is None:
                raise getSqlException(ctx, source, 1002, 1105, cls, mtd, name)
            self._metadata, books = self._getUserData(ctx, source, cls, mtd, database,
                                                      provider, request, scheme, server, name, pwd)
            database.createUser(self.getSchema(), self.Id, name, '')
        self.Request = request
        self._books = Books(ctx, books, new)

    @property
    def Id(self):
        return self._metadata.get('User')
    @property
    def Uri(self):
        return self._metadata.get('Uri')
    @property
    def Scheme(self):
        return self._metadata.get('Scheme')
    @property
    def Server(self):
        return self._metadata.get('Server')
    @property
    def Path(self):
        return self._metadata.get('Path')
    @property
    def Name(self):
        return self._metadata.get('Name')
    @property
    def Password(self):
        return self._password
    @property
    def Books(self):
        return self._books
    @property
    def BaseUrl(self):
        return self.Scheme + self.Server + self.Path

    def isOnLine(self):
        return getConnectionMode(self._ctx, self.Server) != OFFLINE
    def isOffLine(self):
        return self._isOffLine(self.Server)

# Procedures called by DataSource
    def getName(self):
        return self.Name

    def getPassword(self):
        password = ''
        return password

    def getSchema(self):
        # FIXME: We need to replace the dot for schema name
        # FIXME: g_dotcode is used in database procedure too...
        return self.Name.replace('.', chr(g_dotcode))

    def hasSession(self):
        return len(self._sessions) > 0

    def addSession(self, session):
        self._sessions.append(session)

    def removeSession(self, session):
        if session in self._sessions:
            self._sessions.remove(session)

    def unquoteUrl(self, url):
        return self.Request.unquoteUrl(url)

    def getBooks(self):
        return self._books.getBooks()

    def _getUserData(self, ctx, source, cls, mtd, database, provider, request, scheme, server, name, pwd):
        data = provider.insertUser(database, request, scheme, server, name, pwd)
        if data is None:
            raise getSqlException(ctx, source, 1006, 1107, cls, mtd, name)
        return data

    def _isOffLine(self, server):
        return getConnectionMode(self._ctx, server) != ONLINE


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

from .provider import getSqlException

from ..dbconfig import g_user
from ..dbconfig import g_schema

from ..unotool import getConnectionMode
from ..oauth2 import getRequest
from ..oauth2 import g_oauth2

import traceback


class User(unohelper.Base):
    def __init__(self, ctx, database, provider, scheme, server, name, pwd=''):
        try:
            self._ctx = ctx
            self._password = pwd
            self.Request = getRequest(ctx, server, name)
            self._metadata = database.selectUser(server, name)
            self._sessions = []
            new = self._metadata is None
            if new:
                if self._isOffLine(server):
                    raise getSqlException(self._ctx, self, 1004, 1108, '_getNewUser', name)
                self._metadata = self._getNewUser(database, provider, scheme, server, name, pwd)
                self._initNewUser(database, provider)
            self._books = Books(ctx, self._metadata, new)
        except Exception as e:
            msg = "Error: %s" % traceback.format_exc()
            print(msg)

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
        return g_user % self.Id

    def getPassword(self):
        password = ''
        return password

    def getSchema(self):
        return self.Name.replace('.','-')

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

    def _isOffLine(self, server):
        return getConnectionMode(self._ctx, server) != ONLINE

    def _isNewUser(self):
        return self._metadata is None

    def _getNewUser(self, database, provider, scheme, server, name, pwd):
        if self.Request is None:
            raise getSqlException(self._ctx, self, 1003, 1105, '_getNewUser', g_oauth2)
        return provider.insertUser(database, self.Request, scheme, server, name, pwd)

    def _initNewUser(self, database, provider):
        name = self.getName()
        if not database.createUser(name, self.getPassword()):
            raise provider.getSqlException(1005, 1106, '_initNewUser', name)
        database.createUserSchema(self.getSchema(), name)


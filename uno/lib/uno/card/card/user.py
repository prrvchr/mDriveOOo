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
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb.ConnectionMode import OFFLINE
from com.sun.star.ucb.ConnectionMode import ONLINE

from .book import Book

from ..helper import getSqlException
from ..helper import getUserId
from ..helper import getUserSchema

from ..unotool import getConnectionMode

from ..configuration import g_extension

import traceback

class User(object):
    def __init__(self, ctx, source, logger, database, provider, url, scheme, server, name, pwd=''):
        self._cls = 'User'
        mtd = '__init__'
        logger.logprb(INFO, self._cls, mtd, 1501, name)
        self._ctx = ctx
        self._password = pwd
        self._sessions = []
        logger.logprb(INFO, self._cls, mtd, 1502, name)
        metadata, args = database.selectUser(server, name)
        new = metadata is None
        if not new:
            logger.logprb(INFO, self._cls, mtd, 1503, name)
            request = provider.getRequest(url, name)
            if request is None:
                raise getSqlException(ctx, source, 1002, 1506, self._cls, mtd, name, g_extension)
        else:
            logger.logprb(INFO, self._cls, mtd, 1504, name)
            if self._isOffLine(server):
                raise getSqlException(ctx, source, 1004, 1507, self._cls, mtd, server)
            request = provider.getRequest(url, name)
            if request is None:
                raise getSqlException(ctx, source, 1002, 1506, self._cls, mtd, name, g_extension)
            metadata, args = provider.insertUser(database, request, scheme, server, name, pwd)
            if metadata is None:
                raise getSqlException(ctx, source, 1005, 1508, self._cls, mtd, name)
            database.createUser(getUserSchema(metadata), getUserId(metadata), name, '')
        self._request = request
        self._metadata = metadata
        books = (Book(new, **kwargs) for kwargs in args)
        self._books = {book.Uri: book for book in books}
        logger.logprb(INFO, self._cls, mtd, 1505, name)

    @property
    def Id(self):
        return getUserId(self._metadata)
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
    def BaseUrl(self):
        return self.Scheme + self.Server + self.Path
    @property
    def Request(self):
        return self._request

    def isOnLine(self):
        return self._isOnLine(self.Server)

    def isOffLine(self):
        return self._isOffLine(self.Server)

# Procedures called by DataSource
    def getName(self):
        return self.Name

    def getPassword(self):
        password = ''
        return password

    def getSchema(self):
        return getUserSchema(self._metadata)

    def hasBook(self, uri):
        return uri in self._books

    def getBooks(self):
        return self._books.values()

    def getBook(self, uri):
        return self._books[uri]

    def setNewBook(self, uri, **kwargs):
        book = Book(True, **kwargs)
        self._books[uri] = book
        return book

    def hasSession(self):
        return len(self._sessions) > 0

    def addSession(self, session):
        self._sessions.append(session)

    def removeSession(self, session):
        if session in self._sessions:
            self._sessions.remove(session)

    def unquoteUrl(self, url):
        return self.Request.unquoteUrl(url)

    def _isOffLine(self, server):
        return getConnectionMode(self._ctx, server) != ONLINE

    def _isOnLine(self, server):
        return getConnectionMode(self._ctx, server) != OFFLINE


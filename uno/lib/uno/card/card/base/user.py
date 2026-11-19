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

from com.sun.star.ucb.ConnectionMode import OFFLINE
from com.sun.star.ucb.ConnectionMode import ONLINE

from .book import Book

from ..helper import getUserId
from ..helper import getUserSchema

from ...unotool import getConnectionMode

from ...configuration import g_sep


class User():
    def __init__(self, ctx, request, metadata, arguments, token, new):
        self._ctx = ctx
        self._request = request
        self._metadata = metadata
        books = (Book(new, **kwargs) for kwargs in arguments)
        self._books = {book.Uri: book for book in books}
        self._token = token
        self._new = new
        self._sessions = set()
        print("UserBase.__init__() 1 BaseUrl: %s" % self.BaseUrl)

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
    def Token(self):
        return self._token

    @property
    def New(self):
        return self._new

    @property
    def Url(self):
        return self.Server

    @property
    def BaseUrl(self):
        return self.Scheme + g_sep + self.Server + g_sep + self.Path

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
        self._sessions.add(session)

    def removeSession(self, session):
        self._sessions.discard(session)

    def unquoteUrl(self, url):
        return self.Request.unquoteUrl(url)

    def _isOffLine(self, server):
        return getConnectionMode(self._ctx, server) != ONLINE

    def _isOnLine(self, server):
        return getConnectionMode(self._ctx, server) != OFFLINE

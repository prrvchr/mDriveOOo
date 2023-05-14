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

from collections import OrderedDict
import traceback


class Books(unohelper.Base):
    def __init__(self, ctx, metadata, new):
        self._ctx = ctx
        print("Books.__init__() 1")
        self._books = self._getBooks(metadata, new)
        print("Books.__init__() 2")

    def getBooks(self):
        return self._books.values()

    def hasBook(self, uri):
        return uri in self._books

    def getBook(self, uri):
        return self._books[uri]

    def setBook(self, uri, book):
        self._books[uri] = book

    # Private methods
    def _getBooks(self, metadata, new):
        i = 0
        books = OrderedDict()
        aids, names, tags, tokens = self._getBookMetaData(metadata)
        for uri in metadata.getValue('Uris'):
            # FIXME: If url is None we don't add this addressbook
            if uri is None:
                continue
            print("AddressBook._getBooks() Url: %s - Name: %s - Index: %s - Tag: %s - Token: %s" % (uri, names[i], aids[i], tags[i], tokens[i]))
            books[uri] = Book(self._ctx, aids[i], uri, names[i], tags[i], tokens[i], new)
            i += 1
        return books

    def _getBookMetaData(self, data):
        return data.getValue('Aids'), data.getValue('Names'), data.getValue('Tags'), data.getValue('Tokens')


class Book(unohelper.Base):
    def __init__(self, ctx, bid, uri, name, tag, token, new=False):
        self._ctx = ctx
        self._id = bid
        self._uri = uri
        self._name = name
        self._tag = tag
        self._token = token
        self._new = new

    @property
    def Id(self):
        return self._id
    @property
    def Uri(self):
        return self._uri
    @property
    def Name(self):
        return self._name
    @property
    def Tag(self):
        return self._tag
    @property
    def Token(self):
        return self._token

    def isNew(self):
        new = self._new
        self._new = False
        return new

    def hasNameChanged(self, name):
        return self._name != name

    def setName(self, name):
        self.Name = name

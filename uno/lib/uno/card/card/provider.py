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

from .book import Book

from ..cardtool import getSqlException

from ..oauth2 import getRequest

from ..dbtool import getDateTimeFromString

import traceback


class Provider(object):
    def __init__(self, ctx):
        self._ctx = ctx

    # Currently only vCardOOo supports multiple address books
    def supportAddressBook(self):
        return False

    # Currently only vCardOOo does not supports group
    def supportGroup(self):
        return True

    def parseDateTime(self, timestamp):
        datetime = uno.createUnoStruct('com.sun.star.util.DateTime')
        try:
            dt = parser.parse(timestamp)
        except parser.ParserError:
            pass
        else:
            datetime.Year = dt.year
            datetime.Month = dt.month
            datetime.Day = dt.day
            datetime.Hours = dt.hour
            datetime.Minutes = dt.minute
            datetime.Seconds = dt.second
            datetime.NanoSeconds = dt.microsecond * 1000
            datetime.IsUTC = dt.tzinfo == tz.tzutc()
        return datetime

    # Method called from User.__init__()
    # This main method call Request with OAuth2 mode
    def getRequest(self, url, name):
        return getRequest(self._ctx, url, name)

    # Need to be implemented method
    def insertUser(self, source, database, request, scheme, server, name, pwd):
        raise NotImplementedError

    # Method called from DataSource.getConnection()
    def initAddressbooks(self, source, database, user):
        raise NotImplementedError

    def initUserBooks(self, source, database, user, books):
        count = 0
        modified = False
        for uri, name, tag, token in books:
            print("Provider.initUserBooks() 1 Name: %s - Uri: %s - Tag: %s - Token: %s" % (name, uri, tag, token))
            if user.Books.hasBook(uri):
                book = user.Books.getBook(uri)
                if book.hasNameChanged(name):
                    database.updateAddressbookName(book.Id, name)
                    book.setName(name)
                    modified = True
                    print("Provider.initUserBooks() 2 %s" % (name, ))
            else:
                newid = database.insertBook(user.Id, uri, name, tag, token)
                book = Book(self._ctx, True, Book=newid, Uri=uri, Name=name, Tag=tag, Token=token)
                user.Books.setBook(uri, book)
                modified = True
                print("Provider.initUserBooks() 3 %s - %s - %s" % (book.Id, name, uri))
            self.initUserGroups(database, user, book)
            count += 1
        print("Provider.initUserBooks() 4")
        if not count:
            cls, mtd = 'Provider', 'initUserBooks()'
            raise getSqlException(self._ctx, source, 1006, 1611, cls, mtd, user.Name, user.Server)
        if modified and self.supportAddressBook():
            database.initAddressbooks(user)

    def initUserGroups(self, database, user, book):
        raise NotImplementedError

    def firstPullCard(self, database, user, addressbook, pages, count):
        raise NotImplementedError

    def pullCard(self, database, user, addressbook, pages, count):
        raise NotImplementedError

    def parseCard(self, database):
        raise NotImplementedError

    def raiseForStatus(self, source, cls, mtd, response, user):
        name = response.Parameter.Name
        url = response.Parameter.Url
        status = response.StatusCode
        msg = response.Text
        response.close()
        raise getSqlException(self._ctx, source, 1006, 1601, cls, mtd,
                              name, status, user, url, msg)

    def getLoggerArgs(self, response, mtd, parameter, user):
        status = response.StatusCode
        msg = response.Text
        response.close()
        return ['Provider', mtd, 201, parameter.Name, status, user, parameter.Url, msg]

    # Can be overwritten method
    def syncGroups(self, database, user, addressbook, pages, count):
        return pages, count, None


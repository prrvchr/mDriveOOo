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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from .cardtool import getSqlException

from .oauth20 import getRequest

from dateutil import parser
from dateutil import tz

import traceback

class Provider():
    def __init__(self, ctx, src):
        self._cls = 'Provider'
        self._ctx = ctx
        self._src = src

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


    # Method called from User.__init__()
    def insertUser(self, logger, database, request, scheme, server, name, pwd):
        mtd = 'insertUser'
        logger.logprb(INFO, self._cls, mtd, 1301, name)
        userid = self.getNewUserId(request, scheme, server, name, pwd)
        logger.logprb(INFO, self._cls, mtd, 1302, userid, name)
        return database.insertUser(userid, scheme, server, '', name)

    # Need to be implemented method
    def getNewUserId(self, request, scheme, server, name, pwd):
        raise NotImplementedError

    # Method called from DataSource.getConnection()
    def initAddressbooks(self, logger, database, user):
        mtd = 'initAddressbooks'
        logger.logprb(INFO, self._cls, mtd, 1321, user.Name)
        books = self.getAddressbooks(logger, database, user)
        self._initUserBooks(logger, database, user, books)
        logger.logprb(INFO, self._cls, mtd, 1322, user.Name)

    def getAddressbooks(self, logger, database, user):
        raise NotImplementedError

    def _initUserBooks(self, logger, database, user, books):
        count = 0
        modified = False
        mtd = '_initUserBooks'
        logger.logprb(INFO, self._cls, mtd, 1331, user.Name)
        for uri, name, tag, token in books:
            if user.hasBook(uri):
                book = user.getBook(uri)
                if book.isRenamed(name):
                    database.updateAddressbookName(book.Id, name)
                    book.setName(name)
                    modified = True
            else:
                args = database.insertBook(user.Id, uri, name, tag, token)
                book = user.setNewBook(uri, **args)
                modified = True
            self.initUserGroups(logger, database, user, book)
            count += 1
        if not count:
            raise getSqlException(self._ctx, self._src, 1006, 1611, self._cls, 'initUserBooks', user.Name, user.Server)
        if modified and self.supportAddressBook():
            database.initAddressbooks(user)
        logger.logprb(INFO, self._cls, mtd, 1332, user.Name)

    def initUserGroups(self, logger, database, user, book):
        mtd = 'initUserGroups'
        logger.logprb(INFO, self._cls, mtd, 1341, book.Name)
        groups = self.getUserGroups(logger, database, user, book)
        self._initUserGroup(logger, database, user, book, groups)
        logger.logprb(INFO, self._cls, mtd, 1342, book.Name)

    def _initUserGroup(self, logger, database, user, book, groups):
        mtd = 'initUserGroup'
        logger.logprb(INFO, self._cls, mtd, 1351, book.Name)
        for uri, name in groups:
            if book.hasGroup(uri):
                group = book.getGroup(uri)
                if group.isRenamed(name):
                    database.updateGroupName(book.Id, group.Id, name)
                    database.renameGroupView(name, group.Name)
                    group.setName(name)
            else:
                args = database.insertGroup(book.Id, uri, name)
                group = book.setNewGroup(uri, *args)
                database.createGroupView(user, group)
        logger.logprb(INFO, self._cls, mtd, 1352, book.Name)

    def firstPullCard(self, database, user, book, pages, count):
        raise NotImplementedError

    def pullCard(self, database, user, book, pages, count):
        raise NotImplementedError

    def parseCard(self, database):
        raise NotImplementedError

    def raiseForStatus(self, mtd, response, user):
        name = response.Parameter.Name
        url = response.Parameter.Url
        status = response.StatusCode
        msg = response.Text
        response.close()
        raise getSqlException(self._ctx, self._src, 1006, 1601, self._cls, mtd,
                              name, status, user, url, msg)

    def getLoggerArgs(self, response, mtd, parameter, user):
        status = response.StatusCode
        msg = response.Text
        response.close()
        return ['Provider', mtd, 201, parameter.Name, status, user, parameter.Url, msg]

    # Can be overwritten method
    def syncGroups(self, database, user, book, pages, count):
        return pages, count, None


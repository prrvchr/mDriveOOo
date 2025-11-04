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

from com.sun.star.uno import Exception as UnoException

from .database import DataBase

from .provider import Provider

from .card import User

from .card import Replicator

from .card import EventListener
from .card import TerminateListener

from .unotool import getDesktop

from .helper import getSqlException

from .configuration import g_extension

from threading import Event

class DataSource():
    def __init__(self, ctx, source, logger, url):
        self._cls = 'DataSource'
        mtd = '__init__'
        logger.logprb(INFO, self._cls, mtd, 1201)
        self._ctx = ctx
        self._maps = {}
        database = DataBase(ctx, logger, url)
        provider = Provider(ctx, source, database)
        users = {}
        sync = Event()
        self._sync = sync
        self._users = users
        self._database = database
        self._provider = provider
        self._replicator = Replicator(ctx, database, provider, users, sync)
        self._listener = EventListener(self)
        getDesktop(ctx).addTerminateListener(TerminateListener(self._replicator))
        logger.logprb(INFO, self._cls, mtd, 1202)

    @property
    def DataBase(self):
        return self._database

    def isUptoDate(self):
        return self._database.isUptoDate()

    def getDataBaseVersion(self):
        return self._database.Version

# Procedures called by EventListener
    def closeConnection(self, connection):
        name = connection.getMetaData().getUserName()
        if name in self._users:
            user = self._users.get(name)
            user.removeSession(self._database.getSessionId(connection))

# Procedures called by Driver
    def getConnection(self, source, logger, url, scheme, server, account, password=''):
        mtd = 'getConnection'
        uri = self._provider.getUserUri(server, account)
        if uri in self._maps:
            name = self._maps.get(uri)
            user = self._users.get(name)
            if not user.Request.isAuthorized():
                raise getSqlException(self._ctx, source, 1002, 1401, self._cls, mtd, name, g_extension)
        else:
            user = User(self._ctx, source, logger, self._database,
                        self._provider, url, scheme, server, account, password)
            name = user.getName()
        if user.isOnLine():
            try:
                self._provider.initAddressbooks(self._database, user)
            except UnoException as ex:
                e = getSqlException(self._ctx, source, 1001, 1402, self._cls, mtd, name, g_extension)
                e.NextException = ex
                raise e
        connection = self._database.getConnection(name, user.getPassword())
        # XXX: New users are cached only if the connection is successful.
        if not uri in self._maps:
            self._users[name] = user
            self._maps[uri] = name
        user.addSession(self._database.getSessionId(connection))
        # User and/or AddressBooks has been initialized and the connection to the database is done...
        # We can start the database replication in a background task.
        self._sync.set()
        connection.addEventListener(self._listener)
        return connection


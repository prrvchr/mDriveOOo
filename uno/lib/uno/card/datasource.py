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

from com.sun.star.sdbc import SQLException

from com.sun.star.uno import Exception as UnoException

from .database import DataBase

from .provider import Provider

from .setup import SetupCheck

from .card import EventListener
from .card import User

from .runner import DispatchListener

from .card import getSqlException

from .dbinit import getDataSourceUrl
# from .setup import showSetup

from .helper import getExtensions
from .helper import startReplication

from .jdbcdriver import g_agent
from .jdbcdriver import g_java
from .jdbcdriver import g_protocol
from .jdbcdriver import g_script
from .jdbcdriver import g_service

from .configuration import g_extension

import json


class DataSource():
    def __init__(self, ctx, logger, source):
        self._cls = 'DataSource'
        mtd = '__init__'
        logger.logprb(INFO, self._cls, mtd, 1201)
        self._ctx = ctx
        self._maps = {}
        database = DataBase(ctx)
        provider = Provider(ctx, database, source)
        self._users = {}
        self._database = database
        self._provider = provider
        self._listener = EventListener(self)
        self._checked = False
        logger.logprb(INFO, self._cls, mtd, 1202)

    @property
    def DataBase(self):
        return self._database

# Procedures called by EventListener
    def closeConnection(self, connection):
        name = connection.getMetaData().getUserName()
        if name in self._users:
            user = self._users.get(name)
            user.removeSession(self._database.getSessionId(connection))

# Procedures called by DispatchListener
    def dispatchFinished(self, notification):
        print("DataSource.dispatchFinished() state: %s - result: %s" % (notification.State, notification.Result))

# Procedures called by Driver
    def getConnection(self, source, logger, url, scheme, server, username, token=''):
        print("DataSource.getConnection() 1")
        if not self._checked:
            self._checkSetup()
        mtd = 'getConnection'
        uri = self._provider.getUserUri(server, username)
        if uri in self._maps:
            print("DataSource.getConnection() 2")
            name = self._maps.get(uri)
            user = self._users.get(name)
            if not user.Request.isAuthorized():
                raise getSqlException(self._ctx, source, 1002, 1401, self._cls, mtd, name, g_extension)
        else:
            print("DataSource.getConnection() 3")
            user = User(self._ctx, source, logger, self._database, self._provider, scheme, url, server, username, token)
            name = user.getName()
        if user.isOnLine():
            try:
                self._provider.initAddressbooks(self._database, user)
            except UnoException as ex:
                e = getSqlException(self._ctx, source, 1001, 1402, self._cls, mtd, name, g_extension)
                e.NextException = ex
                raise e
        connection = self._database.getConnection(name)
        # XXX: New users are cached only if the connection is successful.
        if uri not in self._maps:
            self._users[name] = user
            self._maps[uri] = name
        user.addSession(self._database.getSessionId(connection))
        # User and/or AddressBooks has been initialized and the connection to the database is done...
        # We can start the database replication in a background task.
        connection.addEventListener(self._listener)
        print("DataSource.getConnection() 4")
        # showSetup(self._ctx, Dispatch=DispatchListener(self), Mode=0)
        startReplication(self._ctx, Dispatch=DispatchListener(self), Args=self._getUserSessions())
        print("DataSource.getConnection() 5")
        return connection

    def _getUserSessions(self):
        users = []
        for user in self._users.values():
            users.append({'url': user.Url, 'server': user.Server, 'name': user.Name, 'token': user.Token, 'new': user.New})
        return json.dumps(users)

    def _checkSetup(self):
        java = g_extension, g_java, g_script
        agent = g_service, g_protocol, g_agent
        database = getDataSourceUrl(self._ctx)
        state = SetupCheck.getState(self._ctx, database=database, java=java, agent=agent, python=True, extensions=getExtensions())
        if not state.runnable:
            raise SQLException(state.getMessage(self._ctx), self, '08001', state.step, None)
        self._checked = True

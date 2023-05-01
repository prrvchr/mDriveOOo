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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.sdb.CommandType import QUERY

from .addressbook import AddressBook
from .replicator import Replicator
from .user import User

from .listener import EventListener
from .listener import TerminateListener

from ..unotool import getDesktop
from ..unotool import getUrl

from ..configuration import g_identifier
from ..configuration import g_group
from ..configuration import g_compact
from ..configuration import g_scheme

import traceback


class DataSource(unohelper.Base):
    def __init__(self, ctx, database, provider):
        self._ctx = ctx
        self._maps = {}
        self._users = {}
        self._listener = EventListener(self)
        self._database = database
        self._provider = provider
        self._replicator = Replicator(ctx, self._database, self._provider, self._users)
        listener = TerminateListener(self._replicator)
        getDesktop(ctx).addTerminateListener(listener)

# Procedures called by EventListener
    def closeConnection(self, connection):
        name = connection.getMetaData().getUserName()
        if name in self._users:
            user = self._users.get(name)
            user.removeSession(self._database.getSessionId(connection))
            print("DataSource.closeConnection() 1: %s - %s" % (len(self._users), name))
        if not self._hasSession():
            self._replicator.stop()
        print("DataSource.closeConnection() 2")

# Procedures called by Driver
    def getConnection(self, scheme, server, account, password):
        try: 
            print("DataSource.getConnection () 1")
            uri = self._provider.getUserUri(server, account)
            if uri in self._maps:
                name = self._maps.get(uri)
                user = self._users.get(name)
            else:
                user = User(self._ctx, self._database, self._provider, scheme, server, account, password)
                name = user.getName()
                self._users[name] = user
                self._maps[uri] = name
            print("DataSource.getConnection () 2")
            if user.isOnLine():
                self._provider.initAddressbooks(self._database, user)
            print("DataSource.getConnection () 3")
            connection = self._database.getConnection(name, user.getPassword())
            print("DataSource.getConnection () 4")
            user.addSession(self._database.getSessionId(connection))
            print("DataSource.getConnection () 5")
            # User and/or AddressBooks has been initialized and the connection to the database is done...
            # We can start the database replication in a background task.
            self._replicator.start()
            print("DataSource.getConnection () 6")
            connection.addEventListener(self._listener)
            print("DataSource.getConnection () 7")
            return connection
        except Exception as e:
            msg = "DataSource.getConnection() Error: %s" % traceback.format_exc()
            print(msg)

    def _hasSession(self):
        for user in self._users.values():
            if user.hasSession():
                return True
        return False

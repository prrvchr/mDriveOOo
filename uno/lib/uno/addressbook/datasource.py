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

from .configuration import g_identifier
from .configuration import g_group
from .configuration import g_compact

from .database import DataBase
from .provider import Provider
from .user import User
from .replicator import Replicator

from .listener import EventListener
from .listener import TerminateListener

from .unotool import getDesktop

import traceback


class DataSource(unohelper.Base):
    def __init__(self, ctx):
        self._ctx = ctx
        self._users = {}
        self._connections = 0
        self._listener = EventListener(self)
        self._provider = Provider(ctx)
        self._database = DataBase(ctx)
        self._replicator = Replicator(ctx, self._database, self._provider, self._users)
        listener = TerminateListener(self._replicator)
        desktop = getDesktop(ctx)
        desktop.addTerminateListener(listener)

    def getConnection(self, user, password):
        connection = self._database.getConnection(user, password)
        connection.addEventListener(self._listener)
        self._connections += 1
        return connection

    def stopReplicator(self):
        if self._connections > 0:
            self._connections -= 1
        print("DataSource.disposeConnection() %s" % self._connections)
        if self._connections == 0:
            self._replicator.stop()

    def setUser(self, name, password):
        if name not in self._users:
            user = User(self._ctx, self._database, self._provider, name, password)
            self._users[name] = user
        # User has been initialized and the connection to the database is done...
        # We can start the database replication in a background task.
        self._replicator.start()

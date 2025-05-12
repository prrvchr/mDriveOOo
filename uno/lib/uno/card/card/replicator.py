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

from ..unotool import getConfiguration

from ..configuration import g_identifier
from ..configuration import g_synclog

from ..logger import getLogger

from threading import Thread
import traceback


class Replicator(Thread):
    def __init__(self, ctx, database, provider, users, sync):
        Thread.__init__(self)
        self._cls = 'Replicator'
        self._ctx = ctx
        self._database = database
        self._provider = provider
        self._config = getConfiguration(ctx, g_identifier, False)
        self._users = users
        self._sync = sync
        self._canceled = False
        self.start()

    def dispose(self):
        self._canceled = True
        self._sync.set()
        self.join()

    def run(self):
        mtd = 'run'
        logger = getLogger(self._ctx, g_synclog, self._cls)
        timeout = self._config.getByName('ReplicateTimeout')
        try:
            logger.logprb(INFO, self._cls, mtd, 101)
            while not self._canceled:
                self._sync.clear()
                self._sync.wait(timeout)
                if self._canceled:
                    continue
                if self._hasConnectedUser():
                    count = self._syncCard(logger)
                    if count > 0:
                        count = self._provider.parseCard(self._database)
                        if self._provider.supportGroup():
                            self._syncGroup(logger)
                    self._database.dispose()
                    code = 102
                else:
                    code = 103
                timeout = self._config.getByName('ReplicateTimeout')
                logger.logprb(INFO, self._cls, mtd, code, timeout // 60)
            logger.logprb(INFO, self._cls, mtd, 104)
        except UnoException as e:
            logger.logprb(SEVERE, self._cls, mtd, 105, e.Message)
        except Exception as e:
            logger.logprb(SEVERE, self._cls, mtd, 106, e, traceback.format_exc())

    def _syncCard(self, logger):
        mtd = '_syncCard'
        users = pages = count = 0
        logger.logprb(INFO, self._cls, mtd, 111)
        try:
            for user in self._users.values():
                if self._canceled:
                    break
                if user.isOffLine():
                    logger.logprb(INFO, self._cls, mtd, 112)
                else:
                    users += 1
                    logger.logprb(INFO, self._cls, mtd, 113, user.Name)
                    for book in user.getBooks():
                        if self._canceled:
                            break
                        if book.isNew():
                            pages, count, args = self._provider.firstPullCard(self._database, user, book, pages, count)
                        else:
                            pages, count, args = self._provider.pullCard(self._database, user, book, pages, count)
                        if args:
                            logger.logprb(SEVERE, *args)
                        else:
                            book.resetNew()
                    logger.logprb(INFO, self._cls, mtd, 114, user.Name)
        except UnoException as e:
            logger.logprb(SEVERE, self._cls, mtd, 115, e.Message)
        except Exception as e:
            logger.logprb(SEVERE, self._cls, mtd, 116, e, traceback.format_exc())
        logger.logprb(INFO, self._cls, mtd, 117, users, pages, count)
        return count

    def _syncGroup(self, logger):
        mtd = '_syncGroup'
        users = pages = count = 0
        logger.logprb(INFO, self._cls, mtd, 121)
        try:
            for user in self._users.values():
                if self._canceled:
                    break
                if user.isOffLine():
                    logger.logprb(INFO, self._cls, mtd, 122)
                else:
                    users += 1
                    logger.logprb(INFO, self._cls, mtd, 123, user.Name)
                    for book in user.getBooks():
                        if self._canceled:
                            break
                        pages, count, args = self._provider.syncGroups(self._database, user, book, pages, count)
                        if args:
                            logger.logprb(SEVERE, *args)
                        elif not self._canceled:
                            self._database.syncGroups(user)
                    logger.logprb(INFO, self._cls, mtd, 124, user.Name)
        except UnoException as e:
            logger.logprb(SEVERE, self._cls, mtd, 125, e.Message)
        except Exception as e:
            logger.logprb(SEVERE, self._cls, mtd, 126, e, traceback.format_exc())
        logger.logprb(INFO, self._cls, mtd, 127, users, pages, count)

    def _hasConnectedUser(self):
        for user in self._users.values():
            if user.hasSession():
                return True
        return False


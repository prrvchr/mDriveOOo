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

from .unotool import getConfiguration

from .configuration import g_identifier
from .configuration import g_synclog

from .logger import getLogger
g_basename = 'Replicator'

from threading import Thread
from threading import Event
import traceback


class Replicator(unohelper.Base):
    def __init__(self, ctx, database, provider, users):
        self._ctx = ctx
        self._database = database
        self._provider = provider
        self._users = users
        self._started = Event()
        self._paused = Event()
        self._disposed = Event()
        self._thread = Thread(target=self._replicate)
        self._thread.start()

    # XRestReplicator
    def dispose(self):
        print("replicator.dispose() 1")
        self._disposed.set()
        self._started.set()
        self._paused.set()
        self._thread.join()
        print("replicator.dispose() 2")

    def stop(self):
        print("replicator.stop() 1")
        self._started.clear()
        self._paused.set()
        print("replicator.stop() 2")

    def start(self):
        self._started.set()
        self._paused.set()

    def _canceled(self):
        return False

    def _canceled1(self):
        return self._disposed.is_set() or not self._started.is_set()

    def _getReplicateTimeout(self):
        configuration = getConfiguration(self._ctx, g_identifier, False)
        timeout = configuration.getByName('ReplicateTimeout')
        return timeout

    def _replicate(self):
        print("replicator.run()1")
        try:
            print("replicator.run()1 begin ****************************************")
            logger = getLogger(self._ctx, g_synclog, g_basename)
            while not self._disposed.is_set():
                print("replicator.run()2 wait to start ****************************************")
                self._started.wait()
                if not self._disposed.is_set():
                    print("replicator.run()3 synchronize started ****************************************")
                    pages, total = self._synchronize(logger)
                    logger.logprb(INFO, 'Replicator', '_replicate()', 101, pages, total)
                    if total > 0:
                        print("replicator.run()4 synchronize started CardSync.jar")
                        pages, total = self._finalize(logger)
                        print("replicator.run()5 synchronize ended CardSync.jar")
                        logger.logprb(INFO, 'Replicator', '_replicate()', 102, pages, total)
                    self._database.dispose()
                    print("replicator.run()6 synchronize ended Pages: %s - Total: %s *******************************************" % (pages, total))
                    if self._started.is_set():
                        print("replicator.run()7 start waitting *******************************************")
                        self._paused.clear()
                        timeout = self._getReplicateTimeout()
                        self._paused.wait(timeout)
                        print("replicator.run()8 end waitting *******************************************")
            print("replicator.run()9 canceled *******************************************")
        except Exception as e:
            msg = "Replicator run(): Error: %s" % traceback.print_exc()
            print(msg)

    def _synchronize(self, logger):
        pages = count = 0
        for user in self._users.values():
            if not user.hasSession():
                continue
            if user.isOffLine():
                logger.logprb(INFO, 'Replicator', '_synchronize()', 111)
            elif self._canceled():
                break
            logger.logprb(INFO, 'Replicator', '_synchronize()', 112, user.Name)
            for book in user.getBooks():
                if self._canceled():
                    break
                if book.isNew():
                    print("Replicator._syncUser() New AddressBook Path: %s" % book.Uri)
                    pages, count = self._provider.firstPullCard(self._database, user, book, pages, count)
                else:
                    pages, count = self._provider.pullCard(self._database, user, book, pages, count)
            logger.logprb(INFO, 'Replicator', '_synchronize()', 113, user.Name)
        return pages, count

    def _finalize(self, logger):
        pages = count = 0
        self._provider.parseCard(self._database)
        for user in self._users.values():
            if not user.hasSession():
                continue
            if user.isOffLine():
                logger.logprb(INFO, 'Replicator', '_finalize()', 121)
            elif self._canceled():
                break
            logger.logprb(INFO, 'Replicator', '_finalize()', 122, user.Name)
            for book in user.getBooks():
                if self._canceled():
                    break
                pages, count = self._provider.syncGroups(self._database, user, book, pages, count)
            logger.logprb(INFO, 'Replicator', '_finalize()', 123, user.Name)
        self._database.syncGroups()
        return pages, count


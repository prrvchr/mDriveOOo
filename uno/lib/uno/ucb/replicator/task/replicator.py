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

from com.sun.star.frame.DispatchResultState import FAILURE
from com.sun.star.frame.DispatchResultState import SUCCESS

from com.sun.star.frame import DispatchResultEvent

from com.sun.star.uno import Exception as UnoException

from ...database import DataBase

from ...provider import Provider

from ...runner import Task

from ...unotool import getNamedValue
from ...unotool import getJobArguments

import json


class Replicator(Task):
    def __init__(self, ctx, callback, data):
        super().__init__(ctx, 'Replicator')
        print("Replicator.__init__() 1")
        self._job = None
        self._listener = None
        self._timeout = None
        self._database = None
        self._provider = None
        self.callback = callback
        self.total = 2
        self.status = 'SUCCESS'
        self.error_cause = None

        self.stats_card = {'users': 0, 'pages': 0, 'count': 0}
        self.stats_group = {'users': 0, 'pages': 0, 'count': 0}
        self.steps = self.getSteps(ctx, data)

    def getSteps(self, ctx, data):
        size = len(data)
        yield self.getStepInitialize(len(data))
        for job, listener, arguments in data:
            kwargs = getJobArguments(arguments)
            yield from self._getJobStepsCount(size, ctx, job, listener, **kwargs)
            yield from self.getJobSteps(ctx, job, listener, **kwargs)
        yield (10104, (), self._finalize)

    def _getJobStepsCount(self, size, ctx, job, listener, **kwargs):
        total = sum(1 for _ in self.getJobSteps(ctx, job, listener, **kwargs)) * size
        yield (10102, (total, ), self._setStepsCount, total)

    def getJobSteps(self, ctx, _job, _listener, /, args, **_kwargs):
        # --- PHASE 1 : SYNCHRONISATION DES CARTES
        users = set()
        sessions = json.loads(args)
        if self._database is None:
            self._database = DataBase(ctx)
        if self._provider is None:
            self._provider = Provider(ctx, self._database)
        for _session in sessions:
            # user = User(ctx, self._provider, self._database, **session)
            user = None
            if user.isOffLine():
                continue
            users.add(user)
            for book in user.getBooks():
                if book.isNew():
                    yield (11103, (user.Name,), self._execFirstPull, user, book)
                else:
                    yield (11103, (user.Name,), self._execPull, user, book)

        yield (11101, (), self._execParseCard)

        # --- PHASE 2 : SYNCHRONISATION DES GROUPES ---
        if self._provider.supportGroup():
            for user in users:
                if user.isOffLine():
                    continue
                for book in user.getBooks():
                    yield (12103, (user.Name,), self._execSyncGroup, user, book)
                    yield (12104, (user.Name,), self._execDbSyncGroup, user)

    def _execFirstPull(self, user, book):
        self.stats_card['users'] += 1
        p, c, args = self._provider.firstPullCard(self._database, user, book, self.stats_card['pages'], self.stats_card['count'])
        if args:
            raise UnoException(f'Erreur FirstPull : {args}')
        self.stats_card['pages'] = p
        self.stats_card['count'] = c
        book.resetNew()

    def _execPull(self, user, book):
        self.stats_card['users'] += 1
        p, c, args = self._provider.pullCard(self._database, user, book, self.stats_card['pages'], self.stats_card['count'])
        if args:
            raise UnoException(f'Erreur Pull : {args}')
        self.stats_card['pages'] = p
        self.stats_card['count'] = c
        book.resetNew()

    def _execParseCard(self):
        if self.stats_card['count'] > 0:
            self._provider.parseCard(self._database)

    def _execSyncGroup(self, user, book):
        self.stats_group['users'] += 1
        p, c, args = self._provider.syncGroups(self._database, user, book, self.stats_group['pages'], self.stats_group['count'])
        if args:
            raise UnoException(f'Erreur SyncGroup : {args}')
        self.stats_group['pages'] = p
        self.stats_group['count'] = c

    def _execDbSyncGroup(self, user):
        self._database.syncGroups(user)

    def getStepInitialize(self, size):
        return (10101, (size, ), self._init)

    def getStepCountSteps(self, total):
        return (10102, (total, ), self._setStepsCount, total)

    def getStepFinalize(self):
        return (10104, (), self._finalize)

    def callback(self, success=True, error=None):
        result = DispatchResultEvent()
        result.Result = self.status
        if not success:
            result.State = FAILURE
            self.error_cause = error
        else:
            result.State = SUCCESS
        result = getNamedValue('SendDispatchResult', result)

        if self._listener is not None:
            self._listener.jobFinished(self._job, (result, ))

    def _finalize(self):
        if self._database:
            self._database.dispose()
        self._database = None

    def _init(self):
        pass

    def _setStepsCount(self, total):
        self.total += total

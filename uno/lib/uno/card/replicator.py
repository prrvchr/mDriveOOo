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

from .database import DataBase

from .provider import Provider

from .runner import Task

from .user import User

from .unotool import getNamedValue

import json


class Replicator(Task):
    def __init__(self, ctx, job, listener, timeout, /, dispatch, args):
        super().__init__(ctx, 'Replicator')
        print("Replicator.__init__() soure: %s - url: %s - sessions: %s" % (args, ))
        self._job = job
        self._listener = listener
        self._timeout = timeout
        self._database = None

        self.status = 'SUCCESS'
        self.error_cause = None

        self.stats_card = {'users': 0, 'pages': 0, 'count': 0}
        self.stats_group = {'users': 0, 'pages': 0, 'count': 0}
        self.steps = self.getSteps(ctx, args)

    def getSteps(self, ctx, args):
        # --- PHASE 1 : SYNCHRONISATION DES CARTES
        users = set()
        sessions = json.load(args)
        self._database = DataBase(ctx)
        provider = Provider(ctx, self._database)
        for session in sessions:
            user = User(ctx, provider, self._database, **session)
            if user.isOffLine():
                continue
            users.add(user)
            for book in user.getBooks():
                if book.isNew():
                    yield (11103, (user.Name,), self._execFirstPull, provider, user, book)
                else:
                    yield (11103, (user.Name,), self._execPull, provider, user, book)

        yield (11101, (), self._execParseCard, provider)

        # --- PHASE 2 : SYNCHRONISATION DES GROUPES ---
        if provider.supportGroup():
            for user in users:
                if user.isOffLine():
                    continue
                for book in user.getBooks():
                    yield (12103, (user.Name,), self._execSyncGroup, provider, user, book)
                    yield (12104, (user.Name,), self._execDbSyncGroup, user)
        yield (10104, (), self._finalize)

    def _execFirstPull(self, provider, user, book):
        self.stats_card['users'] += 1
        p, c, args = provider.firstPullCard(self._database, user, book, self.stats_card['pages'], self.stats_card['count'])
        if args:
            raise UnoException(f'Erreur FirstPull : {args}')
        self.stats_card['pages'] = p
        self.stats_card['count'] = c
        book.resetNew()

    def _execPull(self, provider, user, book):
        self.stats_card['users'] += 1
        p, c, args = provider.pullCard(self._database, user, book, self.stats_card['pages'], self.stats_card['count'])
        if args:
            raise UnoException(f'Erreur Pull : {args}')
        self.stats_card['pages'] = p
        self.stats_card['count'] = c
        book.resetNew()

    def _execParseCard(self, provider):
        if self.stats_card['count'] > 0:
            provider.parseCard(self._database)

    def _execSyncGroup(self, provider, user, book):
        self.stats_group['users'] += 1
        p, c, args = provider.syncGroups(self._database, user, book, self.stats_group['pages'], self.stats_group['count'])
        if args:
            raise UnoException(f'Erreur SyncGroup : {args}')
        self.stats_group['pages'] = p
        self.stats_group['count'] = c

    def _execDbSyncGroup(self, user):
        self._database.syncGroups(user)

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

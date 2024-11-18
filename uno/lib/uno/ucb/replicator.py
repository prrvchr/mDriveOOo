#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-24 https://prrvchr.github.io                                  ║
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

from com.sun.star.ucb.ChangeAction import INSERT
from com.sun.star.ucb.ChangeAction import UPDATE
from com.sun.star.ucb.ChangeAction import MOVE
from com.sun.star.ucb.ChangeAction import DELETE

from com.sun.star.ucb.ContentProperties import TITLE
from com.sun.star.ucb.ContentProperties import CONTENT
from com.sun.star.ucb.ContentProperties import TRASHED

from .unotool import getConfiguration

from .dbtool import currentDateTimeInTZ
from .dbtool import getDateTimeToString

from .database import DataBase

from .logger import getLogger

from .configuration import g_identifier
from .configuration import g_synclog

g_class = 'Replicator'

from threading import Thread
import traceback


class Replicator(Thread):
    def __init__(self, ctx, url, provider, users, sync, lock):
        mtd = '__init__'
        try:
            Thread.__init__(self)
            self._ctx = ctx
            self._full = 2
            self._users = users
            self._sync = sync
            self._lock = lock
            self._canceled = False
            self._fullPull = False
            self._provider = provider
            self._config = getConfiguration(ctx, g_identifier, False)
            self._logger = getLogger(ctx, g_synclog, g_class)
            self._database = DataBase(ctx, self._logger, url)
            sync.clear()
            self.start()
        except Exception as e:
            self._logger.logprb(SEVERE, g_class, mtd, 102, e, traceback.format_exc())
        else:
            self._logger.logprb(INFO, g_class, mtd, 101)

    def fullPull(self):
        return self._fullPull

    def cancel(self):
        self._canceled = True
        self._sync.set()
        self.join()
        self._database.dispose()

    def run(self):
        mtd = 'run'
        try:
            self._logger.logprb(INFO, g_class, mtd, 111, self._provider.Scheme)
            while not self._canceled:
                timeout = self._getReplicateTimeout()
                self._logger.logprb(INFO, g_class, mtd, 112, self._provider.Scheme, timeout // 60)
                self._sync.wait(timeout)
                self._synchronize()
                self._sync.clear()
            self._logger.logprb(INFO, g_class, mtd, 113, self._provider.Scheme)
        except Exception as e:
            self._logger.logprb(SEVERE, g_class, mtd, 114, self._provider.Scheme, e, traceback.format_exc())

    def _synchronize(self):
        mtd = '_synchronize'
        policy = self._getPolicy()
        self._logger.logprb(INFO, g_class, mtd, 121)
        if policy == self._getSynchronizePolicy('NONE_IS_MASTER'):
            self._logger.logprb(INFO, g_class, mtd, 122)
        elif self._provider.isOffLine():
            self._logger.logprb(INFO, g_class, mtd, 123)
        else:
            reset = self._getResetSetting()
            full = reset == self._full
            share = self._getShareSetting()
            for user in self._users.values():
                self._synchronizeUser(user, policy, reset, full, share)
        self._logger.logprb(INFO, g_class, mtd, 124)

    def _synchronizeUser(self, user, policy, reset, full, share):
        mtd = '_synchronizeUser'
        self._logger.logprb(INFO, g_class, mtd, 131, user.Name)
        end = currentDateTimeInTZ()
        sync = False
        if self._isNewUser(user) or reset:
            sync = self._initUser(user, full, share)
        elif policy == self._getSynchronizePolicy('SERVER_IS_MASTER'):
            if self._pullUser(user):
                sync = self._pushUser(user, end)
        elif policy == self._getSynchronizePolicy('CLIENT_IS_MASTER'):
            if self._pushUser(user, end):
                sync = self._pullUser(user)
        if sync:
            self._logger.logprb(INFO, g_class, mtd, 132, user.Name)

    def _checkNewIdentifier(self, user):
        mtd = '_checkNewIdentifier'
        if not self._provider.GenerateIds:
            user.CanAddChild = True
            return
        if self._provider.isOffLine():
            user.CanAddChild = self._database.countIdentifier(user.Id) > 0
            return
        count = self._database.countIdentifier(user.Id)
        if count < min(self._provider.IdentifierRange):
            total, msg = self._provider.pullNewIdentifiers(user)
            if total:
                self._logger.logprb(INFO, g_class, mtd, 211, user.Name, count, total)
            else:
                self._logger.logprb(INFO, g_class, mtd, 212, user.Name, msg)
        # Need to postpone the creation authorization after this verification...
        user.CanAddChild = True

    def _initUser(self, user, full, share):
        mtd = '_initUser'
        try:
            # This procedure is launched only once for each new user
            # This procedure corresponds to the initial pull for a new User (ie: without Token)
            self._logger.logprb(INFO, g_class, mtd, 221, user.Name)
            # In order to make the creation of files or directories possible quickly,
            # it is necessary to run the verification of the identifiers first.
            self._checkNewIdentifier(user)
            count, download, pages, count2, download2, pages2, token = self._provider.firstPull(user, full)
            if share:
                self._logger.logprb(INFO, g_class, mtd, 222, user.Name, count, download, pages)
            self._logger.logprb(INFO, g_class, mtd, 223, user.Name, count2, download2, pages2, token)
            self._provider.initUser(user, token)
            user.TimeStamp = currentDateTimeInTZ()
            user.releaseLock()
            self._fullPull = True
            self._logger.logprb(INFO, g_class, mtd, 224, user.Name)
            return True
        except Exception as e:
            self._logger.logprb(SEVERE, g_class, mtd, 225, e, traceback.format_exc())
            return False

    def _pullUser(self, user):
        mtd = '_pullUser'
        try:
            if self._canceled:
                return False
            self._logger.logprb(INFO, g_class, mtd, 201, user.Name)
            self._checkNewIdentifier(user)
            count, download, pages, token = self._provider.pullUser(user)
            self._logger.logprb(INFO, g_class, mtd, 202, user.Name, count, download, pages, token)
            if token:
                user.Token = token
            self._logger.logprb(INFO, g_class, mtd, 203, user.Name)
            return True
        except Exception as e:
            self._logger.logprb(SEVERE, g_class, mtd, 204, e, traceback.format_exc())
            return False

    def _pushUser(self, user, end):
        mtd = '_pushUser'
        # This procedure corresponds to the push of changes for the entire database 
        # for a user, in chronological order, from 'start' to 'end'...
        try:
            if self._canceled:
                return False
            self._logger.logprb(INFO, g_class, mtd, 301, user.Name)
            items = []
            start = user.TimeStamp
            for item in self._database.getPushItems(user.Id, start, end):
                if self._canceled:
                    break
                metadata = self._database.getMetaData(user.Id, user.RootId, item.get('Id'))
                pushed = self._pushItem(user, item, metadata, start, end)
                if pushed is None:
                    modified = getDateTimeToString(metadata.get('DateModified'))
                    self._logger.logprb(SEVERE, g_class, mtd, 302, metadata.get('Title'), modified, metadata.get('Id'))
                    break
                items.append(pushed)
            else:
                self._logger.logprb(INFO, g_class, mtd, 303, user.Name, len(items))
                # XXX: User was pushed, we update user timestamp if needed
                timestamp = self._database.updatePushItems(user.Id, items)
                if timestamp is not None:
                    user.TimeStamp = timestamp
                self._logger.logprb(INFO, g_class, mtd, 304, user.Name)
                return True
            return False
        except Exception as e:
            self._logger.logprb(SEVERE, g_class, mtd, 305, e, traceback.format_exc())
            return False

    def _pushItem(self, user, item, metadata, start, end):
        mtd = '_pushItem'
        try:
            itemid = item.get('Id')
            newid = None
            timestamp = item.get('TimeStamp')
            action = item.get('ChangeAction')
            chunk, retry, delay = self._getUploadSetting()
            # If the synchronization of an INSERT or an UPDATE fails
            # then the user's TimeStamp will not be updated
            # INSERT procedures, new files and folders are synced here.
            if action & INSERT:
                created = getDateTimeToString(metadata.get('DateCreated'))
                if metadata.get('IsFolder'):
                    newid = self._provider.createFolder(user, itemid, metadata)
                    self._logger.logprb(INFO, g_class, mtd, 311, metadata.get('Title'), created)
                elif metadata.get('IsDocument'):
                    newid, args = self._provider.uploadFile(314, user, itemid, metadata, created, chunk, retry, delay, True)
                    self._logger.logprb(INFO, g_class, mtd, *args)
            # UPDATE procedures, only a few properties are synchronized: Title and content(ie: Size or DateModified)
            elif action & UPDATE:
                for property in self._database.getPushProperties(user.Id, itemid, start, end):
                    properties = property.get('Properties')
                    timestamp = property.get('TimeStamp')
                    modified = getDateTimeToString(metadata.get('DateModified'))
                    if properties & TITLE:
                        newid = self._provider.updateName(user.Request, itemid, metadata)
                        self._logger.logprb(INFO, g_class, mtd, 312, metadata.get('Title'), modified)
                    elif properties & CONTENT:
                        newid, args = self._provider.uploadFile(314, user, itemid, metadata, modified, chunk, retry, delay, False)
                        self._logger.logprb(INFO, g_class, mtd, *args)
                    elif properties & TRASHED:
                        newid = self._provider.updateTrashed(user.Request, itemid, metadata)
                        self._logger.logprb(INFO, g_class, mtd, 313, metadata.get('Title'), modified)
            # MOVE procedures to follow parent changes of a resource
            elif action & MOVE:
                self._database.getItemParentIds(itemid, metadata, start, end)
                newid = self._provider.updateParents(user.Request, itemid, metadata)
            elif action & DELETE:
                newid = self._provider.updateTrashed(user.Request, itemid, metadata)
                self._logger.logprb(INFO, g_class, mtd, 313, metadata.get('Title'), timestamp)
            return newid
        except Exception as e:
            self._logger.logprb(SEVERE, g_class, mtd, 319, e, traceback.format_exc())

    def _isNewUser(self, user):
        return len(user.Token) == 0

    def _getReplicateTimeout(self):
        timeout = self._config.getByName('ReplicateTimeout')
        return timeout

    def _getPolicy(self):
        policy = self._config.getByName('SynchronizePolicy')
        return self._getSynchronizePolicy(policy)

    def _getSynchronizePolicy(self, policy):
        # FIXME: OpenOffice need uno.getConstantByName() vs uno.Enum()
        try:
            return uno.getConstantByName('com.sun.star.ucb.SynchronizePolicy.%s' % policy)
        # FIXME: LibreOffice raise exception on uno.getConstantByName() on Enum...
        except:
            return uno.Enum('com.sun.star.ucb.SynchronizePolicy', policy)

    def _getResetSetting(self):
        reset = self._config.getByName('ResetSync')
        if reset:
            config = getConfiguration(self._ctx, g_identifier, True)
            config.replaceByName('ResetSync', 0)
            if config.hasPendingChanges():
                config.commitChanges()
        return reset

    def _getUploadSetting(self):
        config = self._config.getByHierarchicalName('Settings/Upload')
        return config.getByName('Chunk'), config.getByName('Retry'), config.getByName('Delay')

    def _getShareSetting(self):
        return self._config.getByName('SharedDocuments')


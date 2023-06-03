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

from com.sun.star.ucb.ChangeAction import INSERT
from com.sun.star.ucb.ChangeAction import UPDATE
from com.sun.star.ucb.ChangeAction import MOVE
from com.sun.star.ucb.ChangeAction import DELETE

from com.sun.star.ucb.ContentProperties import TITLE
from com.sun.star.ucb.ContentProperties import CONTENT
from com.sun.star.ucb.ContentProperties import TRASHED

from com.sun.star.rest import HTTPException
from com.sun.star.rest.HTTPStatusCode import BAD_REQUEST

from .unotool import getConfiguration

from .dbtool import currentDateTimeInTZ
from .dbtool import getDateTimeInTZToString
from .dbtool import getDateTimeToString

from .database import DataBase

from .logger import getLogger

from .configuration import g_identifier
from .configuration import g_synclog

g_basename = 'Replicator'

from six import binary_type
from collections import OrderedDict
from threading import Thread
import traceback
import time


class Replicator(unohelper.Base,
                 Thread):
    def __init__(self, ctx, datasource, provider, users, sync, lock):
        Thread.__init__(self)
        self._ctx = ctx
        self._users = users
        self._sync = sync
        self._lock = lock
        self._canceled = False
        self._fullPull = False
        self.DataBase = DataBase(ctx, datasource)
        self._provider = provider
        self._config = getConfiguration(ctx, g_identifier, False)
        self._logger = getLogger(ctx, g_synclog, g_basename)
        sync.clear()
        self.start()

    def fullPull(self):
        return self._fullPull

    def cancel(self):
        self._canceled = True
        self._sync.set()
        self.join()

    def run(self):
        try:
            msg = "Replicator for Scheme: %s loading ... " % self._provider.Scheme
            print("Replicator.run() 1 *************************************************************")
            print("Replicator run() 2")
            while not self._canceled:
                self._sync.wait(self._getReplicateTimeout())
                self._synchronize()
                self._sync.clear()
                print("replicator.run() 3")
            print("replicator.run() 4 *************************************************************")
        except Exception as e:
            msg = "Replicator run(): Error: %s - %s" % (e, traceback.print_exc())
            print(msg)

    def _synchronize(self):
        policy = self._getPolicy()
        if policy == self._getSynchronizePolicy('NONE_IS_MASTER'):
            return
        self._logger.logprb(INFO, 'Replicator', '_synchronize()', 101, getDateTimeInTZToString(currentDateTimeInTZ()))
        if self._provider.isOffLine():
            self._logger.logprb(INFO, 'Replicator', '_synchronize()', 102)
        elif policy == self._getSynchronizePolicy('SERVER_IS_MASTER'):
            if not self._canceled:
                self._pullUsers()
            if not self._canceled:
                self._pushUsers()
        elif policy == self._getSynchronizePolicy('CLIENT_IS_MASTER'):
            if not self._canceled:
                self._pushUsers()
            if not self._canceled:
                self._pullUsers()
        self._logger.logprb(INFO, 'Replicator', '_synchronize()', 103, getDateTimeInTZToString(currentDateTimeInTZ()))

    def _pullUsers(self):
        try:
            for user in self._users.values():
                if self._canceled:
                    break
                self._logger.logprb(INFO, 'Replicator', '_pullUsers()', 111, user.Name, getDateTimeInTZToString(currentDateTimeInTZ()))
                # In order to make the creation of files or directories possible quickly,
                # it is necessary to run the verification of the identifiers first.
                self._checkNewIdentifier(user)
                #if not user.Token:
                if self._isNewUser(user):
                    self._initUser(user)
                else:
                    self._pullUser(user)
                self._logger.logprb(INFO, 'Replicator', '_pullUsers()', 112, user.Name, getDateTimeInTZToString(currentDateTimeInTZ()))
        except Exception as e:
            print("Replicator._pullUsers() ERROR: %s - %s" % (e, traceback.print_exc()))

    def _initUser(self, user):
        # This procedure is launched only once for each new user
        # This procedure corresponds to the initial pull for a new User (ie: without Token)
        pages, count, token = self._provider.firstPull(user)
        print("Replicator._initUser() 1 Count: %s - Pages %s - Token: %s" % (count, pages, token))
        self._provider.initUser(self.DataBase, user, token)
        user.SyncMode = 1
        self._fullPull = True

    def _pullUser(self, user):
        # This procedure is launched each time the synchronization is started
        # This procedure corresponds to the pull for a User (ie: a Token is required)
        print("Replicator._pullUser() 1")
        pages, count, token = self._provider.pullUser(user)
        if token:
            user.setToken(token)
        print("Replicator._pullUser() 2 Items count: %s - Pages count: %s - Token: %s" % (count, pages, token))

    def _pushUsers(self):
        # This procedure is launched each time the synchronization is started
        # This procedure corresponds to the push of changes for the entire database 
        # for all users, in chronological order, from 'start' to 'end'...
        try:
            end = currentDateTimeInTZ()
            for user in self._users.values():
                self._logger.logprb(INFO, 'Replicator', '_pushUsers()', 131, user.Name, getDateTimeInTZToString(currentDateTimeInTZ()))
                if self._isNewUser(user):
                    self._initUser(user)
                items = []
                start = user.TimeStamp
                for item in self.DataBase.getPushItems(user.Id, start, end):
                    print("Replicator._pushUsers() 1 Start: %s - End: %s" % (getDateTimeInTZToString(start), getDateTimeInTZToString(end)))
                    print("Replicator._pushUsers() 2 Item: UserName: %s - ItemId: %s - ChangeAction: %s - TimeStamp: %s" % (user.Name, item.get('ItemId'),item.get('ChangeAction'),getDateTimeInTZToString(item.get('TimeStamp'))))
                    metadata = self.DataBase.getMetaData(user, item)
                    newid = self._pushItem(user, item, metadata, start, end)
                    if newid is not None:
                        items.append(newid)
                    else:
                        modified = getDateTimeToString(metadata.get('DateModified'))
                        self._logger.logprb(SEVERE, 'Replicator', '_pushUsers()', 132, metadata.get('Title'), modified, metadata.get('Id'))
                        break
                if items:
                    self.DataBase.updatePushItems(user, items)
                self._logger.logprb(INFO, 'Replicator', '_pushUsers()', 133, user.Name, getDateTimeInTZToString(currentDateTimeInTZ()))
        except Exception as e:
            print("Replicator.synchronize() ERROR: %s - %s" % (e, traceback.print_exc()))

    def _checkNewIdentifier(self, user):
        if not self._provider.GenerateIds:
            user.CanAddChild = True
            return
        if self._provider.isOffLine():
            user.CanAddChild = self.DataBase.countIdentifier(user.Id) > 0
            return
        if self.DataBase.countIdentifier(user.Id) < min(self._provider.IdentifierRange):
            self._provider.pullNewIdentifiers(user)
        # Need to postpone the creation authorization after this verification...
        user.CanAddChild = True


    def _filterParents(self, call, provider, items, childs, roots, start):
        i = -1
        rows = []
        while len(childs) and len(childs) != i:
            i = len(childs)
            print("replicator._filterParents() %s" % len(childs))
            for item in childs:
                itemid, parents = item
                if all(parent in roots for parent in parents):
                    roots.append(itemid)
                    row = self.DataBase.setDriveCall(call, provider, items[itemid], itemid, parents, start)
                    rows.append(row)
                    childs.remove(item)
            childs.reverse()
        return rows

    def _pushItem(self, user, item, metadata, start, end):
        try:
            itemid = item.get('ItemId')
            newid = None
            timestamp = item.get('TimeStamp')
            action = item.get('ChangeAction')
            chunk, retry, delay = self._getUploadSetting()
            print("Replicator._pushItem() 3 Insert/Update Title: %s Id: %s - Action: %s" % (metadata.get('Title'),
                                                                                 itemid,
                                                                                 action))
            # If the synchronization of an INSERT or an UPDATE fails
            # then the user's TimeStamp will not be updated
            # INSERT procedures, new files and folders are synced here.
            if action & INSERT:
                print("Replicator._pushItem() INSERT 1")
                mediatype = metadata.get('MediaType')
                print("Replicator._pushItem() INSERT 2")
                created = getDateTimeToString(metadata.get('DateCreated'))
                if self._provider.isFolder(mediatype):
                    print("Replicator._pushItem() INSERT 3")
                    newid = self._provider.createFolder(user, itemid, metadata)
                    print("Replicator._pushItem() INSERT 4")
                    self._logger.logprb(INFO, 'Replicator', '_pushItem()', 141, metadata.get('Title'), created)
                    print("Replicator._pushItem() INSERT 5")
                elif self._provider.isLink(mediatype):
                    pass
                elif self._provider.isDocument(mediatype):
                    newid = self._provider.uploadFile(user, itemid, metadata, chunk, retry, delay, True)
                    if newid:
                        self._logger.logprb(INFO, 'Replicator', '_pushItem()', 142, metadata.get('Title'), created)
            # UPDATE procedures, only a few properties are synchronized: Title and content(ie: Size or DateModified)
            elif action & UPDATE:
                for property in self.DataBase.getPushProperties(user.Id, itemid, start, end):
                    properties = property.get('Properties')
                    timestamp = property.get('TimeStamp')
                    modified = getDateTimeToString(metadata.get('DateModified'))
                    if properties & TITLE:
                        newid = self._provider.updateTitle(user.Request, itemid, metadata)
                        self._logger.logprb(INFO, 'Replicator', '_pushItem()', 143, metadata.get('Title'), modified)
                    elif properties & CONTENT:
                        newid = self._provider.uploadFile(user, itemid, metadata, chunk, retry, delay, False)
                        self._logger.logprb(INFO, 'Replicator', '_pushItem()', 144, metadata.get('Title'), modified, metadata.get('Size'))
                    elif properties & TRASHED:
                        newid = self._provider.updateTrashed(user.Request, itemid, metadata)
                        self._logger.logprb(INFO, 'Replicator', '_pushItem()', 145, metadata.get('Title'), modified)
            # MOVE procedures to follow parent changes of a resource
            elif action & MOVE:
                print("Replicator._pushItem() MOVE")
                self.DataBase.getItemParentIds(itemid, metadata, start, end)
                newid = self._provider.updateParents(user.Request, itemid, metadata)
                print("Replicator.._pushItem() MOVE ToAdd: %s - ToRemove: %s" % (toadd, toremove))
            elif action & DELETE:
                print("Replicator._pushItem() DELETE")
                newid = self._provider.updateTrashed(user.Request, itemid, metadata)
                self._logger.logprb(INFO, 'Replicator', '_pushItem()', 145, metadata.get('Title'), timestamp)
            return newid
        except Exception as e:
            msg = "ERROR: %s - %s" % (e, traceback.print_exc())
            self._logger.logp(SEVERE, 'Replicator', '_pushItem()', msg)

    def _isNewUser(self, user):
        return user.SyncMode == 0

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

    def _getUploadSetting(self):
        config = self._config.getByHierarchicalName('Settings/Upload')
        return config.getByName('Chunk'), config.getByName('Retry'), config.getByName('Delay')

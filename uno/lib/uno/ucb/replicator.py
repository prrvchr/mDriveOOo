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

from com.sun.star.ucb.SynchronizePolicy import SERVER_IS_MASTER
from com.sun.star.ucb.SynchronizePolicy import CLIENT_IS_MASTER
from com.sun.star.ucb.SynchronizePolicy import NONE_IS_MASTER

from com.sun.star.ucb.ChangeAction import INSERT
from com.sun.star.ucb.ChangeAction import UPDATE
from com.sun.star.ucb.ChangeAction import MOVE
from com.sun.star.ucb.ChangeAction import DELETE

from com.sun.star.ucb.ContentProperties import TITLE
from com.sun.star.ucb.ContentProperties import CONTENT
from com.sun.star.ucb.ContentProperties import TRASHED

from com.sun.star.rest import HTTPException
from com.sun.star.rest.HTTPStatusCode import BAD_REQUEST

from com.sun.star.ucb import XRestReplicator

from .unotool import getConfiguration

from .dbtool import currentDateTimeInTZ
from .dbtool import getDateTimeInTZToString
from .dbtool import getDateTimeToString

from .database import DataBase

from .logger import getLogger

from .configuration import g_identifier
from .configuration import g_synclog

g_basename = 'Replicator'

from collections import OrderedDict
from threading import Thread
import traceback
import time


class Replicator(unohelper.Base,
                 XRestReplicator,
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
        self.Provider = provider
        self._config = getConfiguration(ctx, g_identifier, False)
        self._logger = getLogger(ctx, g_synclog, g_basename)
        sync.clear()
        self.start()

    # XRestReplicator
    def callBack(self, itemid, response):
        if response.IsPresent:
            self.DataBase.updateItemId(self.Provider, itemid, response.Value)
            return True
        return False


    def fullPull(self):
        return self._fullPull

    def cancel(self):
        self._canceled = True
        self._sync.set()
        self.join()

    def run(self):
        try:
            msg = "Replicator for Scheme: %s loading ... " % self.Provider.Scheme
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
        policy = self._getSynchronizePolicy()
        if policy == NONE_IS_MASTER:
            return
        self._logger.logprb(INFO, 'Replicator', '_synchronize()', 101, getDateTimeInTZToString(currentDateTimeInTZ()))
        if self.Provider.isOffLine():
            self._logger.logprb(INFO, 'Replicator', '_synchronize()', 102)
        elif policy == SERVER_IS_MASTER:
            if not self._canceled:
                self._pullUsers()
            if not self._canceled:
                self._pushUsers()
        elif policy == CLIENT_IS_MASTER:
            if not self._canceled:
                self._pushUsers()
            if not self._canceled:
                self._pullUsers()
        self._logger.logprb(INFO, 'Replicator', '_synchronize()', 103, getDateTimeInTZToString(currentDateTimeInTZ()))

    def _pullUsers(self):
        try:
            print("Replicator._pullUsers() 1")
            for user in self._users.values():
                print("Replicator._pullUsers() 2")
                if self._canceled:
                    break
                self._logger.logprb(INFO, 'Replicator', '_pullUsers()', 111, user.Name, getDateTimeInTZToString(currentDateTimeInTZ()))
                # In order to make the creation of files or directories possible quickly,
                # it is necessary to run the verification of the identifiers first.
                self._checkNewIdentifier(user)
                #if not user.Token:
                if self._isNewUser(user):
                    self._initUser(user)
                    print("Replicator._pullUsers() 3")
                else:
                    self._pullData(user)
                    print("Replicator._pullUsers() 4")
                self._logger.logprb(INFO, 'Replicator', '_pullUsers()', 112, user.Name, getDateTimeInTZToString(currentDateTimeInTZ()))
        except Exception as e:
            print("Replicator._pullUsers() ERROR: %s - %s" % (e, traceback.print_exc()))

    def _initUser(self, user):
        # This procedure is launched only once for each new user
        # This procedure corresponds to the initial pull for a new User (ie: without Token)
        rejected, pages, rows, count = self._firstPull(user)
        print("Replicator._initUser() 1 count: %s - %s pages - %s rows" % (count, pages, rows))
        self._logger.logprb(INFO, 'Replicator', '_initUser()', 121, pages, rows, count)
        if len(rejected):
            self._logger.logprb(SEVERE, 'Replicator', '_initUser()', 122, len(rejected))
        for title, itemid, parents in rejected:
            self._logger.logprb(SEVERE, 'Replicator', '_initUser()', 123, title, itemid, parents)
        print("Replicator._initUser() 2 %s" % count)
        user.Provider.initUser(user.Request, self.DataBase, user.MetaData)
        user.SyncMode = 1
        self._fullPull = True

    def _pullData(self, user):
        # This procedure is launched each time the synchronization is started
        # This procedure corresponds to the pull for a User (ie: a Token is required)
        print("Replicator._pullData() 1")
        parameter = user.Provider.getRequestParameter('getPull', user.MetaData)
        try:
            enumerator = user.Request.getIterator(parameter, None)
            print("Replicator._pullData() 2 %s - %s" % (enumerator.PageCount, enumerator.SyncToken))
            while enumerator.hasMoreElements():
                response = enumerator.nextElement()
                print("Replicator._pullData() 3 %s" % response)
        except HTTPException as e:
            if e.StatusCode == BAD_REQUEST:
                parameter = user.Provider.getRequestParameter('getToken')
                response = user.Request.execute(parameter)
                if response.IsPresent:
                    token = response.Value.getDefaultValue('startPageToken', None)
                    if token is not None:
                        user.MetaData.setValue('Token', token)
        print("Replicator._pullData() 4 %s - %s" % (enumerator.PageCount, enumerator.SyncToken))

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
                    print("Replicator._pushUsers() 2 Item: UserName: %s - ItemId: %s - ChangeAction: %s - TimeStamp: %s" % (user.Name, item.getValue('ItemId'),item.getValue('ChangeAction'),getDateTimeInTZToString(item.getValue('TimeStamp'))))
                    chunk = user.Provider.Chunk
                    url = user.Provider.SourceURL
                    uploader = user.Request.getUploader(chunk, url, self)
                    metadata = self.DataBase.getMetaData(user, item)
                    itemid = item.getValue('ItemId')
                    if self._pushItem(user, itemid, uploader, item, metadata, start, end):
                        items.append(itemid)
                    else:
                        modified = getDateTimeToString(metadata.getValue('DateModified'))
                        self._logger.logprb(SEVERE, 'Replicator', '_pushUsers()', 132, metadata.getValue('Title'), modified, metadata.getValue('Id'))
                        break
                if items:
                    self.DataBase.updatePushItems(user, items)
                print("Replicator._pushUsers() 4")
                self._logger.logprb(INFO, 'Replicator', '_pushUsers()', 133, user.Name, getDateTimeInTZToString(currentDateTimeInTZ()))
        except Exception as e:
            print("Replicator.synchronize() ERROR: %s - %s" % (e, traceback.print_exc()))

    def _checkNewIdentifier(self, user):
        if not user.Provider.GenerateIds:
            user.CanAddChild = True
            return
        if user.Provider.isOffLine():
            user.CanAddChild = self.DataBase.countIdentifier(user.Id) > 0
            return
        if self.DataBase.countIdentifier(user.Id) < min(user.Provider.IdentifierRange):
            enumerator = user.Provider.getIdentifier(user.Request, user.MetaData)
            self.DataBase.insertIdentifier(enumerator, user.Id)
        # Need to postpone the creation authorization after this verification...
        user.CanAddChild = True

    def _firstPull(self, user):
        start = currentDateTimeInTZ()
        rootid = user.RootId
        call = self.DataBase.getFirstPullCall(user.Id, 1, start)
        orphans, pages, rows, count, token = self._getFirstPull(call, user.Provider, user.Request, rootid, start)
        #rows += self._filterParents(call, user.Provider, items, parents, roots, start)
        rejected = self._getRejectedItems(user.Provider, orphans, rootid)
        if count > 0:
            call.executeBatch()
        call.close()
        user.Provider.updateDrive(self.DataBase, user.MetaData, token)
        return rejected, pages, rows, count

    def _getFirstPull(self, call, provider, request, rootid, start):
        orphans = OrderedDict()
        roots = [rootid]
        pages = rows = count = 0
        token = ''
        provider.initFirstPull(rootid)
        while provider.hasFirstPull():
            parameter = provider.getRequestParameter('getFirstPull', provider.getFirstPull())
            enumerator = request.getIterator(parameter, None)
            while enumerator.hasMoreElements():
                item = enumerator.nextElement()
                if self._setFirstPullCall(call, provider, roots, orphans, rootid, item, start):
                    provider.setFirstPull(item)
                    count += 1
            pages += enumerator.PageCount
            rows += enumerator.RowCount
            token = enumerator.SyncToken
        return orphans, pages, rows, count, token

    def _setFirstPullCall(self, call, provider, roots, orphans, rootid, item, timestamp):
        itemid = provider.getItemId(item)
        parents = provider.getItemParent(item, rootid)
        if not all(parent in roots for parent in parents):
            orphans[itemid] = item
            return False
        roots.append(itemid)
        self.DataBase.setFirstPullCall(call, provider, item, itemid, parents, timestamp)
        return True

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

    def _getRejectedItems(self, provider, items, rootid):
        rejected = []
        for itemid in items:
            item = items[itemid]
            title = provider.getItemTitle(item)
            parents = provider.getItemParent(item, rootid)
            rejected.append((title, itemid, ','.join(parents)))
        return rejected

    def _pushItem(self, user, itemid, uploader, item, metadata, start, end):
        try:
            status = False
            timestamp = item.getValue('TimeStamp')
            action = item.getValue('ChangeAction')
            print("Replicator._pushItem() 3 Insert/Update Title: %s Id: %s - Action: %s" % (metadata.getValue('Title'),
                                                                                 itemid,
                                                                                 action))
            # If the synchronization of an INSERT or an UPDATE fails
            # then the user's TimeStamp will not be updated
            # INSERT procedures, new files and folders are synced here.
            if action & INSERT:
                print("Replicator._pushItem() INSERT 1")
                mediatype = metadata.getValue('MediaType')
                print("Replicator._pushItem() INSERT 2")
                created = getDateTimeToString(metadata.getValue('DateCreated'))
                if user.Provider.isFolder(mediatype):
                    print("Replicator._pushItem() INSERT 3")
                    response = user.Provider.createFolder(user.Request, metadata)
                    print("Replicator._pushItem() INSERT 4")
                    status = self.callBack(itemid, response)
                    print("Replicator._pushItem() INSERT 5")
                    self._logger.logprb(INFO, 'Replicator', '_pushItem()', 141, metadata.getValue('Title'), created)
                    print("Replicator._pushItem() INSERT 6")
                elif user.Provider.isLink(mediatype):
                    pass
                elif user.Provider.isDocument(mediatype):
                    if user.Provider.createFile(user.Request, uploader, metadata):
                        #if self._needPush('SizeUpdated', itemid, operations):
                        status = user.Provider.uploadFile(uploader, user, metadata, True)
                        self._logger.logprb(INFO, 'Replicator', '_pushItem()', 142, metadata.getValue('Title'), created)
            # UPDATE procedures, only a few properties are synchronized: Title and content(ie: Size or DateModified)
            elif action & UPDATE:
                for property in self.DataBase.getPushProperties(user.Id, itemid, start, end):
                    status = False
                    properties = property.getValue('Properties')
                    timestamp = property.getValue('TimeStamp')
                    modified = getDateTimeToString(metadata.getValue('DateModified'))
                    if properties & TITLE:
                        status = user.Provider.updateTitle(user.Request, metadata)
                        self._logger.logprb(INFO, 'Replicator', '_pushItem()', 143, metadata.getValue('Title'), modified)
                    elif properties & CONTENT:
                        status = user.Provider.uploadFile(uploader, user, metadata, False)
                        self._logger.logprb(INFO, 'Replicator', '_pushItem()', 144, metadata.getValue('Title'), modified, metadata.getValue('Size'))
                    elif properties & TRASHED:
                        status = user.Provider.updateTrashed(user.Request, metadata)
                        self._logger.logprb(INFO, 'Replicator', '_pushItem()', 145, metadata.getValue('Title'), modified)
                    if not status:
                        break
            # MOVE procedures to follow parent changes of a resource
            elif action & MOVE:
                print("Replicator._pushItem() MOVE")
                self.DataBase.getItemParentIds(itemid, metadata, start, end)
                status = user.Provider.updateParents(user.Request, metadata)
                print("Replicator.._pushItem() MOVE ToAdd: %s - ToRemove: %s" % (toadd, toremove))
            elif action & DELETE:
                print("Replicator._pushItem() DELETE")
                status = user.Provider.updateTrashed(user.Request, metadata)
                self._logger.logprb(INFO, 'Replicator', '_pushItem()', 145, metadata.getValue('Title'), timestamp)
            return status
        except Exception as e:
            msg = "ERROR: %s - %s" % (e, traceback.print_exc())
            self._logger.logp(SEVERE, 'Replicator', '_pushItem()', msg)

    def _isNewUser(self, user):
        return user.SyncMode == 0

    def _getReplicateTimeout(self):
        timeout = self._config.getByName('ReplicateTimeout')
        return timeout

    def _getSynchronizePolicy(self):
        policy = self._config.getByName('SynchronizePolicy')
        return uno.Enum('com.sun.star.ucb.SynchronizePolicy', policy)

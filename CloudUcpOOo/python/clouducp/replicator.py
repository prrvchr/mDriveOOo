#!
# -*- coding: utf_8 -*-

'''
    Copyright (c) 2020 https://prrvchr.github.io

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the Software
    is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
    OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

#from __futur__ import absolute_import

import uno
import unohelper

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb import XRestReplicator

from unolib import parseDateTime
from unolib import unparseDateTime

from .database import DataBase
from .user import User

from .configuration import g_sync

from .logger import logMessage
from .logger import getMessage
g_message = 'replicator'

from collections import OrderedDict
from threading import Thread
import traceback
import time


class Replicator(unohelper.Base,
                 XRestReplicator,
                 Thread):
    def __init__(self, ctx, datasource, provider, users, sync):
        Thread.__init__(self)
        self.ctx = ctx
        self.DataBase = DataBase(self.ctx, datasource)
        self.Provider = provider
        self.Users = users
        self.canceled = False
        self.fullPull = False
        self.sync = sync
        sync.clear()
        self.error = None
        self.start()

    # XRestReplicator
    def cancel(self):
        self.canceled = True
        self.sync.set()
        self.join()
    def callBack(self, username, itemid, response):
        if response.IsPresent:
            self.DataBase.updateItemId(self.Provider, username, itemid, response.Value)
            return True
        return False

    def run(self):
        try:
            msg = "Replicator for Scheme: %s loading ... " % self.Provider.Scheme
            print("Replicator.run() 1 *************************************************************")
            logMessage(self.ctx, INFO, "stage 1", 'Replicator', 'run()')
            print("Replicator run() 2")
            while not self.canceled:
                self.sync.wait(g_sync)
                self._synchronize()
                self.sync.clear()
                print("replicator.run() 3")
            print("replicator.run() 4 *************************************************************")
        except Exception as e:
            msg = "Replicator run(): Error: %s - %s" % (e, traceback.print_exc())
            print(msg)

    def _synchronize(self):
        if self.Provider.isOffLine():
            msg = getMessage(self.ctx, g_message, 101)
            logMessage(self.ctx, INFO, msg, 'Replicator', '_synchronize()')
        elif not self.canceled:
            timestamp = parseDateTime()
            self._syncData(timestamp)

    def _syncData(self, timestamp):
        try:
            print("Replicator.synchronize() 1")
            results = []
            for user in self.Users.values():
                if self.canceled:
                    break
                msg = getMessage(self.ctx, g_message, 111, (user.Name, unparseDateTime(timestamp)))
                logMessage(self.ctx, INFO, msg, 'Replicator', '_syncData()')
                # In order to make the creation of files or directories possible quickly,
                # it is necessary to run the verification of the identifiers first.
                self._checkNewIdentifier(user)
                if not user.Token:
                    start = self._initUser(user)
                    #start = self.DataBase.getUserTimeStamp(user.Id)
                    user.Provider.initUser(user.Request, self.DataBase, user.MetaData)
                else:
                    start = self.DataBase.getUserTimeStamp(user.Id)
                if user.Token:
                    results += self._pullData(user)
                msg = getMessage(self.ctx, g_message, 112, (user.Name, unparseDateTime()))
                logMessage(self.ctx, INFO, msg, 'Replicator', '_syncData()')
            if all(results):
                results += self._pushData(start)
            result = all(results)
            print("Replicator.synchronize() 2 %s" % result)
        except Exception as e:
            print("Replicator.synchronize() ERROR: %s - %s" % (e, traceback.print_exc()))

    def _initUser(self, user):
        # This procedure is launched only once for each new user
        # This procedure corresponds to the initial pull for a new User (ie: without Token)
        rejected, pages, rows, count, start = self._firstPull(user)
        print("Replicator._initUser() 1 count: %s - %s pages - %s rows" % (count, pages, rows))
        msg = getMessage(self.ctx, g_message, 121, (pages, rows, count))
        logMessage(self.ctx, INFO, msg, 'Replicator', '_syncData()')
        if len(rejected):
            msg = getMessage(self.ctx, g_message, 122, len(rejected))
            logMessage(self.ctx, SEVERE, msg, 'Replicator', '_syncData()')
        for item in rejected:
            msg = getMessage(self.ctx, g_message, 123, item)
            logMessage(self.ctx, SEVERE, msg, 'Replicator', '_syncData()')
        print("Replicator._initUser() 2 %s" % count)
        self.fullPull = True
        return start

    def _pullData(self, user):
        # This procedure is launched each time the synchronization is started
        # This procedure corresponds to the pull for a User (ie: a Token is required)
        results = []
        print("Replicator._pullData() 1")
        parameter = user.Provider.getRequestParameter('getPull', user.MetaData)
        enumerator = user.Request.getIterator(parameter, None)
        print("Replicator._pullData() 2 %s - %s" % (enumerator.PageCount, enumerator.SyncToken))
        while enumerator.hasMoreElements():
            response = enumerator.nextElement()
            print("Replicator._pullData() 3 %s" % response)
        print("Replicator._pullData() 4 %s - %s" % (enumerator.PageCount, enumerator.SyncToken))
        return results

    def _pushData(self, start):
        # This procedure is launched each time the synchronization is started
        # This procedure corresponds to the push of changes for the entire database 
        # for all users, in chronological order, from 'start' to 'end'...
        try:
            print("Replicator._pushData() 1")
            results = []
            operations = {'TitleUpdated': [], 'SizeUpdated': [], 'TrashedUpdated': []}
            end = parseDateTime()
            for item in self.DataBase.getPushItems(start, end):
                user = self.Users.get(item.getValue('UserName'), None)
                if user is None:
                    user = User(self.ctx, self, item.getValue('UserName'), self.DataBase)
                print("Replicator._pushData() 2 Insert/Update: %s Items: %s - %s - %s - %s - %s" % (item.getValue('Title'),
                                                                                                    item.getValue('TitleUpdated'),
                                                                                                    item.getValue('SizeUpdated'),
                                                                                                    item.getValue('TrashedUpdated'),
                                                                                                    item.getValue('Size'),
                                                                                                    item.getValue('AtRoot')))
                chunk = user.Provider.Chunk
                url = user.Provider.SourceURL
                uploader = user.Request.getUploader(chunk, url, self)
                results.append(self._pushItem(user, uploader, item, operations))
            print("Replicator._pushData() 3 Created / Updated Items: %s" % (results, ))
            if all(results):
                self.DataBase.updateUserTimeStamp(end, None)
                print("Replicator._pushData() 4 Created / Updated Items OK")
            print("Replicator._pushData() 5")
            return results
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
        separator = ','
        start = parseDateTime()
        rootid = user.RootId
        call = self.DataBase.getFirstPullCall(user.Id, separator, 1, start)
        orphans, pages, rows, count, token = self._getFirstPull(call, user.Provider, user.Request, rootid, separator, start)
        #rows += self._filterParents(call, user.Provider, items, parents, roots, separator, start)
        rejected = self._getRejectedItems(user.Provider, orphans, rootid)
        if count > 0:
            call.executeBatch()
        call.close()
        user.Provider.updateDrive(self.DataBase, user.MetaData, token)
        end = parseDateTime()
        self.DataBase.updateUserTimeStamp(end, user.Id)
        return rejected, pages, rows, count, end

    def _getFirstPull(self, call, provider, request, rootid, separator, start):
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
                if self._setFirstPullCall(call, provider, roots, orphans, rootid, item, separator, start):
                    provider.setFirstPull(item)
                    count += 1
            pages += enumerator.PageCount
            rows += enumerator.RowCount
            token = enumerator.SyncToken
        return orphans, pages, rows, count, token

    def _setFirstPullCall(self, call, provider, roots, orphans, rootid, item, separator, timestamp):
        itemid = provider.getItemId(item)
        parents = provider.getItemParent(item, rootid)
        if not all(parent in roots for parent in parents):
            orphans[itemid] = item
            return False
        roots.append(itemid)
        self.DataBase.setFirstPullCall(call, provider, item, itemid, parents, separator, timestamp)
        return True

    def _filterParents(self, call, provider, items, childs, roots, separator, start):
        i = -1
        rows = []
        while len(childs) and len(childs) != i:
            i = len(childs)
            print("replicator._filterParents() %s" % len(childs))
            for item in childs:
                itemid, parents = item
                if all(parent in roots for parent in parents):
                    roots.append(itemid)
                    row = self.DataBase.setDriveCall(call, provider, items[itemid], itemid, parents, separator, start)
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

    def _pushItem(self, user, uploader, item, operations):
        try:
            result = True
            # If the synchronization of an INSERT or an UPDATE fails
            # then the user's TimeStamp will not be updated
            itemid = item.getValue('Id')
            # INSERT procedures, new files and folders are synced here.
            if all((item.getValue(property) for property in operations)):
                mediatype = item.getValue('MediaType')
                if user.Provider.isFolder(mediatype):
                    response = user.Provider.createFolder(user.Request, item)
                    result = self.callBack(user.Name, itemid, response)
                    format = (item.getValue('Title'), unparseDateTime(item.getValue('TimeStamp')))
                    msg = getMessage(self.ctx, g_message, 131, format)
                    logMessage(self.ctx, INFO, msg, "Replicator", "_pushItem()")
                    print(msg)
                elif user.Provider.isLink(mediatype):
                    pass
                elif user.Provider.isDocument(mediatype):
                    if user.Provider.createFile(user.Request, uploader, item):
                        if self._needPush('SizeUpdated', itemid, operations):
                            result = user.Provider.uploadFile(uploader, user, item, True)
                        format = (item.getValue('Title'), unparseDateTime(item.getValue('TimeStamp')))
                        msg = getMessage(self.ctx, g_message, 132, format)
                        logMessage(self.ctx, INFO, msg, "Replicator", "_pushItem()")
                        print(msg)
            # UPDATE procedures, only a few properties are synchronized: (Size, Title, Trashed)
            elif self._needPush('TitleUpdated', itemid, operations, item):
                result = user.Provider.updateTitle(user.Request, item)
                format = (item.getValue('Title'), unparseDateTime(item.getValue('TimeStamp')))
                msg = getMessage(self.ctx, g_message, 133, format)
                logMessage(self.ctx, INFO, msg, "Replicator", "_pushItem()")
                print(msg)
            elif self._needPush('SizeUpdated', itemid, operations, item):
                result = user.Provider.uploadFile(uploader, user, item, False)
                timestamp = unparseDateTime(item.getValue('TimeStamp'))
                format = (item.getValue('Title'), timestamp, item.getValue('Size'))
                msg = getMessage(self.ctx, g_message, 134, format)
                logMessage(self.ctx, INFO, msg, "Replicator", "_pushItem()")
                print(msg)
            elif self._needPush('TrashedUpdated', itemid, operations, item):
                result = user.Provider.updateTrashed(user.Request, item)
                format = (item.getValue('Title'), unparseDateTime(item.getValue('TimeStamp')))
                msg = getMessage(self.ctx, g_message, 135, format)
                logMessage(self.ctx, INFO, msg, "Replicator", "_pushItem()")
                print(msg)
            else:
                # UPDATE of other properties (TimeStamp...)
                print("Replicator._pushItem() Update None")
            #logMessage(self.ctx, INFO, msg, "Replicator", "_pushItem()")
            if not result:
                timestamp = unparseDateTime(item.getValue('TimeStamp'))
                format = (item.getValue('Title'), timestamp, item.getValue('Id'))
                msg = getMessage(self.ctx, g_message, 136, format)
                logMessage(self.ctx, SEVERE, msg, "Replicator", "_pushItem()")
                print(msg)
            return result
        except Exception as e:
            msg = "ERROR: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, "Replicator", "_pushItem()")

    def _needPush(self, method, itemid, operations, item=None):
        if (True if item is None else item.getValue(method)):
            if itemid not in operations.get(method):
                operations.get(method).append(itemid)
                return True
        return False

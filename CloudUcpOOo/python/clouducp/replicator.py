#!
# -*- coding: utf_8 -*-

#from __futur__ import absolute_import

import uno
import unohelper

from com.sun.star.util import XCancellable
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb import XRestReplicator

from unolib import KeyMap
from unolib import getDateTime
from unolib import unparseTimeStamp
from unolib import parseDateTime

from .configuration import g_sync
from .database import DataBase

from .dbinit import getDataSourceUrl
from .dbinit import createDataBase

from .dbtools import getDataSourceConnection
from .dbtools import createDataSource
from .dbtools import registerDataSource

from .logger import logMessage
from .logger import getMessage

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
    def callBack(self, item, response):
        if response.IsPresent:
            self.DataBase.updateItemId(self.Provider, item, response.Value)

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
            msg = getMessage(self.ctx, 111)
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
                msg = getMessage(self.ctx, 110, user.Name)
                logMessage(self.ctx, INFO, msg, 'Replicator', '_syncData()')
                #self.DataBase.setSession(user.Name)
                if not user.Token:
                    start = self._initUser(user)
                    #start = self.DataBase.getUserTimeStamp(user.Id)
                    user.Provider.initUser(user.Request, self.DataBase, user.MetaData)
                else:
                    start = self.DataBase.getUserTimeStamp(user.Id)
                if user.Token:
                    results += self._pullData(user)
            if all(results):
                results += self._pushData(start)
                msg = getMessage(self.ctx, 116, user.Name)
                logMessage(self.ctx, INFO, msg, 'Replicator', '_syncData()')
            result = all(results)
            print("Replicator.synchronize() 2 %s" % result)
        except Exception as e:
            print("Replicator.synchronize() ERROR: %s - %s" % (e, traceback.print_exc()))

    def _initUser(self, user):
        # In order to make the creation of files or directories possible quickly,
        # it is necessary to run the verification of the identifiers.
        self._checkNewIdentifier(user)
        # This procedure corresponds to the initial pull for a new User (ie: without Token)
        rejected, pages, rows, count, start = self._updateDrive(user)
        print("Replicator._initUser() 1 count: %s - %s pages - %s rows" % (count, pages, rows))
        msg = getMessage(self.ctx, 120, (pages, rows, count))
        logMessage(self.ctx, INFO, msg, 'Replicator', '_syncData()')
        if len(rejected):
            msg = getMessage(self.ctx, 121, len(rejected))
            logMessage(self.ctx, SEVERE, msg, 'Replicator', '_syncData()')
        for item in rejected:
            msg = getMessage(self.ctx, 122, item)
            logMessage(self.ctx, SEVERE, msg, 'Replicator', '_syncData()')
        print("Replicator._initUser() 2 %s" % count)
        self.fullPull = True
        return start

    def _pullData(self, user):
        results = []
        self._checkNewIdentifier(user)
        print("Replicator._pullData() 1")
        parameter = user.Provider.getRequestParameter('getChanges', user.MetaData)
        enumerator = user.Request.getIterator(parameter, None)
        print("Replicator._pullData() 2 %s - %s" % (enumerator.PageCount, enumerator.SyncToken))
        while enumerator.hasMoreElements():
            response = enumerator.nextElement()
            print("Replicator._pullData() 3 %s" % response)
        print("Replicator._pullData() 4 %s - %s" % (enumerator.PageCount, enumerator.SyncToken))
        return results

    def _pushData(self, start):
        try:
            results = []
            operations = {'TitleUpdated': [], 'SizeUpdated': [], 'TrashedUpdated': []}
            end = parseDateTime()
            for item in self.DataBase.getSynchronizeItems(start, end):
                user = self.Users.get(item.getValue('UserName'), None)
                if user is not None:
                    print("Replicator._pushData() Insert/Update: %s Items: %s - %s - %s - %s" % (item.getValue('Title'),
                                                                                                 item.getValue('TitleUpdated'),
                                                                                                 item.getValue('SizeUpdated'),
                                                                                                 item.getValue('TrashedUpdated'),
                                                                                                 item.getValue('Size')))
                    chunk = user.Provider.Chunk
                    url = user.Provider.SourceURL
                    uploader = user.Request.getUploader(chunk, url, self)
                    results.append(self._synchronizeItems(user, uploader, item, operations))
            print("Replicator._pushData() Created / Updated Items: %s" % (results, ))
            if all(results):
                self.DataBase.updateUserTimeStamp(end)
                print("Replicator._pushData() Created / Updated Items OK")
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

    def _updateDrive(self, user):
        separator = ','
        start = parseDateTime()
        rootid = user.RootId
        call = self.DataBase.getDriveCall(user.Id, separator, 1, start)
        orphans, pages, rows, count, token = self._getDriveContent(call, user.Provider, user.Request, rootid, separator, start)
        #rows += self._filterParents(call, user.Provider, items, parents, roots, separator, start)
        rejected = self._getRejectedItems(user.Provider, orphans, rootid)
        if count > 0:
            call.executeBatch()
        call.close()
        end = parseDateTime()
        self.DataBase.updateUserTimeStamp(end)
        user.Provider.updateDrive(self.DataBase, user.MetaData, token)
        return rejected, pages, rows, count, end

    def _getDriveContent(self, call, provider, request, rootid, separator, start):
        orphans = OrderedDict()
        roots = [rootid]
        pages = 0
        rows = 0
        count = 0
        token = ''
        provider.initDriveContent(rootid)
        while provider.hasDriveContent():
            parameter = provider.getRequestParameter('getDriveContent', provider.getDriveContent())
            enumerator = request.getIterator(parameter, None)
            while enumerator.hasMoreElements():
                item = enumerator.nextElement()
                if self._setDriveCall(call, provider, roots, orphans, rootid, item, separator, start):
                    provider.setDriveContent(item)
                    count += 1
            pages += enumerator.PageCount
            rows += enumerator.RowCount
            token = enumerator.SyncToken
        print("Replicator._getDriveContent() %s" % token)
        return orphans, pages, rows, count, token

    def _setDriveCall(self, call, provider, roots, orphans, rootid, item, separator, timestamp):
        itemid = provider.getItemId(item)
        parents = provider.getItemParent(item, rootid)
        if not all(parent in roots for parent in parents):
            orphans[itemid] = item
            return False
        roots.append(itemid)
        self.DataBase.setDriveCall(call, provider, item, itemid, parents, separator, timestamp)
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

    def _synchronizeItems(self, user, uploader, item, operations):
        try:
            response = False
            itemid = item.getValue('Id')
            # INSERT procedures, new files and folders are synced here.
            if all((item.getValue(p) for p in operations)):
                mediatype = item.getValue('MediaType')
                if user.Provider.isFolder(mediatype):
                    response = user.Provider.createFolder(user.Request, item)
                    print("Replicator._synchronizeItems() createFolder: %s - %s" % (item.getValue('Title'), response))
                elif user.Provider.isLink(mediatype):
                    pass
                elif user.Provider.isDocument(mediatype):
                    if user.Provider.createFile(user.Request, uploader, item):
                        if itemid not in operations.get('SizeUpdated'):
                            response = user.Provider.uploadFile(user.Request, uploader, item, True)
                            operations.get('SizeUpdated').append(itemid)
                        else:
                            response = True
                        print("Replicator._synchronizeItems() create/uploadFile: %s - %s" % (item.getValue('Title'), response))
            # UPDATE procedures, only a few properties are synchronized: (Size, Title, Trashed)
            elif item.getValue('TitleUpdated'):
                if itemid not in operations.get('TitleUpdated'):
                    response = user.Provider.updateTitle(user.Request, item)
                    operations.get('TitleUpdated').append(itemid)
                else:
                    response = True
                print("Replicator._synchronizeItems() updateTitle: %s - %s" % (item.getValue('Title'), response))
            elif item.getValue('SizeUpdated'):
                if itemid not in operations.get('SizeUpdated'):
                    response = user.Provider.uploadFile(user.Request, uploader, item, False)
                    operations.get('SizeUpdated').append(itemid)
                else:
                    response = True
                print("Replicator._synchronizeItems() uploadFile: %s - %s" % (item.getValue('Title'), response))
            elif item.getValue('TrashedUpdated'):
                if itemid not in operations.get('TrashedUpdated'):
                    response = user.Provider.updateTrashed(user.Request, item)
                    operations.get('TrashedUpdated').append(itemid)
                else:
                    response = True
                print("Replicator._synchronizeItems() updateTrashed: %s - %s" % (item.getValue('Title'), response))
            else:
                # UPDATE of other properties (TimeStamp...)
                print("Replicator._synchronizeItems() Update None")
                response = True
            #logMessage(self.ctx, INFO, msg, "Replicator", "_synchronizeItems()")
            return response
        except Exception as e:
            msg = "ERROR: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, "Replicator", "_synchronizeItems()")

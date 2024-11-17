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

from com.sun.star.util import XCancellable
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from .unolib import KeyMap

from .unotool import getConfiguration
from .unotool import getDateTime

from .database import DataBase

from .configuration import g_identifier
from .configuration import g_filter
from .configuration import g_synclog

from .logger import getLogger
g_basename = 'Replicator'

from threading import Thread
from threading import Event
from threading import Condition
import traceback


class Replicator(unohelper.Base):
    def __init__(self, ctx, database, provider, users):
        self._ctx = ctx
        self.DataBase = database
        self.Provider = provider
        self.Users = users
        self._logger = getLogger(ctx, g_synclog, g_basename)
        self._started = Event()
        self._paused = Event()
        self._disposed = Event()
        self._count = 0
        self._new = False
        self._default = self.DataBase.getDefaultType()
        self._thread = Thread(target=self._replicate)
        self._thread.start()

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

    def _replicate(self):
        print("replicator.run()1")
        try:
            print("replicator.run()1 begin ****************************************")
            while not self._disposed.is_set():
                print("replicator.run()2 wait to start ****************************************")
                self._started.wait()
                if not self._disposed.is_set():
                    print("replicator.run()3 synchronize started ****************************************")
                    self._count = 0
                    self._synchronize()
                    self.DataBase.dispose()
                    print("replicator.run()4 synchronize ended query=%s *******************************************" % self._count)
                    if self._started.is_set():
                        print("replicator.run()5 start waitting *******************************************")
                        self._paused.clear()
                        self._paused.wait(self._getReplicateTimeout())
                        print("replicator.run()5 end waitting *******************************************")
            print("replicator.run()6 canceled *******************************************")
        except Exception as e:
            msg = "Replicator run(): Error: %s" % traceback.print_exc()
            print(msg)

    def _synchronize(self):
        if self.Provider.isOffLine():
            self._logger.logprb(SEVERE, 'Replicator', '_synchronize()', 201)
        else:
            self._syncData()

    def _syncData(self):
        result = KeyMap()
        timestamp = getDateTime(False)

        self.DataBase.setLoggingChanges(False)
        self.DataBase.saveChanges()
        self.DataBase.Connection.setAutoCommit(False)

        for user in self.Users.values():
            if not self._canceled():
                self._logger.logprb(INFO, 'Replicator', '_synchronize()', 211, user.Account)
                result.setValue(user.Account, self._syncUser(user, timestamp))
                self._logger.logprb(INFO, 'Replicator', '_synchronize()', 212, user.Account)
        if not self._canceled():
            self.DataBase.executeBatchCall()
            self.DataBase.Connection.commit()
            for account in result.getKeys():
                user = self.Users[account]
                user.MetaData += result.getValue(account)
                print("Replicator._syncData(): %s" % (user.MetaData, ))
                self._syncConnection(user, timestamp)
        self.DataBase.executeBatchCall()

        self.DataBase.Connection.commit()
        self.DataBase.setLoggingChanges(True)
        self.DataBase.saveChanges()
        self.DataBase.Connection.setAutoCommit(True)

    def _syncUser(self, user, timestamp):
        result = KeyMap()
        try:
            if self._canceled():
                return result
            result += self._syncPeople(user, timestamp)
            if self._canceled():
                return result
            result += self._syncGroup(user, timestamp)
        except Exception as e:
            self._logger.logprb(SEVERE, 'Replicator', '_synchronize()', 221, e, traceback.print_exc())
        return result

    def _syncPeople(self, user, timestamp):
        token = None
        pages = update = delete = 0
        parameter = self.Provider.getRequestParameter(user.Request, 'People', user)
        iterator = self.Provider.parsePeople(user.Request, parameter)
        map = self.DataBase.getFieldsMap('People', False)
        self.DataBase.mergePeopleData(iterator, timestamp)
        self._logger.logprb(INFO, 'Replicator', '_syncPeople()', 231, pages, update, delete)
        self._count += update + delete
        print("replicator._syncPeople() 1 %s" % 'Resource')
        return parameter.SyncToken

    def _syncPeople1(self, user, timestamp):
        token = None
        method = {'Name': 'People',
                  'PrimaryKey': 'Resource',
                  'ResourceFilter': (),
                  'Deleted': (('metadata','deleted'), True),
                  'Filter': (('metadata', 'primary'), True),
                  'Skip': ('Type', 'metadata')}
        pages = update = delete = 0
        parameter = self.Provider.getRequestParameter(user.Request, method['Name'], user)
        parser = None
        #parser = DataParser(self.DataBase, self.Provider, method['Name'])
        map = self.DataBase.getFieldsMap(method['Name'], False)
        enumerator = user.Request.getEnumeration(parameter, parser)
        while not self._canceled() and enumerator.hasMoreElements():
            response = enumerator.nextElement()
            if response.IsPresent:
                pages += 1
                u, d, t = self._syncResponse(method, user, map, response.Value, timestamp)
                update += u
                delete += d
                token = t
        self._logger.logprb(INFO, 'Replicator', '_syncPeople()', 231, pages, update, delete)
        self._count += update + delete
        print("replicator._syncPeople() 1 %s" % method['PrimaryKey'])
        return token

    def _syncGroup(self, user, timestamp):
        token = None
        method = {'Name': 'Group',
                  'PrimaryKey': 'Resource',
                  'ResourceFilter': (('groupType', ), g_filter),
                  'Deleted': (('metadata','deleted'), True)}
        pages = update = delete = 0
        parameter = self.Provider.getRequestParameter(user.Request, method['Name'], user)
        parser = DataParser(self.DataBase, self.Provider, method['Name'])
        map = self.DataBase.getFieldsMap(method['Name'], False)
        enumerator = user.Request.getEnumeration(parameter, parser)
        while not self._canceled() and enumerator.hasMoreElements():
            response = enumerator.nextElement()
            if response.IsPresent:
                pages += 1
                u, d, t = self._syncResponse(method, user, map, response.Value, timestamp)
                update += u
                delete += d
                token = t
        self._logger.logprb(INFO, 'Replicator', '_syncGroup()', 241, pages, update, delete)
        self._count += update + delete
        return token

    def _syncConnection(self, user, timestamp):
        token = None
        pages = update = delete = 0
        groups = self.DataBase.getUpdatedGroups(user, 'contactGroups/')
        if groups.Count > 0:
            for group in groups:
                name = group.getValue('Name')
                group = group.getValue('Group')
                self.DataBase.createGroupView(user, name, group)
            print("replicator._syncConnection(): %s" % ','.join(groups.getKeys()))
            method = {'Name': 'Connection',
                      'PrimaryKey': 'Group',
                      'ResourceFilter': ()}
            parameter = self.Provider.getRequestParameter(user.Request, method['Name'], groups)
            parser = DataParser(self.DataBase, self.Provider, method['Name'])
            map = self.DataBase.getFieldsMap(method['Name'], False)
            request = user.Request.getRequest(parameter, parser)
            response = request.execute()
            if response.IsPresent:
                pages += 1
                u, d, token = self._syncResponse(method, user, map, response.Value, timestamp)
                update += u
        else:
            print("replicator._syncConnection(): nothing to sync")
        self._logger.logprb(INFO, 'Replicator', '_syncConnection()', 251, pages, len(groups), update)
        self._count += update
        return token

    def _syncResponse(self, method, user, map, data, timestamp):
        update = delete = 0
        token = None
        for key in data.getKeys():
            field = map.getValue(key).getValue('Type')
            if field == 'Field':
                token = self.DataBase.updateSyncToken(user, key, data, timestamp)
            elif field != 'Header':
                u, d = self._mergeResponse(method, user, map, key, data.getValue(key), timestamp, field)
                update += u
                delete += d
        return update, delete, token

    def _mergeResponse(self, method, user, map, key, data, timestamp, field):
        update = delete = 0
        if field == 'Sequence':
            f = map.getValue(key).getValue('Table')
            for d in data:
                u , d, = self._mergeResponse(method, user, map, key, d, timestamp, f)
                update += u
                delete += d
        elif data.hasValue(method['PrimaryKey']):
            if self._filterResponse(data, *method['ResourceFilter']):
                resource = data.getValue(method['PrimaryKey'])
                update, delete = self._getMerge(method, resource, user, map, data, timestamp)
        return update, delete

    def _filterResponse(self, data, filters=(), value=None, index=0):
        if index < len(filters):
            filter = filters[index]
            if data.hasValue(filter):
                return self._filterResponse(data.getValue(filter), filters, value, index + 1)
            return False
        return data if value is None else data == value

    def _getMerge(self, method, resource, user, map, data, timestamp):
        name = method['Name']
        if name == 'People':
            update, delete = self._mergePeople(method, resource, user, map, data, timestamp)
        elif name == 'Group':
            update, delete = self._mergeGroup(method, resource, user, map, data, timestamp)
        elif name == 'Connection':
            update, delete = self._mergeConnection(method, resource, user, map, data, timestamp)
        return update, delete

    def _mergePeople(self, method, resource, user, map, data, timestamp):
        update = delete = 0
        deleted = self._filterResponse(data, *method['Deleted'])
        update, delete = self.DataBase.mergePeople(user, resource, timestamp, deleted)
        for key in data.getKeys():
            if key == method['PrimaryKey']:
                continue
            f = map.getValue(key).getValue('Type')
            update += self._mergePeopleData(method, map, resource, key, data.getValue(key), timestamp, f)
        return update, delete

    def _mergeGroup(self, method, resource, user, map, data, timestamp):
        update = delete = 0
        name = data.getDefaultValue('Name', '')
        deleted = self._filterResponse(data, *method['Deleted'])
        update, delete = self.DataBase.mergeGroup(user, resource, name, timestamp, deleted)
        return update, delete

    def _mergeConnection(self, method, resource, user, map, data, timestamp):
        update = self.DataBase.mergeConnection(user, resource, timestamp)
        return update, 0

    def _mergePeopleData(self, method, map, resource, key, data, timestamp, field):
        update = 0
        if field == 'Sequence':
            f = map.getValue(key).getValue('Table')
            for d in data:
                update += self._mergePeopleData(method, map, resource, key, d, timestamp, f)
        elif field == 'Tables':
            if self._filterResponse(data, *method['Filter']):
                default = self._default.get(key, None)
                typename = data.getDefaultValue('Type', default)
                for label in data.getKeys():
                    if label in method['Skip']:
                        continue
                    value = data.getValue(label)
                    update += self.DataBase.mergePeopleData(key, resource, typename, label, value, timestamp)
        return update

    def _getReplicateTimeout(self):
        configuration = getConfiguration(self._ctx, g_identifier, False)
        timeout = configuration.getByName('ReplicateTimeout')
        return timeout

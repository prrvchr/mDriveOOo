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

import unohelper

from com.sun.star.sdbcx import CheckOption

from .dbinit import createStaticTables
from .dbinit import createStaticIndexes
from .dbinit import createStaticForeignKeys
from .dbinit import getForeignKeys
from .dbinit import getIndexes
from .dbinit import getTableNames
from .dbinit import getTables
from .dbinit import setStaticTable

from .dbtool import checkConnection
from .dbtool import createForeignKeys
from .dbtool import createTables
from .dbtool import createIndexes
from .dbtool import createRoleAndPrivileges
from .dbtool import createViews
from .dbtool import executeQueries
from .dbtool import getConnectionInfos
from .dbtool import getDataBaseForeignKeys
from .dbtool import getDataBaseIndexes
from .dbtool import getDataBaseTables
from .dbtool import getDataSourceConnection
from .dbtool import getDriverInfos
from .dbtool import getTablePrivileges

from ..runner import RunnerException
from ..runner import Task

from ..unotool import checkVersion
from ..unotool import getSimpleFile
from ..unotool import getStringResource

from ..dbconfig import g_catalog
from ..dbconfig import g_csv
from ..dbconfig import g_drvinfos
from ..dbconfig import g_schema
from ..dbconfig import g_version

from ..configuration import g_identifier
from ..configuration import g_resource

import traceback


class DBCheck(Task):
    def __init__(self, ctx, path, url):
        super().__init__()
        self._url = url
        self.path = path
        self._exists = getSimpleFile(ctx).exists(self.path)
        self._success = False
        self._version = None
        self._statics = None
        self._tables = None
        self._connection = None
        self._connected = False
        self._statement = None
        self._callback = None
        self.total = 3
        self.resolver = getStringResource(ctx, g_identifier, g_resource, 'dbtool')
        self.label1 = self.resolver.resolveString(10101)
        self.label2 = self.resolver.resolveString(10102)

    def withCallback(self, callback):
        self._callback = callback
        return self

    def getHeader(self, **kwargs):
        return self.resolver.resolveString(10201).format(**kwargs)

    def setReport(self, reports, success):
        result = self._getResult()
        if not success:
            reports.append((result, '', False))
        return result, ''

    def callback(self, success=True, error=None):
        if self._callback:
            self._callback(self._getSuccess(success), error)

    def stepGetConnection(self, ctx, user, pwd, infos=None):
        new = not self._exists
        try:
            if new:
                infos = getDriverInfos(ctx, self._url, g_drvinfos)
            self._connection = getDataSourceConnection(ctx, self.path, user, pwd, self._url, infos)
        except Exception as e:
            trace = traceback.format_exc()
            raise RunnerException(e, trace)

    def stepCheckConnection(self, ctx):
        new = not self._exists
        if self._connection:
            try:
                self._version = self._connection.getMetaData().getDriverVersion()
                if not checkConnection(self._connection, self._version, g_version, new):
                    self._connection.close()
                    self._connection = None
                else:
                    self._connected = True
                    if new:
                        self._tables = self._connection.getTables()
                        self._statement = self._connection.createStatement()
                    else:
                        self._connection.close()
                        self._connection = None
                        self._success = True
            except Exception as e:
                trace = traceback.format_exc()
                raise RunnerException(e, trace)

    def stepCreateStaticTables(self, tables):
        try:
            success, statics = createStaticTables(g_catalog, g_schema, self._tables, tables)
            if success:
                self._statics = statics
        except Exception as e:
            trace = traceback.format_exc()
            raise RunnerException(e, trace)

    def stepCreateStaticIndexes(self):
        try:
            createStaticIndexes(g_catalog, g_schema, self._tables)
        except Exception as e:
            trace = traceback.format_exc()
            raise RunnerException(e, trace)

    def stepCreateStaticForeignKeys(self, foreignkeys):
        try:
            createStaticForeignKeys(g_catalog, g_schema, self._tables, foreignkeys)
        except Exception as e:
            trace = traceback.format_exc()
            raise RunnerException(e, trace)

    def stepSetStaticTable(self):
        try:
            setStaticTable(self._statement, self._statics, g_csv, True)
        except Exception as e:
            trace = traceback.format_exc()
            raise RunnerException(e, trace)

    def stepCreateTables(self):
        try:
            infos = getConnectionInfos(self._connection, 'AutoIncrementCreation', 'RowVersionCreation')
            createTables(self._tables, getDataBaseTables(self._connection, self._statement, getTables(), getTableNames(), *infos))
        except Exception as e:
            trace = traceback.format_exc()
            raise RunnerException(e, trace)

    def stepCreateIndexes(self):
        try:
            createIndexes(self._tables, getDataBaseIndexes(self._statement, getIndexes()))
        except Exception as e:
            trace = traceback.format_exc()
            raise RunnerException(e, trace)

    def stepCreateForeignKeys(self):
        try:
            createForeignKeys(self._tables, getDataBaseForeignKeys(self._statement, getForeignKeys()))
        except Exception as e:
            trace = traceback.format_exc()
            raise RunnerException(e, trace)

    def stepCreateRoleAndPrivileges(self, privileges):
        try:
            groups = self._connection.getGroups()
            createRoleAndPrivileges(self._tables, groups, privileges(self._statement))
        except Exception as e:
            trace = traceback.format_exc()
            raise RunnerException(e, trace)

    def stepCreateFunctions(self, ctx, functions, *options):
        try:
            executeQueries(ctx, self._statement, functions, 'create%s', *options)
        except Exception as e:
            trace = traceback.format_exc()
            raise RunnerException(e, trace)

    def stepCreateViews(self, ctx, views):
        try:
            createViews(self._connection.getViews(), views(ctx, self._connection))
        except Exception as e:
            trace = traceback.format_exc()
            raise RunnerException(e, trace)

    def stepCreateProcedures(self, ctx, procedures, *options):
        try:
            executeQueries(ctx, self._statement, procedures, 'create%s', *options)
        except Exception as e:
            trace = traceback.format_exc()
            raise RunnerException(e, trace)

    def stepFinalize(self, save=False):
        try:
            if self._statement:
                self._statement.close()
                self._statement = None
            if self._connection:
                if save:
                    self._connection.getParent().DatabaseDocument.storeAsURL(self.path, ())
                    self._success = True
                self._connection.close()
                self._connection = None
        except Exception:
            pass

    def _getStepGetConnection(self, ctx, user, pwd):
        return 10301, (), self.stepGetConnection, ctx, user, pwd

    def _getStepCheckConnection(self, ctx):
        return 10401, (), self.stepCheckConnection, ctx

    def _getStepCreateStaticTables(self, tables=None):
        return 10501, (), self.stepCreateStaticTables, tables

    def _getStepCreateStaticIndexes(self):
        return 10601, (), self.stepCreateStaticIndexes

    def _getStepCreateStaticForeignKeys(self, foreignkeys=None):
        return 10701, (), self.stepCreateStaticForeignKeys, foreignkeys

    def _getStepSetStaticTable(self):
        return 10801, (), self.stepSetStaticTable

    def _getStepCreateTables(self):
        return 10901, (), self.stepCreateTables

    def _getstepCreateIndexes(self):
        return 11001, (), self.stepCreateIndexes

    def _getstepCreateForeignKeys(self):
        return 11101, (), self.stepCreateForeignKeys

    def _getstepCreateRoleAndPrivileges(self, privileges):
        return 11201, (), self.stepCreateRoleAndPrivileges, privileges

    def _getStepCreateFunctions(self, ctx, functions, *options):
        return 11301, (), self.stepCreateFunctions, ctx, functions, *options

    def _getStepCreateViews(self, ctx, views):
        return 11401, (), self.stepCreateViews, ctx, views

    def _getStepCreateProcedures(self, ctx, procedures, *options):
        return 11501, (), self.stepCreateProcedures, ctx, procedures, *options

    def _getStepFinalize(self, save):
        return 11601, (), self.stepFinalize, save

    def _getResult(self):
        if not self._connected:
            code = 11701 if checkVersion(self._version, g_version) else 11702
        elif self._success:
            code = 11703 if self._exists else 11704
        else:
            code = 11705
        return self.resolver.resolveString(code)

    def _getSuccess(self, success):
        return success and self._success


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

from .dbtool import DBCheck

from .dbinit import getDataBaseUrl
from .dbinit import getDataSourceUrl
from .dbinit import getForeignKeys
from .dbinit import getFunctions
from .dbinit import getDefaultPrivileges
from .dbinit import getProcedures
from .dbinit import getStaticTables
from .dbinit import getViews
from .dbinit import getViewPrivileges

from .dbconfig import g_queries

import traceback


class DBSetup(DBCheck):
    def __init__(self, ctx, user='', pwd=''):
        super().__init__(ctx, getDataSourceUrl(ctx), getDataBaseUrl(ctx))
        self.steps = self._getSteps(ctx, user, pwd)

    def _getSteps(self, ctx, user, pwd):
        yield self._getStepGetConnection(ctx, user, pwd)
        yield self._getStepCheckConnection(ctx)
        if self._connection:
            self.total += 1
            yield self._getStepCreateStaticTables(getStaticTables())
            if self._statics:
                self.total += 11
                yield self._getStepCreateStaticIndexes()
                yield self._getStepCreateStaticForeignKeys(getForeignKeys())
                yield self._getStepSetStaticTable()
                yield self._getStepCreateTables()
                yield self._getstepCreateIndexes()
                yield self._getstepCreateForeignKeys()
                yield self._getstepCreateRoleAndPrivileges(getDefaultPrivileges)
                yield self._getStepCreateFunctions(ctx, getFunctions(), g_queries)
                yield self._getStepCreateViews(ctx, getViews)
                yield self._getstepCreateRoleAndPrivileges(getViewPrivileges)
                yield self._getStepCreateProcedures(ctx, getProcedures(), g_queries)
        yield self._getStepFinalize(True)


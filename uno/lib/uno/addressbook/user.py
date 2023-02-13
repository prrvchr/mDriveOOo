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

from com.sun.star.ucb.ConnectionMode import OFFLINE
from com.sun.star.ucb.ConnectionMode import ONLINE

from com.sun.star.sdbc import XRestUser

from .oauth2lib import getRequest
from .oauth2lib import g_oauth2

from .unotool import executeDispatch

from .dbtool import getSqlException

from .logger import getMessage
g_message = 'datasource'

import traceback


class User(unohelper.Base,
           XRestUser):
    def __init__(self, ctx, database, provider, name, password=''):
        self._ctx = ctx
        self.Fields = database.getUserFields()
        #url = 'gcontact:request'
        #executeDispatch(ctx, url)
        self.Request = getRequest(ctx, provider.Host, name)
        self.MetaData = database.selectUser(name)
        if self._isNew():
            self.MetaData = self._getMetaData(database, provider, name)
            self._initUser(database, password)

    @property
    def People(self):
        return self.MetaData.getDefaultValue('People', None)
    @property
    def Resource(self):
        return self.MetaData.getDefaultValue('Resource', None)
    @property
    def Group(self):
        return self.MetaData.getDefaultValue('Group', None)
    @property
    def Account(self):
        return self.MetaData.getDefaultValue('Account', '')
    @property
    def Name(self):
        return self.Account.split('@').pop(0)
    @property
    def PeopleSync(self):
        return self.MetaData.getDefaultValue('PeopleSync', None)
    @property
    def GroupSync(self):
        return self.MetaData.getDefaultValue('GroupSync', None)

    def _isNew(self):
        return self.MetaData is None

    def _getMetaData(self, database, provider, name):
        if self.Request is None:
            raise self._getSqlException(1003, 1105, g_oauth2)
        if provider.isOffLine():
            raise self._getSqlException(1004, 1108, name)
        data = provider.getUser(self.Request, self.Fields)
        if not data.IsPresent:
            raise self._getSqlException(1006, 1107, name)
        userid = provider.getUserId(data.Value)
        return database.insertUser(userid, name)

    def _initUser(self, database, password):
        credential = self._getCredential(password)
        if not database.createUser(*credential):
            raise self._getSqlException(1005, 1106, name)
        format = {'Schema': self.Resource,
                    'User': self.Account,
                    'GroupId': self.Group}
        database.initUser(format)

    def _getCredential(self, password):
        return self.Account, password

    def _getSqlException(self, state, code, *args):
        state = getMessage(self._ctx, g_message, state)
        msg = getMessage(self._ctx, g_message, code, args)
        error = getSqlException(state, code, msg, self)
        return error

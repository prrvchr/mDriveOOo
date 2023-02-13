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

from com.sun.star.ucb import IllegalIdentifierException

from com.sun.star.ucb import XRestUser

from .identifier import Identifier

from .unolib import KeyMap

from .oauth2lib import getRequest
from .oauth2lib import g_oauth2

from .database import DataBase

from .logger import logMessage
from .logger import getMessage
g_message = 'user'

import traceback


class User(unohelper.Base,
           XRestUser):
    def __init__(self, ctx, source, name, lock, database=None):
        self._ctx = ctx
        self._name = name
        self._lock = lock
        self._identifiers = {}
        self.DataBase = database
        self.Provider = source.Provider
        self.Request = getRequest(self._ctx, self.Provider.Scheme, name)
        self.MetaData = source.DataBase.selectUser(name)
        self.CanAddChild = not self.Provider.GenerateIds
        self._initialized = database is not None
        msg = getMessage(self._ctx, g_message, 101)
        logMessage(self._ctx, INFO, msg, "User", "__init__()")

    @property
    def Name(self):
        return self._name
    @property
    def Id(self):
        return self.MetaData.getDefaultValue('UserId', None)
    @property
    def RootId(self):
        return self.MetaData.getDefaultValue('RootId', None)
    @property
    def RootName(self):
        return self.MetaData.getDefaultValue('RootName', None)
    @property
    def Token(self):
        return self.MetaData.getDefaultValue('Token', '')

    # XRestUser
    def isValid(self):
        return self.Id is not None
    def setDataBase(self, datasource, sync, password=''):
        self.DataBase = DataBase(self._ctx, datasource, self.Name, password, sync)
    def getCredential(self, password):
        return self.Name, password

    def isInitialized(self):
        return self._initialized

    def initialize(self, database, password=''):
        if self.Request is None:
            msg = getMessage(self._ctx, g_message, 111, g_oauth2)
            raise IllegalIdentifierException(msg, self)
        if self.MetaData is None:
            if not self.Provider.isOnLine():
                msg = getMessage(self._ctx, g_message, 112, self._name)
                raise IllegalIdentifierException(msg, self)
            data = self.Provider.getUser(self.Request, self._name)
            if not data.IsPresent:
                msg = getMessage(self._ctx, g_message, 113, self._name)
                raise IllegalIdentifierException(msg, self)
            root = self.Provider.getRoot(self.Request, data.Value)
            if not root.IsPresent:
                msg = getMessage(self._ctx, g_message, 113, self._name)
                raise IllegalIdentifierException(msg, self)
            self.MetaData = database.insertUser(self.Provider, data.Value, root.Value)
            if not database.createUser(self._name, password):
                msg = getMessage(self._ctx, g_message, 114, self._name)
                raise IllegalIdentifierException(msg, self)
        self.DataBase = DataBase(self._ctx, database.getDataSource(), self._name, '', self._lock)
        self._initialized = True
        self._lock.set()

    def getIdentifier(self, factory, url):
        if url in self._identifiers:
            identifier = self._identifiers[url]
        else:
            identifier = Identifier(self._ctx, factory, self, url)
            self._identifiers[url] = identifier
        return identifier
    def clearIdentifier(self, url):
        if url in self._identifiers:
            del self._identifiers[url]


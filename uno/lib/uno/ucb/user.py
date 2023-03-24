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

from com.sun.star.ucb.ContentAction import EXCHANGED
from com.sun.star.ucb.ContentAction import REMOVED

from com.sun.star.ucb import IllegalIdentifierException

from com.sun.star.ucb import XRestUser

from .identifier import Identifier

from .unolib import KeyMap

from .oauth2lib import getOAuth2UserName
from .oauth2lib import getRequest
from .oauth2lib import g_oauth2

from .unotool import createService

from .database import DataBase

from .logger import getLogger

from .configuration import g_defaultlog

g_basename = 'user'

import traceback


class User(unohelper.Base,
           XRestUser):
    def __init__(self, ctx, source, name, sync, lock, init=False):
        self._ctx = ctx
        self._name = name
        self._sync = sync
        self._lock = lock
        self._expired = None
        self.DataBase = source.DataBase if init else None
        self.Provider = source.Provider
        self.CanAddChild = not self.Provider.GenerateIds
        if name is not None:
            self.Request = getRequest(ctx, self.Provider.Scheme, name)
        if init:
            self.MetaData = source.DataBase.selectUser(name)
        self._initialized = init
        self._identifiers = {}
        self._logger = getLogger(ctx, g_defaultlog, g_basename)
        self._logger.logprb(INFO, 'User', '__init__()', 101)

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

    def initialize(self, datasource, url, password=''):
        print("User.initialize() 1")
        if self.Name is None:
            self._setUserName(datasource, url)
        if self.Request is None:
            msg = self._logger.resolveString(111, g_oauth2)
            raise IllegalIdentifierException(msg, self)
        print("User.initialize() 2")
        self.MetaData = datasource.DataBase.selectUser(self._name)
        print("User.initialize() 3")
        if self.MetaData is None:
            if not self.Provider.isOnLine():
                msg = self._logger.resolveString(112, self._name)
                raise IllegalIdentifierException(msg, self)
            data = self.Provider.getUser(self.Request, self._name)
            if not data.IsPresent:
                msg = self._logger.resolveString(113, self._name)
                raise IllegalIdentifierException(msg, self)
            root = self.Provider.getRoot(self.Request, data.Value)
            if not root.IsPresent:
                msg = self._logger.resolveString(113, self._name)
                raise IllegalIdentifierException(msg, self)
            self.MetaData = datasource.DataBase.insertUser(self.Provider, data.Value, root.Value)
            if not datasource.DataBase.createUser(self._name, password):
                msg = self._logger.resolveString(114, self._name)
                raise IllegalIdentifierException(msg, self)
        self.DataBase = DataBase(self._ctx, datasource.DataBase.getDataSource(), self._name, password, self._sync)
        print("User.initialize() 4")
        datasource.addUser(self)
        print("User.initialize() 5")
        self._initialized = True
        self._sync.set()
        print("User.initialize() 6")

    def getIdentifier(self, url):
        identifier = None
        if self._expired is not None and url.startswith(self._expired):
            self._removeIdentifiers()
        else:
            identifier = self._identifiers.get(url)
        if identifier is None:
            identifier = Identifier(self._ctx, self, url)
        return identifier

    def updateIdentifier(self, event):
        pass

    def addIdentifier(self, identifier):
        key = identifier.getContentIdentifier()
        print("User.addIdentifier() Uri: %s - Id: %s" % (key, identifier.Id))
        if key not in self._identifiers:
            with self._lock:
                self._identifiers[key] = identifier

    def expireIdentifier(self, url):
        # FIXME: We need to remove all the child of a resource (if it's a folder)
        self._expired = url

    def _removeIdentifiers(self):
        for url in tuple(self._identifiers.keys()):
            if url.startswith(self._expired):
                with self._lock:
                    if url in self._identifiers:
                        del self._identifiers[url]
        self._expired = None

# Internal use of method
    def _setUserName(self, datasource, url):
        name = getOAuth2UserName(self._ctx, self, self.Provider.Scheme)
        if not name:
            msg = self._logger.resolveString(121, url)
            raise IllegalIdentifierException(msg, self)
        self.Request = getRequest(self._ctx, self.Provider.Scheme, name)
        self._name = name


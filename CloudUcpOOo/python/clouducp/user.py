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

import uno
import unohelper

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb import XRestUser

from unolib import KeyMap
from unolib import getRequest

from .database import DataBase

from .logger import logMessage
from .logger import getMessage
g_message = 'user'

import traceback


class User(unohelper.Base,
           XRestUser):
    def __init__(self, ctx, source=None, name=None, database=None):
        self.ctx = ctx
        self.DataBase = database
        # Uri with Scheme but without a Path generate invalid user but we need
        # to return an Identifier, and raise an 'IllegalIdentifierException'
        # when ContentProvider try to get the Content...
        # (ie: ContentProvider.queryContent() -> Identifier.getContent())
        if source is None:
            self.Provider = None
            self.Request = None
            self.MetaData = KeyMap()
        else:
            self.Provider = source.Provider
            self.Request = getRequest(self.ctx, self.Provider.Scheme, name)
            self.MetaData = source.DataBase.selectUser(name)
            self.CanAddChild = not self.Provider.GenerateIds
        msg = getMessage(self.ctx, g_message, 101)
        logMessage(self.ctx, INFO, msg, "User", "__init__()")

    @property
    def Id(self):
        return self.MetaData.getDefaultValue('UserId', None)
    @property
    def Name(self):
        return self.MetaData.getDefaultValue('UserName', None)
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
    def setDataBase(self, datasource, password, sync):
        name, password = self.getCredential(password)
        self.DataBase = DataBase(self.ctx, datasource, name, password, sync)
    def getCredential(self, password):
        return self.Name, password

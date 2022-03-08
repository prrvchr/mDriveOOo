#!
# -*- coding: utf_8 -*-

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

from com.sun.star.ucb import XContentIdentifierFactory
from com.sun.star.ucb import XContentProvider
from com.sun.star.ucb import XParameterizedContentProvider
from com.sun.star.ucb import IllegalIdentifierException

from com.sun.star.ucb import XRestContentProvider

from .oauth2lib import getOAuth2UserName

from .contenttools import getUrl
from .contenttools import getUri

from .datasource import DataSource
from .user import User

from .logger import logMessage
from .logger import getMessage
g_message = 'contentprovider'

import traceback
from threading import Event


class ContentProvider(unohelper.Base,
                      XContentIdentifierFactory,
                      XContentProvider,
                      XParameterizedContentProvider,
                      XRestContentProvider):
    def __init__(self, ctx, plugin):
        self.ctx = ctx
        self.Scheme = ''
        self.Plugin = plugin
        self.DataSource = None
        self.event = Event()
        self._currentUserName = None
        self._error = ''
        msg = getMessage(self.ctx, g_message, 101, self.Plugin)
        logMessage(self.ctx, INFO, msg, 'ContentProvider', '__init__()')

    def __del__(self):
       msg = getMessage(self.ctx, g_message, 171, self.Plugin)
       logMessage(self.ctx, INFO, msg, 'ContentProvider', '__del__()')

    # XParameterizedContentProvider
    def registerInstance(self, scheme, plugin, replace):
        msg = getMessage(self.ctx, g_message, 111, (scheme, plugin))
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'registerInstance()')
        datasource = DataSource(self.ctx, self.event, scheme, plugin)
        if not datasource.isValid():
            logMessage(self.ctx, SEVERE, datasource.Error, 'ContentProvider', 'registerInstance()')
            return None
        self.Scheme = scheme
        self.Plugin = plugin
        self.DataSource = datasource
        msg = getMessage(self.ctx, g_message, 112, (scheme, plugin))
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'registerInstance()')
        return self
    def deregisterInstance(self, scheme, argument):
        msg = getMessage(self.ctx, g_message, 161, scheme)
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'deregisterInstance()')

    # XContentIdentifierFactory
    def createContentIdentifier(self, url):
        try:
            url = getUrl(self.ctx, url)
            uri = getUri(self.ctx, url)
            user = self._getUser(uri, url)
            identifier = self.DataSource.getIdentifier(user, uri)
            print("ContentProvider.createContentIdentifier() %s" % identifier.getContentIdentifier())
            msg = getMessage(self.ctx, g_message, 131, url)
            logMessage(self.ctx, INFO, msg, 'ContentProvider', 'createContentIdentifier()')
            return identifier
        except Exception as e:
            msg = "Error: %s" % traceback.print_exc()
            print(msg)

    # XContentProvider
    def queryContent(self, identifier):
        try:
            url = identifier.getContentIdentifier()
            if not identifier.isValid():
                msg = getMessage(self.ctx, g_message, 141, (url, self._error))
                logMessage(self.ctx, SEVERE, msg, 'ContentProvider', 'queryContent()')
                raise IllegalIdentifierException(msg, identifier)
            content = identifier.getContent()
            self._currentUserName = identifier.User.Name
            msg = getMessage(self.ctx, g_message, 142, url)
            logMessage(self.ctx, INFO, msg, 'ContentProvider', 'queryContent()')
            return content
        except Exception as e:
            msg = "Error: %s" % traceback.print_exc()
            print(msg)

    def compareContentIds(self, id1, id2):
        ids = (id1.getContentIdentifier(), id2.getContentIdentifier())
        if id1.Id == id2.Id and id1.User.Id == id2.User.Id:
            msg = getMessage(self.ctx, g_message, 151, ids)
            compare = 0
        else:
            msg = getMessage(self.ctx, g_message, 152, ids)
            compare = -1
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'compareContentIds()')
        return compare

    def _getUser(self, uri, url):
        if uri is None:
            self._error = getMessage(self.ctx, g_message, 121, url)
            return User(self.ctx)
        if not uri.hasAuthority() or not uri.getPathSegmentCount():
            self._error = getMessage(self.ctx, g_message, 122, url)
            return User(self.ctx)
        name = self._getUserName(uri, url)
        if not name:
            self._error = getMessage(self.ctx, g_message, 123, url)
            return User(self.ctx)
        user = self.DataSource.getUser(name)
        if user is None:
            self._error = self.DataSource.Error
            return User(self.ctx)
        return user

    def _getUserName(self, uri, url):
        if uri.hasAuthority() and uri.getAuthority() != '':
            name = uri.getAuthority()
        elif self._currentUserName is not None:
            name = self._currentUserName
        else:
            name = getOAuth2UserName(self.ctx, self, uri.getScheme())
        return name

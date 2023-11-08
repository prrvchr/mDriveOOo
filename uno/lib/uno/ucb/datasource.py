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

from com.sun.star.util import XCloseListener
from com.sun.star.util import CloseVetoException

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb import IllegalIdentifierException

from .oauth2 import getOAuth2UserName

from .unotool import createService

from .ucp import User

from .provider import Provider

from .replicator import Replicator

from threading import Event
from threading import Lock
import traceback


class DataSource(unohelper.Base,
                 XCloseListener):
    def __init__(self, ctx, logger, database):
        self._ctx = ctx
        self._default = ''
        self._users = {}
        self._logger = logger
        self.Error = None
        self._sync = Event()
        self._lock = Lock()
        self._factory = createService(ctx, 'com.sun.star.uri.UriReferenceFactory')
        database.addCloseListener(self)
        folder, link = database.getContentType()
        self._provider = Provider(ctx, logger, folder, link)
        self.Replicator = Replicator(ctx, database.Url, self._provider, self._users, self._sync, self._lock)
        self.DataBase = database
        self._logger.logprb(INFO, 'DataSource', '__init__()', 301)

    # DataSource
    def getDefaultUser(self):
        return self._default

    # FIXME: Get called from ParameterizedProvider.queryContent()
    def queryContent(self, source, authority, identifier):
        user, path = self._getUser(source, identifier.getContentIdentifier(), authority)
        content = user.getContent(path, authority)
        return content

    # XCloseListener
    def queryClosing(self, source, ownership):
        if ownership:
            raise CloseVetoException('cant close', self)
        print("DataSource.queryClosing() ownership: %s" % ownership)
        if self.Replicator.is_alive():
            self.Replicator.cancel()
            self.Replicator.join()
        self.DataBase.shutdownDataBase(self.Replicator.fullPull())
        self._logger.logprb(INFO, 'DataSource', 'queryClosing()', 341, self._provider.Scheme)
    def notifyClosing(self, source):
        pass

    # Private methods
    def _getUser(self, source, url, authority):
        default = False
        uri = self._factory.parse(url)
        if uri is None:
            msg = self._logger.resolveString(321, url)
            raise IllegalIdentifierException(msg, source)
        if authority:
            if uri.hasAuthority() and uri.getAuthority() != '':
                name = uri.getAuthority()
            else:
                msg = self._logger.resolveString(322, url)
                raise IllegalIdentifierException(msg, source)
        elif self._default:
            name = self._default
        else:
            name = self._getUserName(source, url)
            default = True
        # User never change... we can cache it...
        if name in self._users:
            user = self._users[name]
            if not user.Request.isAuthorized():
                # The user's OAuth2 configuration has been deleted and
                # the OAuth2 configuration wizard has been canceled.
                msg = self._logger.resolveString(323, name)
                raise IllegalIdentifierException(msg, source)
        else:
            user = User(self._ctx, self._logger, source, self.DataBase,
                        self._provider, name, self._sync, self._lock)
            self._users[name] = user
        # FIXME: if the user has been instantiated then we can consider it as the default user
        if default:
            self._default = name
        return user, uri.getPath()

    def _getUserName(self, source, url):
        name = getOAuth2UserName(self._ctx, self, self._provider.Scheme)
        if not name:
            msg = self._logger.resolveString(331, url)
            raise IllegalIdentifierException(msg, source)
        return name


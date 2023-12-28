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

from .unotool import getUrlTransformer
from .unotool import getUriFactory
from .unotool import parseUrl

from .ucp import User
from .ucp import getExceptionMessage

from .provider import Provider

from .replicator import Replicator

from .configuration import g_extension
from .configuration import g_separator

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
        self._urifactory = getUriFactory(ctx)
        self._transformer = getUrlTransformer(ctx)
        database.addCloseListener(self)
        folder, link = database.getContentType()
        self._provider = Provider(ctx, logger, folder, link)
        self.Replicator = Replicator(ctx, database.Url, self._provider, self._users, self._sync, self._lock)
        self.DataBase = database
        self._logger.logprb(INFO, 'DataSource', '__init__()', 301)

    # DataSource
    def getDefaultUser(self):
        return self._default

    def parseIdentifier(self, identifier):
        url = self._getPresentationUrl(identifier.getContentIdentifier())
        return self._urifactory.parse(url)

    # FIXME: Get called from ParameterizedProvider.queryContent()
    def queryContent(self, source, authority, url):
        user, uri = self._getUser(source, authority, url)
        itemid = user.getItemByUri(uri)
        if itemid is None:
            msg = self._logger.resolveString(311, url)
            raise IllegalIdentifierException(msg, source)
        content = user.getContent(authority, itemid)
        if content is None:
            msg = self._logger.resolveString(311, url)
            raise IllegalIdentifierException(msg, source)
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
    def disposing(self, source):
        pass

    # Private methods
    def _getUser(self, source, authority, url):
        default = False
        uri = self._urifactory.parse(self._getPresentationUrl(url))
        if uri is None:
            msg = self._logger.resolveString(321, url)
            raise IllegalIdentifierException(msg, source)
        if authority:
            if uri.hasAuthority() and uri.getAuthority() != '':
                name = uri.getAuthority()
            else:
                msg = self._getExceptionMessage('_getUser()', 322, url)
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
                msg = self._getExceptionMessage('_getUser()', 324, name)
                raise IllegalIdentifierException(msg, source)
        else:
            user = User(self._ctx, source, self._logger, self.DataBase,
                        self._provider, self._sync, name)
            self._users[name] = user
        # FIXME: if the user has been instantiated then we can consider it as the default user
        if default:
            self._default = name
        return user, uri

    def _getPresentationUrl(self, url):
        # FIXME: Sometimes the url can end with a dot or a slash, it must be deleted
        url = url.rstrip('/.')
        uri = parseUrl(self._transformer, url)
        if uri is not None:
            uri = self._transformer.getPresentation(uri, True)
        return uri if uri else url

    def _getUserName(self, source, url):
        name = getOAuth2UserName(self._ctx, self, self._provider.Scheme)
        if not name:
            msg = self._getExceptionMessage('_getUserName', 331, url)
            raise IllegalIdentifierException(msg, source)
        return name

    def _getExceptionMessage(self, method, code, *args):
        return getExceptionMessage(self._ctx, self._logger, 'DataSource', method, code, g_extension, *args)

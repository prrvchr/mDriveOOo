#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb import XContentIdentifierFactory
from com.sun.star.ucb import XContentProvider
from com.sun.star.ucb import XParameterizedContentProvider
from com.sun.star.ucb import IllegalIdentifierException

from com.sun.star.ucb import XRestContentProvider

from unolib import getUserNameFromHandler

from .contenttools import getUrl
from .contenttools import getUri

from .datasource import DataSource
from .user import User

from .logger import logMessage
from .logger import getMessage

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
        msg = getMessage(self.ctx, 301, self.Plugin)
        logMessage(self.ctx, INFO, msg, 'ContentProvider', '__init__()')

    def __del__(self):
       msg = getMessage(self.ctx, 371, self.Plugin)
       logMessage(self.ctx, INFO, msg, 'ContentProvider', '__del__()')

    # XParameterizedContentProvider
    def registerInstance(self, scheme, plugin, replace):
        msg = getMessage(self.ctx, 311, (scheme, plugin))
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'registerInstance()')
        datasource = DataSource(self.ctx, self.event, scheme, plugin)
        if not datasource.isValid():
            logMessage(self.ctx, SEVERE, datasource.Error, 'ContentProvider', 'registerInstance()')
            return None
        self.Scheme = scheme
        self.Plugin = plugin
        self.DataSource = datasource
        msg = getMessage(self.ctx, 312, (scheme, plugin))
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'registerInstance()')
        return self
    def deregisterInstance(self, scheme, argument):
        msg = getMessage(self.ctx, 361, scheme)
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'deregisterInstance()')

    # XContentIdentifierFactory
    def createContentIdentifier(self, url):
        url = getUrl(self.ctx, url)
        uri = getUri(self.ctx, url)
        user = self._getUser(uri, url)
        identifier = self.DataSource.getIdentifier(user, uri)
        msg = getMessage(self.ctx, 331, url)
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'createContentIdentifier()')
        return identifier

    # XContentProvider
    def queryContent(self, identifier):
        url = identifier.getContentIdentifier()
        if not identifier.isValid():
            msg = getMessage(self.ctx, 341, (url, self._error))
            logMessage(self.ctx, SEVERE, msg, 'ContentProvider', 'queryContent()')
            raise IllegalIdentifierException(msg, identifier)
        content = identifier.getContent()
        self._currentUserName = identifier.User.Name
        msg = getMessage(self.ctx, 342, url)
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'queryContent()')
        return content

    def compareContentIds(self, id1, id2):
        ids = (id1.getContentIdentifier(), id2.getContentIdentifier())
        if id1.Id == id2.Id and id1.User.Id == id2.User.Id:
            msg = getMessage(self.ctx, 351, ids)
            compare = 0
        else:
            msg = getMessage(self.ctx, 352, ids)
            compare = -1
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'compareContentIds()')
        return compare

    def _getUser(self, uri, url):
        if uri is None:
            self._error = getMessage(self.ctx, 321, url)
            return User(self.ctx)
        if not uri.hasAuthority() or not uri.getPathSegmentCount():
            self._error = getMessage(self.ctx, 322, url)
            return User(self.ctx)
        name = self._getUserName(uri, url)
        if not name:
            self._error = getMessage(self.ctx, 323, url)
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
            name = getUserNameFromHandler(self.ctx, uri.getScheme(), self)
        return name

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
        msg = "ContentProvider: %s loading ... Done" % self.Plugin
        logMessage(self.ctx, INFO, msg, 'ContentProvider', '__init__()')

    def __del__(self):
       msg = "ContentProvider: %s unloading ... Done" % self.Plugin
       logMessage(self.ctx, INFO, msg, 'ContentProvider', '__del__()')

    # XParameterizedContentProvider
    def registerInstance(self, scheme, plugin, replace):
        msg = "ContentProvider registerInstance: Scheme/Plugin: %s/%s ... Started" % (scheme, plugin)
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'registerInstance()')
        datasource = DataSource(self.ctx, self.event, scheme, plugin)
        if not datasource.isValid():
            logMessage(self.ctx, SEVERE, datasource.Error, 'ContentProvider', 'registerInstance()')
            return None
        self.Scheme = scheme
        self.Plugin = plugin
        self.DataSource = datasource
        msg = "ContentProvider registerInstance: Scheme/Plugin: %s/%s ... Done" % (scheme, plugin)
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'registerInstance()')
        return self
    def deregisterInstance(self, scheme, argument):
        msg = "ContentProvider deregisterInstance: Scheme: %s ... Done" % scheme
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'deregisterInstance()')

    # XContentIdentifierFactory
    def createContentIdentifier(self, url):
        msg = "Identifier: %s ... " % url
        uri = getUri(self.ctx, getUrl(self.ctx, url))
        user = self._getUser(uri, url)
        identifier = self.DataSource.getIdentifier(user, uri)
        msg += "Done"
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'createContentIdentifier()')
        return identifier

    # XContentProvider
    def queryContent(self, identifier):
        url = identifier.getContentIdentifier()
        if not identifier.isValid():
            msg = "Identitifer: %s ... cannot be found: %s" % (url, self._error)
            logMessage(self.ctx, SEVERE, msg, 'ContentProvider', 'queryContent()')
            raise IllegalIdentifierException(msg, identifier)
        content = identifier.getContent()
        self._currentUserName = identifier.User.Name
        msg = "Identitifer: %s ... Done" % url
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'queryContent()')
        return content

    def compareContentIds(self, id1, id2):
        ids = (id1.getContentIdentifier(), id2.getContentIdentifier())
        msg = "Identifiers: %s - %s ..." % ids
        if id1.Id == id2.Id and id1.User.Id == id2.User.Id:
            msg += " seem to be the same..."
            compare = 0
        else:
            msg += " doesn't seem to be the same..."
            compare = -1
        msg += " ... Done"
        logMessage(self.ctx, INFO, msg, 'ContentProvider', 'compareContentIds()')
        return compare

    def _getUser(self, uri, url):
        if uri is None:
            self._error = getMessage(self.ctx, 1201, url)
            return User(self.ctx)
        if not uri.hasAuthority() or not uri.getPathSegmentCount():
            self._error = getMessage(self.ctx, 1202, url)
            return User(self.ctx)
        name = self._getUserName(uri, url)
        if not name:
            self._error = getMessage(self.ctx, 1203, url)
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

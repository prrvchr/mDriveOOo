#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.util import XCloseListener

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb import XRestDataSource

from unolib import g_oauth2
from unolib import createService

from .configuration import g_cache
from .dbtools import getDataSource

from .user import User
from .identifier import Identifier
from .replicator import Replicator
from .database import DataBase

from .logger import logMessage
from .logger import getMessage

from collections import OrderedDict
import traceback


class DataSource(unohelper.Base,
                 XRestDataSource,
                 XCloseListener):
    def __init__(self, ctx, event, scheme, plugin):
        try:
            msg = "DataSource for Scheme: %s loading ... " % scheme
            print("DataSource __init__() 1")
            self.ctx = ctx
            self.scheme = scheme
            self.plugin = plugin
            self._Users = {}
            self._Identifiers = OrderedDict()
            self.Error = None
            self.sync = event
            self.Provider = createService(self.ctx, '%s.Provider' % plugin)
            self.datasource, url, created = getDataSource(self.ctx, scheme, plugin, True)
            self.DataBase = DataBase(self.ctx, self.datasource)
            if created:
                self.Error = self.DataBase.createDataBase()
                if self.Error is None:
                    self.DataBase.storeDataBase(url)
            self.DataBase.addCloseListener(self)
            folder, link = self.DataBase.getContentType()
            self.Provider.initialize(scheme, plugin, folder, link)
            self.replicator = Replicator(ctx, self.datasource, self.Provider, self._Users, self.sync)
            print("DataSource __init__() 2")
            msg += "Done"
            logMessage(self.ctx, INFO, msg, 'DataSource', '__init__()')
        except Exception as e:
            msg = "DataSource __init__(): Error: %s - %s" % (e, traceback.print_exc())
            print(msg)

    # XCloseListener
    def queryClosing(self, source, ownership):
        print("DataSource.queryClosing() 1")
        compact= self.replicator.fullPull
        if self.replicator.is_alive():
            self.replicator.cancel()
            print("DataSource.queryClosing() 2")
            self.replicator.join()
        #self.deregisterInstance(self.Scheme, self.Plugin)
        self.DataBase.shutdownDataBase(compact)
        msg = "DataSource queryClosing: Scheme: %s ... Done" % self.scheme
        logMessage(self.ctx, INFO, msg, 'DataSource', 'queryClosing()')
        print("DataSource.queryClosing() 3 OK")
    def notifyClosing(self, source):
        pass

    # XRestDataSource
    def isValid(self):
        return self.Error is None

    def getUser(self, name, password=''):
        # User never change... we can cache it...
        if name in self._Users:
            user = self._Users[name]
        else:
            user = User(self.ctx, self, name)
            if not self._initializeUser(user, name, password):
                return None
            self._Users[name] = user
            self.sync.set()
        return user

    def getIdentifier(self, user, uri):
        # Identifier never change... we can cache it... if it's valid.
        key = '%s/%s' % (user.Name, uri.getPath().strip('/.'))
        if key in self._Identifiers:
            identifier = self._Identifiers[key]
        else:
            identifier = Identifier(self.ctx, user, uri)
            if identifier.isValid():
                self._Identifiers[key] = identifier
        if len(self._Identifiers) > g_cache:
            self._Identifiers.popitem(False)
        return identifier

    def _initializeUser(self, user, name, password):
        if user.Request is not None:
            if user.MetaData is not None:
                user.setDataBase(self.datasource, password, self.sync)
                return True
            if self.Provider.isOnLine():
                data = self.Provider.getUser(user.Request, name)
                if data.IsPresent:
                    root = self.Provider.getRoot(user.Request, data.Value)
                    if root.IsPresent:
                        user.MetaData = self.DataBase.insertUser(user.Provider, data.Value, root.Value)
                        if self.DataBase.createUser(user, password):
                            user.setDataBase(self.datasource, password, self.sync)
                            return True
                        else:
                            self.Error = getMessage(self.ctx, 1106, name)
                    else:
                        self.Error = getMessage(self.ctx, 1107, name)
                else:
                    self.Error = getMessage(self.ctx, 1107, name)
            else:
                self.Error = getMessage(self.ctx, 1108, name)
        else:
            self.Error = getMessage(self.ctx, 1105, g_oauth2)
        return False

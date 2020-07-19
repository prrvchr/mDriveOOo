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

from .dbtools import getDataSource

from .user import User
from .replicator import Replicator
from .database import DataBase

from .logger import logMessage
from .logger import getMessage

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
            self._CahedUser = {}
            self._Calls = {}
            self.Error = None
            self.sync = event
            self.Provider = createService(self.ctx, '%s.Provider' % plugin)
            print("DataSource __init__() 2")
            self.datasource, url, created = getDataSource(self.ctx, scheme, plugin, True)
            print("DataSource __init__() 3 %s" % created)
            self.DataBase = DataBase(self.ctx, self.datasource)
            if created:
                self.Error = self.DataBase.createDataBase()
                if self.Error is None:
                    self.DataBase.storeDataBase(url)
            self.DataBase.addCloseListener(self)
            folder, link = self.DataBase.getContentType()
            self.Provider.initialize(scheme, plugin, folder, link)
            self.replicator = Replicator(ctx, self.datasource, self.Provider, self._CahedUser, self.sync)
            print("DataSource __init__() 4")
            logMessage(self.ctx, INFO, "stage 2", 'DataSource', '__init__()')
            print("DataSource __init__() 5")
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
        print("DataSource.getUser() 1")
        # User never change... we can cache it...
        if name in self._CahedUser:
            print("DataSource.getUser() 3")
            user = self._CahedUser[name]
        else:
            print("DataSource.getUser() 4")
            user = User(self.ctx, self, name)
            print("DataSource.getUser() 5")
            if not self._initializeUser(user, name, password):
                print("DataSource.getUser() 6 ERROR")
                return None
            self._CahedUser[name] = user
            print("DataSource.getUser() 7")
            self.sync.set()
        print("DataSource.getUser() 8")
        return user

    def getRequest(self, name):
        request = createService(self.ctx, g_oauth2)
        if request is not None:
            request.initializeSession(self.Provider.Scheme, name)
        return request

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

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

import unohelper

from com.sun.star.logging.LogLevel import SEVERE
from com.sun.star.logging.LogLevel import WARNING
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import CONFIG
from com.sun.star.logging.LogLevel import FINE
from com.sun.star.logging.LogLevel import FINER
from com.sun.star.logging.LogLevel import FINEST
from com.sun.star.logging.LogLevel import ALL
from com.sun.star.logging.LogLevel import OFF

from ..unotool import createService
from ..unotool import getConfiguration
from ..unotool import getFileSequence
from ..unotool import getStringResource

from ..configuration import g_identifier
from ..configuration import g_resource


class Pool(unohelper.Base):
    def __init__(self, ctx):
        self._ctx = ctx

    _loggers = {}

    def getLogger(self, name='Logger', resource=None):
        log = '%s.%s' % (g_identifier, name)
        if log not in Pool._loggers:
            if resource is None:
                resource = name
            Pool._loggers[log] = Logger(self._ctx, log, resource)
        return Pool._loggers[log]


class Logger(unohelper.Base):
    def __init__(self, ctx, name, resource):
        self._ctx = ctx
        self._logger = self._getLogger(name)
        self._resolver = getStringResource(ctx, g_identifier, g_resource, resource)
        self._settings = None
        self._listeners = []

# Public getter method
    def isDebugMode(self):
        return self._settings is not None

    def isLoggerEnabled(self):
        level = self._getLogConfig().LogLevel
        enabled = self._isLogEnabled(level)
        return enabled

    def getMessage(self, resource, *args):
        if self._resolver is not None:
            msg = self._resolver.resolveString(resource)
            if args:
                msg = msg % args
        else:
            msg = 'Logger must be initialized with a string resource file'
        return msg

    def getLoggerSetting(self):
        enabled, index, handler = self._getLoggerSetting()
        state = self._getState(handler)
        return enabled, index, state

    def getLoggerUrl(self):
        url = '$(userurl)/$(loggername).log'
        settings = self._getLogConfig().getByName('HandlerSettings')
        if settings.hasByName('FileURL'):
            url = settings.getByName('FileURL')
        service = 'com.sun.star.util.PathSubstitution'
        path = createService(self._ctx, service)
        url = url.replace('$(loggername)', self._logger.Name)
        return path.substituteVariables(url, True)

    def getLoggerText(self):
        url = self.getLoggerUrl()
        length, sequence = getFileSequence(self._ctx, url)
        text = sequence.value.decode('utf-8')
        return text

# Public setter method
    def addLogHandler(self, handler):
        self._logger.addLogHandler(handler)

    def removeLogHandler(self, handler):
        self._logger.removeLogHandler(handler)

    def setDebugMode(self, mode):
        if mode:
            self._setDebugModeOn()
        else:
            self._setDebugModeOff()

    def logResource(self, level, resource, clazz=None, method=None, *args):
        if self._logger.isLoggable(level):
            msg = self.getMessage(resource, args)
            self._logMessage(level, msg, clazz, method)
            print("Logger.logResource() %s - %s - %s - %s" % (level, msg, clazz, method))

    def logMessage(self, level, msg, clazz=None, method=None):
        if self._logger.isLoggable(level):
            self._logMessage(level, msg, clazz, method)
            print("Logger.logMessage() %s - %s - %s - %s" % (level, msg, clazz, method))

    def clearLogger(self, msg='', clazz=None, method=None):
        if self._logger is not None:
            name = self._logger.Name
            self._logger = None
            self._logger = self._getLogger(name)
            self.logMessage(INFO, msg, clazz, method)

    def setLoggerSetting(self, enabled, index, state):
        handler = self._getHandler(state)
        self._setLoggerSetting(enabled, index, handler)

    def addListener(self, listener):
        self._listeners.append(listener)

    def removeListener(self, listener):
        if listener in self._listeners:
            self._listeners.remove(listener)


# Private getter method
    def _getLogger(self, name):
        print("Logger._getLogger() 1 *************************************************")
        service = '/singletons/com.sun.star.logging.LoggerPool'
        logger = self._ctx.getValueByName(service).getNamedLogger(name)
        print("Logger._getLogger() 2: %s" % logger)
        #mri = createService(self._ctx, 'mytools.Mri')
        #mri.inspect(logger)
        return logger

    def _getLoggerSetting(self):
        configuration = self._getLogConfig()
        enabled, index = self._getLogIndex(configuration)
        handler = configuration.DefaultHandler
        return enabled, index, handler

    def _getLogConfig(self):
        name = self._logger.Name
        nodepath = '/org.openoffice.Office.Logging/Settings'
        configuration = getConfiguration(self._ctx, nodepath, True)
        if not configuration.hasByName(name):
            configuration.insertByName(name, configuration.createInstance())
            configuration.commitChanges()
        nodepath += '/%s' % name
        return getConfiguration(self._ctx, nodepath, True)

    def _getLogIndex(self, configuration):
        level = configuration.LogLevel
        enabled = self._isLogEnabled(level)
        if enabled:
            index = self._getLogLevels().index(level)
        else:
            index = 7
        return enabled, index
    
    def _getLogLevels(self):
        levels = (SEVERE,
                  WARNING,
                  INFO,
                  CONFIG,
                  FINE,
                  FINER,
                  FINEST,
                  ALL)
        return levels

    def _isLogEnabled(self, level):
        return level != OFF

    def _getHandler(self, state):
        handlers = {True: 'ConsoleHandler', False: 'FileHandler'}
        return 'com.sun.star.logging.%s' % handlers.get(state)

    def _getState(self, handler):
        states = {'com.sun.star.logging.ConsoleHandler': 1,
                  'com.sun.star.logging.FileHandler': 2}
        return states.get(handler)

# Private setter method
    def _setLoggerSetting(self, enabled, index, handler):
        configuration = self._getLogConfig()
        self._setLogIndex(configuration, enabled, index)
        self._setLogHandler(configuration, handler, index)
        if configuration.hasPendingChanges():
            configuration.commitChanges()
            self.clearLogger()

    def _setLogIndex(self, configuration, enabled, index):
        level = self._getLogLevels()[index] if enabled else OFF
        if configuration.LogLevel != level:
            configuration.LogLevel = level

    def _setLogHandler(self, configuration, handler, index):
        if configuration.DefaultHandler != handler:
            configuration.DefaultHandler = handler
        settings = configuration.getByName('HandlerSettings')
        if settings.hasByName('Threshold'):
            if settings.getByName('Threshold') != index:
                settings.replaceByName('Threshold', index)
        else:
            settings.insertByName('Threshold', index)

    def _setDebugModeOn(self):
        if not self.isDebugMode():
            self._settings = self._getLoggerSetting()
            self._setLoggerSetting(True, 7, 'com.sun.star.logging.FileHandler')

    def _setDebugModeOff(self):
        if self.isDebugMode():
            self._setLoggerSetting(*self._settings)
            self._settings = None

    def _logMessage(self, level, msg, clazz, method):
        if clazz is None or method is None:
            self._logger.log(level, msg)
        else:
            self._logger.logp(level, clazz, method, msg)
        self._refreshLog()

    def _refreshLog(self):
        for listener in self._listeners:
            listener.refreshLog()

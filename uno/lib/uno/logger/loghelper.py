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

from com.sun.star.logging.LogLevel import SEVERE
from com.sun.star.logging.LogLevel import WARNING
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import CONFIG
from com.sun.star.logging.LogLevel import FINE
from com.sun.star.logging.LogLevel import FINER
from com.sun.star.logging.LogLevel import FINEST
from com.sun.star.logging.LogLevel import ALL
from com.sun.star.logging.LogLevel import OFF

from .loggerpool import LoggerPool

from ..unotool import createService
from ..unotool import getConfiguration
from ..unotool import getFileSequence
from ..unotool import getResourceLocation
from ..unotool import getSimpleFile
from ..unotool import getStringResourceWithLocation

from .handler import RollerHandler
from .handler import getRollerHandlerUrl

from ..configuration import g_identifier
from ..configuration import g_resource
from ..configuration import g_defaultlog
from ..configuration import g_basename

import traceback


def getLogger(ctx, logger=g_defaultlog, basename=g_basename):
    return LogWrapper(ctx, logger, basename)

def getLoggerName(name):
    return '%s.%s' % (g_identifier, name)


# This LogWrapper allows using variable number of argument in python
# while the UNO API does not allow it
class LogWrapper(object):
    def __init__(self, ctx, name, basename):
        self._ctx = ctx
        self._basename = basename
        self._url, self._logger = _getPoolLogger(ctx, name, basename)
        self._level = ALL

    # XLogger
    @property
    def Name(self):
        return self._logger.Name

    @property
    def Level(self):
        return self._logger.Level
    @Level.setter
    def Level(self, value):
        self._logger.Level = value

    # Public getter method
    def addLogHandler(self, handler):
        self._logger.addLogHandler(handler)

    def removeLogHandler(self, handler):
        self._logger.removeLogHandler(handler)

    def addRollerHandler(self, handler):
        self._level = self.Level
        self.Level = ALL
        self.addLogHandler(handler)

    def removeRollerHandler(self, handler):
        self._logger.removeLogHandler(handler)
        handler.dispose()
        self.Level = self._level

    def isLoggable(self, level):
        return self._logger.isLoggable(level)

    def log(self, level, message):
        self._logger.log(level, message)

    def logp(self, level, clazz, method, message):
        self._logger.logp(level, clazz, method, message)

    def logrb(self, level, resource, *args):
        if self._logger.hasEntryForId(resource):
            self._logger.logrb(level, resource, args)
        else:
            self._logger.log(level, self._getErrorMessage(resource))

    def logprb(self, level, clazz, method, resource, *args):
        if self._logger.hasEntryForId(resource):
            self._logger.logprb(level, clazz, method, resource, args)
        else:
            self._logger.logp(level, clazz, method, self._getErrorMessage(resource))

    def resolveString(self, resource, *args):
        if self._logger.hasEntryForId(resource):
            return self._logger.resolveString(resource, args)
        else:
            return self._getErrorMessage(resource)

    def _getErrorMessage(self, resource):
        resolver = getStringResourceWithLocation(self._ctx, self._url, 'Logger')
        return self._resolveErrorMessage(resolver, resource)

    def _resolveErrorMessage(self, resolver, resource):
        return resolver.resolveString(151) % (resource, self._url, self._basename)


# This LogController allows using listener and access content of logger
class LogController(LogWrapper):
    def __init__(self, ctx, name, basename=g_basename, listener=None):
        self._ctx = ctx
        self._basename = basename
        self._url, self._logger = _getPoolLogger(ctx, name, basename)
        self._listener = listener
        self._resolver = getStringResourceWithLocation(ctx, self._url, 'Logger')
        self._setting = None
        self._config = getConfiguration(ctx, '/org.openoffice.Office.Logging/Settings', True)
        if listener is not None:
            self._logger.addModifyListener(listener)

# Public getter method
    def getLogContent(self, roller=False):
        url = self._getLoggerUrl(roller)
        length, sequence = getFileSequence(self._ctx, url)
        text = sequence.value.decode('utf-8')
        return text, length

# Public setter method
    def dispose(self):
        if self._listener is not None:
            self._logger.removeModifyListener(self._listener)

    def logInfos(self, level, infos, clazz, method):
        for resource, info in infos.items():
            msg = self._resolver.resolveString(resource) % info
            self._logger.logp(level, clazz, method, msg)

    def clearLogger(self):
        url = getRollerHandlerUrl(self._ctx, self.Name)
        sf = getSimpleFile(self._ctx)
        if sf.exists(url):
            sf.kill(url)
            print("LogController.clearLogger() 1")
            msg = self._resolver.resolveString(161)
            handler = RollerHandler(self._ctx, self.Name)
            self.addRollerHandler(handler)
            self._logMessage(SEVERE, msg, 'Logger', 'clearLogger()')
            self.removeRollerHandler(handler)
            print("LogController.clearLogger() 2")

    def addModifyListener(self, listener):
        self._logger.addModifyListener(listener)

    def removeModifyListener(self, listener):
        self._logger.removeModifyListener(listener)

# Private getter method
    def _getErrorMessage(self, resource):
        return self._resolveErrorMessage(self._resolver, resource)

    def _getLoggerUrl(self, roller=False):
        if roller:
            url = getRollerHandlerUrl(self._ctx, self.Name)
        else:
            url = self._getLoggerConfigurationUrl()
        return url

    def _getLoggerConfigurationUrl(self):
        url = '$(userurl)/$(loggername).log'
        settings = self._getLogConfig().getByName('HandlerSettings')
        if settings.hasByName('FileURL'):
            url = settings.getByName('FileURL')
        service = 'com.sun.star.util.PathSubstitution'
        path = createService(self._ctx, service)
        url = url.replace('$(loggername)', self.Name)
        return path.substituteVariables(url, True)

    def _getLoggerSetting(self):
        config = self._getLogConfig()
        return LogConfig(config.LogLevel, config.DefaultHandler)

    def _getLogConfig(self):
        if not self._config.hasByName(self.Name):
            self._config.insertByName(self.Name, self._config.createInstance())
        return self._config.getByName(self.Name)

# Private setter method
    def _setLoggerSetting(self, setting):
        config = self._getLogConfig()
        config.LogLevel = setting.LogLevel
        config.DefaultHandler = setting.DefaultHandler
        if self._config.hasPendingChanges():
            self._config.commitChanges()

    def _logMessage(self, level, msg, clazz=None, method=None):
        if clazz is None or method is None:
            self._logger.log(level, msg)
        else:
            self._logger.logp(level, clazz, method, msg)


# This LogConfig is a wrapper around the logger configuration
class LogConfig():
    def __init__(self, level=ALL, handler='com.sun.star.logging.FileHandler'):
        self._level = level
        self._handler = handler
        self._defaultlevel = ALL

    @property
    def LogLevel(self):
        return self._level
    @property
    def DefaultHandler(self):
        return self._handler

    def getLevelIndex(self):
        if self.isLogEnabled():
            index = self._getLogLevels().index(self.LogLevel)
        else:
            index = self._getLogLevels().index(self._defaultlevel)
        return index

    def getHandlerId(self):
        return self._getHandlerIds().get(self.DefaultHandler)

    def isLogEnabled(self):
        return self.LogLevel != OFF

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

    def _getHandlerIds(self):
        return {'com.sun.star.logging.ConsoleHandler': 1,
                'com.sun.star.logging.FileHandler': 2}


# This LogSetting is a wrapper around the logger UI setting
class LogSetting(LogConfig):
    def __init__(self, enabled, index, state):
        self._enabled = enabled
        self._index = index
        self._state = state
        self._defaultlevel = ALL

    @property
    def LogLevel(self):
        return self._getLogLevels()[self._index] if self._enabled else OFF
    @property
    def DefaultHandler(self):
        return 'com.sun.star.logging.FileHandler' if self._state else 'com.sun.star.logging.ConsoleHandler'


def _getPoolLogger(ctx, name, basename):
    url = getResourceLocation(ctx, g_identifier, g_resource)
    logger = LoggerPool(ctx).getLocalizedLogger(getLoggerName(name), url, basename)
    return url, logger


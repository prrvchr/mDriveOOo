#!
# -*- coding: utf_8 -*-

from com.sun.star.logging.LogLevel import SEVERE
from com.sun.star.logging.LogLevel import WARNING
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import CONFIG
from com.sun.star.logging.LogLevel import FINE
from com.sun.star.logging.LogLevel import FINER
from com.sun.star.logging.LogLevel import FINEST
from com.sun.star.logging.LogLevel import ALL
from com.sun.star.logging.LogLevel import OFF

from .unotools import getConfiguration
from .unotools import getSimpleFile


g_loggerPool = {}
g_defaultLogger = 'org.openoffice.logging.DefaultLogger'


def logMessage(ctx, level, msg, cls=None, mtd=None, logger=g_defaultLogger):
    log = getLogger(ctx, logger)
    if log.isLoggable(level):
        if cls is None or mtd is None:
            log.log(level, msg)
        else:
            log.logp(level, cls, mtd, msg)

def getLogger(ctx, logger=g_defaultLogger):
    if logger not in g_loggerPool:
        log = ctx.getValueByName('/singletons/com.sun.star.logging.LoggerPool').getNamedLogger(logger)
        g_loggerPool[logger] = log
    return g_loggerPool[logger]

def clearLogger(logger=g_defaultLogger):
    if logger in g_loggerPool:
        del g_loggerPool[logger]

def isLoggerEnabled(ctx, logger=g_defaultLogger):
    level = _getLoggerConfiguration(ctx, logger).LogLevel
    enabled = _isLoggerEnabled(level)
    return enabled

def getLoggerSetting(ctx, logger=g_defaultLogger):
    configuration = _getLoggerConfiguration(ctx, logger)
    enabled, index = _getLogIndex(configuration)
    handler, viewer = _getLogHandler(configuration)
    return enabled, index, handler, viewer

def setLoggerSetting(ctx, enabled, index, handler, logger=g_defaultLogger):
    configuration = _getLoggerConfiguration(ctx, logger)
    _setLogIndex(configuration, enabled, index)
    _setLogHandler(configuration, handler, index)
    if configuration.hasPendingChanges():
        print("logger.setLoggerSetting() configuration.hasPendingChanges")
        configuration.commitChanges()
        clearLogger(ctx)

def getLoggerUrl(ctx, logger=g_defaultLogger):
    url = '$(userurl)/$(loggername).log'
    settings = _getLoggerConfiguration(ctx, logger).getByName('HandlerSettings')
    if settings.hasByName('FileURL'):
        url = settings.getByName('FileURL')
    service = ctx.ServiceManager.createInstance('com.sun.star.util.PathSubstitution')
    return service.substituteVariables(url.replace('$(loggername)', logger), True)

def _getLogIndex(configuration):
    index = 7
    level = configuration.LogLevel
    enabled = _isLoggerEnabled(level)
    if enabled:
        index = _getLogLevels().index(level)
    return enabled, index

def _setLogIndex(configuration, enabled, index):
    level = _getLogLevels()[index] if enabled else OFF
    if configuration.LogLevel != level:
        configuration.LogLevel = level

def _getLogHandler(configuration):
    handler = 1 if configuration.DefaultHandler != 'com.sun.star.logging.FileHandler' else 2
    return handler, handler != 1

def _setLogHandler(configuration, console, index):
    handler = 'com.sun.star.logging.ConsoleHandler' if console else 'com.sun.star.logging.FileHandler'
    if configuration.DefaultHandler != handler:
        configuration.DefaultHandler = handler
    settings = configuration.getByName('HandlerSettings')
    if settings.hasByName('Threshold'):
        if settings.getByName('Threshold') != index:
            settings.replaceByName('Threshold', index)
    else:
        settings.insertByName('Threshold', index)

def _getLoggerConfiguration(ctx, logger):
    nodepath = '/org.openoffice.Office.Logging/Settings'
    configuration = getConfiguration(ctx, nodepath, True)
    if not configuration.hasByName(logger):
        configuration.insertByName(logger, configuration.createInstance())
        configuration.commitChanges()
    nodepath += '/%s' % logger
    return getConfiguration(ctx, nodepath, True)

def _getLogLevels():
    levels = (SEVERE,
              WARNING,
              INFO,
              CONFIG,
              FINE,
              FINER,
              FINEST,
              ALL)
    return levels

def _isLoggerEnabled(level):
    return level != OFF

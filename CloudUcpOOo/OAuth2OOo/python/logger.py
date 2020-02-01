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

from unolib import getConfiguration
from unolib import getStringResource

from .configuration import g_logger
from .configuration import g_identifier

g_loggerPool = {}
g_stringResource = {}
g_pathResource = 'resource'
g_fileResource = 'MessageStrings'


def getMessage(ctx, resource, format=()):
    msg = _getResource(ctx).resolveString('%s' % resource)
    if format:
        msg = msg % format
    return msg

def logMessage(ctx, level, msg, cls=None, mtd=None, logger=g_logger):
    log = _getLogger(ctx, logger)
    if log.isLoggable(level):
        if cls is None or mtd is None:
            log.log(level, msg)
        else:
            log.logp(level, cls, mtd, msg)

def clearLogger(logger=g_logger):
    if logger in g_loggerPool:
        del g_loggerPool[logger]

def isLoggerEnabled(ctx, logger=g_logger):
    level = _getLoggerConfiguration(ctx, logger).LogLevel
    enabled = _isLoggerEnabled(level)
    return enabled

def getLoggerSetting(ctx, logger=g_logger):
    configuration = _getLoggerConfiguration(ctx, logger)
    enabled, index = _getLogIndex(configuration)
    handler = _getLogHandler(configuration)
    return enabled, index, handler

def setLoggerSetting(ctx, enabled, index, handler, logger=g_logger):
    configuration = _getLoggerConfiguration(ctx, logger)
    _setLogIndex(configuration, enabled, index)
    _setLogHandler(configuration, handler, index)
    if configuration.hasPendingChanges():
        configuration.commitChanges()
        clearLogger(logger)

def getLoggerUrl(ctx, logger=g_logger):
    url = '$(userurl)/$(loggername).log'
    settings = _getLoggerConfiguration(ctx, logger).getByName('HandlerSettings')
    if settings.hasByName('FileURL'):
        url = settings.getByName('FileURL')
    service = ctx.ServiceManager.createInstance('com.sun.star.util.PathSubstitution')
    return service.substituteVariables(url.replace('$(loggername)', logger), True)

def _getLogger(ctx, logger=g_logger):
    if logger not in g_loggerPool:
        singleton = '/singletons/com.sun.star.logging.LoggerPool'
        log = ctx.getValueByName(singleton).getNamedLogger(logger)
        g_loggerPool[logger] = log
    return g_loggerPool[logger]

def _getResource(ctx, identifier=g_identifier):
    if identifier not in g_stringResource:
        resource = getStringResource(ctx, identifier, g_pathResource, g_fileResource)
        g_stringResource[identifier] = resource
    return g_stringResource[identifier]

def _getLoggerConfiguration(ctx, logger):
    nodepath = '/org.openoffice.Office.Logging/Settings'
    configuration = getConfiguration(ctx, nodepath, True)
    if not configuration.hasByName(logger):
        configuration.insertByName(logger, configuration.createInstance())
        configuration.commitChanges()
    nodepath += '/%s' % logger
    return getConfiguration(ctx, nodepath, True)

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
    return handler

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

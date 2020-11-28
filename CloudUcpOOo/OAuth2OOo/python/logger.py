#!
# -*- coding: utf_8 -*-

'''
    Copyright (c) 2020 https://prrvchr.github.io

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the Software
    is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
    OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

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

from .configuration import g_identifier

g_resources = {}
g_logger = None
g_debug = False
g_settings = None


# Public getter method
def isDebugMode():
    return g_debug

def isLoggerEnabled(ctx):
    level = _getLogConfig(ctx).LogLevel
    enabled = _isLogEnabled(level)
    return enabled

def getMessage(ctx, fileresource, resource, format=()):
    msg = _getResource(ctx, fileresource).resolveString(resource)
    if format:
        msg = msg % format
    return msg

def getLoggerSetting(ctx):
    enabled, index, handler = _getLoggerSetting(ctx)
    state = _getState(handler)
    return enabled, index, state

def getLoggerUrl(ctx):
    url = '$(userurl)/$(loggername).log'
    settings = _getLogConfig(ctx).getByName('HandlerSettings')
    if settings.hasByName('FileURL'):
        url = settings.getByName('FileURL')
    service = ctx.ServiceManager.createInstance('com.sun.star.util.PathSubstitution')
    logger = _getLogName()
    return service.substituteVariables(url.replace('$(loggername)', logger), True)

# Public setter method
def setDebugMode(ctx, mode):
    if mode:
        _setDebugModeOn(ctx)
    else:
        _setDebugModeOff(ctx)
    _setDebugMode(mode)

def logMessage(ctx, level, msg, cls=None, method=None):
    logger = _getLogger(ctx)
    if logger.isLoggable(level):
        if cls is None or method is None:
            logger.log(level, msg)
        else:
            logger.logp(level, cls, method, msg)

def clearLogger():
    global g_logger
    g_logger = None

def setLoggerSetting(ctx, enabled, index, state):
    handler = _getHandler(state)
    _setLoggerSetting(ctx, enabled, index, handler)

# Private getter method
def _getLogger(ctx):
    if g_logger is None:
        _setLogger(ctx)
    return g_logger

def _getResource(ctx, fileresource):
    if fileresource not in g_resources:
        resource = getStringResource(ctx, g_identifier, _getPathResource(), fileresource)
        g_resources[fileresource] = resource
    return g_resources[fileresource]

def _getLogName():
    return '%s.Logger' % g_identifier

def _getPathResource():
    return 'resource'

def _getLoggerSetting(ctx):
    configuration = _getLogConfig(ctx)
    enabled, index = _getLogIndex(configuration)
    handler = configuration.DefaultHandler
    return enabled, index, handler

def _getLogConfig(ctx):
    logger = _getLogName()
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
    enabled = _isLogEnabled(level)
    if enabled:
        index = _getLogLevels().index(level)
    return enabled, index

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

def _isLogEnabled(level):
    return level != OFF

def _getHandler(state):
    handlers = {True: 'ConsoleHandler', False: 'FileHandler'}
    return 'com.sun.star.logging.%s' % handlers.get(state)

def _getState(handler):
    states = {'com.sun.star.logging.ConsoleHandler' : 1,
              'com.sun.star.logging.FileHandler': 2}
    return states.get(handler)

def _getLogSetting():
    global g_settings
    enabled, index, handler = g_settings['enabled'], g_settings['index'], g_settings['handler']
    g_settings = None
    return enabled, index, handler

def _getDebugSetting():
    return True, 7, 'com.sun.star.logging.FileHandler'

# Private setter method
def _setLogger(ctx):
    global g_logger
    logger = _getLogName()
    singleton = '/singletons/com.sun.star.logging.LoggerPool'
    g_logger = ctx.getValueByName(singleton).getNamedLogger(logger)

def _setLoggerSetting(ctx, enabled, index, handler):
    configuration = _getLogConfig(ctx)
    _setLogIndex(configuration, enabled, index)
    _setLogHandler(configuration, handler, index)
    if configuration.hasPendingChanges():
        configuration.commitChanges()
        clearLogger()

def _setLogIndex(configuration, enabled, index):
    level = _getLogLevels()[index] if enabled else OFF
    if configuration.LogLevel != level:
        configuration.LogLevel = level

def _setLogHandler(configuration, handler, index):
    if configuration.DefaultHandler != handler:
        configuration.DefaultHandler = handler
    settings = configuration.getByName('HandlerSettings')
    if settings.hasByName('Threshold'):
        if settings.getByName('Threshold') != index:
            settings.replaceByName('Threshold', index)
    else:
        settings.insertByName('Threshold', index)

def _setDebugMode(mode):
    global g_debug
    g_debug = mode

def _setDebugModeOn(ctx):
    _setLogSetting(*_getLoggerSetting(ctx))
    _setLoggerSetting(ctx, *_getDebugSetting())

def _setDebugModeOff(ctx):
    if g_settings is not None:
        _setLoggerSetting(ctx, *_getLogSetting())

def _setLogSetting(enabled, index, handler):
    global g_settings
    g_settings = {'enabled': enabled, 'index': index, 'handler': handler}

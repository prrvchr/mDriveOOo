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

from com.sun.star.logging import XLoggerPool2

from .logger import Logger

from ..unotool import getStringResourceWithLocation

from threading import Lock
import traceback


class LoggerPool(unohelper.Base,
                 XLoggerPool2):
    def __init__(self, ctx):
        self._ctx = ctx
        self._default = 'org.openoffice.logging.DefaultLogger'
        self._pool = ctx.getByName('/singletons/com.sun.star.logging.LoggerPool')
        print("LoggerPool.__init__() *******************************")

    # FIXME: for the LoggerPool, the modify listener is global
    _listeners = []
    # FIXME: for the Logger, the modify listener is global
    _loggers = {}
    _resolvers = {}
    _lock = Lock()

    # XLoggerPool
    def getNamedLogger(self, name):
        logger = self._getNamedLogger(name)
        listeners = LoggerPool._loggers[name]
        return Logger(self._ctx, logger, listeners)

    def getDefaultLogger(self):
        return getNamedLogger(self._default)

    # XLoggerPool2
    def getLocalizedLogger(self, name, url, basename):
        logger = self._getNamedLogger(name)
        listeners = LoggerPool._loggers[name]
        key = '%s/%s' % (url, basename)
        with LoggerPool._lock:
            if key not in LoggerPool._resolvers:
                LoggerPool._resolvers[key] = getStringResourceWithLocation(self._ctx, url, basename)
        resolver = LoggerPool._resolvers[key]
        return Logger(self._ctx, logger, listeners, resolver)

    def getLoggerNames(self):
        return tuple(LoggerPool._loggers.keys())

    def getFilteredLoggerNames(self, filter):
        names = []
        start = len(filter) +1
        for name in LoggerPool._loggers:
            if name.startswith(filter):
                names.append(name[start:])
        return tuple(names)

    def addModifyListener(self, listener):
        LoggerPool._listeners.append(listener)

    def removeModifyListener(self, listener):
        if listener in LoggerPool._listeners:
            LoggerPool._listeners.remove(listener)

    def _getNamedLogger(self, name):
        with LoggerPool._lock:
            toadd = name not in LoggerPool._loggers
            if toadd:
                LoggerPool._loggers[name] = []
                print("LoggerPool._getNamedLogger() %s" % name)
        logger = self._pool.getNamedLogger(name)
        if toadd:
            self._notifyListener()
        return logger

    def _notifyListener(self):
        event = uno.createUnoStruct('com.sun.star.lang.EventObject')
        event.Source = self
        for listener in LoggerPool._listeners:
            listener.modified(event)


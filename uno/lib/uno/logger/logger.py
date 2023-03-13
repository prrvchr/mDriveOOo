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

from com.sun.star.logging import XLogger2

import traceback


class Logger(unohelper.Base,
             XLogger2):
    def __init__(self, ctx, logger, listeners, resolver=None):
        self._ctx = ctx
        self._logger = logger
        self._listeners = listeners
        self._resolver = resolver

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

    def addLogHandler(self, handler):
        self._logger.addLogHandler(handler)

    def removeLogHandler(selfself, handler):
        self._logger.removeLogHandler(handler)

    def isLoggable(self, level):
        return self._logger.isLoggable(level)

    def log(self, level, message):
        if self.isLoggable(level):
            self._log(level, message)

    def logp(self, level, clazz, method, message):
        if self.isLoggable(level):
            self._logp(level, clazz, method, message)

    # XLogger2
    def hasEntryForId(self, resource):
        if self._resolver is None:
            return False
        return self._resolver.hasEntryForId(resource)

    def resolveString(self, resource, args):
        if self.hasEntryForId(resource):
            msg = self._resolver.resolveString(resource)
            if args:
                msg = msg % args
        else:
            msg = resource
        return msg

    def logrb(self, level, resource, arguments):
        if self.isLoggable(level):
            message = self.resolveString(resource, arguments)
            self._log(level, message)

    def logprb(self, level, clazz, method, resource, arguments):
        if self.isLoggable(level):
            message = self.resolveString(resource, arguments)
            self._logp(level, clazz, method, message)

    def addModifyListener(self, listener):
        self._listeners.append(listener)

    def removeModifyListener(self, listener):
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _log(self, level, message):
        self._logger.log(level, message)
        self._notifyListener()

    def _logp(self, level, clazz, method, message):
        self._logger.logp(level, clazz, method, message)
        self._notifyListener()

    def _notifyListener(self):
        event = uno.createUnoStruct('com.sun.star.lang.EventObject')
        event.Source = self
        for listener in self._listeners:
            listener.modified(event)


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

from com.sun.star.logging.LogLevel import ALL

from com.sun.star.logging import XLogHandler

from ..unotool import createService


class LogHandler(unohelper.Base,
                 XLogHandler):
    def __init__(self, ctx, callback, level=ALL):
        self._encoding = 'UTF-8'
        service = 'com.sun.star.logging.PlainTextFormatter'
        self._formatter = createService(ctx, service)
        self._level = level
        self._listeners = []
        self._callback = callback

# XLogHandler
    @property
    def Encoding(self):
        return self._encoding
    @Encoding.setter
    def Encoding(self, value):
        self._encoding = value

    @property
    def Formatter(self):
        return self._formatter
    @Formatter.setter
    def Formatter(self, value):
        self._formatter = value

    @property
    def Level(self):
        return self._level
    @Level.setter
    def Level(self, value):
        self._level = value

    def flush(self):
        pass

    def publish(self, record):
        # TODO: Need to do a callback with the record
        self._callback()
        return True

# XComponent <- XLogHandler
    def dispose(self):
        event = uno.createUnoStruct('com.sun.star.lang.EventObject')
        event.Source = self
        for listener in self._listeners:
            listener.disposing(event)

    def addEventListener(self, listener):
        self._listeners.append(listener)

    def removeEventListener(self, listener):
        if listener in self._listeners:
            self._listeners.remove(listener)

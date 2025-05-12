#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-25 https://prrvchr.github.io                                  ║
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
from com.sun.star.logging.LogLevel import OFF

from com.sun.star.logging import XLogHandler

from ..unotool import createService
from ..unotool import getResourceLocation
from ..unotool import getSimpleFile

from ..configuration import g_identifier

g_folderlog = 'log'


def getRollerHandlerUrl(ctx, name):
    path = '%s/%s.log' % (g_folderlog, name)
    return getResourceLocation(ctx, g_identifier, path)


class RollerHandler(unohelper.Base,
                    XLogHandler):
    def __init__(self, ctx, name, level=ALL):
        encoding = 'UTF-8'
        self._encoding = encoding
        self._formatter = createService(ctx, 'com.sun.star.logging.PlainTextFormatter')
        self._url = getRollerHandlerUrl(ctx, name)
        self._sf = getSimpleFile(ctx)
        self._out = createService(ctx, 'com.sun.star.io.TextOutputStream')
        self._out.setEncoding(encoding)
        self._level = level
        self._listeners = []

# XLogHandler
    @property
    def Encoding(self):
        return self._encoding
    @Encoding.setter
    def Encoding(self, value):
        self._encoding = value
        self._out.setEncoding(value)

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
        if self._level <= record.Level < OFF:
            self._publishRecord(record)
            return True
        return False

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

    def _publishRecord(self, record):
        if not self._sf.exists(self._url):
            msg = self._formatter.getHead()
            self._publishMessage(msg)
        msg = self._formatter.format(record)
        self._publishMessage(msg)

    def _publishMessage(self, msg):
        output = self._sf.openFileWrite(self._url)
        output.seek(output.getLength())
        self._out.setOutputStream(output)
        self._out.writeString(msg)
        self._out.getOutputStream().flush()
        self._out.getOutputStream().closeOutput()


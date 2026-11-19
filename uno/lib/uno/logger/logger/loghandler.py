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


class BaseHandler(unohelper.Base,
                  XLogHandler):
    def __init__(self, ctx, level=ALL):
        self._encoding = 'UTF-8'
        self._formatter = createService(ctx, 'com.sun.star.logging.PlainTextFormatter')
        self._level = level
        self._listeners = set()

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

    def publish(self, _record):
        return False

    # XComponent
    def dispose(self):
        event = uno.createUnoStruct('com.sun.star.lang.EventObject', self)
        for listener in list(self._listeners):
            listener.disposing(event)

    def addEventListener(self, listener):
        self._listeners.add(listener)

    def removeEventListener(self, listener):
        self._listeners.discard(listener)


class RollerHandler(BaseHandler):
    def __init__(self, ctx, name, level=ALL):
        super().__init__(ctx, level)
        self._url = getRollerHandlerUrl(ctx, name)
        self._sf = getSimpleFile(ctx)
        self._out = createService(ctx, 'com.sun.star.io.TextOutputStream')
        self._out.setEncoding(self._encoding)

# XLogHandler
    @BaseHandler.Encoding.setter
    def Encoding(self, value):
        self._encoding = value
        self._out.setEncoding(value)

    def publish(self, record):
        if self._level <= record.Level < OFF:
            self._publishRecord(record)
            return True
        return False

    def clearLogger(self):
        if self._sf.exists(self._url):
            self._sf.kill(self._url)

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


class ViewHandler(BaseHandler):
    def __init__(self, ctx, callback, level=ALL):
        super().__init__(ctx, level)
        self._callback = callback

    def publish(self, record):
        if self._level <= record.Level < OFF and self._callback:
            msg = self._formatter.format(record)
            self._callback(msg)
            return True
        return False

    def dispose(self):
        self._callback = None
        super().dispose()

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

from queue import SimpleQueue


class Indicators():
    def __init__(self, text, cancel, indicator=None):
        self._text = text
        self._cancel = cancel
        self._indicators = set()
        self._queue = SimpleQueue()
        if indicator:
            self.addIndicator(indicator)

    def init(self, total, value):
        if self._cancel.isDisposed():
            return False
        while not self._queue.empty():
            added, indicator = self._queue.get_nowait()
            if added:
                indicator.end()
                indicator.start(self._text, total)
                indicator.setValue(value)
                self._indicators.add(indicator)
            else:
                self._indicators.discard(indicator)
        return value == 0 and self.hasIndicator()

    def hasIndicator(self):
        return len(self._indicators) > 0

    def addIndicator(self, indicator):
        self._queue.put_nowait((True, indicator))

    def removeIndicator(self, indicator):
        self._queue.put_nowait((False, indicator))

    def start(self, text, total):
        if self._cancel.isDisposed():
            return
        for indicator in self._indicators:
            indicator.end()
            indicator.start(text, total)

    def set(self, text, value):
        if self._cancel.isDisposed():
            return
        for indicator in self._indicators:
            indicator.setText(text)
            indicator.setValue(value)

    def setValue(self, value):
        if self._cancel.isDisposed():
            return
        for indicator in self._indicators:
            indicator.setValue(value)

    def end(self):
        if self._cancel.isDisposed():
            return
        for indicator in self._indicators:
            indicator.end()

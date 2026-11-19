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

import unohelper

from com.sun.star.task import XStatusIndicator

from .unotool import findFrame
from .unotool import getWindowHeight
from .unotool import setWindowHeight


class Factory():
    def __init__(self, ctx=None, name=None, frame=None, offset=11):
        self._ctx = ctx
        self._name = name
        self._frame = frame if frame is not None else findFrame(ctx, name)
        self._point = getWindowHeight(self._frame, offset)
        self._indicators = set()

    def createIndicator(self):
        indicator = Wrapper(self._frame.createStatusIndicator())
        self._indicators.add(indicator)
        setWindowHeight(self._frame, self._point)
        return indicator

    def resetIndicator(self):
        indicator = self._getFinishedIndicator()
        if indicator:
            setWindowHeight(self._frame, self._point, - 1)
            self._indicators.remove(indicator)

    def _getFinishedIndicator(self):
        for indicator in self._indicators:
            if indicator.state is None:
                return indicator
        return None


class Wrapper(unohelper.Base,
              XStatusIndicator):
    def __init__(self, indicator):
        self._indicator = indicator
        self.state = False

    def start(self, text, total):
        self.state = True
        self._indicator.start(text, total)

    def setValue(self, value):
        self._indicator.setValue(value)

    def setText(self, text):
        self._indicator.setText(text)

    def end(self):
        self.state = None
        self._indicator.end()

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

from com.sun.star.awt.PosSize import SIZE

from com.sun.star.task import XStatusIndicator

from com.sun.star.util.MeasureUnit import APPFONT

from .unotool import findFrame

from threading import Lock
import traceback


class StatusIndicator(unohelper.Base,
                      XStatusIndicator):
    def __init__(self, ctx, name, offset=10):
        frame = findFrame(ctx, name)
        if frame:
            self._window = frame.getContainerWindow()
            self._progress = frame.createStatusIndicator()
            self._point = uno.createUnoStruct('com.sun.star.awt.Point', 0, offset)
            self._lock = Lock()
        else:
            self._window = self._progress = self._point = self._lock = None
        self._value = 0

    def start(self, text, value):
        if self._progress:
            self._setValue(0)
            self._setWindowHeight()
            self._progress.start(text, value)

    def setText(self, text):
        if self._progress:
            self._setText(text)

    def setValue(self, value):
        if self._progress:
            # XXX: In order to be able to progress in the loops it is necessary
            # XXX: to be able to add value to the current progression value.
            # XXX: This is what is done here thanks to a negative value
            self._setValue(value)

    def end(self):
        if self._progress:
            self._progress.end()
            self._setWindowHeight(-1)

    def reset(self):
        if self._progress:
            self._setValue(0)
            self._progress.reset()

    def _setText(self, text):
        with self._lock:
            self._progress.setText(text)

    def _setValue(self, value):
        with self._lock:
            if value < 0:
                self._value += abs(value)
            else:
                self._value = value
            self._progress.setValue(self._value)

    def _setWindowHeight(self, factor=1):
        size = self._window.getPosSize()
        offset = self._window.convertPointToPixel(self._point, APPFONT).Y * factor
        self._window.setPosSize(0, 0, size.Width, size.Height + offset, SIZE)


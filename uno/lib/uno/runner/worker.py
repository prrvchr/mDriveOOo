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

from com.sun.star.awt import XCallback

from ..unotool import getCallBack

from threading import Timer
import time
import traceback


class Worker(unohelper.Base,
             XCallback):
    def __init__(self, ctx, callback, steps, *args):
        self._callback = callback
        self._steps = steps
        self._args = args
        self._delay = 1
        self._asyncCall = getCallBack(ctx)

    def start(self):
        self._call()

    def notify(self, _data):
        try:
            start = time.perf_counter()

            call = next(self._steps)
            self._args = call(*self._args)

            delay = (time.perf_counter() - start) * self._delay
            Timer(delay, self._call).start()

        except StopIteration:
            try:
                if self._callback:
                    self._callback(True, *self._args)
            except Exception:
                print("Worker.notify() StopIteration ERROR: %s" % traceback.format_exc())

        except Exception:
            try:
                if self._callback:
                    self._callback(False, *self._args)
            except Exception:
                print("Worker.notify() Exception ERROR: %s" % traceback.format_exc())

    def _call(self):
        self._asyncCall.addCallback(self, None)

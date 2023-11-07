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

import unohelper

from com.sun.star.util import XModifyListener

import traceback


class PoolListener(unohelper.Base,
                   XModifyListener):
    def __init__(self, manager):
        self._manager = manager

    # XModifyListener
    def modified(self, event):
        try:
            print("PoolListener.modified()")
            self._manager.updateLoggers()
        except Exception as e:
            msg = "Error: %s" % traceback.format_exc()
            print(msg)

    def disposing(self, event):
        pass


class LoggerListener(unohelper.Base,
                     XModifyListener):
    def __init__(self, manager):
        self._manager = manager

    # XModifyListener
    def modified(self, event):
        try:
            print("LoggerListener.modified()")
            self._manager.updateLogger()
        except Exception as e:
            msg = "Error: %s" % traceback.format_exc()
            print(msg)

    def disposing(self, event):
        pass


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

from com.sun.star.frame import XTerminateListener

from com.sun.star.lang import XEventListener


import traceback


class EventListener(unohelper.Base,
                    XEventListener):
    def __init__(self, datasource):
        self._datasource = datasource

# XEventListener
    def disposing(self, event):
        try:
            print("EventListener.disposing() ******************")
            self._datasource.closeConnection(event.Source)
        except Exception as e:
            msg = "EventListener Error: %s" % traceback.format_exc()
            print(msg)


class TerminateListener(unohelper.Base,
                        XTerminateListener):
    def __init__(self, replicator):
        self._replicator = replicator

# XTerminateListener
    def queryTermination(self, event):
        try:
            self._replicator.dispose()
        except Exception as e:
            msg = "TerminateListener Error: %s" % traceback.format_exc()
            print(msg)

    def notifyTermination(self, event):
        pass

    def disposing(self, source):
        pass


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

from com.sun.star.awt import XMouseListener

from com.sun.star.awt.SystemPointer import ARROW
from com.sun.star.awt.SystemPointer import REFHAND

from com.sun.star.system.SystemShellExecuteFlags import URIS_ONLY

from .unotool import createService
from .unotool import executeShell


class LinkListener(unohelper.Base,
                   XMouseListener):
    def __init__(self, ctx, control):
        self._ctx = ctx
        self._url = ''
        self._control = control
        self._pointer = createService(ctx, 'com.sun.star.awt.Pointer')
        self._control.addMouseListener(self)

    def setUrl(self, url):
        self._url = url
        self._control.Model.HelpText = url

    # XMouseListener
    def mousePressed(self, event):
        if self._url and event.Buttons == 1:
            executeShell(self._ctx, self._url, flag=URIS_ONLY)

    def mouseEntered(self, _event):
        if self._url:
            self._pointer.setType(REFHAND)
            self._control.getPeer().setPointer(self._pointer)

    def mouseExited(self, _event):
        if self._url:
            self._pointer.setType(ARROW)
            self._control.getPeer().setPointer(self._pointer)

    def mouseReleased(self, _event):
        pass

    def disposing(self, _event):
        self._control = None
        self._pointer = None

#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-24 https://prrvchr.github.io                                  ║
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

from com.sun.star.ui.dialogs.ExecutableDialogResults import OK

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from .optionsmodel import OptionsModel
from .optionsview import OptionsView
from .optionshandler import OptionsListener
from .optionshandler import Tab1Handler
from .optionshandler import Tab2Handler

from ..unotool import createService
from ..unotool import getFilePicker
from ..unotool import getSimpleFile
from ..unotool import getUrl

from ..logger import LogManager

from ..configuration import g_extension
from ..configuration import g_identifier
from ..configuration import g_defaultlog

import os
import sys
import traceback


class OptionsManager(unohelper.Base):
    def __init__(self, ctx, window, url):
        self._ctx = ctx
        self._disposed = False
        self._disabled = False
        self._model = OptionsModel(ctx, url)
        window.addEventListener(OptionsListener(self))
        self._view = OptionsView(window, *self._model.getViewData())
        self._logmanager = LogManager(ctx, window.getPeer(), 'requirements.txt', g_identifier, g_defaultlog)

    def dispose(self):
        self._logmanager.dispose()
        self._disposed = True

    # TODO: One shot disabler handler
    def isHandlerEnabled(self):
        if self._disabled:
            self._disabled = False
            return False
        return True

# OptionsManager setter methods
    def updateView(self, versions):
        with self._lock:
            self.updateVersion(versions)

    def updateVersion(self, versions):
        with self._lock:
            if not self._disposed:
                protocol = self._view.getSelectedProtocol()
                if protocol in versions:
                    self._view.setVersion(versions[protocol])

    def saveSetting(self):
        self._logmanager.saveSetting()
        if self._model.saveSetting() and self._model.isUpdated():
            self._view.disableDriverLevel()

    def loadSetting(self):
        self._logmanager.loadSetting()
        self._view.initView(*self._model.loadSetting())

    def setDriverService(self, driver):
        self._view.setConnectionLevel(*self._model.setDriverService(driver))

    def setConnectionService(self, level):
        self._model.setConnectionService(level)


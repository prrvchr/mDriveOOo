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

from .optionsmodel import OptionsModel

from .optionsview import OptionsView

from .optionshandler import OptionsListener

from .option import OptionManager as Manager

from ..runner import DispatchListener

from ..setup import SetupCheck

from ..helper import getExtensions

from ..jdbcdriver import g_agent
from ..jdbcdriver import g_java
from ..jdbcdriver import g_protocol
from ..jdbcdriver import g_script
from ..jdbcdriver import g_service

from ..configuration import State
from ..configuration import g_extension

from ..configuration import g_defaultlog

import traceback


class OptionsManager():
    def __init__(self, ctx, logger, window, url=None):
        self._ctx = ctx
        self._disposed = False
        self._java = g_extension, g_java, g_script
        self._agent = g_service, g_protocol, g_agent
        self._extensions = getExtensions()
        self._model = OptionsModel(ctx, logger, url)
        self._manager = Manager(ctx, window, DispatchListener(self), g_defaultlog)
        self._view = OptionsView(window, self._model.getViewData())
        window.addEventListener(OptionsListener(self))
        self._loadView(self.init)

    def init(self, state):
        if not self._disposed:
            self._manager.init(state)
            self._view.refreshView(state)
            if state.java:
                version = self._model.getDriverVersion(self._getConfigApiLevel())
                self._view.setDriverVersion(version)

    def refresh(self, state):
        if not self._disposed:
            self._manager.refresh(state)
            self._view.refreshView(state)

    def dispose(self):
        self._disposed = True
        self._manager.dispose()

# OptionsManager setter methods
    def saveSetting(self):
        if self._manager.saveSetting():
            State.restart = True
            self._loadView(self.refresh)

    def loadSetting(self):
        self._manager.loadSetting()
        self._loadView(self.init)

    def dispatchFinished(self, notification):
        if not self._disposed:
            self._loadView(self.refresh)

# OptionsManager private getter methods
    def _getConfigApiLevel(self):
        return self._manager.getConfigApiLevel()

# OptionsManager private setter methods
    def _loadView(self, callback):
        mode = self._manager.getSetupMode()
        setup = SetupCheck(self._ctx, callback, java=self._java, agent=self._agent, python=True, extensions=self._extensions, mode=mode)
        setup.start()


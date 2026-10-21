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

from .option import OptionManager

from ..runner import DispatchListener

from ..setup import SetupCheck

from ..helper import getExtensions

from ..setup import showSetup

from ..jdbcdriver import g_agent
from ..jdbcdriver import g_java
from ..jdbcdriver import g_protocol
from ..jdbcdriver import g_script
from ..jdbcdriver import g_service

from ..configuration import State
from ..configuration import g_extension
from ..configuration import g_identifier

import traceback


class OptionsManager():
    def __init__(self, ctx, source, logger, window):
        self._ctx = ctx
        self._disposed = False
        self._java = g_extension, g_java, g_script
        self._agent = g_service, g_protocol, g_agent
        self._model = OptionsModel(ctx)
        self._view = OptionsView(window, *self._model.getViewData())
        self._manager = OptionManager(ctx, source, logger, window, self._model.getConfig())
        window.addEventListener(OptionsListener(self))
        self._loadView(self.init)

    def init(self, state):
        if not self._disposed:
            self._manager.init(state)
            self._view.initView(*self._model.getInitData(state))

    def refresh(self, state):
        if not self._disposed:
            self._manager.refresh(state)
            self._view.refreshView(self._model.getRefreshData(state))

    def loadSetting(self):
        self._loadView(self.init)

    def saveSetting(self):
        if self._manager.saveSetting():
            State.restart = True
            self._loadView(self.refresh)

    def dispose(self):
        self._disposed = True

    def showSetup(self):
        mode = self._view.getSetup()
        showSetup(self._ctx, g_identifier, Dispatch=DispatchListener(self), Mode=mode)

    def dispatchFinished(self, notification):
        if not self._disposed:
            self._loadView(self.refresh)

    def _loadView(self, callback):
        mode = self._view.getSetup()
        datasource = self._manager.getDataSourceUrl()
        setup = SetupCheck(self._ctx, callback, datasource, java=self._java, agent=self._agent, python=True, extensions=getExtensions(), mode=mode)
        setup.start()


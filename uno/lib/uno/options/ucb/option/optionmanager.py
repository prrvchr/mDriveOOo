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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.uno import Exception as UnoException

from .optionmodel import OptionModel
from .optionview import OptionView

from ..logger import LogManager

from .optionhandler import OptionHandler

from ...dbtool import getDataSourceConnection

from ...unotool import executeDispatch
from ...unotool import getDesktop
from ...unotool import getFilePicker

from ...configuration import g_defaultlog
from ...configuration import g_synclog

import traceback


class OptionManager():
    def __init__(self, ctx, source, logger, window, config):
        self._ctx = ctx
        self._source = source
        self._logger = logger
        self._model = OptionModel(ctx, config)
        self._view = OptionView(ctx, window, OptionHandler(self), *self._model.getViewData())
        self._logmanager = LogManager(ctx, self._view.getWindow(), 'requirements.txt', g_defaultlog, g_synclog)
        self._logmanager.initView()
        self._logger.logprb(INFO, 'OptionsManager', '__init__', 151)

    def init(self, state):
        self._view.initView(*self._model.getInitData(state))
        self._logmanager.loadSetting()
        self._logger.logprb(INFO, 'OptionsManager', 'init', 161)
        if state.java and state.database:
            try:
                url = self._model.getDatasourceUrl()
                connection = getDataSourceConnection(self._ctx, url)
            except UnoException as e:
                self._logger.logprb(SEVERE, 'OptionsManager', '__init__', 152, e.Message)
            else:
                connection.close()

    def refresh(self, state):
        self._view.refreshView(self._model.getRefreshData(state))

    def saveSetting(self):
        option = self._model.setViewData(*self._view.getViewData())
        changed = self._logmanager.saveSetting()
        self._logger.logprb(INFO, 'OptionsManager', 'saveSetting', 171, option, changed)
        return changed 

    def enableShare(self, enabled):
        self._view.enableShare(enabled)

    def enableSync(self, enabled):
        self._view.enableSync(enabled, self._model.getState())

    def setReset(self, enabled):
        self._view.enableResetFile(enabled)

    def viewData(self):
        url = self._model.getDatasourceUrl()
        getDesktop(self._ctx).loadComponentFromURL(url, '_default', 0, ())

    def viewFile(self):
        fp = getFilePicker(self._ctx)
        fp.setDisplayDirectory(self._model.getFileUrl())
        fp.execute()
        fp.dispose()

    def download(self):
        self._view.setStep(1)

    def upload(self):
        self._view.setStep(2)

    def spinUp(self, index):
        self._view.setChunk(index, self._view.getChunk(index) * 2)

    def spinDown(self, index):
        self._view.setChunk(index, self._view.getChunk(index) / 2)

    def enableMacro(self, enabled):
        self._view.enableCustomize(enabled)

    def customizeMenu(self):
        executeDispatch(self._ctx, '.uno:ConfigureDialog')

    def getDataSourceUrl(self):
        return self._model.getDatasourceUrl()


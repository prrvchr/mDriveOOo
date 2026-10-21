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

from .optionmodel import OptionModel

from .optionview import OptionView

from .optionhandler import OptionHandler

from ...unotool import getDesktop

from ..logger import LogManager

from ...configuration import g_defaultlog
from ...configuration import g_synclog


class OptionManager():
    def __init__(self, ctx, logger, window, config):
        self._ctx = ctx
        self._model = OptionModel(ctx, config)
        self._view = OptionView(ctx, window, OptionHandler(self))
        self._logmanager = LogManager(ctx, self._view.getWindow(), 'requirements.txt', g_defaultlog, g_synclog)
        self._logmanager.initView()
        self._logger = logger
        self._logger.logprb(INFO, 'OptionManager', '__init__()', 301)
        self._model.loadDriver()

    def init(self, state):
        self._view.initView(*self._model.getInitData(state))
        self._logmanager.loadSetting()
        self._logger.logprb(INFO, 'OptionManager', 'init()', 311)

    def refresh(self, state):
        self._view.refreshView(state)

    def saveSetting(self):
        option = self._model.setViewData(*self._view.getViewData())
        saved = self._logmanager.saveSetting()
        self._logger.logprb(INFO, 'OptionManager', 'saveSetting()', 321, option, saved)
        return saved

    def viewData(self):
        getDesktop(self._ctx).loadComponentFromURL(self.getDataSourceUrl(), '_default', 0, ())

    def getDataSourceUrl(self):
        return self._model.getDataSourceUrl()


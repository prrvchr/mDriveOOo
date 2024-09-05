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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from .optionsmodel import OptionsModel
from .optionsview import OptionsView

from ..unotool import executeDispatch
from ..unotool import getDesktop

from ..logger import LogManager

from ..configuration import g_identifier
from ..configuration import g_defaultlog
from ..configuration import g_synclog

import traceback


class OptionsManager():
    def __init__(self, ctx, window, logger):
        self._ctx = ctx
        self._logger = logger
        self._model = OptionsModel(ctx)
        self._view = OptionsView(window, *self._model.getInitData())
        self._view.setViewData(*self._model.getViewData(OptionsManager._restart))
        self._logmanager = LogManager(ctx, window.Peer, 'requirements.txt', g_defaultlog, g_synclog)
        self._logger.logprb(INFO, 'OptionsManager', '__init__()', 151)

    _restart = False

    def loadSetting(self):
        self._view.setViewData(*self._model.getViewData(OptionsManager._restart))
        self._logmanager.loadSetting()
        self._logger.logprb(INFO, 'OptionsManager', 'loadSetting()', 161)

    def saveSetting(self):
        share, name, index, timeout, download, upload = self._view.getViewData()
        option = self._model.setViewData(share, name, index, timeout, download, upload)
        log = self._logmanager.saveSetting()
        if log:
            OptionsManager._restart = True
            self._view.setRestart(True)
        self._logger.logprb(INFO, 'OptionsManager', 'saveSetting()', 171, option, log)

    def enableShare(self, enabled):
        self._view.enableShare(enabled)

    def enableTimeout(self, enabled):
        self._view.enableTimeout(enabled)

    def viewData(self):
        url = self._model.getDatasourceUrl()
        getDesktop(self._ctx).loadComponentFromURL(url, '_default', 0, ())

    def download(self):
        self._view.setStep(1)

    def upload(self):
        self._view.setStep(2)


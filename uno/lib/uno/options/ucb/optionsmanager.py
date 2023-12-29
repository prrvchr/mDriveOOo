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

from .optionsmodel import OptionsModel
from .optionsview import OptionsView

from ..unotool import executeDispatch
from ..unotool import getDesktop

from ..logger import LogManager

from ..configuration import g_identifier
from ..configuration import g_defaultlog
from ..configuration import g_synclog

from collections import OrderedDict
import os
import sys
import traceback


class OptionsManager(unohelper.Base):
    def __init__(self, ctx, window):
        self._ctx = ctx
        self._model = OptionsModel(ctx)
        exist = self._model.hasData()
        resumable = self._model.isResumable()
        data = self._model.getViewData()
        self._view = OptionsView(window, exist, resumable, data)
        self._logger = LogManager(ctx, window.Peer, self._getInfos(), g_identifier, g_defaultlog, g_synclog)

    def saveSetting(self):
        share, name, index, timeout, download, upload = self._view.getViewData()
        self._model.setViewData(share, name, index, timeout, download, upload)
        self._logger.saveSetting()

    def loadSetting(self):
        data = self._model.getViewData()
        self._view.setViewData(*data)
        self._logger.loadSetting()

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

    def _getInfos(self):
        infos = OrderedDict()
        infos['dateutil'] =           ('__version__',     '2.8.2')
        infos['ijson'] =              ('__version__',     '3.2.2')
        infos['packaging'] =          ('__version__',     '23.1')
        infos['six'] =                ('__version__',     '1.16.0')
        return infos

    def _getExceptionMsg(self, e):
        error = repr(e)
        trace = repr(traceback.format_exc())
        return error, trace


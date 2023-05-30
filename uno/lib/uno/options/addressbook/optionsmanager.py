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

from ..unotool import getDesktop

from ..logger import LogManager

from ..configuration import g_identifier
from ..configuration import g_defaultlog

from collections import OrderedDict
import os
import sys
import traceback


class OptionsManager(unohelper.Base):
    def __init__(self, ctx, window, ijson=True):
        self._ctx = ctx
        self._model = OptionsModel(ctx)
        timeout = self._model.getTimeout()
        enabled = self._model.hasDatasource()
        self._view = OptionsView(window, timeout, enabled)
        self._logger = LogManager(self._ctx, window.Peer, self._getInfos(ijson), g_identifier, g_defaultlog)

    def saveSetting(self):
        self._model.setTimeout(self._view.getTimeout())
        self._logger.saveSetting()

    def loadSetting(self):
        self._view.setTimeout(self._model.getTimeout())
        self._logger.loadSetting()

    def viewData(self):
        url = self._model.getDatasourceUrl()
        getDesktop(self._ctx).loadComponentFromURL(url, '_default', 0, ())

    def _getInfos(self, ijson):
        infos = OrderedDict()
        version  = ' '.join(sys.version.split())
        infos[111] = version
        path = os.pathsep.join(sys.path)
        infos[112] = path
        if ijson:
            # Required modules for ijson
            try:
                import cffi
            except Exception as e:
                infos[113] = self._getExceptionMsg(e)
            else:
                infos[114] = (cffi.__version__, cffi.__file__)
        return infos

    def _getExceptionMsg(self, e):
        error = repr(e)
        trace = repr(traceback.format_exc())
        return error, trace


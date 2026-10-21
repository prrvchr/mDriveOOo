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

import uno

from ..runner import Conflict
from ..runner import Extension
from ..runner import Java
from ..runner import Pypi
from ..runner import Python

from ...configuration import State

from ...runner import Runner

from ...unotool import deregisterStartupJob
from ...unotool import getConfiguration
from ...unotool import getStringResource
from ...unotool import saveWindowPosition

from ...configuration import g_extension
from ...configuration import g_identifier

import traceback


class SetupModel():
    def __init__(self, ctx, name, database, java, agent, python, extensions, mode):
        self._ctx = ctx
        self._name = name
        self._extensions = extensions
        self._java = java
        self._agent = agent
        self._database = database
        self._python = python
        self._check = None
        self._packages = None
        self._url = None
        self._mode = mode
        self._reports = []
        self._position = 'SetupPosition'
        self._config = getConfiguration(ctx, g_identifier, True)
        self._resolver = getStringResource(ctx, g_identifier, 'dialogs', 'SetupWindow')
        self._resources = {'Title': 'SetupWindow.Title',
                           'Header': 'SetupWindow.Label1.Label.%s'}

    def savePosition(self, position):
        saveWindowPosition(self._config, position, self._position)

    def getCancel(self):
        return self._cancel

    def getHeader(self, **kwargs):
        return self._check.getHeader(**kwargs)

    def getError(self, error):
        return self._getHeader(4, error=error)

    def getResult(self, success):
        return self._check.setReport(self._reports, success)

    def getReport(self):
        if self._reports:
            return False, *self._reports[0]
        return True, self._getHeader(2 if State.restart else 3)

    def getViewData(self):
        return self._getDialogPosition(), self._getTitle(), self._getHeader(1, extension=g_extension)

    def getDataBasePath(self):
        return self._database.path if self.hasDataBase() else None

    def setCheckExtension(self, callback):
        self._check = Extension(self._ctx, callback, self._extensions)

    def setCheckJava(self, callback):
        self._check = Java(self._ctx, callback, self._java, self._agent)

    def setCheckDataBase(self, callback):
        self._check = self._database.withCallback(callback)

    def setCheckPython(self, callback):
        self._check = Python(self._ctx, callback, self._mode)

    def setPythonData(self):
        self._packages = self._check.packages
        self._url = self._check.url
        self._mode = self._check.mode

    def setCheckPypi(self, callback, state):
        self._check = Pypi(self._ctx, callback, self._packages, self._url, self._mode, state)

    def setCheckConflict(self, callback):
        self._check = Conflict(self._ctx, callback, self._packages, self._url)

    def startCheck(self, progress, cancel):
        runner = Runner(self._ctx, self._check, progress, cancel)
        runner.start()

    def hasDataBase(self):
        return self._database is not None

    def hasPython(self):
        return self._python

    def deregisterJob(self):
        deregisterStartupJob(self._ctx, self._name)

    def _getDialogPosition(self):
        return uno.createUnoStruct('com.sun.star.awt.Point', *self._config.getByName(self._position))

# SetupModel StringRessoure methods
    def _getTitle(self):
        return self._resolver.resolveString(self._resources.get('Title')).format(extension=g_extension)

    def _getHeader(self, code, **kwargs):
        resource = self._resources.get('Header') % code
        return self._resolver.resolveString(resource).format(**kwargs)


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

from com.sun.star.util import CloseVetoException

from .setupmodel import SetupModel

from .setupview import SetupView

from .setuphandler import CloseListener
from .setuphandler import WindowHandler

from ..setupcheck import SetupCheck

from ..setupstate import SetupState

from ...configuration import State

from ...runner import Cancel

from ...unotool import Transferable

from ...unotool import getSystemClipboard
from ...unotool import notifyDispatch

import traceback

class SetupManager():
    def __init__(self, ctx, source, /, database=None, java=None, agent=None, python=False, extensions=None, *, dispatch=None, mode=None, frame=None, name=None, state=None):
        self._ctx = ctx
        self._source = source
        self._dispatch = dispatch
        self._cancel = Cancel()
        self._running = True
        self._steps = None
        self._reported = False
        self._model = SetupModel(ctx, name, database, java, agent, python, extensions, mode)
        self._listener = CloseListener(self)
        self._view = SetupView(ctx, frame, WindowHandler(self), self._listener, name, *self._model.getViewData())
        if state:
            self.notify(state)
        else:
            path = self._model.getDataBasePath()
            self._check = SetupCheck(self._ctx, self.notify, path, java, agent, python, extensions)
            self._check.start()

    def notify(self, state):
        self._running = False
        self._state = state
        self._steps = self._buildSteps()
        self._view.enableButtons(True)

    def isRunnable(self):
        return self._view.execute()

    def dispose(self):
        self._view.dispose()

    def _buildSteps(self) -> list:
        steps = []
        if not self._state.extension:
            steps.append(self._checkExtension)
        if not self._state.java:
            steps.append(self._checkJava)
        if self._state.extension and self._state.java and self._model.hasDataBase():
            steps.append(self._checkDataBase)
        if self._model.hasPython():
            steps.append(self._checkPython)
        return steps

    def next(self):
        if self._running:
            return

        if self._steps:
            step = self._steps.pop(0)
            step()
            return

        if self._state.runnable or not self._steps:
            if not self._reported:
                self._setReport()
                self._reported = True
            else:
                self._running = True
                self._model.deregisterJob()
                self._running = False
                self._close()
                self._dispose()

# XCloseListener
    def queryClosing(self, source, ownership):
        self._close()
        if self._running:
            raise CloseVetoException()
        if not ownership:
            self._dispose()

    def notifyClosing(self, source):
        source.removeCloseListener(self._listener)

    def copy(self):
        transferable = Transferable(self._ctx).getByString(self._view.getTraceBack())
        getSystemClipboard(self._ctx).setContents(transferable, None)

    def cancel(self):
        self._close()
        if not self._running:
            self._dispose()

    def setMaxProgress(self, value):
        self._view.setMaxProgress(value)

    def setProgress(self, text, progress):
        self._view.setProgress(text, progress)

    def _close(self):
        self._cancel.set()
        self._view.enableButtons(False)
        self._model.savePosition(self._view.getWindowPosition())

    def _dispose(self):
        if self._dispatch:
            notifyDispatch(self._source, self._dispatch)
        self._view.close(self._state.runnable)

    def notifyCheck(self, success, error):
        self._running = False
        if self._cancel.isSet():
            return self._dispose()
        if error:
            return self._setError(error)
        self._setResult(success)

    def _checkExtension(self):
        self._running = True
        self._model.setCheckExtension(self.notifyCheck)
        self._setHeader()
        self._model.startCheck(self._view.getIndicator(), self._cancel)

    def _checkJava(self):
        self._running = True
        self._model.setCheckJava(self.notifyCheck)
        self._setHeader()
        self._model.startCheck(self._view.getIndicator(), self._cancel)

    def _checkDataBase(self):
        self._running = True
        self._model.setCheckDataBase(self.notifyCheck)
        self._setHeader()
        self._model.startCheck(self._view.getIndicator(), Cancel())

    def _checkPython(self):
        self._running = True
        self._model.setCheckPython(self.notifyPython)
        self._setHeader()
        self._model.startCheck(self._view.getIndicator(), self._cancel)

    def notifyPython(self, success, checked, internet, error):
        self._running = False
        if self._cancel.isSet():
            return self._dispose()
        if error:
            return self._setError(error)
        self._model.setPythonData()
        if not checked and internet:
            self._steps.insert(0, self._installPackages)
        elif self._state.pcode == 3:
            self._steps.insert(0, self._checkConflict)
        self._setResult(checked)

    def _installPackages(self):
        self._running = True
        self._model.setCheckPypi(self.notifyPypi, self._state)
        self._setHeader()
        self._model.startCheck(self._view.getIndicator(), self._cancel)

    def notifyPypi(self, success, error):
        self._running = False
        if success:
            State.restart = True
        if self._cancel.isSet():
            return self._dispose()
        if error:
            return self._setError(error)
        if self._state.pcode == 3:
            self._steps.insert(0, self._checkConflict)
        self._setResult(success)

    def _checkConflict(self):
        self._running = True
        self._model.setCheckConflict(self.notifyCheck)
        self._setHeader()
        self._model.startCheck(self._view.getIndicator(), self._cancel)

    def _setHeader(self):
        if not self._cancel.isSet():
            self._view.setHeader(self._model.getHeader())

    def _setResult(self, success):
        if not self._cancel.isSet():
            self._view.setResult(*self._model.getResult(success))

    def _setError(self, error):
        if not self._cancel.isSet():
            self._view.setError(self._model.getError(error.cause), error.trace)

    def _setReport(self):
        if not self._cancel.isSet():
            success, *result = self._model.getReport()
            self._view.setResult(*result)
            if success:
                self._step = 7


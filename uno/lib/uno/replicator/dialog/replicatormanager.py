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

from com.sun.star.frame import TerminationVetoException

from com.sun.star.util import CloseVetoException

from .replicatormodel import ReplicatorModel

from .replicatorview import ReplicatorView

from .replicatorhandler import CloseListener
from .replicatorhandler import WindowHandler
from .replicatorhandler import TerminateListener

from ..task import Replicator

from ...dbsetup import DBSetup

from ...logger import LogController

from ...runner import Cancel
from ...runner import Runner

from ...unotool import CallBack

# from ...setup import SetupCheck
from ...setup import SetupManager

from ...logger import ViewHandler

# from ...dbinit import getDataSourceUrl

from ...helper import getExtensions

from ...unotool import getCallBack
from ...unotool import getDesktop

from ...jdbcdriver import g_java
from ...jdbcdriver import g_script

from ...configuration import g_extension
from ...configuration import g_setup
from ...configuration import g_synclog

from threading import Timer


class ReplicatorManager():
    def __init__(self, ctx, job, queue):
        print("ReplicatorManager.__init__() 1")
        self._ctx = ctx
        self._job =job
        self._queue = queue
        self._data = set()
        self._model = ReplicatorModel(ctx)
        self._running = False
        self._cancel = Cancel()
        self._timer = None
        self._closelistener = CloseListener(self)
        self._view = ReplicatorView(ctx, WindowHandler(self), self._closelistener, *self._model.getViewData())
        self._terminatelistener = TerminateListener(self)
        getDesktop(ctx).addTerminateListener(self._terminatelistener)
        self._logger = LogController(ctx, g_synclog)
        self._logger.addRollerHandler()
        self._handler = ViewHandler(ctx, self.updateLog)
        self._logger.addLogHandler(self._handler)
        self._logger.logp(INFO, 'ReplicatorManager', '__init__', 'initialization completed')
        self._view.initLogger(*self._logger.getLogContent(True))
        self._delai = 60
        self._java = g_extension, g_java, g_script
        self._extensions = getExtensions()
        print("ReplicatorManager.__init__() 2")
        self._callback = CallBack(self._startReplicator)
        self._asyncCall = getCallBack(self._ctx)
        self._call()
        # self._check = SetupCheck(ctx, self.notify, database=getDataSourceUrl(ctx), java=self._java, python=True, extensions=self._extensions)
        # self._check.start()

    def notify(self, state):
        if not state.runnable:
            database = DBSetup(self._ctx)
            # parent = self._view.getWindow()
            setup = SetupManager(self._ctx, None, database=database, java=self._java, python=True, extensions=self._extensions, parent=None, name=g_setup, state=state)
            if not setup.isRunnable():
                setup.dispose()
                self._close()
                return
            setup.dispose()
        if not self._cancel.isSet():
            self._startReplicator()
            self._model.initReplicator()
            self._view.setToggleState(*self._model.initToggleState(0))
            self._view.enableButtons(True)

    def updateLog(self, msg):
        self._view.updateLog(msg)

# XCloseListener
    def queryClosing(self, _source, ownership):
        print("ReplicatorManager.queryClosing() ownership: %s" % ownership)
        self._shutDown()
        if not ownership and self._running:
            raise CloseVetoException()
        self._dispose()

    def notifyClosing(self, source):
        print("ReplicatorManager.notifyClosing() *******************************************")
        source.removeCloseListener(self._closelistener)
        self._view.dispose()

# XTerminateListener
    def queryTermination(self, _source):
        print("ReplicatorManager.queryTermination() 1")
        self._shutDown(True)
        if self._running:
            print("ReplicatorManager.queryTermination() 2")
            raise TerminationVetoException()
        print("ReplicatorManager.queryTermination() 3")
        self._dispose()

    def notifyTermination(self, source):
        print("ReplicatorManager.notifyTermination() 1")
        source.removeTerminateListener(self._terminatelistener)
        self._dispose()
        print("ReplicatorManager.notifyTermination() 1")

    def clearLog(self):
        self._logger.clearLogger()
        self._view.initLogger(*self._logger.getLogContent(True))

    def showLog(self, state):
        print("ReplicatorManager.showLog() 1 state: %s" % state)
        self._view.setLogState(*self._model.getLogState(state))

    def closeReplicator(self):
        self._shutDown()
        if not self._running:
            self._close()

    def onReplicationEnd(self, success=True):
        print("ReplicatorManager.onReplicationEnd() 1 success: %s" % success)
        self._running = False
        if self._cancel.isSet():
            self._close()
            if self._cancel.isDisposed():
                print("ReplicatorManager.onReplicationEnd() 2")
                getDesktop(self._ctx).terminate()
        else:
            print("ReplicatorManager.onReplicationEnd() 3")
            self._view.resetIndicator()
            self._view.setLabelState(self._model.getLabelState(0))
            self._timer = Timer(self._delai, self._call)
            self._timer.start()
            print("ReplicatorManager.onReplicationEnd() 4")

    def _startReplicator(self):
        print("ReplicatorManager._startReplicator() 1")
        if self._running or self._cancel.isSet():
            return
        self._running = True
        self._cancelTimer()
        self._updateData()
        self._view.setLabelState(self._model.getLabelState(1))
        indicator = self._view.getIndicator()
        print("ReplicatorManager._startReplicator() 2")

        task = Replicator(self._ctx, self.onReplicationEnd, self._data)
        runner = Runner(self._ctx, task, self._cancel, indicator, self._logger)
        runner.start()

    def _close(self):
        self._view.close()

    def _shutDown(self, terminate=False):
        self._cancel.set(disposed=terminate)
        self._view.setLabelState(self._model.getLabelState(2))
        self._cancelTimer()
        self._logger.removeLogHandler(self._handler)
        self._logger.removeRollerHandler()

    def _dispose(self):
        self._view.enableButtons(False)
        self._model.savePosSize(self._view.getWindowPosSize())
        if self._queue:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except Exception:
                    break
            self._queue = None
        if self._job:
            self._job.__class__._queue = None
            self._job = None

    def _cancelTimer(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _updateData(self):
        while not self._queue.empty():
            self._data.add(self._queue.get())

    def _call(self):
        self._asyncCall.addCallback(self._callback, None)

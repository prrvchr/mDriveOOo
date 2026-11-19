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

import unohelper

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.awt import XCallback

from .error import CancelException
from .error import RunnerException

from .indicators import Indicators

from ..unotool import getCallBack

from threading import Timer
import time
import traceback


class Runner(unohelper.Base,
             XCallback):
    def __init__(self, ctx, task, cancel, indicator=None, logger=None):
        self._task = task
        self._cancel = cancel
        self._indicators = Indicators(task.getMessage(1), cancel, indicator)
        self._logger = logger
        self._total = task.total
        self._asyncCall = getCallBack(ctx)

    def addStatusIndicator(self, indicator):
        self._indicators.addIndicator(indicator)

    def removeStatusIndicator(self, indicator):
        self._indicators.removeIndicator(indicator)

    def start(self):
        self._call()

    def notify(self, _data):
        try:
            start = time.perf_counter()

            if self._indicators.init(self._total, self._task.step) and self._logger:
                self._logger.logp(INFO, 'Runner', 'start', self._task.getMessage(1))

            if self._cancel.isSet():
                raise CancelException()

            if self._task.isExtended(self._total):
                self._total = self._task.total
                if self._indicators.hasIndicator():
                    msg = self._task.getMessage(2)
                    self._indicators.start(msg, self._task.total)
                    self._indicators.set(msg, self._task.step)
                    if self._logger:
                        self._logger.logp(INFO, 'Runner', 'extended', msg)

            resource, options, call, *args = next(self._task.steps)

            if self._indicators.hasIndicator():
                msg = self._task.resolveString(resource, *options)
                self._indicators.set(msg, self._task.step)
                if self._logger:
                    self._logger.logp(INFO, *self._getLogInfos(resource, msg))

            call(*args)
            self._task.step += 1
            delay = (time.perf_counter() - start) * self._task.delay

            # FIXME: If we want an indicator that reaches the end, we must update its value separately.
            # FIXME: If it’s too fast, it might give the impression that the progress bar does not reach the end.
            if self._indicators.hasIndicator():
                if self._task.step == self._total:
                    delay = max(0.1, delay)
                self._indicators.setValue(self._task.step)
            Timer(delay, self._call).start()

        except StopIteration:
            try:
                if self._indicators.hasIndicator():
                    self._indicators.end()
                    if self._logger:
                        msg = self._task.getMessage(4)
                        self._logger.logp(INFO, 'Runner', 'stop', msg)
                self._task.callback()
            except Exception:
                print("Runner.notify() StopIteration ERROR: %s" % traceback.format_exc())

        except CancelException:
            try:
                self._finalize()
                if self._indicators.hasIndicator():
                    self._indicators.end()
                    if self._logger:
                        msg = self._task.getMessage(5)
                        self._logger.logp(SEVERE, 'Runner', 'CancelException', msg)
                print("Runner.CancelException msg: %s" % self._task.getMessage(5))
                self._task.callback(False)
            except Exception:
                print("Runner.notify() CancelException ERROR: %s" % traceback.format_exc())

        except RunnerException as e:
            try:
                self._finalize()
                if self._indicators.hasIndicator():
                    self._indicators.end()
                    if self._logger:
                        msg = self._task.getMessage(6, e.cause, e.trace)
                        self._logger.logp(SEVERE, 'Runner', 'RunnerException', msg)
                self._task.callback(False, e)
            except Exception:
                print("Runner.notify() RunnerException ERROR: %s" % e.trace)
            print("Runner.notify() RunnerException ERROR: %s" % e.trace)

        except Exception as e:
            try:
                skipped = self._task.skipSteps()
                if skipped > 0:
                    self._task.step += skipped
                    if self._indicators.hasIndicator():
                        msg = self._task.getMessage(3)
                        self._indicators.set(msg, self._task.step)
                        if self._logger:
                            self._logger.logp(SEVERE, 'Runner', 'skipSteps', msg)
                    Timer(self._task.delay, self._call).start()
                else:
                    self._finalize()
                    trace = traceback.format_exc()
                    if self._indicators.hasIndicator():
                        self._indicators.end()
                        if self._logger:
                            error = e.__class__.__name__
                            msg = self._task.getMessage(6, error, trace)
                            self._logger.logp(SEVERE, 'Runner', 'Exception', msg)
                    self._task.callback(False, RunnerException(e, trace))
            except Exception:
                print("Runner.notify() Exception ERROR: %s" % traceback.format_exc())
            print("Runner.notify() Exception ERROR: %s" % traceback.format_exc())

    def _call(self):
        self._asyncCall.addCallback(self, None)

    def _finalize(self):
        step = self._task.getStepFinalize()
        if step is None:
            return
        resource, options, call, *args = step
        call(*args)
        if self._indicators.hasIndicator():
            msg = self._task.resolveString(resource, *options)
            self._indicators.set(msg, self._total)
            if self._logger:
                self._logger.logp(INFO, *self._getLogInfos(resource, msg))

    def _getLogInfos(self, resource, msg):
        return self._task.getClass(resource), self._task.getMethod(resource), msg

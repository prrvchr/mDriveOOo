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

from com.sun.star.awt import XCallback

from .setupstate import SetupState

from ..unotool import getCallBack
from ..unotool import getResourceLocation
from ..unotool import getSimpleFile
from ..unotool import getStringResource

from .helper import checkAgent
from .helper import checkExtension
from .helper import checkPython
from .helper import getJavaStatus
from .helper import getJavaVersion
from .helper import getRequirementsUrl
from .helper import getSetupUpdateMode

from ..configuration import g_identifier
from ..configuration import g_resource

from threading import Timer
import traceback


class SetupCheck(unohelper.Base,
                 XCallback):
    def __init__(self, ctx, callback, /, database=None, java=None, agent=None, python=False, extensions=None, *, mode=None, progress=None):
        self._ctx = ctx
        self._callback = callback
        self._progress = progress
        self._resolver = getStringResource(ctx, g_identifier, g_resource, 'SetupCheck') if progress else None
        self._asyncCall = getCallBack(ctx)
        self._state = SetupState()
        self._step = 0
        total = len(extensions) if extensions else 0
        self._total = total + sum(1 for x in (database, java, java, java and agent, python) if x)
        self._steps = self._getCheckStep(ctx, database, java, agent, python, extensions, mode)

    def start(self):
        if self._progress:
            self._progress.start(self._resolver.resolveString(10101), self._total)
        Timer(0.1, self._call).start()

    def notify(self, data):
        try:
            resource, args, call, *kwargs = next(self._steps)
            call(*kwargs)
            if self._progress:
                self._step += 1
                self._progress.setText(self._resolver.resolveString(resource) % args)
                self._progress.setValue(self._step)
            Timer(0.1, self._call).start()
        except StopIteration:
            self._callback(self._state)
        except Exception as e:
            self._callback(SetupState(False))

    def stepCheckExtension(self, ctx, identifier, name, version):
        self._state.extension &= checkExtension(ctx, identifier, name, version)

    def stepCheckJavaStatus(self, ctx):
        self._state.jcode = getJavaStatus(ctx)

    def stepCheckJavaVersion(self, ctx, extension, version, script):
        self._state.jcode, _ = getJavaVersion(ctx, extension, version, script)

    def stepCheckJavaAgent(self, ctx, service, url, agent):
        self._state.jcode = checkAgent(ctx, service, url, agent)

    def stepCheckDataBase(self, ctx, database):
        self._state.database = getSimpleFile(ctx).exists(database)

    def stepCheckPython(self, ctx, mode):
        self._state.pcode = 2
        url = getResourceLocation(ctx, g_identifier)
        requirements = getRequirementsUrl(url)
        if getSimpleFile(ctx).exists(requirements):
            if mode is None:
                mode = getSetupUpdateMode(ctx, g_identifier)
            self._state.pcode = checkPython(url, requirements, mode)

    def _getCheckStep(self, ctx, database, java, agent, python, extensions, mode):
        if extensions:
            for identifier, infos in extensions.items():
                yield self._getStepCheckExtension(ctx, identifier, *infos)
        if java:
            yield self._getStepCheckJavaStatus(ctx)
            if self._state.java:
                yield self._getStepCheckJavaVersion(ctx, *java)
            if self._state.java and agent:
                yield self._getStepCheckJavaAgent(ctx, *agent)
        if database:
            yield self._getStepCheckDataBase(ctx, database)
        if python:
            yield self._getStepCheckPython(ctx, mode)

    def _call(self):
       self._asyncCall.addCallback(self, None)

    def _getStepCheckExtension(self, ctx, identifier, name, version):
        return 10201, (name, version), self.stepCheckExtension, ctx, identifier, name, version

    def _getStepCheckJavaStatus(self, ctx):
        return 10301, (), self.stepCheckJavaStatus, ctx

    def _getStepCheckJavaVersion(self, ctx, extension, version, script):
        return 10401, (version, ), self.stepCheckJavaVersion, ctx, extension, version, script

    def _getStepCheckJavaAgent(self, ctx, service, url, agent):
        return 10501, (), self.stepCheckJavaAgent, ctx, service, url, agent

    def _getStepCheckDataBase(self, ctx, database):
        return 10601, (database, ), self.stepCheckDataBase, ctx, database

    def _getStepCheckPython(self, ctx, mode):
        return 10701, (), self.stepCheckPython, ctx, mode

    def _hasJava(self):
        return self._code == 0

    @classmethod
    def isValid(cls, ctx, database=None, java=None, agent=None, python=False, extensions=None, mode=None):
        code = None
        if extensions:
            for identifier, infos in extensions.items():
                if not checkExtension(ctx, identifier, *infos):
                    return False
        if java:
            code = getJavaStatus(ctx)
            if code != 0:
                return False
            code, _ = getJavaVersion(ctx, *java)
            if code != 0:
                return False
            if agent and checkAgent(ctx, *agent):
                return False
        if database and not getSimpleFile(ctx).exists(database):
            return False
        if python:
            url = getResourceLocation(ctx, g_identifier)
            requirements = getRequirementsUrl(url)
            if getSimpleFile(self._ctx).exists(requirements):
                if mode is None:
                    mode = getSetupUpdateMode(ctx, g_identifier)
                code = checkPython(url, requirements, mode)
                if code != 0:
                    return False
        return True


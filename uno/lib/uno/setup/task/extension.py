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

from .setup import Setup

from ...unotool import Resource

from ..helper import checkExtension


class Extension(Setup):
    def __init__(self, ctx, callback, extensions):
        super().__init__(ctx, callback)
        self._absent = []
        self._present = []
        self.total = len(extensions)
        self._resources = {1: Resource(10101), 2: Resource(10102)}
        self.steps = self._getSetupSteps(ctx, extensions)

    def getHeader(self, **kwargs):
        return self._resolver.resolveString(10201).format(**kwargs)

    def setReport(self, reports, success):
        if not success:
            reports.append(self._getReport(success))
        return self._getHeader(success), self._getResult(success)

    def callback(self, success=True, error=None):
        self._callback(self._getSuccess(success), error)

    def stepCheckExtension(self, ctx, identifier, name, version):
        if checkExtension(ctx, identifier, name, version):
            self._present.append((name, version))
        else:
            self._absent.append((name, version))

    def _getSetupSteps(self, ctx, extensions):
        for identifier, infos in extensions.items():
            yield self._getStepCheckExtension(ctx, identifier, *infos)

    def _getStepCheckExtension(self, ctx, identifier, name, version):
        return 10301, (name, version), self.stepCheckExtension, ctx, identifier, name, version

    def _getHeader(self, success):
        code = 10401 if success else 10402
        return self._resolver.resolveString(code)

    def _getReport(self, success):
        return self._resolver.resolveString(10501), self._getResult(success), False

    def _getResult(self, success):
        extensions = self._present if success else self._absent
        return '\n'.join(['%s version %s' % (name, version) for (name, version) in extensions])

    def _getSuccess(self, success):
        return success and len(self._absent) == 0

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

from .check import Check

from ..helper import checkPython
from ..helper import getRequirementsUrl
from ..helper import hasFaultySuffix
from ..helper import installPackage
from ..helper import renamePackageSuffix
from ..helper import uninstallPackage

import traceback


class Pypi(Check):
    def __init__(self, ctx, callback, packages, url, mode, state):
        super().__init__(ctx, callback)
        self._installed = {}
        self._aborted = {}
        self._url = url
        self._path = url + '/service/pythonpath'
        self._mode = mode
        self._state = state
        self._fautly = False
        self.packages = {}
        self.total = 2
        self.label1 = self.resolver.resolveString(40101)
        self.label2 = self.resolver.resolveString(40102)
        self.steps = self._getCheckStep(packages)

    def getHeader(self, **kwargs):
        return self.resolver.resolveString(40201).format(**kwargs)

    def setReport(self, reports, success):
        if not success:
            reports.append(self._getReport(success))
        return self._getHeader(success), self._getResult(success), True

    def callback(self, success=True, error=None):
        self._callback(self._getSuccess(success), error)

    def stepGetStepCount(self, packages):
        self.total += sum(i for i in self._getStepCount(packages))

    def stepUninstallPackage(self, package):
        uninstallPackage(package, self._path)

    def stepInstallPackage(self, package, version, url):
        if installPackage(url, self._path):
            self._installed[package] = version
        else:
            self._aborted[package] = version

    def stepRenamePackage(self, package):
        renamePackageSuffix(package, self._path)

    def stepSetPythonCode(self, packages):
        requirements = getRequirementsUrl(self._url)
        self._state.pcode = checkPython(self._url, requirements, self._mode)
        self.packages = packages

    def _getCheckStep(self, packages):
        yield self._getStepGetStepCount(packages)
        for package, data in packages.items():
            version1, version2, url = data
            if version1 != version2:
                if version1:
                    yield self._getStepUninstallPackage(package)
                yield self._getStepInstallPackage(package, version2, url)
                if self._fautly:
                    yield self._getStepRenamePackage(package)
        yield self._getStepSetPythonCode(packages)

    def _getStepGetStepCount(self, packages):
        return 40301, (), self.stepGetStepCount, packages

    def _getStepUninstallPackage(self, package):
        return 40401, (package, ), self.stepUninstallPackage, package

    def _getStepInstallPackage(self, package, version, url):
        return 40501, (package, ), self.stepInstallPackage, package, version, url

    def _getStepRenamePackage(self, package):
        return 40601, (package, ), self.stepRenamePackage, package

    def _getStepSetPythonCode(self, packages):
        return 40701, (), self.stepSetPythonCode, packages

    def _getStepCount(self, packages):
        self._fautly = hasFaultySuffix()
        for package, data in packages.items():
            version1, version2, url = data
            if version1 != version2:
                if self._fautly:
                    yield 3 if version1 else 2
                else:
                    yield 2 if version1 else 1

    def _getHeader(self, success):
        code = 40801 if success else 40802
        return self.resolver.resolveString(code)

    def _getReport(self, success):
        return self._getHeader(success), self._getResult(success), True

    def _getResult(self, success):
        modules = self._installed if success else self._aborted
        return ', '.join(['%s version %s' % (module, version) for module, version in modules.items()])

    def _getSuccess(self, success):
        return success and len(self._aborted) == 0


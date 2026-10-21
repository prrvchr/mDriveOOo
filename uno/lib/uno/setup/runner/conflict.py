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

from ..helper import getExtensionName
from ..helper import getInstalledPackages
from ..helper import getOsLocation
from ..helper import parsePackageName

from ...unotool import getResourceLocation

from ...configuration import g_identifier

import importlib
import os
import traceback


class Conflict(Check):
    def __init__(self, ctx, callback, packages, url):
        super().__init__(ctx, callback)
        self._paths = {}
        self._packages = None
        self._location = None
        self._extensions = None
        self._results = {}
        self._parse = lambda x: x[1]
        dists = list(importlib.metadata.distributions())
        self.total = len(dists) + 1
        self.label1 = self.resolver.resolveString(50101)
        self.label2 = self.resolver.resolveString(50102)
        self.steps = self._getCheckStep(ctx, dists, packages, url)

    def getHeader(self, **kwargs):
        return self.resolver.resolveString(50201).format(**kwargs)

    def setReport(self, reports, success):
        result = self._getResult()
        if not success:
            reports.append((self._getReport(), result, False))
        return self._getHeader(), result

    def callback(self, success=True, error=None):
        success = len(self._paths) == 0
        self._callback(success, error)

    def stepInitialize(self, ctx, packages, url):
        if url is None:
            url = getResourceLocation(ctx, g_identifier)
        self._location = getOsLocation(url)
        if not packages:
            packages = getInstalledPackages(self._location)
            self._parse = lambda x: x
        self._packages = packages

    def stepGetPackages(self, package, dist):
        if package and parsePackageName(package) in self._packages:
            version = self._parse(self._packages[parsePackageName(package)])
            path = os.path.normpath(dist.locate_file(''))
            if not path.startswith(self._location):
                if dist.version != version:
                    if path not in self._paths:
                        self._paths[path] = []
                    self._paths[path].append((package, dist.version))

    def stepGetExtensions(self, ctx):
        extensions = {}
        service = '/singletons/com.sun.star.deployment.PackageInformationProvider'
        provider = ctx.getValueByName(service)
        for identifier, version in provider.getExtensionList():
            location = getOsLocation(provider.getPackageLocation(identifier))
            extensions[getExtensionName(location, identifier)] = location
        self._extensions = extensions

    def stepGetResults(self, path, packages):
        for name, location in self._extensions.items():
            if path.startswith(location):
                if name in self._results:
                    self._results[name].extend(packages)
                else:
                    self._results[name] = packages
                break
        else:
            if path in self._results:
                self._results[path].extend(packages)
            else:
                self._results[path] = packages

    def _getCheckStep(self, ctx, dists, packages, url):
        yield self._getStepInitialize(ctx, packages, url)
        for dist in dists:
            yield self._getStepGetPackages(dist)
        if self._paths:
            yield from self._getCheckStepConflict(ctx)

    def _getCheckStepConflict(self, ctx):
        self.total += len(self._paths) + 1
        yield self._getStepGetExtensions(ctx)
        for path, packages in self._paths.items():
            yield self._getStepGetResults(path, packages)

    def _getStepInitialize(self, ctx, packages, url):
        return 50301, (), self.stepInitialize, ctx, packages, url

    def _getStepGetPackages(self, dist):
        package = dist.metadata.get('Name')
        return 50401, (package, ), self.stepGetPackages, package, dist

    def _getStepGetExtensions(self, ctx):
        return 50501, (), self.stepGetExtensions, ctx

    def _getStepGetResults(self, path, packages):
        return 50601, (path, ), self.stepGetResults, path, packages

    def _getHeader(self):
        return self.resolver.resolveString(50701)

    def _getReport(self):
        return self.resolver.resolveString(50801)

    def _getPackages(self, packages):
        return ', '.join(f'{pkg} version {ver}' for pkg, ver in packages)

    def _getResult(self):
        return '\n'.join(f'{ext}: {self._getPackages(pkgs)}' for ext, pkgs in self._results.items())


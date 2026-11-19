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

from ..unotool import getStringResource

from ..configuration import g_identifier
from ..configuration import g_resource


class Task():
    def __init__(self, ctx, resource, callback=None):
        self._resolver = getStringResource(ctx, g_identifier, g_resource, resource)
        self._resources = {}
        self._callback = callback
        self.total = 0
        self.delay = 1
        self.step = 0

    def isExtended(self, total):
        return self.total > total

    def skipSteps(self):
        return 0

    def stepGetSkipStep(self):
        pass

    def getStepFinalize(self):
        return None

    def callback(self, success=True, error=None):
        pass

    def resolveString(self, resource, *args):
        return self._resolver.resolveString(resource).format(*args)

    def getClass(self, resource):
        return self.resolveString(self._getResource(resource, 10000))

    def getMethod(self, resource):
        return self.resolveString(self._getResource(resource, 100))

    def getMessage(self, code, *args):
        if code in self._resources:
            resource = self._resources.get(code)
            if resource.formatter:
                args = resource.formatter(self)
            return self._resolver.resolveString(resource.id).format(*args)
        return ''

    def _getStepSkipStep(self, code, *args):
        return code, args, self.stepGetSkipStep

    def _getResource(self, resource, factor):
        return (resource // factor) * factor

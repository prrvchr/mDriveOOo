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

from ..setup import canUpdatePackages

from ..unotool import getConfiguration
from ..unotool import getStringResource

from ..configuration import g_identifier

import traceback


class OptionsModel():
    def __init__(self, ctx):
        self._update = canUpdatePackages()
        self._config = getConfiguration(ctx, g_identifier, True)
        self._resolver = getStringResource(ctx, g_identifier, 'dialogs', 'OptionsDialog')
        self._resources = {'Links': 'OptionsDialog.Hyperlink%s.Url'}

    @property
    def _Setup(self):
        return self._config.getByName('SetupUpdate')

# OptionModel getter methods
    def getViewData(self):
        return self._update, self._getLinks()

    def getInitData(self, state):
        return self._Setup, state

    def getConfig(self):
        return self._config

# OptionModel setter methods
    def saveData(self, setup):
        if self._update and setup != self._Setup:
            self._config.replaceByName('SetupUpdate', setup)

    def _getLinks(self):
        links = []
        for i in range(1, 2):
            resource = self._resources.get('Links') % i
            links.append(self._resolver.resolveString(resource))
        return tuple(links)


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

from com.sun.star.frame import XDispatchProvider

from com.sun.star.lang import XInitialization
from com.sun.star.lang import XServiceInfo

from mdrive import Dispatch

from mdrive import hasInterface

from mdrive import g_identifier
from mdrive import g_scheme

import traceback

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = 'io.github.prrvchr.mDriveOOo.Dispatcher'
g_ServiceNames = ('io.github.prrvchr.mDriveOOo.Dispatcher', )


class Dispatcher(unohelper.Base,
                 XDispatchProvider,
                 XInitialization,
                 XServiceInfo):
    def __init__(self, ctx):
        self._ctx = ctx
        self._frame = None
        self._protocol = '%s:' % g_scheme

# XInitialization
    def initialize(self, args):
        service = 'com.sun.star.frame.Frame'
        interface = 'com.sun.star.lang.XServiceInfo'
        if len(args) > 0 and hasInterface(args[0], interface) and args[0].supportsService(service):
            self._frame = args[0]

# XDispatchProvider
    def queryDispatch(self, url, frame, flags):
        dispatch = None
        if url.Protocol == self._protocol:
            dispatch = Dispatch(self._ctx, self._frame)
        return dispatch

    def queryDispatches(self, requests):
        dispatches = []
        for request in requests:
            dispatch = self.queryDispatch(request.FeatureURL, request.FrameName, request.SearchFlags)
            dispatches.append(dispatch)
        return tuple(dispatches)

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)

    def getImplementationName(self):
        return g_ImplementationName

    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)

g_ImplementationHelper.addImplementation(Dispatcher,                      # UNO object class
                                         g_ImplementationName,            # Implementation name
                                         g_ServiceNames)                  # List of implemented services

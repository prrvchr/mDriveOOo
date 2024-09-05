#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-24 https://prrvchr.github.io                                  ║
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

import uno

from com.sun.star.logging.LogLevel import SEVERE
from com.sun.star.logging.LogLevel import WARNING
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import CONFIG
from com.sun.star.logging.LogLevel import FINE
from com.sun.star.logging.LogLevel import FINER
from com.sun.star.logging.LogLevel import FINEST
from com.sun.star.logging.LogLevel import ALL
from com.sun.star.logging.LogLevel import OFF

from ..loggerpool import LoggerPool

from ..logconfig import LogConfig

from ..loghelper import getLoggerName

from ...unotool import getResourceLocation
from ...unotool import getSimpleFile
from ...unotool import getStringResourceWithLocation

from ...configuration import g_identifier
from ...configuration import g_resource
from ...configuration import g_basename

from packaging.requirements import Requirement
from importlib import metadata
import pkg_resources as pkgr
import os, sys
import traceback


class LogModel():
    def __init__(self, ctx, listener, names):
        self._ctx = ctx
        self._listener = listener
        self._names = names
        self._setting = '/org.openoffice.Office.Logging/Settings'
        self._url = getResourceLocation(ctx, g_identifier, g_resource)
        self._resolver = getStringResourceWithLocation(ctx, self._url, 'Logger')
        self._config = LogConfig(ctx)
        self._pool = LoggerPool(ctx)
        self._pool.addModifyListener(listener)
        self._logger = self._pool.getLocalizedLogger(getLoggerName(names[0]), self._url, g_basename)

# Public getter method
    def getLoggerNames(self):
        names = list(self._names)
        for name in self._pool.getFilteredLoggerNames(g_identifier):
            if name not in names:
                names.append(name)
        return tuple(names)

    def getLoggerSetting(self, name):
        self._logger = self._pool.getLocalizedLogger(name, self._url, g_basename)
        return self._getLoggerSetting(name)

    def loadSetting(self):
        self._config.loadSetting()
        return self._getLoggerSetting(self._logger.Name)

    def getLogContent(self):
        return self._config.getLoggerContent(self._logger.Name)

    def getLoggerData(self):
        return self._config.getLoggerData(self._logger.Name)

    def saveSetting(self):
        return self._config.saveSetting()

# Public setter method
    def dispose(self):
        self._pool.removeModifyListener(self._listener)

    def enableLogger(self, enabled, level):
        config = self._config.getSetting(self._logger.Name)
        config.LogLevel = self._getLogLevels(level) if enabled else OFF

    def toggleHandler(self, index):
        config = self._config.getSetting(self._logger.Name)
        config.DefaultHandler = self._getLogHandler(index)

    def setLevel(self, level):
        config = self._config.getSetting(self._logger.Name)
        config.LogLevel = self._getLogLevels(level)

    def setLogSetting(self, setting):
        config = self._config.getSetting(self._logger.Name)
        config.LogLevel = setting.LogLevel
        config.DefaultHandler = setting.DefaultHandler

    def addModifyListener(self, listener):
        self._logger.addModifyListener(listener)

    def removeModifyListener(self, listener):
        self._logger.removeModifyListener(listener)

    def logInfos(self, level, clazz, method, requirements):
        msg = self._resolver.resolveString(121).format(sys.version)
        self._logger.logp(level, clazz, method, msg)
        msg = self._resolver.resolveString(122).format(os.pathsep.join(sys.path))
        self._logger.logp(level, clazz, method, msg)
        # If a requirements file exists at the extension root,
        # then we check if the requirements are met
        url = getResourceLocation(self._ctx, g_identifier, requirements)
        if getSimpleFile(self._ctx).exists(url):
            self._logRequirements(level, clazz, method, url)

# Private getter method
    def _getLoggerSetting(self, name):
        config = self._config.getSetting(name)
        level = config.LogLevel
        enabled = level != OFF
        return enabled, self._getLevelIndex(level), self._getHandlerIndex(config.DefaultHandler)

    def _getLogLevels(self, level):
        return self._logLevels()[level]

    def _getLevelIndex(self, level):
        if level in self._logLevels():
            index = self._logLevels().index(level)
        else:
            index = len(self._logLevels()) - 1
        return index

    def _getLogHandler(self, index):
        return self._logHandlers()[index -1]

    def _getHandlerIndex(self, handler):
        return self._logHandlers().index(handler) + 1

    def _logHandlers(self):
        return ('com.sun.star.logging.ConsoleHandler',
                'com.sun.star.logging.FileHandler')

    def _logLevels(self):
        return (SEVERE,
                WARNING,
                INFO,
                CONFIG,
                FINE,
                FINER,
                FINEST,
                ALL)

    def _logRequirements(self, level, clazz, method, url):
        info = sys.version_info
        ver = '%s.%s.%s' % (info.major, info.minor, info.micro)
        path = uno.fileUrlToSystemPath(url)
        with open(path) as requirements:
            for requirement in pkgr.parse_requirements(requirements):
                name = requirement.project_name
                try:
                    data = metadata.metadata(name)
                    dver = data.get('Version')
                    # FIXME: In the absence of 'Requires-Python' information, we assume
                    # FIXME: that the package works with the current version of Python.
                    pver = data.get('Requires-Python')
                    if pver is None:
                        print(f"WARNING: Package <{name}> does not provide 'Requires-Python' metadata: open an issue if possible on the package site")
                        pver = '>=' + ver
                    distfiles = metadata.files(name)
                    if distfiles:
                        location = distfiles[0].locate()
                    else:
                        # FIXME: If package is already installed on Python system in dist-packages
                        # FIXME: we need to use: pkgr.get_distribution(name).location
                        location = pkgr.get_distribution(name).location
                    if location:
                        # FIXME: Since we are not installing packages but just integrating them into the LibreOffice extension with pythonpath,
                        # FIXME: we also need to check if the Python version required by the package matches the system Python version.
                        req = Requirement('python' + pver)
                        if dver in requirement:
                            if ver in req.specifier:
                                msg = self._resolver.resolveString(131).format(name, dver, location)
                            else:
                                msg = self._resolver.resolveString(132).format(name, dver, pver, ver, location)
                        elif ver in req.specifier:
                            _op, rver = requirement.specs[0]
                            msg = self._resolver.resolveString(133).format(name, dver, rver, location)
                        else:
                            _op, rver = requirement.specs[0]
                            msg = self._resolver.resolveString(134).format(name, dver, pver, rver, ver, location)
                    else:
                        _op, rver = requirement.specs[0]
                        msg = self._resolver.resolveString(135).format(name, dver, rver)
                except Exception as e:
                    msg = self._resolver.resolveString(136).format(name, e, traceback.format_exc())
                self._logger.logp(level, clazz, method, msg)


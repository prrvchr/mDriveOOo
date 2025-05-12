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

from com.sun.star.ucb.SynchronizePolicy import SERVER_IS_MASTER
from com.sun.star.ucb.SynchronizePolicy import CLIENT_IS_MASTER
from com.sun.star.ucb.SynchronizePolicy import NONE_IS_MASTER

from ..unotool import getConfiguration
from ..unotool import getResourceLocation
from ..unotool import getSimpleFile
from ..unotool import getStringResource

from ..dbconfig  import g_folder

from ..ucp import g_ucbseparator

from ..configuration import g_identifier
from ..configuration import g_scheme

import traceback


class OptionsModel():
    def __init__(self, ctx):
        self._config = getConfiguration(ctx, g_identifier, True)
        self._common = getConfiguration(ctx, 'org.openoffice.Office.Common', True)
        self._url = getResourceLocation(ctx, g_identifier)
        self._policies = {'SERVER_IS_MASTER': 1, 'CLIENT_IS_MASTER': 2, 'NONE_IS_MASTER': 3}
        self._factors = {'Timeout': 60, 'Chunk': 1024}
        sf = getSimpleFile(ctx)
        self._hasdatabase = sf.exists(self.getDatasourceUrl())
        self._hasfile = sf.exists(self.getFileUrl())
        self._resolver = getStringResource(ctx, g_identifier, 'dialogs', 'OptionsDialog')
        self._resources = {'Link': 'OptionsDialog.Hyperlink1.Link'}


    @property
    def _ResetSync(self):
        return self._config.getByName('ResetSync')
    @property
    def _IsShared(self):
        return self._config.getByName('SharedDocuments')
    @property
    def _ShareName(self):
        return self._config.getByName('SharedFolderName')
    @property
    def _Policy(self):
        policy = self._config.getByName('SynchronizePolicy')
        return self._policies.get(policy)
    @property
    def _Timeout(self):
        timeout = self._config.getByName('ReplicateTimeout')
        return timeout // self._factors['Timeout']
    @property
    def _Download(self):
        config = self._config.getByHierarchicalName('Settings/Download')
        return self._getSetting(config)
    @property
    def _Upload(self):
        config = self._config.getByHierarchicalName('Settings/Upload')
        return self._getSetting(config)
    @property
    def _SupportShare(self):
        return self._config.getByName('SupportShare')
    @property
    def _Macro(self):
        return self._common.getByHierarchicalName('Misc/UseSystemFileDialog')

# OptionsModel getter methods
    def getInitData(self):
        resumable = self._config.getByName('ResumableUpload')
        return self._hasdatabase, self._hasfile, resumable, self._getLink()

    def hasDataBase(self):
        return self._hasdatabase

    def getViewData(self, restart):
        return (self._hasdatabase, self._ResetSync, self._SupportShare,
                self._IsShared, self._ShareName, self._Policy,
                self._Timeout, self._Download, self._Upload, self._Macro, restart)

    def getDatasourceUrl(self):
        folder = g_ucbseparator + g_folder + g_ucbseparator + g_scheme
        return self._url + folder + '.odb'

    def getFileUrl(self):
        folder = g_ucbseparator + g_scheme
        return self._url + folder

# OptionsModel setter methods
    def setViewData(self, reset, share, name, index, timeout, download, upload, macro):
        changed = False
        self._setReset(reset)
        self._setShared(share)
        self._setShare(name)
        self._setPolicy(index)
        self._setTimeout(timeout)
        self._setDownload(download)
        self._setUpload(upload)
        if self._config.hasPendingChanges():
            self._config.commitChanges()
            changed = True
        self._setMacro(macro)
        if self._common.hasPendingChanges():
            self._common.commitChanges()
        return changed

# OptionsModel private getter methods
    def _getSynchronizePolicy(self, index):
        for policy, value in self._policies.items():
            if value == index:
                return policy

    def _getSetting(self, config):
        setting = {}
        for name in config.getElementNames():
            value = config.getByName(name)
            if name in self._factors:
                value = value / self._factors[name]
            setting[name] = value
        return setting

# OptionsModel private setter methods
    def _setReset(self, enabled):
        if enabled != self._ResetSync:
            self._config.replaceByName('ResetSync', enabled)

    def _setShared(self, enabled):
        if enabled != self._IsShared:
            self._config.replaceByName('SharedDocuments', enabled)

    def _setShare(self, name):
        if name and name != self._ShareName:
            self._config.replaceByName('SharedFolderName', name)

    def _setPolicy(self, index):
        if index != self._Policy:
            policy = self._getSynchronizePolicy(index)
            self._config.replaceByName('SynchronizePolicy', policy)

    def _setTimeout(self, timeout):
        if timeout != self._Timeout:
            self._config.replaceByName('ReplicateTimeout', timeout * self._factors['Timeout'])

    def _setDownload(self, setting):
        if setting != self._Download:
            config = self._config.getByHierarchicalName('Settings/Download')
            self._setSetting(config, setting)

    def _setUpload(self, setting):
        if setting != self._Upload:
            config = self._config.getByHierarchicalName('Settings/Upload')
            self._setSetting(config, setting)

    def _setSetting(self, config, setting):
        for name, value in setting.items():
            if name in self._factors:
                value = value * self._factors[name]
            config.replaceByName(name, value)

    def _setMacro(self, enabled):
        if enabled != self._Macro:
            self._common.replaceByHierarchicalName('Misc/UseSystemFileDialog', enabled)

    def _getLink(self):
        resource = self._resources.get('Link')
        return self._resolver.resolveString(resource)


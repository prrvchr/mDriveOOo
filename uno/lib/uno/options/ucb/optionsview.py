#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020 https://prrvchr.github.io                                     ║
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

import traceback


class OptionsView(unohelper.Base):
    def __init__(self, window, exist, resumable, data):
        self._window = window
        self.setViewData(*data)
        if exist:
            self._disableShare()
        self._getDatasource().Model.Enabled = exist
        self._getUpload().Model.Enabled = resumable

# OptionsView getter methods
    def getViewData(self):
        share = bool(self._getShare().State)
        name = self._getShareName().Text
        index = self._getOptionIndex()
        timeout = int(self._getTimeout().Value)
        download = self._getSetting(0)
        upload = self._getSetting(1)
        return share, name, index, timeout, download, upload

# OptionsView setter methods
    def setStep(self, step):
        self._window.Model.Step = step

    def setViewData(self, support, share, name, index, timeout, download, upload):
        if support:
            self._getShare().State = int(share)
            self._getShareName().Text = name
            self.enableShare(share)
        else:
            self._getShare().State = 0
            self._getShare().Model.Enabled = False
            self._getShareName().Text = name
            self.enableShare(False)
        self._getOption(index).State = 1
        self.enableTimeout(index != 3)
        self._getTimeout().Value = timeout
        self._setSetting(download, 0)
        self._setSetting(upload, 1)

    def enableShare(self, enabled):
        self._getShareName().Model.Enabled = enabled

    def enableTimeout(self, enabled):
        self._getTimeoutLabel().Model.Enabled = enabled
        self._getTimeout().Model.Enabled = enabled

# OptionsView private getter methods
    def _getOptionIndex(self):
        for index in range(1,4):
            if self._getOption(index).State:
                return index

    def _getSetting(self, offset):
        setting = {}
        setting['Chunk'] = int(self._getChunk(2 + offset).Value)
        setting['Delay'] = int(self._getDelay(4 + offset).Value)
        setting['Retry'] = int(self._getRetry(6 + offset).Value)
        return setting

# OptionsView private setter methods
    def _disableShare(self):
        self._getShare().Model.Enabled = False
        self._getShareName().Model.Enabled = False

    def _setSetting(self, setting, offset):
        self._getChunk(2 + offset).Value = setting.get('Chunk')
        self._getDelay(4 + offset).Value = setting.get('Delay')
        self._getRetry(6 + offset).Value = setting.get('Retry')

# OptionsView private control methods
    def _getShare(self):
        return self._window.getControl('CheckBox1')

    def _getShareName(self):
        return self._window.getControl('TextField1')

    def _getOption(self, index):
        return self._window.getControl('OptionButton%s' % index)

    def _getTimeoutLabel(self):
        return self._window.getControl('Label2')

    def _getTimeout(self):
        return self._window.getControl('NumericField1')

    def _getDatasource(self):
        return self._window.getControl('CommandButton1')

    def _getUpload(self):
        return self._window.getControl('OptionButton5')

    def _getChunk(self, index):
        return self._window.getControl('NumericField%s' % index)

    def _getDelay(self, index):
        return self._window.getControl('NumericField%s' % index)

    def _getRetry(self, index):
        return self._window.getControl('NumericField%s' % index)


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

import traceback


class OptionsView():
    def __init__(self, window, exist, hasfile, resumable):
        self._window = window
        if exist:
            self._disableShare()
        self._getResetSync().Model.Enabled = exist
        self._getResetFile().Model.Enabled = exist
        self._getDatasource().Model.Enabled = exist
        self._getFile().Model.Enabled = hasfile
        self._getUpload().Model.Enabled = resumable

# OptionsView getter methods
    def getViewData(self):
        reset = self._getResetSync().State
        reset += self._getResetFile().State
        share = bool(self._getShare().State)
        name = self._getShareName().Text
        index = self._getOptionIndex()
        timeout = int(self._getTimeout().Value)
        download = self._getSetting(0)
        upload = self._getSetting(1)
        return reset, share, name, index, timeout, download, upload

    def getChunk(self, index):
        return int(self._getChunk(index).Value)

# OptionsView setter methods
    def setStep(self, step, restart):
        self._window.Model.Step = step
        # XXX: If we change the step, we have to restore the visibility of the controls
        # XXX: because it was lost (ie: after setting the new step everything is visible).
        self.setRestart(restart)

    def setViewData(self, exist, reset, support, share, name, index, timeout, download, upload, restart):
        self._getResetSync().State = int(reset != 0)
        self._getResetFile().State = int(reset == 2)
        self.enableResetFile(reset != 0)
        if support:
            self._getShare().State = int(share)
            self._getShare().Model.Enabled = True
            self._getShareName().Text = name
            self.enableShare(share)
        else:
            self._getShare().State = 0
            self._getShare().Model.Enabled = False
            self._getShareName().Text = name
            self.enableShare(False)
        self._getOption(index).State = 1
        self.enableSync(index != 3, restart, exist)
        self._getTimeout().Value = timeout
        self._setSetting(download, 0)
        self._setSetting(upload, 1)
        self.setRestart(restart)

    def enableShare(self, enabled):
        self._getShareName().Model.Enabled = enabled

    def enableSync(self, enabled, restart, exist):
        self._getResetSync().Model.Enabled = enabled and exist
        self._getTimeoutLabel().Model.Enabled = enabled
        self._getTimeout().Model.Enabled = enabled
        self._enableUpload(enabled, restart)

    def enableResetFile(self, enabled):
        self._getResetFile().Model.Enabled = enabled
        if not enabled:
            self._getResetFile().State = 0

    def setRestart(self, enabled):
        self._getRestart().setVisible(enabled)

    def setChunk(self, index, chunk):
        control = self._getChunk(index)
        control.Value = chunk
        self._getSpinUp(index).Model.Enabled = chunk < control.Max
        enabled = chunk > control.Min
        self._getSpinDown(index).Model.Enabled = enabled
        if not enabled:
            self._getSpinUp(index).setFocus()

# OptionsView private getter methods
    def _getOptionIndex(self):
        for index in range(1,4):
            if self._getOption(index).State:
                return index

    def _getSetting(self, index):
        return {'Chunk': int(self._getChunk(index).Value),
                'Delay': int(self._getDelay(index).Value),
                'Retry': int(self._getRetry(index).Value)}

# OptionsView private setter methods
    def _disableShare(self):
        self._getShare().Model.Enabled = False
        self._getShareName().Model.Enabled = False

    def _setSetting(self, setting, index):
        self.setChunk(index, setting.get('Chunk'))
        self._getDelay(index).Value = setting.get('Delay')
        self._getRetry(index).Value = setting.get('Retry')

    def _enableUpload(self, enabled, restart):
        control = self._getUpload()
        if not enabled and control.State:
            self._getDownload().State = 1
            self.setStep(1, restart)
        control.Model.Enabled = enabled

# OptionsView private control methods
    def _getResetSync(self):
        return self._window.getControl('CheckBox1')

    def _getResetFile(self):
        return self._window.getControl('CheckBox2')

    def _getShare(self):
        return self._window.getControl('CheckBox3')

    def _getShareName(self):
        return self._window.getControl('TextField1')

    def _getOption(self, index):
        return self._window.getControl('OptionButton%s' % index)

    def _getTimeoutLabel(self):
        return self._window.getControl('Label3')

    def _getTimeout(self):
        return self._window.getControl('NumericField1')

    def _getDatasource(self):
        return self._window.getControl('CommandButton1')

    def _getFile(self):
        return self._window.getControl('CommandButton2')

    def _getSpinUp(self, index):
        index += 3
        return self._window.getControl('CommandButton%s' % index)

    def _getSpinDown(self, index):
        index += 5
        return self._window.getControl('CommandButton%s' % index)

    def _getDownload(self):
        return self._window.getControl('OptionButton4')

    def _getUpload(self):
        return self._window.getControl('OptionButton5')

    def _getChunk(self, index):
        index += 2
        return self._window.getControl('NumericField%s' % index)

    def _getDelay(self, index):
        index += 4
        return self._window.getControl('NumericField%s' % index)

    def _getRetry(self, index):
        index += 6
        return self._window.getControl('NumericField%s' % index)

    def _getRestart(self):
        return self._window.getControl('Label8')


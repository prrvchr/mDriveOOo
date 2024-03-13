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
import unohelper

from ..loghelper import LogSetting

from ...unotool import getContainerWindow
from ...unotool import getDialog

from ...configuration import g_extension


class LogWindow():
    def __init__(self, ctx, handler, parent):
        self._window = getContainerWindow(ctx, parent, handler, g_extension, 'LogWindow')
        self._window.setVisible(True)

# LogWindow getter methods
    def getParent(self):
        return self._window.getPeer()

    def getLogger(self):
        return self._getLoggers().getSelectedItem()

    def getLogSetting(self):
        enabled = bool(self._getLogger().State)
        index = self._getLevel().getSelectedItemPos()
        state = self._getFileHandler().State
        return LogSetting(enabled, index, state)

# LogWindow setter methods
    def initLogger(self, loggers):
        control = self._getLoggers()
        control.Model.StringItemList = loggers
        control.selectItemPos(0, True)

    def setLogger(self, logger):
        self._getLoggers().selectItem(logger, True)

    def updateLoggers(self, loggers):
        self._getLoggers().Model.StringItemList = loggers

    def enableLogger(self, enabled):
        self._getLogger().State = int(enabled)
        self._getLevelLabel().Model.Enabled = enabled
        self._getLevel().Model.Enabled = enabled
        self._getConsoleHandler().Model.Enabled = enabled
        self._getOutputLabel().Model.Enabled = enabled
        control = self._getFileHandler()
        control.Model.Enabled = enabled
        self.toggleHandler(enabled and control.State)

    def setLogSetting(self, setting):
        self._getHandler(setting.getHandlerId()).State = 1
        self._getLevel().selectItemPos(setting.getLevelIndex(), True)
        self.enableLogger(setting.isLogEnabled())

    def toggleHandler(self, enabled):
        self._getViewer().Model.Enabled = enabled

# LogWindow private control methods
    def _getLoggers(self):
        return self._window.getControl('ListBox1')

    def _getLogger(self):
        return self._window.getControl('CheckBox1')

    def _getOutputLabel(self):
        return self._window.getControl('Label2')

    def _getLevelLabel(self):
        return self._window.getControl('Label3')

    def _getLevel(self):
        return self._window.getControl('ListBox2')

    def _getHandler(self, index):
        return self._window.getControl('OptionButton%s' % index)

    def _getConsoleHandler(self):
        return self._window.getControl('OptionButton1')

    def _getFileHandler(self):
        return self._window.getControl('OptionButton2')

    def _getViewer(self):
        return self._window.getControl('CommandButton1')


class LogDialog():
    def __init__(self, ctx, handler, parent, extension, writable, url, text, length):
        self._dialog = getDialog(ctx, extension, 'LogDialog', handler, parent)
        self._dialog.Title = url
        self._getButtonClear().Model.Enabled = writable
        self.updateLogger(text, length)

# LogDialog getter methods
    def getDialog(self):
        return self._dialog

# LogDialog setter methods
    def updateLogger(self, text, length):
        control = self._getLogger()
        control.Text = text
        selection = uno.createUnoStruct('com.sun.star.awt.Selection', length, length)
        control.setSelection(selection)

# LogDialog private control methods
    def _getLogger(self):
        return self._dialog.getControl('TextField1')

    def _getButtonClear(self):
        return self._dialog.getControl('CommandButton2')

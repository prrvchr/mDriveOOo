#!
# -*- coding: utf_8 -*-

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

import uno
import unohelper

from com.sun.star.ui.dialogs.WizardButton import NEXT
from com.sun.star.ui.dialogs.WizardButton import PREVIOUS
from com.sun.star.ui.dialogs.WizardButton import FINISH
from com.sun.star.ui.dialogs.WizardButton import CANCEL
from com.sun.star.ui.dialogs.WizardButton import HELP

from ..unotool import getDialog

from .wizardhandler import DialogHandler, ItemHandler

from ..configuration import g_extension

import traceback


class WizardView(unohelper.Base):
    def __init__(self, ctx, manager, parent, title):
        handler = DialogHandler(manager)
        self._dialog = getDialog(ctx, g_extension, 'Wizard', handler, parent)
        rectangle = uno.createUnoStruct('com.sun.star.awt.Rectangle', 0, 0, 85, 180)
        roadmap = self._getRoadmap('Roadmap1', title, rectangle, 0)
        handler = ItemHandler(manager)
        roadmap.addItemListener(handler)
        self._button = {CANCEL: 1, FINISH: 2, NEXT: 3, PREVIOUS: 4, HELP: 5}
        self._spacer = 5

# WizardView getter methods
    def getDialog(self):
        return self._dialog

    def getRoadmapModel(self):
        return self._getRoadmapControl().Model

# WizardView setter methods
    def execute(self):
        return self._dialog.execute()

    def endDialog(self, result):
        self._dialog.endDialog(result)

    def dispose(self):
        self._dialog.dispose()
        self._dialog = None

    def isDisposed(self):
        return self._dialog is None

    def setDialogTitle(self, title):
        self._dialog.setTitle(title)

    def setDialogSize(self, page):
        button = self._getButton(HELP).Model
        button.PositionY  = page.Height + self._spacer
        dialog = self._dialog.Model
        dialog.Height = button.PositionY + button.Height + self._spacer
        dialog.Width = page.PositionX + page.Width
        # We assume all buttons are named appropriately
        for i in (1,2,3,4):
            self._setButtonPosition(i, button.PositionY, dialog.Width)

    def enableHelpButton(self, enabled):
        self._getButton(HELP).Model.Enabled = enabled

    def enableButton(self, button, enabled):
        self._getButton(button).Model.Enabled = enabled

    def setDefaultButton(self, button):
        self._getButton(button).Model.DefaultButton = True

    def updateButtonPrevious(self, enabled):
        self._getButton(PREVIOUS).Model.Enabled = enabled

    def updateButtonNext(self, enabled):
        button = self._getButton(NEXT).Model
        button.Enabled = enabled
        if enabled:
            button.DefaultButton = True

    def updateButtonFinish(self, enabled):
        button = self._getButton(FINISH).Model
        button.Enabled = enabled
        if enabled:
            button.DefaultButton = True

# WizardView private control methods
    def _getRoadmapControl(self):
        return self._dialog.getControl('Roadmap1')

    def _getButtonByIndex(self, index):
        return self._dialog.getControl('CommandButton%s' % index)

# WizardView private methods
    def _getRoadmap(self, name, title, rectangle, tabindex):
        roadmap = self._getRoadmapModel(name, title, rectangle, tabindex)
        self._dialog.Model.insertByName(name, roadmap)
        return self._dialog.getControl(name)

    def _getRoadmapModel(self, name, title, rectangle, tabindex):
        service = 'com.sun.star.awt.UnoControlRoadmapModel'
        model = self._dialog.Model.createInstance(service)
        model.Name = name
        model.Text = title
        model.PositionX = rectangle.X
        model.PositionY = rectangle.Y
        model.Height = rectangle.Height
        model.Width = rectangle.Width
        model.TabIndex = tabindex
        return model

    def _setButtonPosition(self, step, y, width):
        # We assume that all buttons are the same Width
        button = self._getButtonByIndex(step).Model
        button.PositionX = width - step * (button.Width + self._spacer)
        button.PositionY = y

    def _getButton(self, button):
        index = self._button.get(button)
        return self._getButtonByIndex(index)

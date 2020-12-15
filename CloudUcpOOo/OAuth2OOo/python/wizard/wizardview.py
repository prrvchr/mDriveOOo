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

from unolib import getDialog

from .configuration import g_extension

import traceback


class WizardView(unohelper.Base):
    def __init__(self, ctx, handler, xdl, parent):
        self._spacer = 5
        rectangle = uno.createUnoStruct('com.sun.star.awt.Rectangle', 0, 0, 85, 180)
        self._roadmap = {'name': 'RoadmapControl1', 'index': 1, 'area': rectangle}
        self._button = {CANCEL: 1, FINISH: 2, NEXT: 3, PREVIOUS: 4, HELP: 5}
        self.DialogWindow = getDialog(ctx, g_extension, xdl, handler, parent)
        #self._createPeer(parent)
        #self.DialogWindow.toFront()

    def getRoadmapName(self):
        return self._roadmap.get('name')

    def getRoadmapTabIndex(self):
        return self._roadmap.get('index')

    def getRoadmapArea(self):
        return self._roadmap.get('area')

    def getRoadmapTitle(self):
        return self._getRoadmapTitle()

    def initWizard(self, roadmap):
        self.DialogWindow.Model.insertByName(roadmap.Name, roadmap)
        return self._getRoadmap()

    def getPageStep(self, model, pageid):
        return model.resolveString(self._getRoadmapStep(pageid))

# WizardView setter methods
    def setDialogSize(self, page):
        button = self._getButton(HELP).Model
        button.PositionY  = page.Height + self._spacer
        dialog = self.DialogWindow.Model
        dialog.Height = button.PositionY + button.Height + self._spacer
        dialog.Width = page.PositionX + page.Width
        # We assume all buttons are named appropriately
        for i in (1,2,3,4):
            self._setButtonPosition(i, button.PositionY, dialog.Width)

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

# WizardView private methods
    def _setButtonPosition(self, step, y, width):
        # We assume that all buttons are the same Width
        button = self._getButtonByIndex(step).Model
        button.PositionX = width - step * (button.Width + self._spacer)
        button.PositionY = y

    def _getButton(self, button):
        index = self._button.get(button)
        return self._getButtonByIndex(index)

    def _createPeer(self, peer=None):
        self.DialogWindow.setVisible(False)
        toolkit = createService(self.ctx, 'com.sun.star.awt.Toolkit')
        if peer is None:
            peer = toolkit.getDesktopWindow()
        self.DialogWindow.createPeer(toolkit, peer)
        #self.xWindowPeer = self.DialogWindow.getPeer()
        return self.DialogWindow.getPeer()

# WizardView private message methods
    def _getRoadmapTitle(self):
        return 'Wizard.Roadmap.Text'

    def _getRoadmapStep(self, pageid):
        return 'PageWizard%s.Step' % pageid

# WizardView private control methods
    def _getRoadmap(self):
        return self.DialogWindow.getControl(self.getRoadmapName())

    def _getButtonByIndex(self, index):
        return self.DialogWindow.getControl('CommandButton%s' % index)

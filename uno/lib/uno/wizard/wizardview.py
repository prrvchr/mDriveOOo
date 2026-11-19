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

from com.sun.star.awt import Size
from com.sun.star.awt.PosSize import SIZE

from com.sun.star.ui.dialogs.WizardButton import NEXT
from com.sun.star.ui.dialogs.WizardButton import PREVIOUS
from com.sun.star.ui.dialogs.WizardButton import FINISH
from com.sun.star.ui.dialogs.WizardButton import CANCEL
from com.sun.star.ui.dialogs.WizardButton import HELP

from com.sun.star.util.MeasureUnit import APPFONT

from ..unotool import Layout
from ..unotool import SubLayout

from ..unotool import getContainerWindow
from ..unotool import getDialog
from ..unotool import getParentWindow
from ..unotool import setWindowPosSize
from ..unotool import getTopWindow

from ..configuration import g_identifier


class WizardView():
    def __init__(self, ctx, handler, listener, parent, name, title, resize, possize):
        if name:
            # XXX: With a name we use a TOP XWindow
            self._dialog = None
            self._frame = getTopWindow(ctx, name)
            window = self._frame.getContainerWindow()
            self._window = getContainerWindow(ctx, window, handler, g_identifier, 'Wizard')
            # XXX: setComponent is needed if we want a StatusIndicator at the bottom
            self._frame.setComponent(self._window, None)
            self._frame.addCloseListener(listener)
            setWindowPosSize(ctx, window, self._window, possize)
        else:
            # XXX: Without name we use a MODAL XDialog
            self._frame = None
            parent = getParentWindow(ctx, parent)
            self._dialog = getDialog(ctx, g_identifier, 'WizardDialog', parent=parent)
            self._window = getContainerWindow(ctx, self._dialog.getPeer(), handler, g_identifier, 'Wizard')
        self._name = 'Roadmap1'
        self._setRoadmap(title, 1)
        self._buttons = {HELP: 1, PREVIOUS: 2, NEXT: 3, FINISH: 4, CANCEL: 5}
        self._layout = None
        if not self.isModal() and not resize:
            self._layout = self._getLayout()
            self._window.addWindowListener(self._layout)
            window.setVisible(True)
            self._window.setVisible(True)

# WizardView getter methods
    def getLayout(self):
        return self._layout

    def isModal(self):
        return self._frame is None

    def getPageWindow(self):
        return self._getPageWindow()

    def getDialogWindow(self):
        if self.isModal():
            return self._dialog
        return self._window

    def getRoadmapModel(self):
        return self._getRoadmap().Model

# WizardView setter methods
    def addItemListener(self, listener):
        self._getRoadmap().addItemListener(listener)

    def execute(self):
        if self.isModal():
            return self._dialog.execute()
        return 0

    def endDialog(self, result):
        if self.isModal():
            self._dialog.endDialog(result)

    def close(self):
        if not self.isModal():
            self._frame.close(True)

    def dispose(self):
        if self.isModal():
            self._dialog.dispose()

    def setDialogTitle(self, title):
        if self.isModal():
            self._dialog.setTitle(title)
        else:
            self._frame.setTitle(title)

    def setDialogSize(self, page):
        frame = self._getPageWindow().Model
        x = page.Width - frame.Width
        y = page.Height - frame.Height
        frame.Width = page.Width
        frame.Height = page.Height
        dialog = self._window.Model
        dialog.Width += x
        dialog.Height += y
        self._getRoadmap().Model.Height += y
        self._getRoadmapFrame().Model.Height += y
        for button in self._buttons:
            self._setButtonPosition(button, x, y)
        if self.isModal():
            window = self._dialog
        else:
            window = self._frame.getContainerWindow()
        size = self._window.convertSizeToPixel(Size(dialog.Width, dialog.Height), APPFONT)
        window.setPosSize(0, 0, size.Width, size.Height, SIZE)
        self._layout = self._getLayout()
        if not self.isModal():
            self._window.addWindowListener(self._layout)
        # XXX: Visibility should be done after size adjustment
        window.setVisible(True)
        self._window.setVisible(True)

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

# WizardView private methods
    def _setRoadmap(self, title, tabindex):
        roadmap = self._getRoadmapModel(title, tabindex)
        self._window.Model.insertByName(self._name, roadmap)

    def _getRoadmapModel(self, title, tabindex):
        service = 'com.sun.star.awt.UnoControlRoadmapModel'
        model = self._window.Model.createInstance(service)
        model.Name = self._name
        model.Text = title
        frame = self._getRoadmapFrame().Model
        model.PositionX = frame.PositionX + 1
        model.PositionY = frame.PositionY + 1
        model.Border = 1
        model.Height = frame.Height - 2
        model.Width = frame.Width - 2
        model.TabIndex = tabindex
        return model

    def _getLayout(self):
        return SubLayout(Layout(self._window, **self._getLayouts()))

    def _getLayouts(self):
        return {'verticals': (self._getRoadmapFrame(), self._getRoadmap()),
                'lefts':     (self._getButton(HELP), ),
                'bottoms':   (self._getButtonByIndex(i) for i in range(2, 6)),
                'controls':  (self._getPageWindow(), )}

    def _setButtonPosition(self, name, x, y):
        button = self._getButton(name).Model
        button.PositionY += y
        if name != HELP:
            button.PositionX += x

    def _getButton(self, button):
        index = self._buttons.get(button)
        return self._getButtonByIndex(index)

# WizardView private control methods
    def _getRoadmap(self):
        return self._window.getControl(self._name)

    def _getRoadmapFrame(self):
        return self._window.getControl('FrameControl1')

    def _getPageWindow(self):
        return self._window.getControl('FrameControl2')

    def _getButtonByIndex(self, index):
        return self._window.getControl('CommandButton%s' % index)

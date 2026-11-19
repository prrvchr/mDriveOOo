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

import uno

from com.sun.star.awt import Rectangle
from com.sun.star.awt import Size

from com.sun.star.awt.PosSize import HEIGHT

from com.sun.star.util.MeasureUnit import APPFONT

from ...unotool import Layout
from ...unotool import Indicator

from ...unotool import getContainerWindow
from ...unotool import getDesktop
from ...unotool import getTopWindow
from ...unotool import getWindowPosSize
from ...unotool import setWindowPosSize

from ...configuration import g_replicator
from ...configuration import g_identifier
from ...configuration import g_offset


class ReplicatorView():
    def __init__(self, ctx, handler, listener, possize, title):
        self._ctx = ctx
        self._frame = getTopWindow(ctx, g_replicator)
        window = self._frame.getContainerWindow()
        self._window = getContainerWindow(ctx, window, handler, g_identifier, 'Replicator')
        # XXX: setComponent is needed if we want a StatusIndicator at the bottom
        self._frame.setComponent(self._window, None)
        self._frame.addCloseListener(listener)

        self._margin = self._window.Model.Height - self._getLogTextPos()
        mini = self._getLogText().Model.PositionY
        self._mini = self._window.convertSizeToPixel(Size(0, mini), APPFONT).Height
        height = possize.Height if possize.Height > 0 else self._window.Model.Height
        self._height = self._window.convertSizeToPixel(Size(0, height), APPFONT).Height

        width = possize.Width if possize.Width > 0 else self._window.Model.Width
        rectangle = Rectangle(possize.X, possize.Y, width, mini)
        setWindowPosSize(ctx, window, self._window, rectangle)
        # if possize.Height <= 0:
        #    delta = window.getPosSize().Height - self._window.getPosSize().Height
        #    self._height += delta

        self._layout = Layout(self._window, **self._getLayouts())
        self._window.addWindowListener(self._layout)

        self._indicator = Indicator(frame=self._frame, offset=g_offset)
        self._frame.setTitle(title)
        self._window.setVisible(True)
        window.setVisible(True)

# ReplicatorView getter methods
    def getWindowPosSize(self):
        window = self._frame.getContainerWindow()
        if self._window.Model.Step == 1 and self._height > window.getPosSize().Height:
            window.setPosSize(0, 0, 0, self._height, HEIGHT)
        return getWindowPosSize(window)

    def getWindow(self):
        return self._frame.getContainerWindow()

    def getIndicator(self):
        return self._indicator.createIndicator()

# ReplicatorView setter methods
    def resetIndicator(self):
        self._indicator.resetIndicator()
        control = self._getLogText()
        length = len(control.Text)
        self._refreshLog(control, length)

    def setLogState(self, label, state):
        self._getLogButton().Model.Label = label
        self._window.Model.Step = int(state == 0)
        window = self._frame.getContainerWindow()
        delta = window.getPosSize().Height - self._window.getPosSize().Height
        mini = self._mini + delta
        if state:
            if self._height > mini:
                height = self._height
            else:
                height = self._getExpandedHeight(delta)
        else:
            current = window.getPosSize().Height
            if current > mini:
                self._height = current
            height = mini
        window.setPosSize(0, 0, 0, height, HEIGHT)

    def initLogger(self, text, length):
        control = self._getLogText()
        control.Text = text
        self._refreshLog(control, length)

    def updateLog(self, msg):
        control = self._getLogText()
        length = len(control.Text)
        selection = uno.createUnoStruct('com.sun.star.awt.Selection', length, length)
        control.insertText(selection, msg)
        end = length + len(msg)
        self._refreshLog(control, end)

    def close(self):
        self._frame.close(True)

    def dispose(self):
        if self._frame:
            self._frame.setComponent(None, None)
            self._frame.getContainerWindow().dispose()
            getDesktop(self._ctx).getFrames().remove(self._frame)
            self._frame = None

    def enableButtons(self, enabled):
        self._getLogButton().Model.Enabled = enabled
        self._getCloseButton().Model.Enabled = enabled

    def setLabelState(self, text):
        self._getLabelState().Text = text

# ReplicatorView private methods
    def _getExpandedHeight(self, delta):
        model = self._getLogText().Model
        height = model.PositionY + model.Height + self._margin
        size = self._window.convertSizeToPixel(Size(0, height), APPFONT)
        return size.Height + delta

    def _getLogTextPos(self):
        model = self._getLogText().Model
        return model.PositionY + model.Height

    def _refreshLog(self, control, lenght):
        selection = uno.createUnoStruct('com.sun.star.awt.Selection', lenght, lenght)
        control.setSelection(selection)

    def _getLayouts(self):
        return {'controls': (self._getLogText(), ),
                'tops': (self._getLogButton(), self._getCloseButton())}

# ReplicatorView private control methods
    def _getLabelState(self):
        return self._window.getControl('Label1')

    def _getLogText(self):
        return self._window.getControl('TextField1')

    def _getLogButton(self):
        return self._window.getControl('CommandButton2')

    def _getCloseButton(self):
        return self._window.getControl('CommandButton3')

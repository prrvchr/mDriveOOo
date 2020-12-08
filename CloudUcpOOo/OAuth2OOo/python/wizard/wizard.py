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

from com.sun.star.ui.dialogs import XWizard
from com.sun.star.lang import XInitialization

from com.sun.star.lang import IllegalArgumentException
from com.sun.star.util import InvalidStateException
from com.sun.star.container import NoSuchElementException

from unolib import getDialog
from unolib import hasInterface

from .wizardmanager import WizardManager

from .configuration import g_extension

from .logger import getMessage
g_message = 'wizard'

import traceback


class Wizard(unohelper.Base,
             XWizard,
             XInitialization):
    def __init__(self, ctx, auto=-1, resize=False, parent=None):
        try:
            self.ctx = ctx
            self._helpUrl = ''
            self._manager = WizardManager(self.ctx, auto, resize, parent)
            self._manager.initWizard()
            print("Wizard.__init__()")
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            print(msg)

    @property
    def HelpURL(self):
        return self._helpUrl
    @HelpURL.setter
    def HelpURL(self, url):
        self._helpUrl = url
        self.DialogWindow.getControl('CommandButton5').Model.Enabled = url != ''
    @property
    def DialogWindow(self):
        return self._manager._view.DialogWindow
    @DialogWindow.setter
    def DialogWindow(self, dialog):
        self._manager._view.DialogWindow = dialog

    # XInitialization
    def initialize(self, arguments):
        if not isinstance(arguments, tuple) or len(arguments) != 2:
            raise self._getIllegalArgumentException(0, 101)
        paths, controller = arguments
        if not isinstance(paths, tuple) or len(paths) < 1:
            raise self._getIllegalArgumentException(0, 102)
        interface = 'com.sun.star.ui.dialogs.XWizardController'
        if not hasInterface(controller, interface):
            raise self._getIllegalArgumentException(0, 103)
        self._manager.setPaths(paths)
        self._manager._controller = controller

    # XWizard
    def getCurrentPage(self):
        return self._manager.getCurrentPage()

    def enableButton(self, button, enabled):
        self._manager.enableButton(button, enabled)

    def setDefaultButton(self, button):
        self._manager.setDefaultButton(button)

    def travelNext(self):
        return self._manager.travelNext()

    def travelPrevious(self):
        return self._manager.travelPrevious()

    def enablePage(self, pageid, enabled):
        if not self._manager.isPathInitialized():
            raise self._getInvalidStateException(111)
        path = self._manager.getCurrentPath()
        if pageid not in path:
            raise self._getNoSuchElementException(112)
        if pageid == self._manager._model.getCurrentPageId():
            raise self._getInvalidStateException(113)
        self._manager.enablePage(pageid, enabled)

    def updateTravelUI(self):
        self._manager.updateTravelUI()

    def advanceTo(self, pageid):
        return self._manager.advanceTo(pageid)

    def goBackTo(self, pageid):
        return self._manager.goBackTo(pageid)

    def activatePath(self, index, final):
        if not self._manager.isMultiPaths():
            raise self._getInvalidStateException(121)
        if index not in self._manager.getMultiPathsIndex():
            raise self._getNoSuchElementException(122)
        path = self._manager.getPath(index)
        page = self._manager._model.getCurrentPageId()
        if page != -1 and page not in path:
            raise self._getInvalidStateException(123)
        self._manager.activatePath(index, final)

    # XExecutableDialog -> XWizard
    def setTitle(self, title):
        self.DialogWindow.setTitle(title)

    def execute(self):
        return self._manager.executeWizard(self.DialogWindow)

    # Private methods
    def _getIllegalArgumentException(self, position, code):
        e = IllegalArgumentException()
        e.ArgumentPosition = position
        e.Message = getMessage(self.ctx, g_message, code)
        e.Context = self
        return e

    def _getInvalidStateException(self, code):
        e = InvalidStateException()
        e.Message = getMessage(self.ctx, g_message, code)
        e.Context = self
        return e

    def _getNoSuchElementException(self, code):
        e = NoSuchElementException()
        e.Message = getMessage(self.ctx, g_message, code)
        e.Context = self
        return e

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
from com.sun.star.awt import XDialogEventHandler
from com.sun.star.awt import XItemListener

from com.sun.star.lang import IllegalArgumentException
from com.sun.star.util import InvalidStateException
from com.sun.star.container import NoSuchElementException

from com.sun.star.ui.dialogs.WizardTravelType import FORWARD
from com.sun.star.ui.dialogs.WizardTravelType import BACKWARD
from com.sun.star.ui.dialogs.WizardTravelType import FINISH

from com.sun.star.ui.dialogs.WizardButton import NEXT
from com.sun.star.ui.dialogs.WizardButton import PREVIOUS
from com.sun.star.ui.dialogs.WizardButton import FINISH
from com.sun.star.ui.dialogs.WizardButton import CANCEL
from com.sun.star.ui.dialogs.WizardButton import HELP

from com.sun.star.ui.dialogs.ExecutableDialogResults import OK

from unolib import getDialog
from unolib import createService
from unolib import getStringResource
from unolib import hasInterface

from .configuration import g_identifier
from .configuration import g_extension

from .logger import getMessage
g_message = 'wizard'

import traceback


class Wizard(unohelper.Base,
             XWizard,
             XInitialization,
             XItemListener,
             XDialogEventHandler):
    def __init__(self, ctx, auto=-1, resize=False, parent=None):
        print("Wizard.__init__() 1")
        self.ctx = ctx
        self._auto = auto
        self._resize = resize
        self._spacer = 5
        self._pages = {}
        self._paths = ()
        self._currentPage = -1
        self._currentPath = -1
        self._firstPage = -1
        self._lastPage = -1
        self._multiPaths = False
        self._controller = None
        self._helpUrl = ''
        print("Wizard.__init__() 2")
        self._stringResource = getStringResource(self.ctx, g_identifier, g_extension)
        print("Wizard.__init__() 3")
        #self._dialog = getDialog(self.ctx, g_extension, 'Wizard')
        self._dialog = getDialog(self.ctx, g_extension, 'Wizard', self, parent)
        point = uno.createUnoStruct('com.sun.star.awt.Point', 0, 0)
        size = uno.createUnoStruct('com.sun.star.awt.Size', 85, 180)
        print("Wizard.__init__() 4")
        roadmap = self._getRoadmapControl('RoadmapControl1', point, size)
        print("Wizard.__init__() 5")
        roadmap.addItemListener(self)
        self._createPeer(parent)
        self._dialog.toFront()
        print("Wizard.__init__() 6")

    @property
    def HelpURL(self):
        return self._helpUrl
    @HelpURL.setter
    def HelpURL(self, url):
        self._helpUrl = url
        self._dialog.getControl('CommandButton5').Model.Enabled = url != ''
    @property
    def DialogWindow(self):
        return self._dialog

    def _createPeer(self, peer=None):
        self._dialog.setVisible(False)
        toolkit = createService(self.ctx, 'com.sun.star.awt.Toolkit')
        if peer is None:
            peer = toolkit.getDesktopWindow()
        self._dialog.createPeer(toolkit, peer)
        #self.xWindowPeer = self.DialogWindow.getPeer()
        return self._dialog.getPeer()


    # XInitialization
    def initialize(self, args):
        if not isinstance(args, tuple) or len(args) != 2:
            raise self._getIllegalArgumentException(0, 101)
        paths = args[0]
        controller = args[1]
        if not isinstance(paths, tuple) or len(paths) < 2:
            raise self._getIllegalArgumentException(0, 102)
        interface = 'com.sun.star.ui.dialogs.XWizardController'
        if not hasInterface(controller, interface):
            raise self._getIllegalArgumentException(0, 103)
        self._paths = paths
        self._multiPaths = isinstance(paths[0], tuple)
        self._controller = controller

    # XItemListener
    def itemStateChanged(self, event):
        page = event.ItemId
        if self._currentPage != page:
            if not self._setPage(self._currentPage, page):
                self._getRoadmap().CurrentItemID = self._currentPage

    def disposing(self, event):
        pass

    # XDialogEventHandler
    def callHandlerMethod(self, dialog, event, method):
        handled = False
        self._dialog.toFront()
        if method == 'Help':
            handled = True
        elif method == 'Previous':
            self.travelPrevious()
            handled = True
        elif method == 'Next':
            self.travelNext()
            handled = True
        elif method == 'Finish':
            handled = self._doFinish()
        return handled

    def getSupportedMethodNames(self):
        return ('Help', 'Previous', 'Next', 'Finish')

    # XWizard
    def getCurrentPage(self):
        if self._currentPage in self._pages:
            return self._pages[self._currentPage]
        return None

    def enableButton(self, button, enabled):
        if button == HELP:
            self._dialog.getControl('CommandButton5').Model.Enabled = enabled
        elif button == PREVIOUS:
            self._dialog.getControl('CommandButton4').Model.Enabled = enabled
        elif button == NEXT:
            self._dialog.getControl('CommandButton3').Model.Enabled = enabled
        elif button == FINISH:
            self._dialog.getControl('CommandButton2').Model.Enabled = enabled
        elif button == CANCEL:
            self._dialog.getControl('CommandButton1').Model.Enabled = enabled

    def setDefaultButton(self, button):
        if button == HELP:
            self._dialog.getControl('CommandButton5').Model.DefaultButton = True
        elif button == PREVIOUS:
            self._dialog.getControl('CommandButton4').Model.DefaultButton = True
        elif button == NEXT:
            self._dialog.getControl('CommandButton3').Model.DefaultButton = True
        elif button == FINISH:
            self._dialog.getControl('CommandButton2').Model.DefaultButton = True
        elif button == CANCEL:
            self._dialog.getControl('CommandButton1').Model.DefaultButton = True

    def travelNext(self):
        page = self._getNextPage()
        if page is not None:
            return self._setCurrentPage(self._currentPage, page)
        return False

    def travelPrevious(self):
        page = self._getPreviousPage()
        if page is not None:
            return self._setCurrentPage(self._currentPage, page)
        return False

    def enablePage(self, page, enabled):
        if page == self._currentPage:
            raise self._getInvalidStateException(111)
        path = self._getPath(False)
        if page not in path:
            raise self._getNoSuchElementException(112)
        index = path.index(page)
        self._getRoadmap().getByIndex(index).Enabled = enabled

    def updateTravelUI(self):
        self._updateRoadmap()
        self._updateButton()

    def advanceTo(self, page):
        if page in self._getPath():
            return self._setCurrentPage(self._currentPage, page)
        return False

    def goBackTo(self, page):
        if page in self._getPath():
            return self._setCurrentPage(self._currentPage, page)
        return False

    def activatePath(self, index, final):
        if not self._multiPaths:
            return
        if index not in range(len(self._paths)):
            raise self._getNoSuchElementException(121)
        path = self._paths[index]
        if self._currentPage != -1 and self._currentPage not in path:
            raise self._getInvalidStateException(122)
        if self._currentPath != index or self._isFinal != final:
            self._initPath(index, final)

    # XExecutableDialog -> XWizard
    def setTitle(self, title):
        self._dialog.setTitle(title)

    def execute(self):
        print("Wizard.execute() 1")
        if self._currentPath == -1:
            self._initPath(0, False)
        self._initPage()
        print("Wizard.execute() 2")
        #self._setButtonFocus()
        return self._dialog.execute()

    # Private methods
    def _getRoadmap(self):
        return self._dialog.getControl('RoadmapControl1').getModel()

    def _isFinal(self):
        return self._getRoadmap().Complete

    def _isFirstPage(self):
        return self._currentPage == self._firstPage

    def _isLastPage(self):
        return self._isFinal() and self._currentPage == self._lastPage

    def _getCurrentPath(self):
        return self._paths[self._currentPath] if self._multiPaths else self._paths

    def _getPreviousPage(self):
        path = self._getPath()
        if self._currentPage in path:
            i = path.index(self._currentPage) - 1
            if i >= 0:
                return path[i]
        return None

    def _getNextPage(self):
        path = self._getPath()
        if self._currentPage in path:
            i = path.index(self._currentPage) + 1
            if i < len(path):
                return path[i]
        return None

    def _doFinish(self):
        if self._isLastPage():
            if self._pages[self._currentPage].commitPage(self._getCommitReason()):
                if self._controller.confirmFinish():
                    self._dialog.endDialog(OK)
        return True

    def _setCurrentPage(self, old, new):
        if self._setPage(old, new):
            return True
        return False

    def _initPath(self, index, final):
        final, paths = self._getActivePath(index, final)
        self._firstPage = min(paths)
        self._lastPage = max(paths)
        self._initRoadmap(paths, final)

    def _getActivePath(self, index, final):
        if self._multiPaths:
            paths = self._paths[index] if final else self._getFollowingPath(index)
            self._currentPath = index
            final = paths == self._paths[self._currentPath]
        else:
            final, paths = True, self._paths
        return final, paths

    def _getFollowingPath(self, index):
        paths = []
        i = 0
        for page in self._paths[index]:
            if page > self._currentPage:
                for j in range(len(self._paths)):
                    if j in (index, self._currentPath):
                        continue
                    if i >= len(self._paths[j]) or page != self._paths[j][i]:
                        return tuple(paths)
            paths.append(page)
            i += 1
        return tuple(paths)

    def _getPath(self, enabled=True):
        paths = []
        roadmap = self._getRoadmap()
        for i in range(roadmap.getCount()):
            item = roadmap.getByIndex(i)
            if not enabled:
                paths.append(item.ID)
            elif item.Enabled:
                paths.append(item.ID)
        return tuple(paths)

    def _initRoadmap(self, paths, final):
        roadmap = self._getRoadmap()
        initialized = roadmap.CurrentItemID != -1
        for i in range(roadmap.getCount() -1, -1, -1):
            roadmap.removeByIndex(i)
        i = 0
        for page in paths:
            item = roadmap.createInstance()
            item.ID = page
            item.Label = self._controller.getPageTitle(page)
            if i != 0:
                item.Enabled = initialized and self._canAdvancePage(pageid)
            roadmap.insertByIndex(i, item)
            pageid = page
            i += 1
        if initialized:
            roadmap.CurrentItemID = self._currentPage
        roadmap.Complete = final

    def _updateRoadmap(self):
        roadmap = self._getRoadmap()
        for i in range(roadmap.getCount()):
            item = roadmap.getByIndex(i)
            if i == 0:
                item.Enabled = True
            elif itemid in self._pages:
                item.Enabled = self._canAdvancePage(itemid)
            else:
                item.Enabled = False
            itemid = item.ID
        
    def _updateButton(self):
        self._dialog.getControl('CommandButton4').Model.Enabled = not self._isFirstPage()
        enabled = self._getNextPage() is not None and self._canAdvance()
        self._dialog.getControl('CommandButton3').Model.Enabled = enabled
        enabled = self._isLastPage()
        self._dialog.getControl('CommandButton2').Model.Enabled = enabled
        button = 'CommandButton2' if enabled else 'CommandButton3'
        self._dialog.getControl(button).Model.DefaultButton = True

    def _setButtonFocus(self):
        button = 'CommandButton2' if self._isLastPage() else 'CommandButton3'
        self._dialog.getControl(button).setFocus()

    def _canAdvance(self):
        return self._controller.canAdvance() and self._canAdvancePage(self._currentPage)

    def _canAdvancePage(self, page):
        if page in self._pages:
            return self._pages[page].canAdvance()
        return False

    def _initPage(self):
        self._setPageStep(self._firstPage)
        nextpage = self._isAutoLoad()
        while nextpage and self._canAdvance():
            nextpage = self._initNextPage()

    def _initNextPage(self):
        page = self._getNextPage()
        if page is not None:
            return self._setPage(self._currentPage, page) and self._isAutoLoad(page)
        return False

    def _isAutoLoad(self, page=None):
        nextindex = 1 if page is None else self._getCurrentPath().index(page) +1
        return nextindex < self._auto

    def _setPage(self, old, new):
        if self._deactivatePage(old, new):
            self._setPageStep(new)
            return True
        return False

    def _setPageStep(self, pageid):
        self._setDialogStep(0)
        # TODO: PageId can be equal to zero but Model.Step must be > 0
        step = self._getDialogStep(pageid)
        if pageid not in self._pages:
            parent = self._dialog.getPeer()
            page = self._controller.createPage(parent, pageid)
            model = page.Window.getModel()
            self._setModelStep(model, step)
            self._pages[pageid] = self._setPageWindow(model, page)
        self._currentPage = self._getRoadmap().CurrentItemID = pageid
        self._updateRoadmap()
        self._updateButton()
        self._activatePage(pageid)
        self._setDialogStep(step)

    def _setPageWindow(self, model, page):
        if self._resize:
            self._setDialogSize(model)
            self._resize = False
        self._dialog.addControl(model.Name, page.Window)
        return page

    def _setDialogSize(self, model):
        roadmap = self._getRoadmap()
        roadmap.Height = model.Height
        roadmap.Width = model.PositionX
        button = self._dialog.getControl('CommandButton5').getModel()
        button.PositionY  = model.Height + self._spacer
        dialog = self._dialog.getModel()
        dialog.Height = button.PositionY + button.Height + self._spacer
        dialog.Width = model.PositionX + model.Width
        # We assume all buttons are named appropriately
        for i in (1,2,3,4):
            self._setButtonPosition(model, i, button.PositionY, dialog.Width)

    def _setButtonPosition(self, model, step, y, width):
        # We assume that all buttons are the same Width
        button = self._dialog.getControl('CommandButton%s' % step).getModel()
        button.PositionX = width - step * (button.Width + self._spacer)
        button.PositionY = y

    def _setModelStep(self, model, step):
        model.PositionX = self._getRoadmap().Width
        model.PositionY = 0
        model.Step = step
        for control in model.getControlModels():
            control.Step = step

    def _deactivatePage(self, old, new):
        if old in self._pages:
            if self._pages[old].commitPage(self._getCommitReason(old, new)):
                self._controller.onDeactivatePage(old)
                return True
        return False

    def _getCommitReason(self, old=None, new=None):
        old = self._currentPage if old is None else old
        new = self._currentPage if new is None else new
        if old < new:
            return FORWARD
        elif old > new:
            return BACKWARD
        else:
            return FINISH

    def _activatePage(self, page):
        if page in self._pages:
            self._controller.onActivatePage(page)
            self._pages[page].activatePage()

    def _getDialogStep(self, pageid):
        return pageid + 1

    def _setDialogStep(self, step):
        self._dialog.getModel().Step = step

    def _getRoadmapControl(self, name, point, size):
        dialog = self._dialog.getModel()
        model = self._getRoadmapModel(dialog, name, point, size)
        dialog.insertByName(name, model)
        return self._dialog.getControl(name)

    def _getRoadmapModel(self, dialog, name, point, size):
        model = dialog.createInstance('com.sun.star.awt.UnoControlRoadmapModel')
        model.Name = name
        model.PositionX = point.X
        model.PositionY = point.Y
        model.Height = size.Height
        model.Width = size.Width
        model.Text = self._stringResource.resolveString('Wizard.Roadmap.Text')
        return model

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

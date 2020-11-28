#!
# -*- coding: utf_8 -*-

'''
    Copyright (c) 2020 https://prrvchr.github.io

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the Software
    is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
    OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import uno
import unohelper

from com.sun.star.ui.dialogs.WizardTravelType import FORWARD
from com.sun.star.ui.dialogs.WizardTravelType import BACKWARD
from com.sun.star.ui.dialogs.WizardTravelType import FINISH

from com.sun.star.ui.dialogs.ExecutableDialogResults import OK

from .wizardmodel import WizardModel
from .wizardview import WizardView
from .wizardhandler import DialogHandler, ItemHandler

from unolib import createService

import traceback


class WizardManager(unohelper.Base):
    def __init__(self, ctx, auto, resize, parent):
        self.ctx = ctx
        self._auto = auto
        self._resize = resize
        self._paths = ()
        self._currentPath = -1
        self._multiPaths = False
        self._controller = None
        self._model = WizardModel(self.ctx)
        handler = DialogHandler(self)
        self._view = WizardView(self.ctx, handler, 'Wizard', parent)

    def initWizard(self):
        model = self._model.initWizard(self._view)
        roadmap = self._view.initWizard(model)
        roadmap.addItemListener(ItemHandler(self))

    def getPageStep(self, pageid):
        return self._view.getPageStep(self._model, pageid)

    def getCurrentPage(self):
        return self._model.getCurrentPage()

    def getCurrentPath(self):
        if self.isMultiPaths():
            return self._paths[self._currentPath]
        return self._paths

    def setPaths(self, paths):
        self._paths = paths
        self._multiPaths = isinstance(paths[0], tuple)

    def getPath(self, index):
        return self._paths[index]

    def isMultiPaths(self):
        return self._multiPaths

    def isPathInitialized(self):
        return not self._multiPaths or self._currentPath != -1

    def getMultiPathsIndex(self):
        return range(len(self._paths))

    def activatePath(self, index, final):
        if self._currentPath != index or self._isComplete() != final:
            self._initPath(index, final)
            self._model.updateRoadmap(self._getFirstPage())

    def doFinish(self, dialog):
        if self._isLastPage():
            reason = self._getCommitReason()
            if self._model.doFinish(reason):
                if self._controller.confirmFinish():
                    dialog.endDialog(OK)

    def changeRoadmapStep(self, page):
        pageid = self._model.getCurrentPageId()
        if pageid != page:
            if not self._setCurrentPage(page):
                self._model.setCurrentPageId(pageid)

    def enableButton(self, button, enabled):
        self._view.enableButton(button, enabled)

    def setDefaultButton(self, button):
        self._view.setDefaultButton(button)

    def travelNext(self):
        page = self._getNextPage()
        if page is not None:
            return self._setCurrentPage(page)
        return False

    def travelPrevious(self):
        page = self._getPreviousPage()
        if page is not None:
            return self._setCurrentPage(page)
        return False

    def enablePage(self, pageid, enabled):
        changed = self._model.enablePage(pageid, enabled)
        if changed:
            self._model.updateRoadmap(self._getFirstPage())

    def updateTravelUI(self):
        self._model.updateRoadmap(self._getFirstPage())
        self._updateButton()

    def advanceTo(self, page):
        if page in self._model.getRoadmapPath():
            return self._setCurrentPage(page)
        return False

    def goBackTo(self, page):
        if page in self._model.getRoadmapPath():
            return self._setCurrentPage(page)
        return False

    def executeWizard(self, dialog):
        if not self._isCurrentPathSet():
            self._initPath(0, False)
        self._initPage()
        return dialog.execute()

# WizardManager private methods
    def _isCurrentPathSet(self):
        return self._currentPath != -1

    def _getActivePath(self):
        return self._model.getActivePath(self.getCurrentPath())

    def _initPath(self, index, final):
        complete, paths = self._getPath(index, final)
        self._model.initRoadmap(self._controller, paths, complete)

    def _getPath(self, index, final):
        if self.isMultiPaths():
            paths = self._paths[index] if final else self._getCommunPath(index)
            self._currentPath = index
        else:
            final, paths = True, self._paths
        return final, paths

    def _getCommunPath(self, index):
        paths = []
        i = 0
        pageid = self._model.getCurrentPageId()
        for page in self._paths[index]:
            if page > pageid:
                for j in range(len(self._paths)):
                    if j == index or j == self._currentPath:
                        continue
                    if i >= len(self._paths[j]) or page != self._paths[j][i]:
                        return tuple(paths)
            paths.append(page)
            i += 1
        return tuple(paths)

    def _initPage(self):
        self._setPage(self._getFirstPage())
        nextpage = self._isAutoLoad()
        while nextpage and self._canAdvance():
            nextpage = self._initNextPage()

    def _isAutoLoad(self, page=None):
        nextindex = self._getFirstPage() if page is None else self.getCurrentPath().index(page) + 1
        return nextindex < self._auto

    def _initNextPage(self):
        page = self._getNextPage()
        if page is not None:
            return self._setCurrentPage(page) and self._isAutoLoad(page)
        return False

    def _canAdvance(self):
        return self._controller.canAdvance() and self._model.canAdvance()

    def _getPreviousPage(self):
        path = self._model.getRoadmapPath()
        page = self._model.getCurrentPageId()
        if page in path:
            i = path.index(page) - 1
            if i >= 0:
                return path[i]
        return None

    def _getNextPage(self):
        path = self._model.getRoadmapPath()
        page = self._model.getCurrentPageId()
        if page in path:
            i = path.index(page) + 1
            if i < len(path):
                return path[i]
        return None

    def _setCurrentPage(self, page):
        if self._deactivatePage(page):
            self._setPage(page)
            return True
        return False

    def _setPage(self, pageid):
        try:
            print("WizardManager._setPage() 1")
            if not self._model.hasPage(pageid):
                print("WizardManager._setPage() 2")
                window = self._view.DialogWindow
                print("WizardManager._setPage() 3")
                page = self._controller.createPage(window.getPeer(), pageid)
                print("WizardManager._setPage() 4")
                name = self._setPageModel(page)
                self._model.addPage(pageid, self._setPageWindow(window, page, name))
                print("WizardManager._setPage() 5")
            self._model.setCurrentPageId(pageid)
            self._activatePage(pageid)
            # TODO: Fixed: XWizard.updateTravelUI() must be done after XWizardPage.activatePage()
            self._model.updateRoadmap(self._getFirstPage())
            self._updateButton()
            print("WizardManager._setPage() 6")
            self._model.setPageVisible(pageid, True)
            print("WizardManager._setPage() 7")
        except Exception as e:
            msg = "WizardManager._setPage() Error: %s - %s" % (e, traceback.print_exc())
            print(msg)

    def _updateButton(self):
        self._view.updateButtonPrevious(not self._isFirstPage())
        enabled = self._getNextPage() is not None and self._canAdvance()
        self._view.updateButtonNext(enabled)
        enabled = self._isLastPage() and self._canAdvance()
        self._view.updateButtonFinish(enabled)

    def _deactivatePage(self, new):
        old = self._model.getCurrentPageId()
        reason = self._getCommitReason(old, new)
        if self._model.deactivatePage(old, reason):
            self._controller.onDeactivatePage(old)
            self._model.setPageVisible(old, False)
            return True
        return False

    def _getCommitReason(self, old=None, new=None):
        page = self._model.getCurrentPageId()
        old = page if old is None else old
        new = page if new is None else new
        if old < new:
            return FORWARD
        elif old > new:
            return BACKWARD
        else:
            return FINISH

    def _setPageModel(self, page):
        model = page.Window.getModel()
        # TODO: Fixed: Resizing should be done, if necessary, instead of modifying the model
        if self._resize:
            self._resizeWizard(model)
            model.PositionY = 0
        else:
            model.PositionX = self._model.getRoadmapWidth()
            model.PositionY = 0
        return model.Name

    def _resizeWizard(self, model):
        self._model.setRoadmapSize(model)
        self._view.setDialogSize(model)
        self._resize = False

    def _setPageWindow(self, window, page, name):
        window.addControl(name, page.Window)
        return page

    def _activatePage(self, page):
        self._controller.onActivatePage(page)
        self._model.activatePage(page)

    def _getFirstPage(self):
        return min(self._getActivePath())

    def _getLastPage(self):
        return max(self._getActivePath())

    def _isFirstPage(self):
        return self._model.getCurrentPageId() == self._getFirstPage()

    def _isLastPage(self):
        return self._isComplete() and self._model.getCurrentPageId() == self._getLastPage()

    def _isComplete(self):
        return self._model.isComplete()

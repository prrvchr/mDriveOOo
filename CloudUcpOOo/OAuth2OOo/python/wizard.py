#!
# -*- coding: utf_8 -*-

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

from unolib import getDialog
from unolib import createService
from unolib import getStringResource

from .configuration import g_identifier
from .configuration import g_extension

from .logger import getMessage

import traceback


class Wizard(unohelper.Base,
             XWizard,
             XInitialization,
             XItemListener,
             XDialogEventHandler):
    def __init__(self, ctx):
        self.ctx = ctx
        self._pages = {}
        self._paths = ()
        self._currentPage = -1
        self._currentPath = -1
        self._firstPage = -1
        self._lastPage = -1
        self._multiPath = False
        self._controller = None
        self._helpUrl = ''
        self._stringResource = getStringResource(self.ctx, g_identifier, g_extension)
        self._dialog = getDialog(self.ctx, g_extension, 'Wizard', self)
        point = uno.createUnoStruct('com.sun.star.awt.Point', 0, 0)
        size = uno.createUnoStruct('com.sun.star.awt.Size', 85, 180)
        roadmap = self._getRoadmapControl('RoadmapControl1', point, size)
        roadmap.addItemListener(self)

    @property
    def HelpURL(self):
        return self._helpUrl
    @HelpURL.setter
    def HelpURL(self, url):
        self._helpUrl = url
        self._dialog.getControl('CommandButton1').Model.Enabled = url != ''
    @property
    def DialogWindow(self):
        return self._dialog

    # XInitialization
    def initialize(self, args):
        code = self._getInvalidArgumentCode(args)
        if code != -1:
            raise self._getIllegalArgumentException(0, code)
        paths = args[0]
        code = self._getInvalidPathsCode(paths)
        if code != -1:
            raise self._getIllegalArgumentException(0, code)
        self._multiPath = isinstance(paths[0], tuple)
        self._paths = paths
        controller = args[1]
        code = self._getInvalidControllerCode(controller)
        if code != -1:
            raise self._getIllegalArgumentException(0, code)
        self._controller = controller

    # XItemListener
    def itemStateChanged(self, event):
        if self._setPage(self._currentPage, event.ItemId):
            self.updateTravelUI()
        else:
            self._getRoadmap().CurrentItemID = self._currentPage

    def disposing(self, event):
        pass

    # XDialogEventHandler
    def callHandlerMethod(self, dialog, event, method):
        handled = False
        if method == 'Help':
            handled = True
        elif method == 'Next':
            self.travelNext()
            handled = True
        elif method == 'Previous':
            self.travelPrevious()
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
            self._dialog.getControl('CommandButton1').Model.Enabled = enabled
        elif button == PREVIOUS:
            self._dialog.getControl('CommandButton2').Model.Enabled = enabled
        elif button == NEXT:
            self._dialog.getControl('CommandButton3').Model.Enabled = enabled
        elif button == FINISH:
            self._dialog.getControl('CommandButton4').Model.Enabled = enabled
        elif button == CANCEL:
            self._dialog.getControl('CommandButton5').Model.Enabled = enabled

    def setDefaultButton(self, button):
        if button == HELP:
            self._dialog.getControl('CommandButton1').Model.DefaultButton = True
        elif button == PREVIOUS:
            self._dialog.getControl('CommandButton2').Model.DefaultButton = True
        elif button == NEXT:
            self._dialog.getControl('CommandButton3').Model.DefaultButton = True
        elif button == FINISH:
            self._dialog.getControl('CommandButton4').Model.DefaultButton = True
        elif button == CANCEL:
            self._dialog.getControl('CommandButton5').Model.DefaultButton = True

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
            raise self._getInvalidStateException(102)
        path = self._getPath(False)
        if page not in path:
            raise self._getNoSuchElementException(103)
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
        if page in self.self._getPath():
            return self._setCurrentPage(self._currentPage, page)
        return False

    def activatePath(self, index, final):
        if not self._multiPath:
            return
        if index not in range(len(self._paths)):
            raise self._getNoSuchElementException(104)
        if self._currentPath != -1:
            old = self._paths[self._currentPath]
            new = self._paths[index]
            commun = self._getCommunPaths((old, new))
            if self._currentPage not in commun:
                raise self._getInvalidStateException(105)
        self._initPaths(index, final)

    # XExecutableDialog -> XWizard
    def setTitle(self, title):
        self._dialog.setTitle(title)

    def execute(self):
        if self._currentPath == -1:
            self._initPaths(0, False)
        self._initPage(self._firstPage)
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
                    self._dialog.endExecute()
        return True

    def _setCurrentPage(self, old, new):
        if self._setPage(old, new):
            self.updateTravelUI()
            return True
        return False

    def _initPaths(self, index, final):
        if self._multiPath:
            final, path = self._initMultiplePathsWizard(index, final)
        else:
            final, path = self._initSinglePathWizard()
        self._firstPage = min(path)
        self._lastPage = max(path)
        self._initRoadmap(path, final)
        self._updateButton()
        #self.updateTravelUI()

    def _initSinglePathWizard(self):
        return True, self._paths

    def _initMultiplePathsWizard(self, index, final):
        path = self._getActivePath(self._paths, index, final)
        self._currentPath = index
        final = path == self._paths[self._currentPath]
        return final, path

    def _getActivePath(self, paths, index, final):
        if final:
            return paths[index]
        if index != -1:
            return self._getUniquePaths(paths, index)
        return self._getCommunPaths(paths)

    def _getUniquePaths(self, paths, index):
        commun = []
        i = 0
        for p in paths[index]:
            for j in range(0, len(paths)):
                if p != paths[j][i]:
                    return tuple(commun)
            commun.append(p)
            i += 1
        return tuple(commun)

    def _getCommunPaths(self, paths):
        commun = []
        i = 0
        for p in paths[0]:
            for j in range(1, len(paths)):
                if p != paths[j][i]:
                    return tuple(commun)
            commun.append(p)
            i += 1
        return tuple(commun)

    def _getPath(self, enabled=True):
        path = []
        roadmap = self._getRoadmap()
        for i in range(roadmap.getCount()):
            item = roadmap.getByIndex(i)
            if not enabled:
                path.append(item.ID)
            elif item.Enabled:
                path.append(item.ID)
        return tuple(path)

    def _initRoadmap(self, path, final):
        roadmap = self._getRoadmap()
        initialized = roadmap.CurrentItemID != -1
        for i in range(roadmap.getCount()-1, -1, -1):
            roadmap.removeByIndex(i)
        i = 0
        for page in path:
            item = roadmap.createInstance()
            item.ID = page
            item.Label = self._controller.getPageTitle(page)
            if i != 0:
                item.Enabled = initialized and self._canPageAdvance(id)
            roadmap.insertByIndex(i, item)
            id = page
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
            elif id in self._pages:
                item.Enabled = self._canPageAdvance(id)
            else:
                item.Enabled = False
            id = item.ID
        
    def _updateButton(self):
        self._dialog.getControl('CommandButton2').Model.Enabled = not self._isFirstPage()
        enabled = self._getNextPage() is not None and self._canAdvance()
        self._dialog.getControl('CommandButton3').Model.Enabled = enabled
        enabled = self._isLastPage()
        self._dialog.getControl('CommandButton4').Model.Enabled = enabled
        button = 'CommandButton4' if enabled else 'CommandButton3'
        self._dialog.getControl(button).Model.DefaultButton = True

    def _canAdvance(self):
        return self._controller.canAdvance() and self._canPageAdvance(self._currentPage)

    def _canPageAdvance(self, page):
        if page in self._pages:
            return self._pages[page].canAdvance()
        return False

    def _setPage(self, old, new):
        if self._deactivatePage(old, new):
            self._initPage(new)
            return True
        return False

    def _initPage(self, id):
        self._setDialogStep(0)
        # TODO: PageId can be equal to zero but Model.Step must be > 0
        step = self._getDialogStep(id)
        if id not in self._pages:
            parent = self._dialog.getPeer()
            page = self._controller.createPage(parent, id)
            model = page.Window.getModel()
            self._setModelStep(model, step)
            self._dialog.addControl(model.Name, page.Window)
            #self._dialog.getModel().insertByName(model.Name, model)
            self._pages[id] = page
        self._currentPage = self._getRoadmap().CurrentItemID = id
        self._setDialogStep(step)
        self._activatePage(id)

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

    def _getDialogStep(self, id):
        return id + 1

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
        #model.Border = 0
        return model

    def _getInvalidArgumentCode(self, args):
        if not isinstance(args, tuple) or len(args) != 2:
            return 100
        return -1

    def _getInvalidPathsCode(self, paths):
        if not isinstance(paths, tuple) or len(paths) < 1:
             return 101
        return -1

    def _getInvalidControllerCode(self, controller):
        return -1

    def _getIllegalArgumentException(self, position, code):
        e = IllegalArgumentException()
        e.ArgumentPosition = position
        e.Message = getMessage(self.ctx, code)
        e.Context = self
        return e

    def _getInvalidStateException(self, code):
        e = InvalidStateException()
        e.Message = getMessage(self.ctx, code)
        e.Context = self
        return e

    def _getNoSuchElementException(self, code):
        e = NoSuchElementException()
        e.Message = getMessage(self.ctx, code)
        e.Context = self
        return e

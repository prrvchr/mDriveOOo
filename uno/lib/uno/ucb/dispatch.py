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
import unohelper

from com.sun.star.ui.dialogs.TemplateDescription import FILEOPEN_SIMPLE
from com.sun.star.ui.dialogs.TemplateDescription import FILESAVE_SIMPLE

from com.sun.star.frame import FeatureStateEvent

from com.sun.star.frame import XNotifyingDispatch

from com.sun.star.frame.DispatchResultState import SUCCESS
from com.sun.star.frame.DispatchResultState import FAILURE

from .unotool import createService
from .unotool import getArgumentSet
from .unotool import getDesktop
from .unotool import getMessageBox
from .unotool import getToolKit

import traceback


class Dispatch(unohelper.Base,
               XNotifyingDispatch):
    def __init__(self, ctx, frame):
        self._ctx = ctx
        self._frame = frame
        self._listeners = []
        self._service = 'com.sun.star.ui.dialogs.OfficeFilePicker'
        self._sep = '/'

    _path = ''

# XNotifyingDispatch
    def dispatchWithNotification(self, url, arguments, listener):
        state, result = self.dispatch(url, arguments)
        struct = 'com.sun.star.frame.DispatchResultEvent'
        notification = uno.createUnoStruct(struct, self, state, result)
        listener.dispatchFinished(notification)

    def dispatch(self, url, arguments):
        state = FAILURE
        result = ()
        if url.Path == 'Open':
            urls, state = self._open()
            if state == SUCCESS:
                desktop = getDesktop(self._ctx)
                for url in urls:
                    desktop.loadComponentFromURL(url, '_default', 0, ())
        elif url.Path == 'SaveAs':
            document = self._frame.getController().getModel()
            state = self._saveAs(document)
        elif url.Path == 'ShowWarning':
            state = self._showWarning(arguments)
        return state, result

    def addStatusListener(self, listener, url):
        state = FeatureStateEvent()
        state.FeatureURL = url
        state.IsEnabled = True
        #state.State = True
        listener.statusChanged(state)
        self._listeners.append(listener);

    def removeStatusListener(self, listener, url):
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _open(self):
        state = FAILURE
        fp = createService(self._ctx, self._service, FILEOPEN_SIMPLE)
        fp.setDisplayDirectory(Dispatch._path)
        fp.setMultiSelectionMode(True)
        urls = ()
        if fp.execute():
            urls = fp.getSelectedFiles()
            Dispatch._path = fp.getDisplayDirectory()
            state = SUCCESS
        fp.dispose()
        return urls, state

    def _saveAs(self, document):
        state = FAILURE
        source = document.getURL()
        path, _, name = source.rpartition(self._sep)
        fp = createService(self._ctx, self._service, FILESAVE_SIMPLE)
        fp.setDisplayDirectory(path + self._sep)
        fp.setDefaultName(name)
        if fp.execute():
            target = fp.getSelectedFiles()[0]
            Dispatch._path = fp.getDisplayDirectory()
            if source != target:
                document.storeAsURL(target, ())
            else:
                document.store()
            state = SUCCESS
        fp.dispose()
        return state

    def _showWarning(self, arguments):
        toolkit = getToolKit(self._ctx)
        peer = toolkit.getActiveTopWindow()
        args = getArgumentSet(arguments)
        msgbox = getMessageBox(toolkit, peer, args['Box'], args['Button'], args['Title'], args['Message'])
        msgbox.execute()
        msgbox.dispose()
        return SUCCESS

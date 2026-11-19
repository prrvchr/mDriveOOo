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
from .unotool import getConfiguration
from .unotool import getDesktop
from .unotool import getLastNamedParts

from .configuration import g_identifier
from .configuration import g_sep


class Dispatch(unohelper.Base,
               XNotifyingDispatch):
    def __init__(self, ctx, frame):
        self._ctx = ctx
        self._frame = frame
        self._listeners = []
        self._config = getConfiguration(ctx, g_identifier, True)
        self._path = self._config.getByName('DisplayDirectory')
        self._service = 'com.sun.star.ui.dialogs.OfficeFilePicker'

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
        return state, result

    def addStatusListener(self, listener, url):
        state = FeatureStateEvent()
        state.FeatureURL = url
        state.IsEnabled = True
        # state.State = True
        listener.statusChanged(state)
        self._listeners.append(listener)

    def removeStatusListener(self, listener, _url):
        if listener in self._listeners:
            self._listeners.remove(listener)

# Private methods
    def _open(self):
        state = FAILURE
        fp = createService(self._ctx, self._service, FILEOPEN_SIMPLE)
        fp.setDisplayDirectory(self._path)
        fp.setMultiSelectionMode(True)
        urls = ()
        if fp.execute():
            self._setPath(fp.getDisplayDirectory())
            urls = fp.getSelectedFiles()
            state = SUCCESS
        fp.dispose()
        return urls, state

    def _saveAs(self, document):
        state = FAILURE
        source = document.getURL()
        path, name = getLastNamedParts(source, g_sep)
        fp = createService(self._ctx, self._service, FILESAVE_SIMPLE)
        fp.setDisplayDirectory(path + g_sep)
        fp.setDefaultName(name)
        if fp.execute():
            self._setPath(fp.getDisplayDirectory())
            target = fp.getSelectedFiles()[0]
            if source != target:
                document.storeAsURL(target, ())
            else:
                document.store()
            state = SUCCESS
        fp.dispose()
        return state

    def _setPath(self, path):
        if path != self._path:
            self._config.replaceByName('DisplayDirectory', path)
            self._path = path
        if self._config.hasPendingChanges():
            self._config.commitChanges()

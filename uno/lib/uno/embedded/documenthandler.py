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

import unohelper

from com.sun.star.embed.ElementModes import SEEKABLEREAD
from com.sun.star.embed.ElementModes import READWRITE

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.document import XStorageChangeListener

from com.sun.star.util import XCloseListener

from .unotool import createService
from .unotool import getDesktop
from .unotool import getSimpleFile
from .unotool import getUriFactory
from .unotool import getUrlTransformer
from .unotool import hasInterface
from .unotool import parseUrl

from .configuration import g_protocol
from .configuration import g_options
from .configuration import g_shutdown

import traceback


class DocumentHandler(unohelper.Base,
                      XCloseListener,
                      XStorageChangeListener):
    def __init__(self, ctx, lock, logger, url):
        self._ctx = ctx
        self._folder = 'database'
        self._prefix = '.'
        self._suffix = '.lck'
        self._lock = lock
        self._logger = logger
        self._listening = False
        self._path, self._name = self._getDataBaseInfo(url)
        self._url = url

    @property
    def URL(self):
        return self._url

    # XCloseListener
    def queryClosing(self, event, owner):
        url = self._url
        self._logger.logprb(INFO, 'DocumentHandler', 'queryClosing()', 201, url)
        with self._lock:
            document = event.Source
            if self._closeDataBase(document):
                sf = getSimpleFile(self._ctx)
                if sf.isFolder(self._path):
                    sf.kill(self._path)
            self._url = None
        self._logger.logprb(INFO, 'DocumentHandler', 'queryClosing()', 202, url)

    def notifyClosing(self, event):
        pass

    # XStorageChangeListener
    def notifyStorageChange(self, document, storage):
        url = document.getLocation()
        self._logger.logprb(INFO, 'DocumentHandler', 'notifyStorageChange()', 211, url)
        with self._lock:
            newpath, newname = self._getDataBaseInfo(url)
            if self._switchDataBase(document, storage, newname):
                sf = getSimpleFile(self._ctx)
                if sf.isFolder(self._path):
                    sf.kill(self._path)
            self._path = newpath
            self._name = newname
            self._url = url
            document.removeCloseListener(self)
        self._logger.logprb(INFO, 'DocumentHandler', 'notifyStorageChange()', 212, url)

    # XEventListener
    def disposing(self, event):
        url = self._url
        self._logger.logprb(INFO, 'DocumentHandler', 'disposing()', 221, url)
        document = event.Source
        document.removeCloseListener(self)
        document.removeStorageChangeListener(self)
        self._url = None
        self._logger.logprb(INFO, 'DocumentHandler', 'disposing()', 222, url)

    # DocumentHandler getter methods
    def getConnectionUrl(self, document, storage, url):
        with self._lock:
            sf = getSimpleFile(self._ctx)
            if not sf.exists(self._path):
                if storage.hasElements():
                    # FIXME: With OpenOffice getElementNames() return a String
                    # FIXME: if storage has no elements.
                    self._openDataBase(sf, storage)
                else:
                    sf.createFolder(self._path)
            # FIXME: With OpenOffice there is no Document in the info
            # FIXME: parameter provided during the connection
            if document is None:
                document = self._getDocument(url)
            # FIXME: We want to add the StorageChangeListener only once
            if not self._listening:
                document.addStorageChangeListener(self)
                self._listening = True
            # FIXME: If storage has been changed the closeListener has been removed
            document.addCloseListener(self)
            #mri = createService(self._ctx, 'mytools.Mri')
            #mri.inspect(document)
            return self._getConnectionUrl()

    # DocumentHandler private getter methods
    def _getDataBaseInfo(self, location):
        transformer = getUrlTransformer(self._ctx)
        url = parseUrl(transformer, location)
        name = self._getDataBaseName(transformer, url)
        path = self._getDataBasePath(transformer, url, name)
        return path, name

    def _getDataBasePath(self, transformer, url, name):
        path = self._getDocumentPath(transformer, url)
        return '%s%s%s%s' % (path, self._prefix, name, self._suffix)

    def _getDocumentPath(self, transformer, url):
        path = parseUrl(transformer, url.Protocol + url.Path)
        return transformer.getPresentation(path, False)

    def _getDataBaseName(self, transformer, location):
        url = transformer.getPresentation(location, False)
        uri = getUriFactory(self._ctx).parse(url)
        name = uri.getPathSegment(uri.getPathSegmentCount() -1)
        return self._getDocumentName(name)

    def _getDocumentName(self, title):
        name, sep, extension = title.rpartition('.')
        return name if sep else extension

    def _getFileUrl(self, name):
        # FIXME: If the odb file was Save As while the connection was closed,
        # FIXME: then the contents of the database folder must be renamed
        # FIXME: The cleaning of the odb file is done when it is closed
        if not name.startswith(self._name):
            name = self._getStorageName(name, self._getDocumentName(name), self._name)
        return '%s/%s' % (self._path, name)
 
    def _getDocument(self, url):
        document = None
        interface = 'com.sun.star.frame.XStorable'
        components = getDesktop(self._ctx).getComponents().createEnumeration()
        while components.hasMoreElements():
            component = components.nextElement()
            if hasInterface(component, interface) and component.hasLocation() and component.getLocation() == url:
                document = component
                break
        return document

    def _getConnectionUrl(self):
        return '%s%s/%s%s%s' % (g_protocol, self._path, self._name, g_options, g_shutdown)

    def _getStorageName(self, name, oldname, newname):
        return name.replace(oldname, newname)

    def _closeDataBase(self, document):
        try:
            target = document.getDocumentSubStorage(self._folder, READWRITE)
            service = 'com.sun.star.embed.FileSystemStorageFactory'
            args = (self._path, READWRITE)
            source = createService(self._ctx, service).createInstanceWithArguments(args)
            # FIXME: With OpenOffice getElementNames() return a String
            # FIXME: if storage has no elements.
            if source.hasElements():
                for name in source.getElementNames():
                    if source.isStreamElement(name):
                        if target.hasByName(name):
                            target.removeElement(name)
                        self._logger.logprb(INFO, 'DocumentHandler', '_closeDataBase()', 231, name)
                        source.copyElementTo(name, target, name)
                        self._logger.logprb(INFO, 'DocumentHandler', '_closeDataBase()', 232, name)
                # FIXME: We need to clean the odb file if Save As as been used with a closed connection
                if target.hasElements():
                    for name in target.getElementNames():
                        if not name.startswith(self._name):
                            target.removeElement(name)
            target.commit()
            target.dispose()
            source.dispose()
            document.store()
            return True
        except Exception as e:
            self._logger.logprb(SEVERE, 'DocumentHandler', '_closeDataBase()', 233, self._url, traceback.format_exc())
            return False

    def _switchDataBase(self, document, storage, newname):
        try:
            target = storage.openStorageElement(self._folder, READWRITE)
            service = 'com.sun.star.embed.FileSystemStorageFactory'
            args = (self._path, READWRITE)
            source = createService(self._ctx, service).createInstanceWithArguments(args)
            # FIXME: With OpenOffice getElementNames() return a String
            # FIXME: if storage has no elements.
            if source.hasElements():
                for name in source.getElementNames():
                    if source.isStreamElement(name):
                        self._logger.logprb(INFO, 'DocumentHandler', '_switchDataBase()', 241, name)
                        self._moveStorage(source, target, name, newname)
                        self._logger.logprb(INFO, 'DocumentHandler', '_switchDataBase()', 242, name)
            target.commit()
            target.dispose()
            source.dispose()
            document.store()
            return True
        except Exception as e:
            self._logger.logprb(SEVERE, 'DocumentHandler', '_switchDataBase()', 243, self._url, traceback.format_exc())
            return False

    # DocumentHandler private setter methods
    def _openDataBase(self, sf, source):
        for name in source.getElementNames():
            url = self._getFileUrl(name)
            if not sf.exists(url):
                if source.isStreamElement(name):
                    input = source.openStreamElement(name, SEEKABLEREAD).getInputStream()
                    sf.writeFile(url, input)
                    input.closeInput()
        source.dispose()

    def _moveStorage(self, source, target, oldname, newname):
        if target.hasByName(oldname):
            target.removeElement(oldname)
        name = self._getStorageName(oldname, self._name, newname)
        if target.hasByName(name):
            target.removeElement(name)
        source.copyElementTo(oldname, target, name)

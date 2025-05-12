#!
# -*- coding: utf_8 -*-

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

from com.sun.star.embed.ElementModes import SEEKABLEREAD
from com.sun.star.embed.ElementModes import READWRITE
from com.sun.star.embed.ElementModes import TRUNCATE

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
from .configuration import g_catalog
from .configuration import g_options
from .configuration import g_create
from .configuration import g_exist
from .configuration import g_path
from .configuration import g_shutdown

import traceback


class DocumentHandler(unohelper.Base,
                      XCloseListener,
                      XStorageChangeListener):
    def __init__(self, ctx, lock, logger, driver, url):
        self._ctx = ctx
        self._directory = 'database'
        self._prefix = '.'
        self._suffix = '.lck'
        self._sep = '/'
        self._lock = lock
        self._logger = logger
        self._created = False
        self._path, self._folder = self._getDataBaseInfo(url)
        self._driver = driver
        self._url = url

    @property
    def URL(self):
        return self._url

    # XCloseListener
    def queryClosing(self, event, owner):
        url = self._url
        cls, method = 'DocumentHandler', 'queryClosing()'
        self._logger.logprb(INFO, cls, method, 201, url)
        with self._lock:
            document = event.Source
            target = document.getDocumentSubStorage(self._directory, READWRITE)
            if self._closeDataBase(document, target, cls, method, 241):
                self._removeFolder()
            self._url = None
        self._logger.logprb(INFO, cls, method, 202, url)

    def notifyClosing(self, event):
        pass

    # XStorageChangeListener
    def notifyStorageChange(self, document, storage):
        # The document has been save as with a new name
        url = document.getLocation()
        cls, method = 'DocumentHandler', 'notifyStorageChange()'
        self._logger.logprb(INFO, cls, method, 211, url)
        with self._lock:
            path, folder = self._getDataBaseInfo(url)
            target = storage.openStorageElement(self._directory, READWRITE)
            if self._closeDataBase(document, target, cls, method, 251):
                self._removeFolder()
            self._path = path
            self._folder = folder
            self._url = url
        self._logger.logprb(INFO, cls, method, 212, url)

    # XEventListener
    def disposing(self, event):
        document = event.Source
        url = document.getLocation()
        self._logger.logprb(INFO, 'DocumentHandler', 'disposing()', 221, url)
        document.removeCloseListener(self)
        document.removeStorageChangeListener(self)
        self._url = None
        self._logger.logprb(INFO, 'DocumentHandler', 'disposing()', 222, url)

    # DocumentHandler setter methods
    def removeFolder(self):
        # XXX: The database folder will be deleted only if it was created
        if self._created:
            self._removeFolder()

    # DocumentHandler getter methods
    def getConnectionUrl(self, storage):
        with self._lock:
            sf = getSimpleFile(self._ctx)
            url = self._getDataBaseUrl()
            exist = storage.hasElements()
            if not sf.exists(url):
                # XXX: The database folder will be deleted only if it was created
                self._created = True
                sf.createFolder(url)
                if exist:
                    count = self._extractStorage(sf, storage, url)
                    self._logger.logprb(INFO, 'DocumentHandler', 'getConnectionUrl()', 231, count)
            return self._getConnectionUrl(exist)

    def getDocument(self):
        document = None
        interface = 'com.sun.star.frame.XStorable'
        components = getDesktop(self._ctx).getComponents().createEnumeration()
        while components.hasMoreElements():
            component = components.nextElement()
            if hasInterface(component, interface) and component.hasLocation() and component.getLocation() == self._url:
                document = component
                break
        return document

    # DocumentHandler private getter methods
    def _getDataBaseInfo(self, location):
        transformer = getUrlTransformer(self._ctx)
        url = parseUrl(transformer, location)
        path = self._getDataBasePath(transformer, url)
        folder = self._getDataBaseFolder(transformer, url)
        return path, folder

    def _getDataBaseUrl(self):
        return self._path + self._prefix + self._folder + self._suffix

    def _getDataBasePath(self, transformer, url):
        path = parseUrl(transformer, url.Protocol + url.Path)
        return transformer.getPresentation(path, False)

    def _getDataBaseFolder(self, transformer, location):
        url = transformer.getPresentation(location, False)
        uri = getUriFactory(self._ctx).parse(url)
        name = uri.getPathSegment(uri.getPathSegmentCount() -1)
        return self._getDocumentName(name)

    def _getDocumentName(self, title):
        name, sep, extension = title.rpartition('.')
        return name if sep else extension

    def _getConnectionUrl(self, exist):
        path = self._getConnectionPath()
        url = g_protocol + path + g_options
        return url + g_exist if exist else url + g_create

    def _getConnectionPath(self):
        url = self._getDataBaseUrl() + self._sep + g_catalog
        return uno.fileUrlToSystemPath(url) if g_path else url

    def _closeDataBase(self, document, target, cls, method, resource):
        try:
            if g_shutdown:
                self._shutdownDataBase()
            service = 'com.sun.star.embed.FileSystemStorageFactory'
            args = (self._getDataBaseUrl(), SEEKABLEREAD)
            source = createService(self._ctx, service).createInstanceWithArguments(args)
            count = self._copyStorage(source, target)
            self._logger.logprb(INFO, cls, method, resource, count)
            document.store()
            return True
        except Exception as e:
            self._logger.logprb(SEVERE, cls, method, resource + 1, self._url, traceback.format_exc())
            return False

    def _shutdownDataBase(self):
        # XXX: Some databases need to be shutdown if we want all files to be closed (ie: Derby)
        path = self._getConnectionPath()
        url = g_protocol + path + g_shutdown
        try:
            self._driver.connect(url, ())
        except Exception as e:
            pass

    # DocumentHandler private setter methods
    def _copyStorage(self, source, target):
        count = 0
        if source.hasElements():
            for name in source.getElementNames():
                if source.isStreamElement(name):
                    if target.hasByName(name):
                        target.removeElement(name)
                    source.copyElementTo(name, target, name)
                    count += 1
                else:
                    count += self._copyStorage(source.openStorageElement(name, SEEKABLEREAD),
                                               target.openStorageElement(name, READWRITE))
        target.commit()
        target.dispose()
        source.dispose()
        return count

    def _extractStorage(self, sf, source, url):
        count = 0
        if source.hasElements():
            for name in source.getElementNames():
                path = self._getPath(url, name)
                if source.isStreamElement(name):
                    input = source.openStreamElement(name, SEEKABLEREAD).getInputStream()
                    sf.writeFile(path, input)
                    input.closeInput()
                    count += 1
                else:
                    sf.createFolder(path)
                    count += self._extractStorage(sf, source.openStorageElement(name, SEEKABLEREAD), path)
        source.dispose()
        return count

    def _getPath(self, path, name):
        return path + self._sep + name

    def _removeFolder(self):
        url = self._getDataBaseUrl()
        sf = getSimpleFile(self._ctx)
        if sf.isFolder(url):
            sf.kill(url)


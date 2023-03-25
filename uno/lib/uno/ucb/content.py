#!
# -*- coding: utf-8 -*-

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

from com.sun.star.beans import XPropertiesChangeNotifier

from com.sun.star.beans.PropertyAttribute import BOUND
from com.sun.star.beans.PropertyAttribute import CONSTRAINED
from com.sun.star.beans.PropertyAttribute import READONLY
from com.sun.star.beans.PropertyAttribute import TRANSIENT

from com.sun.star.container import XChild

from com.sun.star.lang import NoSupportException
from com.sun.star.lang import XComponent

from com.sun.star.ucb import XContent
from com.sun.star.ucb import XCommandProcessor2
from com.sun.star.ucb import XContentCreator
from com.sun.star.ucb import InteractiveBadTransferURLException
from com.sun.star.ucb import CommandAbortedException

from com.sun.star.ucb.ContentAction import INSERTED
from com.sun.star.ucb.ContentAction import EXCHANGED

from com.sun.star.ucb.ContentInfoAttribute import KIND_DOCUMENT
from com.sun.star.ucb.ContentInfoAttribute import KIND_FOLDER
from com.sun.star.ucb.ContentInfoAttribute import KIND_LINK

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb import XRestContent

from .unolib import PropertySetInfo

from .unotool import createService
from .unotool import getSimpleFile
from .unotool import getProperty
from .unotool import hasInterface

from .contentlib import CommandInfo
from .contentlib import Row
from .contentlib import DynamicResultSet

from .contentcore import getPropertiesValues
from .contentcore import setPropertiesValues

from .contenttools import getCommandInfo
from .contenttools import getContentEvent
from .contenttools import getContentInfo
from .contenttools import getMimeType

from .logger import getLogger

from .configuration import g_defaultlog

import traceback


class Content(unohelper.Base,
              XContent,
              XComponent,
              XCommandProcessor2,
              XContentCreator,
              XChild,
              XPropertiesChangeNotifier,
              XRestContent):
    def __init__(self, ctx, identifier):
        self._ctx = ctx
        msg = "Content loading ... "
        self._identifier = identifier
        self.MetaData = identifier.MetaData
        self._commandInfo = self._getCommandInfo()
        self._contentListeners = []
        self._propertiesListener = {}
        self._listeners = []
        msg += "Done."
        self._logger = getLogger(ctx, g_defaultlog)
        self._logger.logp(INFO, 'Content', '__init__()', msg)

    @property
    def IsFolder(self):
        return self.MetaData.getValue('IsFolder')
    @property
    def IsDocument(self):
        return self.MetaData.getValue('IsDocument')
    @property
    def CanAddChild(self):
        return self.MetaData.getValue('CanAddChild')


    # XComponent
    def dispose(self):
        event = uno.createUnoStruct('com.sun.star.lang.EventObject')
        event.Source = self
        for listener in self._listeners:
            print("Content.dispose() ***************************************************************")
            listener.disposing(event)

    def addEventListener(self, listener):
        self._listeners.append(listener)

    def removeEventListener(self, listener):
        if listener in self._listeners:
            self._listeners.remove(listener)

    # XChild
    def getParent(self):
        content = None
        print("Content.getParent() 1")
        if not self._identifier.isRoot():
            print("Content.getParent() 1")
            content = self._identifier.getParent().getContent()
        print("Content.getParent() 1")
        return content

    def setParent(self, parent):
        raise NoSupportException('Parent can not be set', self)

    # XPropertiesChangeNotifier
    def addPropertiesChangeListener(self, names, listener):
        for name in names:
            if name not in self._propertiesListener:
                self._propertiesListener[name] = []
            if listener not in self._propertiesListener[name]:
                self._propertiesListener[name].append(listener)
    def removePropertiesChangeListener(self, names, listener):
        for name in names:
            if name in self._propertiesListener:
                if listener in self._propertiesListener[name]:
                    self._propertiesListener[name].remove(listener)

    # XContentCreator
    def queryCreatableContentsInfo(self):
        return self.getIdentifier().getCreatableContentsInfo()
    def createNewContent(self, info):
        # To avoid circular imports, the creation of new content is delegated to
        # Identifier.createNewContent() since the identifier also creates Content
        # with Identifier.createContent()
        print("Content.createNewContent() 1")
        return self._identifier.createNewContent(info.Type)

    # XContent
    def getIdentifier(self):
        return self._identifier
    def getContentType(self):
        return self.MetaData.getValue('ContentType')
    def addContentEventListener(self, listener):
        print("Content.addContentEventListener() ***************************************************************")
        self._contentListeners.append(listener)
    def removeContentEventListener(self, listener):
        if listener in self._contentListeners:
            self._contentListeners.remove(listener)

    # XCommandProcessor2
    def createCommandIdentifier(self):
        print("Content.createCommandIdentifier() 1")
        return 1
    def execute(self, command, id, environment):
        print("Content.execute() 1  Commande Name: %s ****************************************************************" % command.Name)
        url = self.getIdentifier().getContentIdentifier()
        user = self.getIdentifier().User
        print("Content.execute() %s - %s - %s" % (command.Name, url, self.getIdentifier().Id))
        msg = "command.Name: %s" % command.Name
        self._logger.logp(INFO, 'Content', 'execute()', msg)
        if command.Name == 'getCommandInfo':
            return CommandInfo(self._getCommandInfo())
        elif command.Name == 'getPropertySetInfo':
            return PropertySetInfo(self._identifier._propertySetInfo)
        elif command.Name == 'getPropertyValues':
            values = getPropertiesValues(self._logger, self, command.Argument)
            return Row(values)
        elif command.Name == 'setPropertyValues':
            return setPropertiesValues(self._logger, self, environment, command.Argument)
        elif command.Name == 'delete':
            self.MetaData.insertValue('Trashed', True)
            user.DataBase.updateContent(user.Id, self._identifier.Id, 'Trashed', True)
        elif command.Name == 'open':
            if self.IsFolder:
                print("Content.execute() open 1")
                # Not Used: command.Argument.Properties - Implement me ;-)
                select = self._identifier.getFolderContent(self.MetaData)
                print("Content.execute() open 2")
                msg += " IsFolder: %s" % self.IsFolder
                self._logger.logp(INFO, 'Content', 'execute()', msg)
                print("Content.execute() open 3")
                return DynamicResultSet(self._identifier.User, select)
            elif self.IsDocument:
                print("Content.execute() open 4")
                sf = getSimpleFile(self._ctx)
                url, size = self._identifier.getDocumentContent(sf, self.MetaData, 0)
                if not size:
                    title = self.MetaData.getValue('Title')
                    msg = "Error while downloading file: %s" % title
                    print("Content.execute() %s" % msg)
                    raise CommandAbortedException(msg, self)
                sink = command.Argument.Sink
                isreadonly = self.MetaData.getValue('IsReadOnly')
                if hasInterface(sink, 'com.sun.star.io.XActiveDataSink'):
                    sink.setInputStream(sf.openFileRead(url))
                elif not isreadonly and hasInterface(sink, 'com.sun.star.io.XActiveDataStreamer'):
                    sink.setStream(sf.openFileReadWrite(url))
        elif command.Name == 'insert':
            # The Insert command is only used to create a new folder or a new document
            # (ie: File Save As).
            # It saves the content created by 'createNewContent' from the parent folder
            # right after the Title property is initialized
            print("Content.execute() insert 1 - %s - %s - %s" % (self.IsFolder,
                                                                 self._identifier.Id,
                                                                 self.MetaData.getValue('Title')))
            if self.IsFolder:
                #mediatype = self._identifier.User.Provider.Folder
                #self.MetaData.insertValue('MediaType', mediatype)
                print("Content.execute() insert 2 ************** %s" % self.MetaData.getValue('MediaType'))
                try:
                    if self._identifier.insertNewContent(self.MetaData):
                        print("Content.execute() insert 3")
                        # Need to consum the new Identifier if needed...
                        self._identifier.deleteNewIdentifier()
                        print("Content.execute() insert 4")
                except Exception as e:
                    msg = "Content.Insert() Error: %s" % traceback.print_exc()
                    print(msg)
                    raise e
                        
            elif self.IsDocument:
                stream = command.Argument.Data
                replace = command.Argument.ReplaceExisting
                sf = getSimpleFile(self._ctx)
                url = self._identifier.User.Provider.SourceURL
                target = '%s/%s' % (url, self._identifier.Id)
                if sf.exists(target) and not replace:
                    return
                if hasInterface(stream, 'com.sun.star.io.XInputStream'):
                    sf.writeFile(target, stream)
                    # For document type resources, the media type is always unknown...
                    mediatype = getMimeType(self._ctx, stream)
                    self.MetaData.setValue('MediaType', mediatype)
                    stream.closeInput()
                    print("Content.execute() insert 2 ************** %s" % mediatype)
                    if self._identifier.insertNewContent(self.MetaData):
                        # Need to consum the new Identifier if needed...
                        self._identifier.deleteNewIdentifier()
                        print("Content.execute() insert 3")

        elif command.Name == 'createNewContent' and self.IsFolder:
            return self.createNewContent(command.Argument)
        elif command.Name == 'transfer' and self.IsFolder:
            # Transfer command is used for document 'File Save' or 'File Save As'
            # NewTitle come from:
            # - Last segment path of 'XContent.getIdentifier().getContentIdentifier()' for OpenOffice
            # - Property 'Title' of 'XContent' for LibreOffice
            # If the content has been renamed, the last segment is the new Title of the content
            title = command.Argument.NewTitle
            source = command.Argument.SourceURL
            move = command.Argument.MoveData
            clash = command.Argument.NameClash
            print("Content.execute() transfert 1 %s - %s -%s - %s" % (title, source, move, clash))
            # We check if 'NewTitle' is a child of this folder by recovering its ItemId
            itemid = user.DataBase.getChildId(self._identifier.Id, title)
            if itemid is None:
                print("Content.execute() transfert 2 %s" % itemid)
                # ItemId could not be found: 'NewTitle' does not exist in the folder...
                # For new document (File Save As) we use commands:
                # - createNewContent: for creating an empty new Content
                # - Insert at new Content for committing change
                # To execute these commands, we must throw an exception
                msg = "Couln't handle Url: %s" % source
                raise InteractiveBadTransferURLException(msg, self)
            print("Content.execute() transfert 3 %s - %s" % (itemid, source))
            sf = getSimpleFile(self._ctx)
            if not sf.exists(source):
                raise CommandAbortedException("Error while saving file: %s" % source, self)
            inputstream = sf.openFileRead(source)
            target = '%s/%s' % (user.Provider.SourceURL, itemid)
            sf.writeFile(target, inputstream)
            inputstream.closeInput()
            # We need to update the Size
            user.DataBase.updateContent(user.Id, itemid, 'Size', sf.getSize(target))
            if move:
                pass #must delete object
        elif command.Name == 'flush' and self.IsFolder:
            pass

    def abort(self, id):
        pass
    def releaseCommandIdentifier(self, id):
        pass

    def _getCommandInfo(self):
        commands = {}
        t1 = uno.getTypeByName('com.sun.star.ucb.XCommandInfo')
        commands['getCommandInfo'] = getCommandInfo('getCommandInfo', t1)
        t2 = uno.getTypeByName('com.sun.star.beans.XPropertySetInfo')
        commands['getPropertySetInfo'] = getCommandInfo('getPropertySetInfo', t2)
        t3 = uno.getTypeByName('[]com.sun.star.beans.Property')
        commands['getPropertyValues'] = getCommandInfo('getPropertyValues', t3)
        t4 = uno.getTypeByName('[]com.sun.star.beans.PropertyValue')
        commands['setPropertyValues'] = getCommandInfo('setPropertyValues', t4)
        try:
            t5 = uno.getTypeByName('com.sun.star.ucb.OpenCommandArgument3')
        except RuntimeError as e:
            t5 = uno.getTypeByName('com.sun.star.ucb.OpenCommandArgument2')
        commands['open'] = getCommandInfo('open', t5)
        try:
            t6 = uno.getTypeByName('com.sun.star.ucb.InsertCommandArgument2')
        except RuntimeError as e:
            t6 = uno.getTypeByName('com.sun.star.ucb.InsertCommandArgument')
        commands['insert'] = getCommandInfo('insert', t6)
        if not self._identifier.isRoot():
            commands['delete'] = getCommandInfo('delete', uno.getTypeByName('boolean'))
        try:
            t7 = uno.getTypeByName('com.sun.star.ucb.TransferInfo2')
        except RuntimeError as e:
            t7 = uno.getTypeByName('com.sun.star.ucb.TransferInfo')
        commands['transfer'] = getCommandInfo('transfer', t7)
        commands['flush'] = getCommandInfo('flush')
        print("Content._getCommandInfo() CanAddChild: %s   **********************************************" % self.CanAddChild)
        if self.CanAddChild:
            t8 = uno.getTypeByName('com.sun.star.ucb.ContentInfo')
            commands['createNewContent'] = getCommandInfo('createNewContent', t8)
        return commands

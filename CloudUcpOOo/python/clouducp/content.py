#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.container import XChild
from com.sun.star.lang import NoSupportException
from com.sun.star.ucb import XContent
from com.sun.star.ucb import XCommandProcessor2
from com.sun.star.ucb import XContentCreator
from com.sun.star.ucb import InteractiveBadTransferURLException
from com.sun.star.ucb import CommandAbortedException
from com.sun.star.beans import XPropertiesChangeNotifier

from com.sun.star.beans.PropertyAttribute import BOUND
from com.sun.star.beans.PropertyAttribute import CONSTRAINED
from com.sun.star.beans.PropertyAttribute import READONLY
from com.sun.star.beans.PropertyAttribute import TRANSIENT

from com.sun.star.ucb.ContentInfoAttribute import KIND_DOCUMENT
from com.sun.star.ucb.ContentInfoAttribute import KIND_FOLDER
from com.sun.star.ucb.ContentInfoAttribute import KIND_LINK

from com.sun.star.ucb.ContentAction import INSERTED
from com.sun.star.ucb.ContentAction import EXCHANGED

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb import XRestContent

from unolib import getSimpleFile
from unolib import getProperty
from unolib import PropertySetInfo
from unolib import getInterfaceTypes

from .contentlib import CommandInfo
from .contentlib import Row
from .contentlib import DynamicResultSet

from .contentcore import getPropertiesValues
from .contentcore import setPropertiesValues

from .contenttools import getCommandInfo
from .contenttools import getContentInfo
from .contenttools import getMimeType

from .logger import logMessage

import traceback


class Content(unohelper.Base,
              XContent,
              XCommandProcessor2,
              XContentCreator,
              XChild,
              XPropertiesChangeNotifier,
              XRestContent):
    def __init__(self, ctx, identifier):
        self.ctx = ctx
        msg = "Content loading ... "
        self.Identifier = identifier
        self.MetaData = identifier.MetaData
        self._commandInfo = self._getCommandInfo()
        self._contentListeners = []
        self._propertiesListener = {}
        msg += "Done."
        logMessage(self.ctx, INFO, msg, "Content", "__init__()")

    @property
    def IsFolder(self):
        return self.MetaData.getValue('IsFolder')
    @property
    def IsDocument(self):
        return self.MetaData.getValue('IsDocument')
    @property
    def CanAddChild(self):
        return self.MetaData.getValue('CanAddChild')

    # XChild
    def getParent(self):
        content = None
        if not self.Identifier.isRoot():
            identifier = self.Identifier.getParent()
            content = identifier.getContent()
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
        print("Content.queryCreatableContentsInfo()")
        return self.MetaData.getValue('CreatableContentsInfo')
    def createNewContent(self, info):
        # To avoid circular imports, the creation of new identifiers is delegated to
        # Identifier.createNewIdentifier() since the identifier also creates Content
        # with Identifier.getContent()
        identifier = self.Identifier.createNewIdentifier(info.Type)
        print("Content.createNewContent() Folder: %s create New Id: %s" % (self.MetaData.getValue('Title'), identifier.Id))
        return identifier.getContent()

    # XContent
    def getIdentifier(self):
        return self.Identifier
    def getContentType(self):
        return self.MetaData.getValue('ContentType')
    def addContentEventListener(self, listener):
        if listener not in self._contentListeners:
            self._contentListeners.append(listener)
    def removeContentEventListener(self, listener):
        if listener in self._contentListeners:
            self._contentListeners.remove(listener)

    # XCommandProcessor2
    def createCommandIdentifier(self):
        return 1
    def execute(self, command, id, environment):
        try:
            url = self.getIdentifier().getContentIdentifier()
            print("Content.execute() %s - %s - %s" % (command.Name, url, self.getIdentifier().Id))
            msg = "command.Name: %s" % command.Name
            logMessage(self.ctx, INFO, msg, "Content", "execute()")
            if command.Name == 'getCommandInfo':
                return CommandInfo(self._commandInfo)
            elif command.Name == 'getPropertySetInfo':
                return PropertySetInfo(self.Identifier._propertySetInfo)
            elif command.Name == 'getPropertyValues':
                namedvalues = getPropertiesValues(self.ctx, self, command.Argument)
                return Row(namedvalues)
            elif command.Name == 'setPropertyValues':
                return setPropertiesValues(self.ctx, self, environment, command.Argument)
            elif command.Name == 'delete':
                self.MetaData.insertValue('Trashed', True)
                user = self.Identifier.User
                user.DataBase.updateContent(user.Id, self.Identifier.Id, 'Trashed', True)
            elif command.Name == 'open':
                if self.IsFolder:
                    # Not Used: command.Argument.Properties - Implement me ;-)
                    select = self.Identifier.getFolderContent(self.MetaData)
                    msg += " IsFolder: %s" % self.IsFolder
                    logMessage(self.ctx, INFO, msg, "Content", "execute()")
                    return DynamicResultSet(self.ctx, select)
                elif self.IsDocument:
                    sf = getSimpleFile(self.ctx)
                    url, size = self.Identifier.getDocumentContent(sf, self.MetaData, 0)
                    if not size:
                        title = self.MetaData.getValue('Title')
                        msg = "Error while downloading file: %s" % title
                        print("Content.execute() %s" % msg)
                        raise CommandAbortedException(msg, self)
                    sink = command.Argument.Sink
                    interfaces = getInterfaceTypes(sink)
                    datasink = uno.getTypeByName('com.sun.star.io.XActiveDataSink')
                    datastream = uno.getTypeByName('com.sun.star.io.XActiveDataStreamer')
                    isreadonly = self.MetaData.getValue('IsReadOnly')
                    if datasink in interfaces:
                        sink.setInputStream(sf.openFileRead(url))
                    elif not isreadonly and datastream in interfaces:
                        sink.setStream(sf.openFileReadWrite(url))
            elif command.Name == 'insert':
                # The Insert command is only used to create a new folder or a new document
                # (ie: File Save As).
                # It saves the content created by 'createNewContent' from the parent folder
                print("Content.execute() insert 1 - %s - %s - %s" % (self.IsFolder,
                                                                     self.Identifier.Id,
                                                                     self.MetaData.getValue('Title')))
                if self.IsFolder:
                    mediatype = self.Identifier.User.Provider.Folder
                    self.MetaData.insertValue('MediaType', mediatype)
                    print("Content.execute() insert 2 ************** %s" % mediatype)
                    if self.Identifier.insertNewContent(self.MetaData):
                        # Need to consum the new Identifier if needed...
                        self.Identifier.deleteNewIdentifier()
                    print("Content.execute() insert 3")
                elif self.IsDocument:
                    stream = command.Argument.Data
                    replace = command.Argument.ReplaceExisting
                    sf = getSimpleFile(self.ctx)
                    url = self.Identifier.User.Provider.SourceURL
                    target = '%s/%s' % (url, self.Identifier.Id)
                    if sf.exists(target) and not replace:
                        return
                    inputstream = uno.getTypeByName('com.sun.star.io.XInputStream')
                    if inputstream in getInterfaceTypes(stream):
                        sf.writeFile(target, stream)
                        mediatype = getMimeType(self.ctx, stream)
                        self.MetaData.insertValue('MediaType', mediatype)
                        stream.closeInput()
                        print("Content.execute() insert 2 ************** %s" % mediatype)
                        if self.Identifier.insertNewContent(self.MetaData):
                            # Need to consum the new Identifier if needed...
                            self.Identifier.deleteNewIdentifier()
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
                user = self.Identifier.User
                itemid = user.DataBase.getChildId(user.Id, self.Identifier.Id, title)
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
                sf = getSimpleFile(self.ctx)
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
        except CommandAbortedException as e:
            raise e
        except InteractiveBadTransferURLException as e:
            raise e
        except Exception as e:
            msg += " ERROR: %s" % e
            logMessage(self.ctx, SEVERE, msg, "Content", "execute()")

    def abort(self, id):
        pass
    def releaseCommandIdentifier(self, id):
        pass

    def _getCommandInfo(self):
        commands = {}
        commands['getCommandInfo'] = getCommandInfo('getCommandInfo')
        commands['getPropertySetInfo'] = getCommandInfo('getPropertySetInfo')
        t1 = uno.getTypeByName('[]com.sun.star.beans.Property')
        commands['getPropertyValues'] = getCommandInfo('getPropertyValues', t1)
        t2 = uno.getTypeByName('[]com.sun.star.beans.PropertyValue')
        commands['setPropertyValues'] = getCommandInfo('setPropertyValues', t2)
        try:
            t3 = uno.getTypeByName('com.sun.star.ucb.OpenCommandArgument3')
        except RuntimeError as e:
            t3 = uno.getTypeByName('com.sun.star.ucb.OpenCommandArgument2')
        commands['open'] = getCommandInfo('open', t3)
        try:
            t4 = uno.getTypeByName('com.sun.star.ucb.InsertCommandArgument2')
        except RuntimeError as e:
            t4 = uno.getTypeByName('com.sun.star.ucb.InsertCommandArgument')
        commands['insert'] = getCommandInfo('insert', t4)
        if not self.Identifier.isRoot():
            commands['delete'] = getCommandInfo('delete', uno.getTypeByName('boolean'))
        if self.CanAddChild:
            t5 = uno.getTypeByName('com.sun.star.ucb.ContentInfo')
            commands['createNewContent'] = getCommandInfo('createNewContent', t5)
            try:
                t6 = uno.getTypeByName('com.sun.star.ucb.TransferInfo2')
            except RuntimeError as e:
                t6 = uno.getTypeByName('com.sun.star.ucb.TransferInfo')
            commands['transfer'] = getCommandInfo('transfer', t6)
            commands['flush'] = getCommandInfo('flush')
        return commands

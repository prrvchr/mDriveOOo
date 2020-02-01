#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.uno import XInterface
from com.sun.star.uno import RuntimeException as UnoRuntimeException
from com.sun.star.container import XChild
from com.sun.star.lang import XComponent
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
from unolib import getPropertyValueSet
from unolib import PropertySetInfo

from .contentlib import CommandInfo
from .contentlib import Row
from .contentlib import DynamicResultSet
from .contentcore import getPropertiesValues
from .contentcore import setPropertiesValues
from .contenttools import getCommandInfo
from .contenttools import getContentInfo
from .contenttools import getUcb
from .contenttools import getUcp
from .contenttools import getUri
from .contenttools import getMimeType
from .logger import logMessage

import traceback


class Content(unohelper.Base,
              XComponent,
              XContent,
              XCommandProcessor2,
              XContentCreator,
              XChild,
              XPropertiesChangeNotifier,
              XRestContent):
    def __init__(self, ctx, identifier, data):
        self.ctx = ctx
        msg = "Content loading ... "
        self.Identifier = identifier
        self.MetaData = data
        creatablecontent = self._getCreatableContentsInfo()
        self.MetaData.insertValue('CreatableContentsInfo', creatablecontent)
        self._commandInfo = self._getCommandInfo()
        self._propertySetInfo = self._getPropertySetInfo()
        self.contentListeners = []
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

    # XComponent
    def dispose(self):
        print("Content.dispose()")
    def addEventListener(self, listener):
        print("Content.addEventListener()")
    def removeEventListener(self, listener):
        print("Content.removeEventListener()")

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

    # XChild
    def getParent(self):
        if self.Identifier.IsRoot:
            return XInterface()
        identifier = self.Identifier.getParent()
        return identifier.getContent()
    def setParent(self, parent):
        raise NoSupportException('Parent can not be set', self)

    # XContentCreator
    def queryCreatableContentsInfo(self):
        return self.MetaData.getValue('CreatableContentsInfo')
    def createNewContent(self, info):
        identifier = self.Identifier.createNewIdentifier(info.Type)
        return identifier.getContent()

    # XContent
    def getIdentifier(self):
        return self.Identifier
    def getContentType(self):
        return self.MetaData.getValue('ContentType')
    def addContentEventListener(self, listener):
        if listener not in self.contentListeners:
            self.contentListeners.append(listener)
    def removeContentEventListener(self, listener):
        if listener in self.contentListeners:
            self.contentListeners.remove(listener)

    # XCommandProcessor2
    def createCommandIdentifier(self):
        return 1
    def execute(self, command, id, environment):
        try:
            msg = "command.Name: %s" % command.Name
            logMessage(self.ctx, INFO, msg, "Content", "execute()")
            if command.Name == 'getCommandInfo':
                return CommandInfo(self._commandInfo)
            elif command.Name == 'getPropertySetInfo':
                return PropertySetInfo(self._propertySetInfo)
            elif command.Name == 'getPropertyValues':
                namedvalues = getPropertiesValues(self.ctx, self, command.Argument)
                return Row(namedvalues)
            elif command.Name == 'setPropertyValues':
                return setPropertiesValues(self.ctx, self, environment, command.Argument)
            elif command.Name == 'delete':
                self.MetaData.insertValue('Trashed', self.Identifier.updateTrashed(True, False))
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
                        raise CommandAbortedException(msg, self)
                    s = command.Argument.Sink
                    sink = uno.getTypeByName('com.sun.star.io.XActiveDataSink')
                    stream = uno.getTypeByName('com.sun.star.io.XActiveDataStreamer')
                    isreadonly = self.MetaData.getValue('IsReadOnly')
                    if s.queryInterface(sink):
                        s.setInputStream(sf.openFileRead(url))
                    elif not isreadonly and s.queryInterface(stream):
                        s.setStream(sf.openFileReadWrite(url))
            elif command.Name == 'insert':
                if self.IsFolder:
                    mediatype = self.Identifier.User.DataSource.Provider.Folder
                    self.MetaData.insertValue('MediaType', mediatype)
                    if self.Identifier.insertNewFolder(self.MetaData):
                        pass
                    #identifier = self.getIdentifier()
                    #ucp = getUcp(self.ctx, identifier.getContentProviderScheme())
                    #self.addPropertiesChangeListener(('Id', 'Name', 'Size', 'Trashed', 'Loaded'), ucp)
                    #propertyChange(self, 'Id', identifier.Id, CREATED | FOLDER)
                    #parent = identifier.getParent()
                    #event = getContentEvent(self, INSERTED, self, parent)
                    #ucp.queryContent(parent).notify(event)
                elif self.IsDocument:
                    # The Insert command is only used to create a new document (File Save As)
                    # it saves content from createNewContent from the parent folder
                    stream = command.Argument.Data
                    replace = command.Argument.ReplaceExisting
                    sf = getSimpleFile(self.ctx)
                    url = self.Identifier.User.DataSource.Provider.SourceURL
                    target = '%s/%s' % (url, self.Identifier.Id)
                    if sf.exists(target) and not replace:
                        pass
                    elif stream.queryInterface(uno.getTypeByName('com.sun.star.io.XInputStream')):
                        sf.writeFile(target, stream)
                        mediatype = getMimeType(self.ctx, stream)
                        self.MetaData.insertValue('MediaType', mediatype)
                        stream.closeInput()
                        if self.Identifier.insertNewDocument(self.MetaData):
                            pass
                        #ucp = getUcp(self.ctx, identifier.getContentProviderScheme())
                        #self.addPropertiesChangeListener(('Id', 'Name', 'Size', 'Trashed', 'Loaded'), ucp)
                        #propertyChange(self, 'Id', identifier.Id, CREATED | FILE)
                        #parent = identifier.getParent()
                        #event = getContentEvent(self, INSERTED, self, parent)
                        #ucp.queryContent(parent).notify(event)
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
                # We check if 'command.Argument.NewTitle' is an Id
                if self.Identifier.isChildId(title):
                    id = title
                else:
                    # It appears that 'command.Argument.NewTitle' is not an Id but a Title...
                    # If 'NewTitle' exist and is unique in the folder, we can retrieve its Id
                    id = self.Identifier.selectChildId(title)
                    if not id:
                        # Id could not be found: NewTitle does not exist in the folder...
                        # For new document (File Save As) we use commands:
                        # - createNewContent: for creating an empty new Content
                        # - Insert at new Content for committing change
                        # To execute these commands, we must throw an exception
                        msg = "Couln't handle Url: %s" % source
                        raise InteractiveBadTransferURLException(msg, self)
                sf = getSimpleFile(self.ctx)
                if not sf.exists(source):
                    raise CommandAbortedException("Error while saving file: %s" % source, self)
                inputstream = sf.openFileRead(source)
                target = '%s/%s' % (self.Identifier.User.DataSource.Provider.SourceURL, id)
                sf.writeFile(target, inputstream)
                inputstream.closeInput()
                # We need to commit change: Size is the property chainning all DataSource change
                if not self.Identifier.User.updateSize(id, self.Identifier.Id, sf.getSize(target)):
                    raise CommandAbortedException("Error while saving file: %s" % source, self)
                #ucb = getUcb(self.ctx)
                #identifier = ucb.createContentIdentifier('%s/%s' % (self.Identifier.BaseURL, title))
                #data = getPropertyValueSet({'Size': sf.getSize(target)})
                #content = ucb.queryContent(identifier)
                #executeContentCommand(content, 'setPropertyValues', data, environment)
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

    def _getCreatableContentsInfo(self):
        content = []
        if self.IsFolder and self.CanAddChild:
            provider = self.Identifier.DataSource.Provider
            properties = (getProperty('Title', 'string', BOUND), )
            content.append(getContentInfo(provider.Folder, KIND_FOLDER, properties))
            content.append(getContentInfo(provider.Office, KIND_DOCUMENT, properties))
            #if provider.hasProprietaryFormat:
            #    content.append(getContentInfo(provider.ProprietaryFormat, KIND_DOCUMENT, properties))
        return tuple(content)

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
        if not self.Identifier.IsRoot:
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

    def _getPropertySetInfo(self):
        RO = 0 if self.Identifier.IsNew else READONLY
        properties = {}
        properties['ContentType'] = getProperty('ContentType', 'string', BOUND | RO)
        properties['MediaType'] = getProperty('MediaType', 'string', BOUND | READONLY)
        properties['IsDocument'] = getProperty('IsDocument', 'boolean', BOUND | RO)
        properties['IsFolder'] = getProperty('IsFolder', 'boolean', BOUND | RO)
        properties['Title'] = getProperty('Title', 'string', BOUND | CONSTRAINED)
        properties['Size'] = getProperty('Size', 'long', BOUND | RO)
        created = getProperty('DateCreated', 'com.sun.star.util.DateTime', BOUND | READONLY)
        properties['DateCreated'] = created
        modified = getProperty('DateModified', 'com.sun.star.util.DateTime', BOUND | RO)
        properties['DateModified'] = modified
        properties['IsReadOnly'] = getProperty('IsReadOnly', 'boolean', BOUND | RO)
        info = getProperty('CreatableContentsInfo','[]com.sun.star.ucb.ContentInfo', BOUND | RO)
        properties['CreatableContentsInfo'] = info
        properties['CasePreservingURL'] = getProperty('CasePreservingURL', 'string', BOUND | RO)
        properties['BaseURI'] = getProperty('BaseURI', 'string', BOUND | READONLY)
        properties['TitleOnServer'] = getProperty('TitleOnServer', 'string', BOUND)
        properties['IsHidden'] = getProperty('IsHidden', 'boolean', BOUND | RO)
        properties['IsVolume'] = getProperty('IsVolume', 'boolean', BOUND | RO)
        properties['IsRemote'] = getProperty('IsRemote', 'boolean', BOUND | RO)
        properties['IsRemoveable'] = getProperty('IsRemoveable', 'boolean', BOUND | RO)
        properties['IsFloppy'] = getProperty('IsFloppy', 'boolean', BOUND | RO)
        properties['IsCompactDisc'] = getProperty('IsCompactDisc', 'boolean', BOUND | RO)
        return properties

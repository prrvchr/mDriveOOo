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

from com.sun.star.beans import UnknownPropertyException
from com.sun.star.beans import XPropertiesChangeNotifier

from com.sun.star.ucb.ConnectionMode import OFFLINE
from com.sun.star.ucb.ConnectionMode import ONLINE

from com.sun.star.beans.PropertyAttribute import BOUND
from com.sun.star.beans.PropertyAttribute import CONSTRAINED
from com.sun.star.beans.PropertyAttribute import READONLY
from com.sun.star.beans.PropertyAttribute import TRANSIENT

from com.sun.star.container import XChild

from com.sun.star.lang import IllegalAccessException
from com.sun.star.lang import NoSupportException
from com.sun.star.lang import XComponent

from com.sun.star.ucb import CommandAbortedException
from com.sun.star.ucb import IllegalIdentifierException
from com.sun.star.ucb import InteractiveBadTransferURLException
from com.sun.star.ucb import XCommandProcessor2
from com.sun.star.ucb import XContent
from com.sun.star.ucb import XContentCreator

from com.sun.star.ucb.ContentAction import INSERTED
from com.sun.star.ucb.ContentAction import EXCHANGED

from com.sun.star.ucb.ContentInfoAttribute import KIND_DOCUMENT
from com.sun.star.ucb.ContentInfoAttribute import KIND_FOLDER
from com.sun.star.ucb.ContentInfoAttribute import KIND_LINK

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from ..unolib import PropertySetInfo

from ..unotool import createService
from ..unotool import getNamedValue
from ..unotool import getProperty
from ..unotool import getPropertyValueSet
from ..unotool import getSimpleFile
from ..unotool import hasInterface

from .contentlib import CommandInfo
from .contentlib import Row
from .contentlib import DynamicResultSet

from .contenthelper import getCommandInfo
from .contenthelper import getContentEvent
from .contenthelper import getContentInfo
from .contenthelper import getInteractiveAugmentedIOException
from .contenthelper import getMimeType

from .contentidentifier import ContentIdentifier

from ..logger import getLogger

from ..configuration import g_defaultlog
from ..configuration import g_scheme
from ..configuration import g_separator

import traceback


class Content(unohelper.Base,
              XContent,
              XComponent,
              XCommandProcessor2,
              XContentCreator,
              XChild,
              XPropertiesChangeNotifier):
    def __init__(self, ctx, user, authority=True, url='', data=None):
        self._ctx = ctx
        self._user = user
        self._authority = authority
        self._new = data is not None
        self._contentListeners = []
        self._propertiesListener = {}
        self._listeners = []
        self._logger = user._logger
        self.MetaData = data if self._new else self._getMetaData(url)
        self._commandInfo = self._getCommandInfo()
        self._propertySetInfo = self._getPropertySetInfo()
        self._logger.logprb(INFO, 'Content', '__init__()', 501)

    @property
    def IsFolder(self):
        return self.MetaData.get('IsFolder')
    @property
    def IsDocument(self):
        return self.MetaData.get('IsDocument')
    @property
    def IsRoot(self):
        return self.MetaData.get('IsRoot')
    @property
    def CanAddChild(self):
        return self.MetaData.get('CanAddChild')

    @property
    def Id(self):
        return self.MetaData.get('Id')
    @property
    def ParentId(self):
        return self.MetaData.get('ParentId')
    @property
    def Path(self):
        return self.MetaData.get('Path')
    @property
    def Title(self):
        return self.MetaData.get('Title')
    @property
    def MediaType(self):
        return self.MetaData.get('MediaType', 'application/octet-stream')
    @property
    def ConnectionMode(self):
        return self.MetaData.get('ConnectionMode')
    def setConnectionMode(self, mode):
        self.MetaData['ConnectionMode'] = mode

    @property
    def User(self):
        return self._user

    def setAuthority(self, authority):
        self._authority = authority

    # XComponent
    def dispose(self):
        event = uno.createUnoStruct('com.sun.star.lang.EventObject')
        event.Source = self
        for listener in self._listeners:
            listener.disposing(event)

    def addEventListener(self, listener):
        self._listeners.append(listener)

    def removeEventListener(self, listener):
        if listener in self._listeners:
            self._listeners.remove(listener)

    # XChild
    def getParent(self):
        if self.IsRoot:
            return None
        return self._user.getContent(self.Path, self._authority)

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
        return self._user.getCreatableContentsInfo(self.CanAddChild)
    def createNewContent(self, info):
        path = self._user.getContentPath(self.Path, self.Title, self.IsRoot)
        return self._user.createNewContent(self.Id, path, self._authority, info.Type)

    # XContent
    def getIdentifier(self):
        identifier = self._user.getContentIdentifier(self._authority, self.Path, self.Title, self.IsRoot)
        return identifier
    def getContentType(self):
        return self.MetaData.get('ContentType')
    def addContentEventListener(self, listener):
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
        uri = self._user.getContentPath(self.Path, self.Title, self.IsRoot)
        print("Content.execute() %s - %s - %s" % (command.Name, uri, self.Id))
        msg = "command.Name: %s" % command.Name
        self._logger.logp(INFO, 'Content', 'execute()', msg)

        if command.Name == 'getCommandInfo':
            return CommandInfo(self._getCommandInfo())

        elif command.Name == 'getPropertySetInfo':
            return PropertySetInfo(self._propertySetInfo)

        elif command.Name == 'getPropertyValues':
            values = self._getPropertiesValues(command.Argument)
            return Row(values)

        elif command.Name == 'setPropertyValues':
            return self._setPropertiesValues(environment, command.Argument)

        elif command.Name == 'delete':
            self.MetaData['Trashed'] = True
            self._user.DataBase.updateContent(self._user.Id, self.Id, 'Trashed', True)

        elif command.Name == 'open':
            try:
                print("Content.execute() open  Mode: %s" % command.Argument.Mode)
                if self.IsFolder:
                    print("Content.execute() open 1")
                    select = self._getFolderContent(command.Argument.Properties)
                    print("Content.execute() open 2")
                    msg += " IsFolder: %s" % self.IsFolder
                    self._logger.logp(INFO, 'Content', 'execute()', msg)
                    print("Content.execute() open 3")
                    return DynamicResultSet(self._user, uri, self._authority, select)
                elif self.IsDocument:
                    print("Content.execute() open 4")
                    sf = getSimpleFile(self._ctx)
                    url, size = self._getDocumentContent(sf)
                    if not size:
                        title = self.MetaData.get('Title')
                        msg = "Error while downloading file: %s" % title
                        print("Content.execute() %s" % msg)
                        raise CommandAbortedException(msg, self)
                    sink = command.Argument.Sink
                    isreadonly = self.MetaData.get('IsReadOnly')
                    if hasInterface(sink, 'com.sun.star.io.XActiveDataSink'):
                        sink.setInputStream(sf.openFileRead(url))
                    elif not isreadonly and hasInterface(sink, 'com.sun.star.io.XActiveDataStreamer'):
                        sink.setStream(sf.openFileReadWrite(url))
            except Exception as e:
                msg = "Content.Open() Error: %s" % traceback.format_exc()
                print(msg)
                raise e

        elif command.Name == 'createNewContent' and self.IsFolder:
            return self.createNewContent(command.Argument)

        elif command.Name == 'insert':
            # The Insert command is only used to create a new folder or a new document
            # (ie: File Save As).
            # It saves the content created by 'createNewContent' from the parent folder
            # right after the Title property is initialized
            print("Content.execute() insert 1 - %s - %s - %s" % (self.IsFolder,
                                                                 self.Id,
                                                                 self.MetaData.get('Title')))
            if self.IsFolder:
                print("Content.execute() insert 2 ************** %s" % self.MetaData.get('MediaType'))
                try:
                    if self._user.insertNewContent(self.MetaData):
                        print("Content.execute() insert 3")
                        # Need to consum the new Identifier if needed...
                        self._user.deleteNewIdentifier(self.Id)
                        print("Content.execute() insert 4")
                except Exception as e:
                    msg = "Content.Insert() Error: %s" % traceback.print_exc()
                    print(msg)
                    raise e
                        
            elif self.IsDocument:
                stream = command.Argument.Data
                replace = command.Argument.ReplaceExisting
                sf = getSimpleFile(self._ctx)
                target = self._user.getTargetUrl(self.Id)
                if sf.exists(target) and not replace:
                    return
                if hasInterface(stream, 'com.sun.star.io.XInputStream'):
                    sf.writeFile(target, stream)
                    # For document type resources, the media type is always unknown...
                    mediatype = getMimeType(self._ctx, stream)
                    self.MetaData['MediaType'] = mediatype
                    stream.closeInput()
                    print("Content.execute() insert 2 ************** %s" % mediatype)
                    if self._user.insertNewContent(self.MetaData):
                        # Need to consum the new Identifier if needed...
                        self._user.deleteNewIdentifier(self.Id)
                        print("Content.execute() insert 3")

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
            itemid = self._user.DataBase.getChildId(self.Id, title)
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
            target = self._user.getTargetUrl(itemid)
            sf.writeFile(target, inputstream)
            inputstream.closeInput()
            # We need to update the Size
            self._user.DataBase.updateContent(self._user.Id, itemid, 'Size', sf.getSize(target))
            if move:
                pass #must delete object

        elif command.Name == 'flush' and self.IsFolder:
            pass

    def abort(self, id):
        pass
    def releaseCommandIdentifier(self, id):
        pass

    # Private methods
    def _getMetaData(self, url):
        if self._user.isRootPath(url):
            itemid = self._user.RootId
        else:
            itemid = self._user.DataBase.getIdentifier(self._user, url)
        if itemid is None:
            msg = self._logger.resolveString(511, url)
            raise IllegalIdentifierException(msg, self)
        data = self._user.DataBase.getItem(self._user, itemid)
        if data is None:
            msg = self._logger.resolveString(512, itemid, url)
            raise IllegalIdentifierException(msg, self)
        return data

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
        if not self.IsRoot:
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

    def _getPropertySetInfo(self):
        RO = 0 if self._new else READONLY
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
        #properties['BaseURI'] = getProperty('BaseURI', 'string', BOUND | READONLY)
        properties['TitleOnServer'] = getProperty('TitleOnServer', 'string', BOUND)
        properties['IsHidden'] = getProperty('IsHidden', 'boolean', BOUND | RO)
        properties['IsVolume'] = getProperty('IsVolume', 'boolean', BOUND | RO)
        properties['IsRemote'] = getProperty('IsRemote', 'boolean', BOUND | RO)
        properties['IsRemoveable'] = getProperty('IsRemoveable', 'boolean', BOUND | RO)
        properties['IsFloppy'] = getProperty('IsFloppy', 'boolean', BOUND | RO)
        properties['IsCompactDisc'] = getProperty('IsCompactDisc', 'boolean', BOUND | RO)
        properties['IsVersionable'] = getProperty('IsVersionable', 'boolean', BOUND | RO)
        properties['ConnectionMode'] = getProperty('ConnectionMode', 'short', BOUND | READONLY)
        return properties

    def _getPropertiesValues(self, properties):
        values = []
        for property in properties:
            value = None
            if all((hasattr(property, 'Name'),
                    property.Name in self._propertySetInfo,
                    property.Name in self.MetaData)):
                value = self.MetaData.get(property.Name)
                msg = "Name: %s - Value: %s" % (property.Name, value)
                level = INFO
                print("content._getPropertiesValues(): %s: %s" % (property.Name, value))
            else:
                msg = "ERROR: Requested property: %s is not available" % property.Name
                level = SEVERE
            self._logger.logp(level, 'Content', '_getPropertiesValues()', msg)
            values.append(getNamedValue(property.Name, value))
        return tuple(values)

    def _setPropertiesValues(self, environment, properties):
        try:
            results = []
            for property in properties:
                if all((hasattr(property, 'Name'),
                        hasattr(property, 'Value'),
                        property.Name in self._propertySetInfo)):
                    result, level, msg = self._setPropertyValue(environment, property)
                else:
                    msg = "ERROR: Requested property: %s is not available" % property.Name
                    level = SEVERE
                    error = UnknownPropertyException(msg, self)
                    result = uno.Any('com.sun.star.beans.UnknownPropertyException', error)
                self._logger.logp(level, 'Content', '_setPropertiesValues()', msg)
                results.append(result)
            return tuple(results)
        except Exception as e:
            msg = "Content._setPropertiesValues() Error: %s" % traceback.format_exc()
            print(msg)


    def _setPropertyValue(self, environment, property):
        name, value = property.Name, property.Value
        print("Content._setPropertyValue() 1 %s - %s" % (name, value))
        if self._propertySetInfo.get(name).Attributes & READONLY:
            msg = "ERROR: Requested property: %s is READONLY" % name
            level = SEVERE
            error = IllegalAccessException(msg, self)
            result = uno.Any('com.sun.star.lang.IllegalAccessException', error)
        else:
            result, level, msg = self._setProperty(environment, name, value)
        return result, level, msg


    def _setProperty(self, environment, name, value):
        if name == 'Title':
            result, level, msg = self._setTitle(environment, value)
        else:
            self.MetaData[name] = value
            msg = "Set property: %s value: %s" % (name, value)
            level = INFO
            result = None
        return result, level, msg

    def _setTitle(self, environment, title):
        print("Identifier.setTitle() 2 Title: %s" % (title, ))
        url = self.getIdentifier().getContentIdentifier()
        if u'~' in title:
            msg = "Can't set property: Title value: %s contains invalid character: '~'." % title
            level = SEVERE
            data = getPropertyValueSet({'Uri': url,'ResourceName': title})
            error = getInteractiveAugmentedIOException(msg, environment, 'QUERY', 'INVALID_CHARACTER', data)
            result = uno.Any('com.sun.star.ucb.InteractiveAugmentedIOException', error)
        elif not self._user.Provider.SupportDuplicate and self._user.DataBase.hasTitle(self._user.Id, self.ParentId, title):
            print("Identifier.setTitle() 3 Title: %s" % (title, ))
            msg = "Can't set property: %s value: %s - Name Clash Error" % ('Title', title)
            level = SEVERE
            data = getPropertyValueSet({'TargetFolderURL': url,
                                        'ClashingName': title,
                                        'ProposedNewName': '%s(1)' % title})
            #data = getPropertyValueSet({'Uri': self.getIdentifier().getContentIdentifier(),'ResourceName': title})
            error = getInteractiveAugmentedIOException(msg, environment, 'QUERY', 'ALREADY_EXISTING', data)
            result = uno.Any('com.sun.star.ucb.InteractiveAugmentedIOException', error)
        else:
            print("Identifier.setTitle() 4 Title: %s" % (title, ))
            # FIXME: When you change Title you must change also the Identifier.getContentIdentifier()
            if not self._new:
                # And as the uri changes we also have to clear this Identifier from the cache.
                # New Identifier bypass the cache: they are created by the folder's Identifier
                # (ie: createNewIdentifier()) and have same uri as this folder.
                self._user.expireIdentifier(self.getIdentifier())
            if self._user.Provider.SupportDuplicate:
                newtitle = self._user.DataBase.getNewTitle(title, self.ParentId, self.IsFolder)
            else:
                newtitle = title
            print("Identifier.setTitle() 5 Title: %s - New Title: %s" % (title, newtitle))
            self.MetaData['Title'] = title
            self.MetaData['TitleOnServer'] = newtitle
            # If the identifier is new then the content is not yet in the database.
            # It will be inserted by the insert command of the XCommandProcessor2.execute()
            if not self._new:
                self._user.DataBase.updateContent(self._user.Id, self.Id, 'Title', title)
            path = self._user.getContentPath(self.Path, newtitle, self.IsRoot)
            print("Identifier.setTitle() 3 Path: %s - Url: %s" % (path, self.getIdentifier().getContentIdentifier()))
            msg = "Set property: %s value: %s" % ('Title', title)
            level = INFO
            result = None
        return result, level, msg

    def _getFolderContent(self, properties):
        try:
            select, updated = self._updateFolderContent(properties)
            if updated:
                loaded = self._user.DataBase.updateConnectionMode(self._user.Id, self.Id, OFFLINE, ONLINE)
                self.setConnectionMode(loaded)
            return select
        except Exception as e:
            msg = "Error: %s" % traceback.print_exc()
            print(msg)
            raise e

    def _updateFolderContent(self, properties):
        updated = False
        if ONLINE == self.ConnectionMode == self._user.SessionMode:
            url = self._user.getContentPath(self.Path, self.Title, self.IsRoot)
            self._logger.logprb(INFO, 'Content', '_updateFolderContent()', 411, url)
            updated = self._user.Provider.updateFolderContent(self)
        mode = self._user.SessionMode
        scheme = self._user.getContentScheme(self._authority)
        select = self._user.DataBase.getChildren(self._user.Name, self.Id, properties, mode, scheme)
        return select, updated

    def _getDocumentContent(self, sf):
        size = 0
        url = self._user.Provider.SourceURL + g_separator + self.Id
        if self.ConnectionMode == OFFLINE and sf.exists(url):
            return url, sf.getSize(url)
        if self._user.Provider.getDocumentContent(self, url):
            loaded = self._user.DataBase.updateConnectionMode(self._user.Id, self.Id, OFFLINE, ONLINE)
            self.setConnectionMode(loaded)
        else:
            pass
            # TODO: raise correct exception
        return url, sf.getSize(url)



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

from com.sun.star.ucb.NameClash import OVERWRITE

from com.sun.star.beans.PropertyAttribute import BOUND
from com.sun.star.beans.PropertyAttribute import CONSTRAINED
from com.sun.star.beans.PropertyAttribute import READONLY
from com.sun.star.beans.PropertyAttribute import TRANSIENT

from com.sun.star.container import XChild

from com.sun.star.lang import IllegalAccessException
from com.sun.star.lang import NoSupportException
from com.sun.star.lang import XComponent
from com.sun.star.lang import XServiceInfo

from com.sun.star.ucb import CommandAbortedException
from com.sun.star.ucb import IllegalIdentifierException
from com.sun.star.ucb import InteractiveBadTransferURLException
from com.sun.star.ucb import UnsupportedCommandException
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
from ..unotool import hasInterface

from .contentlib import CommandInfo
from .contentlib import Row
from .contentlib import DynamicResultSet

from .contenthelper import getCommandInfo
from .contenthelper import getContentEvent
from .contenthelper import getContentInfo
from .contenthelper import getInteractiveAugmentedIOException
from .contenthelper import getMimeType

from .identifier import Identifier

from .configuration import g_ucbprefix
from .configuration import g_ucbsuffix

import traceback


class Content(unohelper.Base,
              XServiceInfo,
              XContent,
              XComponent,
              XCommandProcessor2,
              XContentCreator,
              XChild,
              XPropertiesChangeNotifier):
    def __init__(self, ctx, user, authority, data, new=False):
        self._ctx = ctx
        self._user = user
        self._authority = authority
        self.MetaData = data
        self._new = new
        self._url = None
        self._listeners = []
        self._contentListeners = []
        self._propertiesListener = {}
        self._commandid = {}
        self._logger = user._logger
        self._commandInfo = self._getCommandInfo()
        self._propertySetInfo = self._getPropertySetInfo()
        self._services = ('com.sun.star.ucb.Content', )
        self._logger.logprb(INFO, 'Content', '__init__()', 601)

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
    def IsRenamed(self):
        return self.MetaData.get('Name') != self.Title
    @property
    def CanRename(self):
        return self.MetaData.get('CanRename') and not self.IsRenamed
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
    def Size(self):
        return self.MetaData.get('Size')
    @property
    def Link(self):
        return self.MetaData.get('Link')
    @property
    def Name(self):
        return self.MetaData.get('Name')
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

    @property
    def _identifier(self):
        return self._user.getContentIdentifier(self._authority, self.Path, self.Title)

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
        content = None
        try:
            if not self.IsRoot:
                content = self._user.getContentByParent(self._authority, self.ParentId, self.Path)
        except Exception as e:
            self._logger.logprb(SEVERE, 'Content', 'getParent()', 651, e, traceback.format_exc())
        return content

    def setParent(self, parent):
        raise NoSupportException('Parent can not be set', self)

    # XPropertiesChangeNotifier
    def addPropertiesChangeListener(self, names, listener):
        for name in names:
            if name not in self._propertiesListener:
                self._propertiesListener[name] = []
            listeners = self._propertiesListener[name]
            if listener not in listeners:
                listeners.append(listener)
    def removePropertiesChangeListener(self, names, listener):
        for name in names:
            if name in self._propertiesListener:
                listeners = self._propertiesListener[name]
                if listener in listeners:
                    listeners.remove(listener)

    # XContentCreator
    def queryCreatableContentsInfo(self):
        return self._getCreatableContentsInfo()
    def createNewContent(self, info):
        self._logger.logprb(INFO, 'Content', 'createNewContent()', 661, self._identifier)
        return self._user.createNewContent(self._authority, self.Id, self.Path, self.Title, info.Type)

    # XContent
    def getIdentifier(self):
        try:
            identifier = self._identifier
            self._logger.logprb(INFO, 'Content', 'getIdentifier()', 641, identifier)
            return Identifier(identifier)
        except Exception as e:
            self._logger.logprb(SEVERE, 'Content', 'getIdentifier()', 642, e, traceback.format_exc())

    def getContentType(self):
        return self.MetaData.get('ContentType')

    def addContentEventListener(self, listener):
        self._contentListeners.append(listener)

    def removeContentEventListener(self, listener):
        if listener in self._contentListeners:
            self._contentListeners.remove(listener)

    # XCommandProcessor2
    def createCommandIdentifier(self):
        return 1

    def execute(self, command, cmdid, environment):
        self._logger.logprb(INFO, 'Content', 'execute()', 631, command.Name, self._identifier)
        if command.Name == 'getCommandInfo':
            return CommandInfo(self._getCommandInfo())

        elif command.Name == 'getPropertySetInfo':
            return PropertySetInfo(self._propertySetInfo, self._logger)

        elif command.Name == 'getPropertyValues':
            values = self._getPropertiesValues(command.Argument)
            return Row(values)

        elif command.Name == 'setPropertyValues':
            return self._setPropertiesValues(environment, command.Argument)

        elif command.Name == 'delete':
            self.MetaData['Trashed'] = True
            self._user.updateContent(self.Id, 'Trashed', True)

        elif command.Name == 'open':
            if self.IsFolder:
                properties = command.Argument.Properties
                select = self._getFolderContent(properties)
                return DynamicResultSet(self._user, self._authority, select)
            elif self.IsDocument:
                sf = self._user.Provider.getSimpleFile()
                url, size = self._getDocumentContent(sf)
                if not size:
                    msg = self._logger.resolveString(632, self._identifier)
                    raise CommandAbortedException(msg, self)
                input = command.Argument.Sink
                isreadonly = self.MetaData.get('IsReadOnly')
                sink = hasInterface(input, 'com.sun.star.io.XActiveDataSink')
                stream = hasInterface(input, 'com.sun.star.io.XActiveDataStreamer')
                if not isreadonly and stream:
                    input.setStream(sf.openFileReadWrite(url))
                elif sink:
                    input.setInputStream(sf.openFileRead(url))

        elif command.Name == 'createNewContent' and self.IsFolder:
            return self.createNewContent(command.Argument)

        elif command.Name == 'insert':
            # The Insert command is only used to create a new folder or a new document
            # (ie: File Save As).
            # It saves the content created by 'createNewContent' from the parent folder
            # right after the Title property is initialized
            if self.IsDocument:
                sf = self._user.Provider.getSimpleFile()
                target = self._user.Provider.getTargetUrl(self.Id)
                replace = command.Argument.ReplaceExisting
                if sf.exists(target) and not replace:
                    return
                stream = command.Argument.Data
                if hasInterface(stream, 'com.sun.star.io.XInputStream'):
                    sf.writeFile(target, stream)
                    mimetype = command.Argument.MimeType
                    # For document type resources, the media type is always unknown...
                    mediatype = mimetype if mimetype else getMimeType(self._ctx, stream)
                    stream.closeInput()
                    self.MetaData['MediaType'] = mediatype

            if self._user.insertNewContent(self._authority, self.MetaData):
                # Need to consum the new Identifier if needed...
                self._user.deleteNewIdentifier(self.Id)

        elif command.Name == 'transfer':
            # see github/libreoffice/ucb/source/core/ucbcmds.cxx
            if not self.IsFolder:
                msg = self._logger.resolveString(633, self._identifier)
                UnsupportedCommandException(msg, self)
            newtitle = command.Argument.NewTitle
            source = command.Argument.SourceURL
            move = command.Argument.MoveData
            clash = command.Argument.NameClash
            mimetype = command.Argument.MimeType
            # Transfer command is used for document 'File Save' or 'File Save As'
            # NewTitle come from:
            # - Last segment path of 'XContent.getIdentifier().getContentIdentifier()' for OpenOffice
            # - Property 'Title' of 'XContent' for LibreOffice
            # If the content has been renamed, the last segment is the new Title of the content
            # We check if 'NewTitle' is a child of this folder by recovering its ItemId
            itemid = self._user.getChildId(self.Id, self.Path, self.Title, newtitle)
            if itemid is None or clash != OVERWRITE:
                # ItemId could not be found: 'NewTitle' does not exist in the folder...
                # or NewTitle exist but we don't have the OVERWRITE flag set...
                # When saving a new document with (File save) or when creating 
                # a new document with (File Save As) we use commands:
                # - createNewContent: for creating an empty new Content
                # - Insert at new Content for committing change
                # To execute these commands, we must throw an exception
                msg = self._logger.resolveString(634, source, self._identifier)
                raise InteractiveBadTransferURLException(msg, self)
            sf = self._user.Provider.getSimpleFile()
            if not sf.exists(source):
                raise CommandAbortedException("Error while saving file: %s" % source, self)
            inputstream = sf.openFileRead(source)
            target = self._user.Provider.getTargetUrl(itemid)
            sf.writeFile(target, inputstream)
            inputstream.closeInput()
            # We need to update the Size
            size = sf.getSize(target)
            self._logger.logprb(INFO, 'Content', 'execute()', 635, self._identifier, size)
            self._user.updateContent(itemid, 'Size', size)
            if move:
                # TODO: must delete object
                pass 

        elif command.Name == 'flush':
            pass

    def abort(self, id):
        pass
    def releaseCommandIdentifier(self, id):
        pass

    def getContentListeners(self):
        return self._contentListeners

    # Private methods
    def _isNew(self):
        return self._new

    def _getCreatableContentsInfo(self):
        return self._user.getCreatableContentsInfo(self.CanAddChild) if self.IsFolder else ()

    def _getPropertiesValues(self, properties):
        values = []
        for property in properties:
            value = None
            if (property.Name in self._propertySetInfo):
                value, level, msg = self._getPropertyValue(property.Name)
            else:
                msg = "ERROR: Requested property: %s is not available" % property.Name
                print(msg)
                level = SEVERE
            if msg:
                self._logger.logp(level, 'Content', '_getPropertiesValues()', msg)
            values.append(getNamedValue(property.Name, value))
        return tuple(values)

    def _getPropertyValue(self, name):
        msg = ''
        value = None
        level = INFO
        # Dynamic values
        if name == 'CasePreservingURL':
            value = ''
        elif name == 'CreatableContentsInfo':
            value = self._getCreatableContentsInfo()
        elif name in self.MetaData:
            value = self.MetaData.get(name)
            msg = "Name: %s - Value: %s" % (name, value)
        else:
            msg = "ERROR: Requested property: %s is not available" % name
            print(msg)
            level = SEVERE
        return value, level, msg

    def _setPropertiesValues(self, environment, properties):
        results = []
        for property in properties:
            if (property.Name in self._propertySetInfo):
                result, level, msg = self._setPropertyValue(environment, property.Name, property.Value)
            else:
                msg = "ERROR: Requested property: %s is not available" % property.Name
                print(msg)
                level = SEVERE
                error = UnknownPropertyException(msg, self)
                result = uno.Any('com.sun.star.beans.UnknownPropertyException', error)
            if msg:
                self._logger.logp(level, 'Content', '_setPropertiesValues()', msg)
            results.append(result)
        return tuple(results)

    def _setPropertyValue(self, environment, name, value):
        if self._propertySetInfo.get(name).Attributes & READONLY:
            msg = "ERROR: Requested property: %s is READONLY" % name
            print(msg)
            level = SEVERE
            error = IllegalAccessException(msg, self)
            result = uno.Any('com.sun.star.lang.IllegalAccessException', error)
        else:
            result, level, msg = self._setProperty(environment, name, value)
        return result, level, msg

    def _setProperty(self, environment, name, value):
        if name == 'Title':
            result, level, msg = self._setTitle(environment, value)
        elif name == 'CasePreservingURL':
            msg = ""
            level = INFO
            result = None
        elif name == 'CreatableContentsInfo':
            msg = ""
            level = INFO
            result = None
        elif name in self.MetaData:
            self.MetaData[name] = value
            msg = "Content: %s set property: %s value: %s" % (self._identifier, name, value)
            level = INFO
            result = None
        else:
            msg = "ERROR: Requested property: %s is unknown" % name
            print(msg)
            level = SEVERE
            error = IllegalAccessException(msg, self)
            result = uno.Any('com.sun.star.lang.IllegalAccessException', error)
        return result, level, msg

    def _setTitle(self, environment, newtitle):
        if len(newtitle) == 0:
            msg = "ERROR: Requested property: Title value is EMPTY"
            level = SEVERE
            error = IllegalAccessException(msg, self)
            result = uno.Any('com.sun.star.lang.IllegalAccessException', error)
        elif self.Title != self.MetaData.get('Name'):
            msg = "ERROR: Requested property: Title can't be changed"
            level = SEVERE
            error = IllegalAccessException(msg, self)
            result = uno.Any('com.sun.star.lang.IllegalAccessException', error)
        elif self._user.DataBase.hasTitle(self._user.Id, self.ParentId, newtitle):
            msg = "ERROR: Requested property: Title duplicate name clash"
            level = SEVERE
            error = IllegalAccessException(msg, self)
            result = uno.Any('com.sun.star.lang.IllegalAccessException', error)
        else:
            self.MetaData['Name'] = newtitle
            self.MetaData['Title'] = newtitle
            # If the identifier is new then the content is not yet in the database.
            # It will be inserted by the insert command of the XCommandProcessor2.execute()
            # But we must make this content accessible by an appropriate entry in the user paths cache
            if not self._isNew():
                self._user.updateContent(self.Id, 'Name', newtitle)
            msg = "Set property: %s value: %s" % ('Title', newtitle)
            level = INFO
            result = None
        return result, level, msg

    def _getFolderContent(self, properties):
        select, updated = self._updateFolderContent(properties)
        if updated:
            loaded = self._user.updateConnectionMode(self.Id, OFFLINE)
            self.setConnectionMode(loaded)
        return select

    def _updateFolderContent(self, properties):
        updated = False
        if ONLINE == self.ConnectionMode == self._user.SessionMode:
            self._logger.logprb(INFO, 'Content', '_updateFolderContent()', 621, self._identifier)
            updated = self._user.Provider.updateFolderContent(self)
        select = self._user.getChildren(self._authority, self.Path, self.Title, properties)
        return select, updated

    def _getDocumentContent(self, sf):
        size = 0
        url = self._user.Provider.getTargetUrl(self.Id)
        if self.ConnectionMode == OFFLINE and sf.exists(url):
            return url, sf.getSize(url)
        if self._user.Provider.getDocumentContent(self, url):
            loaded = self._user.updateConnectionMode(self.Id, OFFLINE)
            self.setConnectionMode(loaded)
        else:
            pass
            # TODO: raise correct exception
        return url, sf.getSize(url)

    def _getCommandInfo(self):
        commands = {}
        if self.CanAddChild:
            commands['createNewContent'] =    getCommandInfo('createNewContent',   'com.sun.star.ucb.ContentInfo')
        if not self.IsRoot:
            commands['delete'] =              getCommandInfo('delete',             'boolean')
        commands['flush'] =                   getCommandInfo('flush')
        commands['getCommandInfo'] =          getCommandInfo('getCommandInfo',     'com.sun.star.ucb.XCommandInfo')
        commands['getPropertySetInfo'] =      getCommandInfo('getPropertySetInfo', 'com.sun.star.beans.XPropertySetInfo')
        commands['getPropertyValues'] =       getCommandInfo('getPropertyValues',  '[]com.sun.star.beans.Property')
        commands['insert'] =                  getCommandInfo('insert',             'com.sun.star.ucb.InsertCommandArgument2')
        commands['open'] =                    getCommandInfo('open',               'com.sun.star.ucb.OpenCommandArgument3')
        commands['setPropertyValues'] =       getCommandInfo('setPropertyValues',  '[]com.sun.star.beans.PropertyValue')
        if self.IsFolder:
            commands['transfer'] =            getCommandInfo('transfer',           'com.sun.star.ucb.TransferInfo2')
        return commands

    def _getPropertySetInfo(self):
        RO = 0 if self._isNew() else READONLY
        properties = {}
        # XXX: Although CasePreservingURL is not used, the presence of this property is necessary for LibreOffice to save files correctly.
        properties['CasePreservingURL'] =     getProperty('CasePreservingURL',     'string',                               BOUND | RO)
        properties['ConnectionMode'] =        getProperty('ConnectionMode',        'short',                                BOUND | READONLY)
        properties['ContentType'] =           getProperty('ContentType',           'string',                               BOUND | RO)
        properties['CreatableContentsInfo'] = getProperty('CreatableContentsInfo', '[]com.sun.star.ucb.ContentInfo',       BOUND | RO)
        properties['DateCreated'] =           getProperty('DateCreated',           'com.sun.star.util.DateTime',           BOUND | READONLY)
        properties['DateModified'] =          getProperty('DateModified',          'com.sun.star.util.DateTime',           BOUND | RO)
        properties['IsCompactDisc'] =         getProperty('IsCompactDisc',         'boolean',                              BOUND | RO)
        properties['IsDocument'] =            getProperty('IsDocument',            'boolean',                              BOUND | RO)
        properties['IsFloppy'] =              getProperty('IsFloppy',              'boolean',                              BOUND | RO)
        properties['IsFolder'] =              getProperty('IsFolder',              'boolean',                              BOUND | RO)
        properties['IsHidden'] =              getProperty('IsHidden',              'boolean',                              BOUND | RO)
        properties['IsReadOnly'] =            getProperty('IsReadOnly',            'boolean',                              BOUND | RO)
        properties['IsRemote'] =              getProperty('IsRemote',              'boolean',                              BOUND | RO)
        properties['IsRemoveable'] =          getProperty('IsRemoveable',          'boolean',                              BOUND | RO)
        properties['IsVersionable'] =         getProperty('IsVersionable',         'boolean',                              BOUND | RO)
        properties['IsVolume'] =              getProperty('IsVolume',              'boolean',                              BOUND | RO)
        properties['MediaType'] =             getProperty('MediaType',             'string',                               BOUND | READONLY)
        properties['Size'] =                  getProperty('Size',                  'hyper',                                BOUND | RO)
        properties['Title'] =                 getProperty('Title',                 'string',                               BOUND | CONSTRAINED)
        return properties


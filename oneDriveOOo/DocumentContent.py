#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.awt import XCallback
from com.sun.star.container import XChild
from com.sun.star.lang import NoSupportException
from com.sun.star.lang import XServiceInfo
from com.sun.star.ucb import CommandAbortedException
from com.sun.star.ucb import XContent
from com.sun.star.ucb import XCommandProcessor2
from com.sun.star.ucb.ConnectionMode import OFFLINE
from com.sun.star.ucb.ContentAction import INSERTED
from com.sun.star.ucb.ContentAction import EXCHANGED

try:
    from clouducp import CommandInfo
    from clouducp import CommandInfoChangeNotifier
    from clouducp import Initialization
    from clouducp import PropertiesChangeNotifier
    from clouducp import PropertyContainer
    from clouducp import PropertySetInfo
    from clouducp import PropertySetInfoChangeNotifier
    from clouducp import Row
    from clouducp import getCommandInfo
    from clouducp import getContentEvent
    from clouducp import getLogger
    from clouducp import getMimeType
    from clouducp import getPropertiesValues
    from clouducp import getProperty
    from clouducp import getSimpleFile
    from clouducp import getUcb
    from clouducp import getUcp
    from clouducp import propertyChange
    from clouducp import setPropertiesValues
    from clouducp import CREATED
    from clouducp import FILE
except ImportError:
    from onedrive import CommandInfo
    from onedrive import CommandInfoChangeNotifier
    from onedrive import Initialization
    from onedrive import PropertiesChangeNotifier
    from onedrive import PropertyContainer
    from onedrive import PropertySetInfo
    from onedrive import PropertySetInfoChangeNotifier
    from onedrive import Row
    from onedrive import getCommandInfo
    from onedrive import getContentEvent
    from onedrive import getLogger
    from onedrive import getMimeType
    from onedrive import getPropertiesValues
    from onedrive import getProperty
    from onedrive import getSimpleFile
    from onedrive import getUcb
    from onedrive import getUcp
    from onedrive import propertyChange
    from onedrive import setPropertiesValues
    from onedrive import CREATED
    from onedrive import FILE

from onedrive import parseDateTime
from onedrive import g_doc_map
from onedrive import g_plugin


# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = '%s.DocumentContent' % g_plugin


class DocumentContent(unohelper.Base,
                      XServiceInfo,
                      XContent,
                      XChild,
                      XCommandProcessor2,
                      XCallback,
                      CommandInfoChangeNotifier,
                      Initialization,
                      PropertiesChangeNotifier,
                      PropertyContainer,
                      PropertySetInfoChangeNotifier):
    def __init__(self, ctx, *namedvalues):
        self.ctx = ctx
        self.Logger = getLogger(self.ctx)
        level = uno.getConstantByName("com.sun.star.logging.LogLevel.INFO")
        msg = "DriveDocumentContent loading ..."
        self.Logger.logp(level, "DriveDocumentContent", "__init__()", msg)
        self.Identifier = None

        self.ContentType = 'application/vnd.google-apps.document'
        self.Name = 'Sans Nom'
        self.IsFolder = False
        self.IsDocument = True
        self.DateCreated = parseDateTime()
        self.DateModified = parseDateTime()
        self._Trashed = False

        self.CanAddChild = False
        self.CanRename = True
        self.IsReadOnly = False
        self.IsVersionable = False
        self._Loaded = 1

        self.IsHidden = False
        self.IsVolume = False
        self.IsRemote = False
        self.IsRemoveable = False
        self.IsFloppy = False
        self.IsCompactDisc = False

        self.listeners = []
        self.contentListeners = []
        self.propertiesListener = {}
        self.propertyInfoListeners = []
        self.commandInfoListeners = []

        self.typeMaps = g_doc_map

        self.initialize(namedvalues)
        
        self._commandInfo = self._getCommandInfo()
        self._propertySetInfo = self._getPropertySetInfo()

        identifier = self.getIdentifier()
        self.ObjectId = identifier.Id
        self.TargetURL = identifier.getContentIdentifier()
        self.BaseURI = identifier.BaseURL
        msg = "DriveDocumentContent loading Uri: %s ... Done" % identifier.getContentIdentifier()
        self.Logger.logp(level, "DriveDocumentContent", "__init__()", msg)

    @property
    def UserName(self):
        return self.getIdentifier().User.Name
    @property
    def TitleOnServer(self):
        # LibreOffice specifique property
        return self.Name
    @property
    def Title(self):
        # LibreOffice use this property for 'transfer command' in 'command.Argument.NewTitle'
        return self.getIdentifier().Title
    @Title.setter
    def Title(self, title):
        identifier = self.getIdentifier()
        old = self.Name
        self.Name = title
        propertyChange(self, 'Name', old, title)
        event = getContentEvent(self, EXCHANGED, self, identifier)
        self.notify(event)
    @property
    def Size(self):
        return 0
    @Size.setter
    def Size(self, size):
        propertyChange(self, 'Size', 0, 0)
    @property
    def Trashed(self):
        return self._Trashed
    @Trashed.setter
    def Trashed(self, trashed):
        propertyChange(self, 'Trashed', self._Trashed, trashed)
        self._Trashed = trashed
    @property
    def MimeType(self):
        return self.getIdentifier().MimeType
    @MimeType.setter
    def MimeType(self, mimetype):
        self.getIdentifier().MimeType = self.typeMaps.get(mimetype)
    @property
    def MediaType(self):
        return self.getIdentifier().MimeType
    @property
    def Loaded(self):
        return self._Loaded
    @Loaded.setter
    def Loaded(self, loaded):
        propertyChange(self, 'Loaded', self._Loaded, loaded)
        self._Loaded = loaded
    @property
    def CasePreservingURL(self):
        return self.getIdentifier().getContentIdentifier()
    @CasePreservingURL.setter
    def CasePreservingURL(self, url):
        pass
    @property
    def CreatableContentsInfo(self):
        return ()
    @CreatableContentsInfo.setter
    def CreatableContentsInfo(self, contentinfo):
        pass

    # XCallback
    def notify(self, event):
        for listener in self.contentListeners:
            listener.contentEvent(event)

    # XChild
    def getParent(self):
        return getUcb(self.ctx).queryContent(self.getIdentifier().getParent())
    def setParent(self, parent):
        raise NoSupportException('Parent can not be set', self)

    # XContent
    def getIdentifier(self):
        return self.Identifier
    def getContentType(self):
        return self.ContentType
    def addContentEventListener(self, listener):
        if listener not in self.contentListeners:
            self.contentListeners.append(listener)
    def removeContentEventListener(self, listener):
        if listener in self.contentListeners:
            self.contentListeners.remove(listener)

    # XCommandProcessor2
    def createCommandIdentifier(self):
        return 0
    def execute(self, command, id, environment):
        result = None
        level = uno.getConstantByName("com.sun.star.logging.LogLevel.INFO")
        msg = "Command name: %s ..." % command.Name
        if command.Name == 'getCommandInfo':
            result = CommandInfo(self._commandInfo)
        elif command.Name == 'getPropertySetInfo':
            result = PropertySetInfo(self._propertySetInfo)
        elif command.Name == 'getPropertyValues':
            namedvalues = getPropertiesValues(self, command.Argument, self.Logger)
            result = Row(namedvalues)
        elif command.Name == 'setPropertyValues':
            result = setPropertiesValues(self, environment, command.Argument, self._propertySetInfo, self.Logger)
        elif command.Name == 'open':
            sf = getSimpleFile(self.ctx)
            url = self._getUrl(sf)
            if url is None:
                raise CommandAbortedException("Error while downloading file: %s" % self.Name, self)
            sink = command.Argument.Sink
            stream = uno.getTypeByName('com.sun.star.io.XActiveDataStreamer')
            if sink.queryInterface(uno.getTypeByName('com.sun.star.io.XActiveDataSink')):
                msg += " ReadOnly mode selected ..."
                sink.setInputStream(sf.openFileRead(url))
            elif not self.IsReadOnly and sink.queryInterface(stream):
                msg += " ReadWrite mode selected ..."
                sink.setStream(sf.openFileReadWrite(url))
        elif command.Name == 'insert':
            # The Insert command is only used to create a new document (File Save As)
            # it saves content from createNewContent from the parent folder
            print("DriveDocumentContent.execute(): insert %s" % command.Argument)
            identifier = self.getIdentifier()
            stream = command.Argument.Data
            sf = getSimpleFile(self.ctx)
            target = '%s/%s' % (identifier.SourceURL, identifier.Id)
            if sf.exists(target) and not command.Argument.ReplaceExisting:
                pass
            elif stream.queryInterface(uno.getTypeByName('com.sun.star.io.XInputStream')):
                ucp = getUcp(self.ctx, identifier.getContentProviderScheme())
                sf.writeFile(target, stream)
                self.MimeType = getMimeType(self.ctx, stream)
                stream.closeInput()
                self.Size = sf.getSize(target)
                self.addPropertiesChangeListener(('Id', 'Name', 'Size', 'Trashed', 'Loaded'), ucp)
                propertyChange(self, 'Id', identifier.Id, CREATED | FILE)
                parent = identifier.getParent()
                event = getContentEvent(self, INSERTED, self, parent)
                ucp.queryContent(parent).notify(event)
        elif command.Name == 'delete':
            print("DriveDocumentContent.execute(): delete")
            self.Trashed = True
        msg += " Done"
        self.Logger.logp(level, "DriveOfficeContent", "execute()", msg)
        return result
    def abort(self, id):
        pass
    def releaseCommandIdentifier(self, id):
        pass

    def _setMimeType(self, mimetype):
        for k,v in self.typeMaps.items():
            if v == mimetype:
                self.MimeType = k
                return
        self.MimeType = mimetype

    def _getUrl(self, sf):
        identifier = self.getIdentifier()
        url = '%s/%s' % (identifier.SourceURL, identifier.Id)
        if self.Loaded == OFFLINE and sf.exists(url):
            return url
        try:
            stream = identifier.createInputStream()
            sf.writeFile(url, stream)
        except:
            return None
        else:
            self.Loaded = OFFLINE
        finally:
            stream.closeInput()
        return url

    def _getCommandInfo(self):
        commands = {}
        commands['getCommandInfo'] = getCommandInfo('getCommandInfo')
        commands['getPropertySetInfo'] = getCommandInfo('getPropertySetInfo')
        commands['getPropertyValues'] = getCommandInfo('getPropertyValues', '[]com.sun.star.beans.Property')
        commands['setPropertyValues'] = getCommandInfo('setPropertyValues', '[]com.sun.star.beans.PropertyValue')
        commands['open'] = getCommandInfo('open', 'com.sun.star.ucb.OpenCommandArgument2')
        commands['insert'] = getCommandInfo('insert', 'com.sun.star.ucb.InsertCommandArgument')
        commands['delete'] = getCommandInfo('delete', 'boolean')
        return commands

    def _getPropertySetInfo(self):
        properties = {}
        bound = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.BOUND')
        constrained = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.CONSTRAINED')
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        ro = 0 if self.getIdentifier().IsNew else readonly
        properties['ContentType'] = getProperty('ContentType', 'string', bound | ro)
        properties['MimeType'] = getProperty('MimeType', 'string', bound | readonly)
        properties['MediaType'] = getProperty('MediaType', 'string', bound | readonly)
        properties['IsDocument'] = getProperty('IsDocument', 'boolean', bound | ro)
        properties['IsFolder'] = getProperty('IsFolder', 'boolean', bound | ro)
        properties['Title'] = getProperty('Title', 'string', bound | constrained)
        properties['Size'] = getProperty('Size', 'long', bound)
        properties['DateModified'] = getProperty('DateModified', 'com.sun.star.util.DateTime', bound | ro)
        properties['DateCreated'] = getProperty('DateCreated', 'com.sun.star.util.DateTime', bound | readonly)
        properties['IsReadOnly'] = getProperty('IsReadOnly', 'boolean', bound | ro)
        properties['Loaded'] = getProperty('Loaded', 'long', bound)

        properties['BaseURI'] = getProperty('BaseURI', 'string', bound | readonly)
        properties['TargetURL'] = getProperty('TargetURL', 'string', bound | readonly)
        properties['TitleOnServer'] = getProperty('TitleOnServer', 'string', bound)

        properties['ObjectId'] = getProperty('ObjectId', 'string', bound | readonly)
        properties['CasePreservingURL'] = getProperty('CasePreservingURL', 'string', bound)
        properties['CreatableContentsInfo'] = getProperty('CreatableContentsInfo', '[]com.sun.star.ucb.ContentInfo', bound)

        properties['IsHidden'] = getProperty('IsHidden', 'boolean', bound | ro)
        properties['IsVolume'] = getProperty('IsVolume', 'boolean', bound | ro)
        properties['IsRemote'] = getProperty('IsRemote', 'boolean', bound | ro)
        properties['IsRemoveable'] = getProperty('IsRemoveable', 'boolean', bound | ro)
        properties['IsFloppy'] = getProperty('IsFloppy', 'boolean', bound | ro)
        properties['IsCompactDisc'] = getProperty('IsCompactDisc', 'boolean', bound | ro)
        return properties

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(DocumentContent,                                                    # UNO object class
                                         g_ImplementationName,                                               # Implementation name
                                        (g_ImplementationName, 'com.sun.star.ucb.Content'))                  # List of implemented services

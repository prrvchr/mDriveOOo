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

from com.sun.star.awt import Point
from com.sun.star.awt import Rectangle
from com.sun.star.awt import Size

from com.sun.star.awt.PosSize import POSSIZE
from com.sun.star.awt.PosSize import SIZE

from com.sun.star.awt.MessageBoxType import ERRORBOX

from com.sun.star.awt.WindowAttribute import SHOW
from com.sun.star.awt.WindowAttribute import MINSIZE
from com.sun.star.awt.WindowAttribute import BORDER
from com.sun.star.awt.WindowAttribute import MOVEABLE
from com.sun.star.awt.WindowAttribute import CLOSEABLE
from com.sun.star.awt.WindowAttribute import NODECORATION

from com.sun.star.awt.WindowClass import TOP
from com.sun.star.awt.WindowClass import CONTAINER

from com.sun.star.beans.PropertyState import DIRECT_VALUE

from com.sun.star.connection import NoConnectException

from com.sun.star.document.MacroExecMode import ALWAYS_EXECUTE_NO_WARN

from com.sun.star.frame.FrameSearchFlag import GLOBAL
from com.sun.star.frame.DispatchResultState import SUCCESS

from com.sun.star.lang import WrappedTargetRuntimeException

from com.sun.star.ucb.ConnectionMode import ONLINE
from com.sun.star.ucb.ConnectionMode import OFFLINE

from com.sun.star.ui.dialogs.ExecutableDialogResults import OK

from com.sun.star.util.MeasureUnit import APPFONT

import binascii
import datetime
import operator
from packaging.version import Version
import socket
import traceback


def checkInternet(host="8.8.8.8", port=53, timeout=3):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
        return True
    except (OSError, socket.timeout):
        return False

def checkVersion(version, minimum, op=operator.ge):
    if not version or not minimum:
        return False
    try:
        return op(Version(version), Version(minimum))
    except InvalidVersion:
        return False

def getConnectionMode(ctx, host, port=80):
    connector = getConnector(ctx)
    try:
        connection = connector.connect('socket,host=%s,port=%s' % (host, port))
    except NoConnectException:
        mode = OFFLINE
    else:
        try:
            connection.close()
        except:
            pass
        mode = ONLINE
    return mode

def getConnector(ctx):
    return createService(ctx, 'com.sun.star.connection.Connector')

def getDriverManager(ctx):
    return createService(ctx, 'com.sun.star.sdbc.DriverManager')

def getDesktop(ctx):
    return createService(ctx, 'com.sun.star.frame.Desktop')

def getDispatcher(ctx):
    return createService(ctx, 'com.sun.star.frame.DispatchHelper')

def getToolKit(ctx):
    return createService(ctx, 'com.sun.star.awt.Toolkit')

def getSimpleFile(ctx):
    return createService(ctx, 'com.sun.star.ucb.SimpleFileAccess')

def getFilePicker(ctx):
    return createService(ctx, 'com.sun.star.ui.dialogs.FilePicker')

def getUriFactory(ctx):
    return createService(ctx, 'com.sun.star.uri.UriReferenceFactory')

def getTempFile(ctx):
    return createService(ctx, 'com.sun.star.io.TempFile')

def getTypeDetection(ctx):
    return createService(ctx, 'com.sun.star.document.TypeDetection')

def getPathSettings(ctx):
    return createService(ctx, 'com.sun.star.util.PathSettings')

def getUrlTransformer(ctx):
    return createService(ctx, 'com.sun.star.util.URLTransformer')

def getSystemClipboard(ctx):
    return createService(ctx, 'com.sun.star.datatransfer.clipboard.SystemClipboard')

def getInteractionHandler(ctx):
    return createService(ctx, 'com.sun.star.task.InteractionHandler')

def getMailMerge(ctx):
    return createService(ctx, 'com.sun.star.text.MailMerge')

def getMri(ctx):
    return createService(ctx, 'mytools.Mri')

def getCallBack(ctx):
    return createService(ctx, 'com.sun.star.awt.AsyncCallback')

def getRowSet(ctx):
    return createService(ctx, 'com.sun.star.sdb.RowSet')

def getSequenceInputStream(ctx, sequence):
    service = 'com.sun.star.io.SequenceInputStream'
    return createService(ctx, service, sequence)

def getMimeTypeFactory(ctx):
    return createService(ctx, 'com.sun.star.datatransfer.MimeContentTypeFactory')

def getUrlPresentation(ctx, location, password=False):
    url = uno.createUnoStruct('com.sun.star.util.URL')
    url.Complete = location
    return getUrlTransformer(ctx).getPresentation(url, password)

def getUrl(ctx, location, protocol=None):
    transformer = getUrlTransformer(ctx)
    return parseUrl(transformer, location, protocol)

def parseUrl(transformer, location, protocol=None):
    url = uno.createUnoStruct('com.sun.star.util.URL')
    url.Complete = location
    if protocol is None:
        success, url = transformer.parseStrict(url)
    else:
        success, url = transformer.parseSmart(url, protocol)
    return url if success else None

def getDocument(ctx, url, readonly=True):
    # XXX: ReadOnly: documents opened for mailing are opened readonly because they must
    # XXX: be opened as a new document and this document could be open already
    # XXX: OpenNewView: always open a new document because it must be disposed afterwards.
    # XXX: Hidden: mailing is done in a hidden view
    # XXX: Silence: load document for mailing without user interaction
    arguments = {'ReadOnly': readonly, 'OpenNewView': True, 'Hidden': True, 'Silence': True}
    descriptor = getPropertyValueSet(arguments)
    document = getDesktop(ctx).loadComponentFromURL(url, '_blank', 0, descriptor)
    return document

def hasStartupJob(ctx, job):
    config = getConfiguration(ctx, '/org.openoffice.Office.Jobs/Events/OnStartApp/JobList')
    return config.hasByName(job)

def registerStartupJob(ctx, job):
    config = getConfiguration(ctx, '/org.openoffice.Office.Jobs/Events/OnStartApp/JobList', True)
    if not config.hasByName(job):
        config.insertByName(job, config.createInstance())
        config.commitChanges()

def deregisterStartupJob(ctx, job):
    config = getConfiguration(ctx, '/org.openoffice.Office.Jobs/Events/OnStartApp/JobList', True)
    if config.hasByName(job):
        config.removeByName(job)
        config.commitChanges()

def getExceptionMessage(exception):
    messages = []
    if hasattr(exception, 'args'):
        messages = [arg for arg in exception.args if isinstance(arg, str)]
    count = len(messages)
    if count == 0:
        try:
            message = str(exception)
        except UnicodeDecodeError:
            message = repr(exception)
    elif count == 1:
        message = messages[0]
    else:
        message = max(messages, key=len)
    if isinstance(message, bytes):
        message = message.decode('utf-8')
    message = ' '.join(message.split())
    return message

def getFileSequence(ctx, url, default=None):
    path = None
    fs = getSimpleFile(ctx)
    if fs.exists(url):
        path = url
    elif default is not None and fs.exists(default):
        path = default
    if path is None:
        sequence = uno.ByteSequence(b'')
    else:
        sequence = getStreamSequence(fs.openFileRead(path))
    return len(sequence), sequence

def getPathSubstitution(ctx, path):
     pathsubstitution = createService(ctx, 'com.sun.star.util.PathSubstitution')
     return pathsubstitution.substituteVariables(path, True)

def getStreamSequence(stream, chunk=64*1024):
    close = False
    sequence = uno.ByteSequence(b'')
    while not close:
        count, buffer = stream.readBytes(None, chunk)
        close = count != chunk
        sequence += buffer
    stream.closeInput()
    return sequence

def hasInterface(component, interface):
    for t in getComponentTypes(component):
        if t.typeName == interface:
            return True
    return False

def hasFrameInterface(component):
    frame = 'com.sun.star.frame.XFrame2'
    desktop = 'com.sun.star.frame.XDesktop2'
    return hasInterface(component, frame) or hasInterface(component, desktop)

def hasService(ctx, name):
    service = createService(ctx, name)
    return service is not None

def getComponentTypes(component):
    try:
        return component.getTypes()
    except:
        return ()

def getInterfaceNames(component):
    return (t.typeName for t in getComponentTypes(component))

def getInterfaceTypes(component):
    return getComponentTypes(component)

def getProperty(name, type=None, attributes=None, handle=-1):
    property = uno.createUnoStruct('com.sun.star.beans.Property')
    property.Name = name
    property.Handle = handle
    if isinstance(type, uno.Type):
        property.Type = type
    elif type is not None:
        property.Type = uno.getTypeByName(type)
    if attributes is not None:
        property.Attributes = attributes
    return property

def getExtensionVersion(ctx, extension):
    service = '/singletons/com.sun.star.deployment.PackageInformationProvider'
    provider = ctx.getValueByName(service)
    for name, version in provider.getExtensionList():
        if name == extension:
            return version
    return None

def getLastNamedParts(name, sep='.'):
    part1, sep, part2 = name.rpartition(sep)
    if not sep:
        part1, part2 = part2, None
    return part1, part2

def getLibreOfficeInfo(ctx):
    config = getConfiguration(ctx, '/org.openoffice.Setup/Product')
    name = config.getByName('ooName')
    version = config.getByName('ooSetupVersion')
    return name, version

def getLibreOfficeVersion(ctx):
    version = getConfiguration(ctx, '/org.openoffice.Setup/Product').getByName('ooSetupVersion')
    return version

def getResourceLocation(ctx, identifier, path=None):
    service = '/singletons/com.sun.star.deployment.PackageInformationProvider'
    provider = ctx.getValueByName(service)
    location = provider.getPackageLocation(identifier)
    if path is not None:
        location += '/%s' % path
    return location

def getConfiguration(ctx, path, update=False, language=None):
    service = 'com.sun.star.configuration.ConfigurationProvider'
    provider = createService(ctx, service)
    service = 'com.sun.star.configuration.Configuration'
    service += 'UpdateAccess' if update else 'Access'
    nodepath = uno.createUnoStruct('com.sun.star.beans.NamedValue')
    nodepath.Name = 'nodepath'
    nodepath.Value = path
    if language is None:
        arguments = (nodepath, )
    else:
        locale = uno.createUnoStruct('com.sun.star.beans.NamedValue')
        locale.Name = 'Locale'
        locale.Value = language
        arguments = (nodepath, locale)
    return provider.createInstanceWithArguments(service, arguments)

def getCurrentLocale(ctx):
    nodepath = '/org.openoffice.Setup/L10N'
    parts = getConfiguration(ctx, nodepath).getByName('ooLocale').split('-')
    locale = uno.createUnoStruct('com.sun.star.lang.Locale', parts[0], '', '')
    if len(parts) > 1:
        locale.Country = parts[1]
    else:
        service = createService(ctx, 'com.sun.star.i18n.LocaleData')
        locale.Country = service.getLanguageCountryInfo(locale).Country
    return locale

def getStringResource(ctx, identifier, path=None, filename='DialogStrings', locale=None):
    url = getResourceLocation(ctx, identifier, path)
    return getStringResourceWithLocation(ctx, url, filename, locale)

def getStringResourceWithLocation(ctx, url, filename, locale=None):
    service = 'com.sun.star.resource.StringResourceWithLocation'
    if locale is None:
        locale = getCurrentLocale(ctx)
    handler = getInteractionHandler(ctx)
    args = (url, True, locale, filename, '', handler)
    return createService(ctx, service, *args)

def generateUuid():
    return binascii.hexlify(uno.generateUuid().value).decode('utf-8')

def setProgress(callback, caller, value):
    data = {'call': 'progress', 'value': value}
    callback.addCallback(caller, getNamedValueSet(data))

def getDialog(ctx, identifier, xdl, handler=None, parent=None):
    dialog = None
    provider = createService(ctx, 'com.sun.star.awt.DialogProvider2')
    url = getDialogUrl(identifier, xdl)
    if handler and parent:
        properties = getNamedValueSet({'ParentWindow': parent, 'EventHandler': handler})
        dialog = provider.createDialogWithArguments(url, properties)
    else:
        if handler:
            dialog = provider.createDialogWithHandler(url, handler)
        else:
            dialog = provider.createDialog(url)
        toolkit = getToolKit(ctx)
        dialog.createPeer(toolkit, toolkit.getDesktopWindow())
    return dialog

def findFrame(ctx, name, flags=GLOBAL):
    return getDesktop(ctx).findFrame(name, flags)

def getDialogPosSize(ctx, extension, xdl, point=None, unit=APPFONT):
    dialog = getDialog(ctx, extension, xdl)
    size = dialog.convertSizeToPixel(Size(dialog.Model.Width, dialog.Model.Height), unit)
    dialog.dispose()
    if point is None:
        point = Point(0, 0)
    return Rectangle(point.X, point.Y, size.Width, size.Height)

def getTopWindow(ctx, name, rectangle=None, parent=None, modal=TOP, attrs=BORDER | MOVEABLE | CLOSEABLE | NODECORATION):
    descriptor = uno.createUnoStruct('com.sun.star.awt.WindowDescriptor')
    descriptor.Type = modal
    descriptor.WindowServiceName = 'window'
    if parent:
        descriptor.Parent = parent
    else:
        descriptor.ParentIndex = -1
    if rectangle:
        attrs |= SHOW
        descriptor.Bounds = rectangle
    descriptor.WindowAttributes = attrs
    # XXX: We use the TaskCreator UNO service instead of Frame
    # XXX: in order to be able to assign a title to the window.
    service = 'com.sun.star.frame.TaskCreator'
    arguments = {'FrameName': name, 'ContainerWindow': getToolKit(ctx).createWindow(descriptor)}
    frame = createService(ctx, service).createInstanceWithArguments(getNamedValueSet(arguments))
    getDesktop(ctx).getFrames().append(frame)
    return frame

def getDialogPosition(dialog, window):
    size = window.getPosSize()
    pos = dialog.convertPointToLogic(Point(size.X, size.Y), APPFONT)
    x = dialog.Model.PositionX + pos.X
    y = dialog.Model.PositionY + pos.Y
    return Point(x, y)

def setDialogPosition(ctx, dialog, window, point, titlebar=9):
    x, y = _getPosition(ctx, dialog, point)
    size = window.getPosSize()
    pos = dialog.convertPointToLogic(Point(size.X, size.Y), APPFONT)
    dialog.Model.PositionX = x - pos.X
    dialog.Model.PositionY = y - pos.Y - titlebar

def getWindowPosition(window):
    size = window.getPosSize()
    return window.convertPointToLogic(Point(size.X, size.Y), APPFONT)

def setWindowPosition(ctx, window, dialog, point, title):
    x, y = _getPosition(ctx, dialog, point)
    size = dialog.convertSizeToPixel(Size(dialog.Model.Width, dialog.Model.Height), APPFONT)
    point = dialog.convertPointToPixel(Point(x, y), APPFONT)
    window.getContainerWindow().setPosSize(point.X, point.Y, size.Width, size.Height, POSSIZE)
    window.setTitle(title)
    # FIXME: If the window loads before the desktop, it should not be made visible.
    if getDesktop(ctx).getCurrentFrame() is not None:
        window.getContainerWindow().setVisible(True)
    dialog.setVisible(True)

def _getPosition(ctx, dialog, point):
    area = getToolKit(ctx).getWorkArea()
    size = dialog.convertSizeToLogic(Size(area.Width, area.Height), APPFONT)
    width = dialog.Model.Width
    height = dialog.Model.Height
    if 0 <= point.X <= (size.Width - width) and 0 <= point.Y <= (size.Height - height):
        x = point.X
        y = point.Y
    else:
        x = (size.Width - width) // 2
        y = (size.Height - height) // 2
    x = max(0, min(x, size.Width - width))
    y = max(0, min(y, size.Height - height))
    return x, y

def getDialogSize(ctx, extension, xdl, point=None, unit=APPFONT):
    dialog = getDialog(ctx, extension, xdl)
    size = dialog.convertSizeToPixel(Size(dialog.Model.Width, dialog.Model.Height), unit)
    dialog.dispose()
    if point is None:
        point = Point(0, 0)
    return Rectangle(point.X, point.Y, size.Width, size.Height)

def saveWindowPosition(config, position, property):
    if config.hasByName(property):
        any = uno.Any('[]long', (position.X, position.Y))
        uno.invoke(config, 'replaceByName', (property, any))
        config.commitChanges()

def getWindowHeight(window, offset):
    size = window.getPosSize()
    point = window.convertPointToPixel(Point(0, offset), APPFONT)
    return Point(size.Height, size.Height + point.Y)

def setWindowHeight(frame, height):
    window = frame.getContainerWindow()
    size = window.getPosSize()
    window.setPosSize(0, 0, size.Width, height, SIZE)

def getContainerWindow(ctx, parent, handler, identifier, xdl):
    service = 'com.sun.star.awt.ContainerWindowProvider'
    provider = createService(ctx, service)
    url = getDialogUrl(identifier, xdl)
    return provider.createContainerWindow(url, '', parent, handler)

def getFileUrl(ctx, title, path, filters=(), multi=False):
    url = None
    filepicker = getFilePicker(ctx)
    filepicker.setTitle(title)
    filepicker.setDisplayDirectory(path)
    for name, filter in filters:
        filepicker.appendFilter(name, filter)
        if not filepicker.getCurrentFilter():
            filepicker.setCurrentFilter(name)
    filepicker.setMultiSelectionMode(multi)
    if filepicker.execute() == OK:
        if multi:
            url = filepicker.getSelectedFiles()
        else:
            url = filepicker.getSelectedFiles()[0]
        path = filepicker.getDisplayDirectory()
    filepicker.dispose()
    return url, path

def getDialogUrl(identifier, xdl):
    return 'vnd.sun.star.extension://%s/dialogs/%s.xdl' % (identifier, xdl)

def executeShell(ctx, url, option=''):
    shell = createService(ctx, 'com.sun.star.system.SystemShellExecute')
    shell.execute(url, option, 0)

def executeDispatch(ctx, url, /, **kwargs):
    frame = _getCurrentFrame(ctx)
    properties = getPropertyValueSet(kwargs)
    getDispatcher(ctx).executeDispatch(frame, url, '', 0, properties)

def executeDesktopDispatch(ctx, url, listener=None, /, **kwargs):
    frame = _getCurrentFrame(ctx)
    properties = getPropertyValueSet(kwargs)
    executeFrameDispatch(ctx, frame, url, listener, *properties)

def getJobArguments(arguments):
    kwargs = {}
    for argument in arguments:
        if (argument.Name == 'DynamicData'):
            for arg in argument.Value:
                kwargs[arg.Name.lower()] = arg.Value
    return kwargs

def getJobArgument(kwargs, key='dispatch'):
    argument = None
    for name in kwargs:
        if (name == key):
            argument = kwargs[name]
            break
    return argument

def notifyDispatch(source, listener, result=SUCCESS, value=None):
    if listener is not None:
        struct = 'com.sun.star.frame.DispatchResultEvent'
        notification = uno.createUnoStruct(struct, source, result, value)
        listener.dispatchFinished(notification)

def _getCurrentFrame(ctx):
    desktop = getDesktop(ctx)
    frame = desktop.getCurrentFrame()
    if frame is None:
        frame = desktop
    return frame

def executeFrameDispatch(ctx, frame, url, listener=None, /, *properties):
    url = getUrl(ctx, url)
    dispatcher = frame.queryDispatch(url, '', 0)
    if dispatcher is not None:
        if listener is not None:
            dispatcher.dispatchWithNotification(url, properties, listener)
        else:
            dispatcher.dispatch(url, properties)

def createMessageBox(ctx, title, message, box=ERRORBOX, button=1, parent=None):
    toolkit = getToolKit(ctx)
    if parent is None:
        parent = toolkit.getDesktopWindow()
    return toolkit.createMessageBox(parent, box, button, title, message)

def createService(ctx, name, *args, **kwargs):
    if args:
        service = ctx.ServiceManager.createInstanceWithArgumentsAndContext(name, args, ctx)
    elif kwargs:
        arguments = getNamedValueSet(kwargs)
        service = ctx.ServiceManager.createInstanceWithArgumentsAndContext(name, arguments, ctx)
    else:
        service = ctx.ServiceManager.createInstanceWithContext(name, ctx)
    return service

def getArgumentSet(properties, lower=True):
    arguments = {}
    for property in properties:
        name = property.Name
        if lower:
            name = name.lower()
        arguments[name] = property.Value
    return arguments

def getDefaultPropertyValueSet(args, default):
    properties = []
    for key in args:
        properties.append(getPropertyValue(key, default))
    return tuple(properties)

def getPropertyValueSet(kwargs):
    properties = []
    for key, value in kwargs.items():
        properties.append(getPropertyValue(key, value))
    return tuple(properties)

def getPropertyValue(name, value, state=DIRECT_VALUE, handle=-1):
    property = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
    property.Name = name
    property.Handle = handle
    property.Value = value
    property.State = state
    return property

def getNamedValueSet(kwargs):
    namedvalues = []
    for key, value in kwargs.items():
        namedvalues.append(getNamedValue(key, value))
    return tuple(namedvalues)

def getNamedValue(name, value):
    namedvalue = uno.createUnoStruct('com.sun.star.beans.NamedValue')
    namedvalue.Name = name
    namedvalue.Value = value
    return namedvalue

def getPropertySetInfoChangeEvent(source, name, reason, handle=-1):
    event = uno.createUnoStruct('com.sun.star.beans.PropertySetInfoChangeEvent')
    event.Source = source
    event.Name = name
    event.Handle = handle
    event.Reason = reason

def _getUniqueName(frames, name):
    count = 0
    for i in range(frames.getCount()):
        if frames.getByIndex(i).getName() == name:
            count += 1
    if count > 0:
        name = '%s - %s' % (name, (count +1))
    return name

def getDateTime(utc=True):
    if utc:
        t = datetime.datetime.utcnow()
    else:
        t = datetime.datetime.now()
    return _getDateTime(t.microsecond, t.second, t.minute, t.hour, t.day, t.month, t.year, utc)

def parseDateTime(timestr='', format='%Y-%m-%dT%H:%M:%S.%fZ', utc=True):
    if timestr != '':
        t = datetime.datetime.strptime(timestr, format)
    elif utc:
        t = datetime.datetime.utcnow()
    else:
        t = datetime.datetime.now()
    return _getDateTime(t.microsecond, t.second, t.minute, t.hour, t.day, t.month, t.year, utc)

def unparseDateTime(t=None, utc=True, decimal=6):
    if t is None:
        if utc:
            now = datetime.datetime.utcnow()
        else:
            now = datetime.datetime.now()
        return now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    fraction = 0
    if hasattr(t, 'HundredthSeconds'):
        fraction = t.HundredthSeconds // (10 ** (3 -decimal))
    elif hasattr(t, 'NanoSeconds'):
        fraction = t.NanoSeconds // (10 ** (9 - decimal))
    format = '%04d-%02d-%02dT%02d:%02d:%02d.%'
    format += '0%sdZ' % decimal
    return format % (t.Year, t.Month, t.Day, t.Hours, t.Minutes, t.Seconds, fraction)

def unparseTimeStamp(t=None, utc=True):
    if t is None:
        if utc:
            now = datetime.datetime.utcnow()
        else:
            now = datetime.datetime.now()
        return now.strftime('%Y-%m-%d %H:%M:%S')
    format = '%04d-%02d-%02d %02d:%02d:%02d'
    return format % (t.Year, t.Month, t.Day, t.Hours, t.Minutes, t.Seconds)

def _getDateTime(microsecond=0, second=0, minute=0, hour=0, day=1, month=1, year=1970, utc=True):
    t = uno.createUnoStruct('com.sun.star.util.DateTime')
    t.Year = year
    t.Month = month
    t.Day = day
    t.Hours = hour
    t.Minutes = minute
    t.Seconds = second
    if hasattr(t, 'HundredthSeconds'):
        t.HundredthSeconds = microsecond // 10000
    elif hasattr(t, 'NanoSeconds'):
        t.NanoSeconds = microsecond * 1000
    if hasattr(t, 'IsUTC'):
        t.IsUTC = utc
    return t

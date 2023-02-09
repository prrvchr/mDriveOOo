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

from com.sun.star.awt import Rectangle

from com.sun.star.connection import NoConnectException

from com.sun.star.document.MacroExecMode import ALWAYS_EXECUTE_NO_WARN

from com.sun.star.lang import WrappedTargetRuntimeException

from com.sun.star.ucb.ConnectionMode import ONLINE
from com.sun.star.ucb.ConnectionMode import OFFLINE

from com.sun.star.ui.dialogs.ExecutableDialogResults import OK

from six import binary_type, string_types
import datetime
import binascii
import traceback


def getConnectionMode(ctx, host, port=80):
    connector = createService(ctx, 'com.sun.star.connection.Connector')
    try:
        connection = connector.connect('socket,host=%s,port=%s' % (host, port))
    except NoConnectException:
        mode = OFFLINE
    else:
        connection.close()
        mode = ONLINE
    return mode

def getDesktop(ctx):
    return createService(ctx, 'com.sun.star.frame.Desktop')

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

def getInteractionHandler(ctx):
    return createService(ctx, 'com.sun.star.task.InteractionHandler')

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

def getDocument(ctx, url):
    properties = {'Hidden': True,
                  'OpenNewView': True,
                  'MacroExecutionMode': ALWAYS_EXECUTE_NO_WARN}
    descriptor = getPropertyValueSet(properties)
    document = getDesktop(ctx).loadComponentFromURL(url, '_blank', 0, descriptor)
    return document

def getExceptionMessage(exception):
    messages = []
    if hasattr(exception, 'args'):
        messages = [arg for arg in exception.args if isinstance(arg, string_types)]
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
    if isinstance(message, binary_type):
        message = message.decode('utf-8')
    message = ' '.join(message.split())
    return message

def getFileSequence(ctx, url, default=None):
    length = 0
    sequence = uno.ByteSequence(b'')
    fs = getSimpleFile(ctx)
    if fs.exists(url):
        inputstream = fs.openFileRead(url)
        size = fs.getSize(url)
        length, sequence = _getSequence(inputstream, size)
    elif default is not None and fs.exists(default):
        inputstream = fs.openFileRead(default)
        size = fs.getSize(default)
        length, sequence = _getSequence(inputstream, size)
    return length, sequence

def _getSequence(inputstream, length):
    length, sequence = inputstream.readBytes(None, length)
    inputstream.closeInput()
    return length, sequence

def hasInterface(component, interface):
    for t in getComponentTypes(component):
        if t.typeName == interface:
            return True
    return False

def getComponentTypes(component):
    try:
        types = component.getTypes()
    except:
        types = ()
    return types

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
    service = 'com.sun.star.resource.StringResourceWithLocation'
    location = getResourceLocation(ctx, identifier, path)
    if locale is None:
        locale = getCurrentLocale(ctx)
    handler = getInteractionHandler(ctx)
    args = (location, True, locale, filename, '', handler)
    return createService(ctx, service, *args)

def generateUuid():
    return binascii.hexlify(uno.generateUuid().value).decode('utf-8')

def getDialog(ctx, library, xdl, handler=None, window=None):
    dialog = None
    provider = createService(ctx, 'com.sun.star.awt.DialogProvider2')
    url = getDialogUrl(library, xdl)
    if handler is None and window is None:
        dialog = provider.createDialog(url)
        toolkit = createService(ctx, 'com.sun.star.awt.Toolkit')
        dialog.createPeer(toolkit, None)
    elif handler is not None and window is None:
        dialog = provider.createDialogWithHandler(url, handler)
        toolkit = createService(ctx, 'com.sun.star.awt.Toolkit')
        dialog.createPeer(toolkit, None)
    else:
        args = getNamedValueSet({'ParentWindow': window, 'EventHandler': handler})
        dialog = provider.createDialogWithArguments(url, args)
    return dialog

def getContainerWindow(ctx, parent, handler, library, xdl):
    window = None
    service = 'com.sun.star.awt.ContainerWindowProvider'
    provider = createService(ctx, service)
    url = getDialogUrl(library, xdl)
    try:
        window = provider.createContainerWindow(url, '', parent, handler)
    except WrappedTargetRuntimeException as e:
        print("unotool.getContainerWindow() ERROR: %s - %s" % (e, traceback.print_exc()))
    return window

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
        url = filepicker.getFiles()[0]
        if multi:
            try:
                urls = filepicker.getSelectedFiles()
            except:
                urls = filepicker.getFiles()
                if len(urls) > 1:
                    urls = [url + u for u in urls[1:]]
            url = urls
        path = filepicker.getDisplayDirectory()
    filepicker.dispose()
    return url, path

def getDialogUrl(library, xdl):
    return 'vnd.sun.star.script:%s.%s?location=application' % (library, xdl)

def executeShell(ctx, url, option=''):
    shell = createService(ctx, 'com.sun.star.system.SystemShellExecute')
    shell.execute(url, option, 0)

def executeFrameDispatch(ctx, frame, url, arguments=(), listener=None):
    url = getUrl(ctx, url)
    dispatcher = frame.queryDispatch(url, '', 0)
    if dispatcher is not None:
        if listener is not None:
            dispatcher.dispatchWithNotification(url, arguments, listener)
            print("unotool.executeFrameDispatch() dispatchWithNotification")
        else:
            dispatcher.dispatch(url, arguments)
            print("unotool.executeFrameDispatch() dispatch")

def executeDispatch(ctx, url, arguments=(), listener=None):
    frame = getDesktop(ctx).getCurrentFrame()
    executeFrameDispatch(ctx, frame, url, arguments, listener)

def createMessageBox(peer, message, title, box='message', buttons=2):
    boxtypes = {'message': 'MESSAGEBOX',
                'info': 'INFOBOX',
                'warning': 'WARNINGBOX',
                'error': 'ERRORBOX',
                'query': 'QUERYBOX'}
    box = uno.Enum('com.sun.star.awt.MessageBoxType', boxtypes.get(box, 'MESSAGEBOX'))
    return peer.getToolkit().createMessageBox(peer, box, buttons, title, message)

def createService(ctx, name, *args, **kwargs):
    if args:
        service = ctx.ServiceManager.createInstanceWithArgumentsAndContext(name, args, ctx)
    elif kwargs:
        arguments = getNamedValueSet(kwargs)
        service = ctx.ServiceManager.createInstanceWithArgumentsAndContext(name, arguments, ctx)
    else:
        service = ctx.ServiceManager.createInstanceWithContext(name, ctx)
    return service

def getPropertyValueSet(kwargs):
    properties = []
    for key, value in kwargs.items():
        properties.append(getPropertyValue(key, value))
    return tuple(properties)

def getPropertyValue(name, value, state=0, handle=-1):
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

def createWindow(ctx, extension, xdl, name):
    dialog = getDialog(ctx, extension, xdl, None, None)
    possize = Rectangle(dialog.Model.PositionX, dialog.Model.PositionY, dialog.Model.Width, dialog.Model.Height)
    dialog.dispose()
    desktop = getDesktop(ctx)
    args = getNamedValueSet({'FrameName': name, 'PosSize': possize})
    frame = createService(ctx, 'com.sun.star.frame.TaskCreator').createInstanceWithArguments(args)
    frames = desktop.getFrames()
    frame.setTitle(_getUniqueName(frames, name))
    frame.setCreator(desktop)
    frames.append(frame)
    return frame.getContainerWindow()

def _getUniqueName(frames, name):
    count = 0
    for i in range(frames.getCount()):
        if frames.getByIndex(i).getName() == name:
            count += 1
    if count > 0:
        name = '%s - %s' % (name, (count +1))
    return name


def getParentWindow(ctx):
    desktop = getDesktop(ctx)
    try:
        parent = desktop.getCurrentFrame().getContainerWindow()
    except:
        parent = None
    return parent

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

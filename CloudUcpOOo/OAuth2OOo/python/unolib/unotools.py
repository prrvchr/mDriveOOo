#!
# -*- coding: utf_8 -*-

import uno

from com.sun.star.lang import WrappedTargetRuntimeException
from com.sun.star.connection import NoConnectException
from com.sun.star.ucb.ConnectionMode import ONLINE
from com.sun.star.ucb.ConnectionMode import OFFLINE

from .unolib import InteractionHandler

import datetime
import binascii
import traceback


def getConnectionMode(ctx, host, port=80):
    connector = ctx.ServiceManager.createInstance('com.sun.star.connection.Connector')
    try:
        connection = connector.connect('socket,host=%s,port=%s' % (host, port))
    except NoConnectException:
        mode = OFFLINE
    else:
        connection.close()
        mode = ONLINE
    return mode

def getSimpleFile(ctx):
    return ctx.ServiceManager.createInstance('com.sun.star.ucb.SimpleFileAccess')

def getFileSequence(ctx, url, default=None):
    length, sequence = 0, uno.ByteSequence(b'')
    fs = getSimpleFile(ctx)
    if fs.exists(url):
        length, sequence = _getSequence(fs.openFileRead(url), fs.getSize(url))
    elif default is not None and fs.exists(default):
        length, sequence = _getSequence(fs.openFileRead(default), fs.getSize(default))
    return length, sequence

def _getSequence(inputstream, length):
    length, sequence = inputstream.readBytes(None, length)
    inputstream.closeInput()
    return length, sequence

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

def getConfiguration(ctx, nodepath, update=False):
    service = 'com.sun.star.configuration.ConfigurationProvider'
    provider = ctx.ServiceManager.createInstance(service)
    service = 'com.sun.star.configuration.ConfigurationUpdateAccess' if update else \
              'com.sun.star.configuration.ConfigurationAccess'
    arguments = (uno.createUnoStruct('com.sun.star.beans.NamedValue', 'nodepath', nodepath), )
    return provider.createInstanceWithArguments(service, arguments)

def getCurrentLocale(ctx):
    service = '/org.openoffice.Setup/L10N'
    parts = getConfiguration(ctx, service).getByName('ooLocale').split('-')
    locale = uno.createUnoStruct('com.sun.star.lang.Locale', parts[0], '', '')
    if len(parts) > 1:
        locale.Country = parts[1]
    else:
        service = ctx.ServiceManager.createInstance('com.sun.star.i18n.LocaleData')
        locale.Country = service.getLanguageCountryInfo(locale).Country
    return locale

def getStringResource(ctx, identifier, path=None, filename='DialogStrings', locale=None):
    service = 'com.sun.star.resource.StringResourceWithLocation'
    location = getResourceLocation(ctx, identifier, path)
    if locale is None:
        locale = getCurrentLocale(ctx)
    arguments = (location, True, locale, filename, '', InteractionHandler())
    return ctx.ServiceManager.createInstanceWithArgumentsAndContext(service, arguments, ctx)

def generateUuid():
    return binascii.hexlify(uno.generateUuid().value).decode('utf-8')

def getDialog(ctx, window, handler, library, xdl):
    dialog = None
    provider = ctx.ServiceManager.createInstance('com.sun.star.awt.DialogProvider')
    url = getDialogUrl(library, xdl)
    arguments = getNamedValueSet({'ParentWindow': window, 'EventHandler': handler})
    dialog = provider.createDialogWithArguments(url, arguments)
    return dialog

def getContainerWindow(ctx, parent, handler, library, xdl):
    window = None
    service = 'com.sun.star.awt.ContainerWindowProvider'
    provider = ctx.ServiceManager.createInstanceWithContext(service, ctx)
    url = getDialogUrl(library, xdl)
    try:
        window = provider.createContainerWindow(url, '', parent, handler)
    except WrappedTargetRuntimeException as e:
        print("unotools.getContainerWindow() ERROR: %s - %s" % (e, traceback.print_exc()))
    return window

def getDialogUrl(library, xdl):
    return 'vnd.sun.star.script:%s.%s?location=application' % (library, xdl)

def createMessageBox(peer, message, title, box='message', buttons=2):
    boxtypes = {'message': 'MESSAGEBOX',
                'info': 'INFOBOX',
                'warning': 'WARNINGBOX',
                'error': 'ERRORBOX',
                'query': 'QUERYBOX'}
    box = uno.Enum('com.sun.star.awt.MessageBoxType', boxtypes.get(box, 'MESSAGEBOX'))
    return peer.getToolkit().createMessageBox(peer, box, buttons, title, message)

def createService(ctx, name, **kwargs):
    if kwargs:
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

def getPropertyValue(name, value, state=None, handle=-1):
    property = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
    property.Name = name
    property.Handle = handle
    property.Value = value
    s = state if state else uno.Enum('com.sun.star.beans.PropertyState', 'DIRECT_VALUE')
    property.State = s
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

def getInteractionHandler(ctx):
    service = 'com.sun.star.task.InteractionHandler'
    desktop = ctx.ServiceManager.createInstance('com.sun.star.frame.Desktop')
    args = getPropertyValueSet({'Parent': desktop.ActiveFrame.ComponentWindow})
    interaction = ctx.ServiceManager.createInstanceWithArguments(service, args)
    return interaction

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


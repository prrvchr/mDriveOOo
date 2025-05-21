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

from com.sun.star.connection import NoConnectException

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb.ContentAction import INSERTED
from com.sun.star.ucb.ContentAction import REMOVED
from com.sun.star.ucb.ContentAction import DELETED
from com.sun.star.ucb.ContentAction import EXCHANGED

from com.sun.star.ucb import IllegalIdentifierException
from com.sun.star.ucb import InteractiveAugmentedIOException

from com.sun.star.ucb.ConnectionMode import ONLINE
from com.sun.star.ucb.ConnectionMode import OFFLINE

from com.sun.star.sdb import ParametersRequest

from .dbtool import getConnectionUrl
from .dbtool import getDataSourceConnection
from .dbtool import getDriverInfos

from .unotool import checkVersion
from .unotool import createMessageBox
from .unotool import createService
from .unotool import executeDispatch
from .unotool import hasInterface
from .unotool import getDesktop
from .unotool import getDispatcher
from .unotool import getExtensionVersion
from .unotool import getNamedValueSet
from .unotool import getParentWindow
from .unotool import getProperty
from .unotool import getPropertyValue
from .unotool import getPropertyValueSet
from .unotool import getSimpleFile
from .unotool import parseUrl

from .dbinit import createDataBase

from .oauth20 import getOAuth2Version
from .oauth20 import g_extension as g_oauth2ext
from .oauth20 import g_version as g_oauth2ver

from .jdbcdriver import g_extension as g_jdbcext
from .jdbcdriver import g_identifier as g_jdbcid
from .jdbcdriver import g_version as g_jdbcver

from .dbconfig import g_drvinfos
from .dbconfig import g_folder
from .dbconfig import g_version

from .configuration import g_extension
from .configuration import g_scheme

from .ucp import g_ucbseparator


def getPresentationUrl(transformer, url):
    # FIXME: Sometimes the url can end with a dot, it must be removed
    url = url.rstrip('.')
    uri = parseUrl(transformer, url)
    if uri is not None:
        url = transformer.getPresentation(uri, True)
    return url

def getDataBaseUrl(ctx):
    return getConnectionUrl(ctx, g_folder + g_ucbseparator + g_scheme)

def getDataBaseConnection(ctx, source, logger, url, create=True, warn=True):
    _checkConfiguration(ctx, source, logger, warn)
    odb = url + '.odb'
    new = not getSimpleFile(ctx).exists(odb)
    connection = _getDataSourceConnection(ctx, url, new)
    _checkConnection(ctx, source, connection, logger, new, warn)
    if new and create:
        createDataBase(ctx, connection)
        connection.getParent().DatabaseDocument.storeAsURL(odb, ())
    return connection

def propertyChange(source, name, oldvalue, newvalue):
    if name in source.propertiesListener:
        events = (_getPropertyChangeEvent(source, name, oldvalue, newvalue), )
        for listener in source.propertiesListener[name]:
            listener.propertiesChange(events)

def setContentData(content, call, properties, index=1):
    row = _getContentProperties(content, properties)
    for i, name in enumerate(properties, 1):
        value = row.getObject(i, None)
        print ("items._setContentData(): name:%s - value:%s" % (name, value))
        if value is None:
            continue
        if name in ('Name', 'MimeType'):
            call.setString(index, value)
        elif name in ('DateCreated', 'DateModified'):
            call.setTimestamp(index, value)
        elif name in ('Trashed', 'CanAddChild', 'CanRename', 'IsReadOnly', 'IsVersionable'):
            call.setBoolean(index, value)
        elif name in ('Size', 'ConnectionMode'):
            call.setLong(index, value)
        index += 1
    return index

def getPump(ctx):
    return ctx.ServiceManager.createInstance('com.sun.star.io.Pump')

def getPipe(ctx):
    return ctx.ServiceManager.createInstance('com.sun.star.io.Pipe')

def getContentEvent(source, action, content, id):
    event = uno.createUnoStruct('com.sun.star.ucb.ContentEvent')
    event.Source = source
    event.Action = action
    event.Content = content
    event.Id = id
    return event

def getCommand(name, argument, handle=-1):
    command = uno.createUnoStruct('com.sun.star.ucb.Command')
    command.Name = name
    command.Handle = handle
    command.Argument = argument
    return command

def getCommandInfo(name, typename='', handle=-1):
    command = uno.createUnoStruct('com.sun.star.ucb.CommandInfo')
    command.Name = name
    if typename:
        command.ArgType = uno.getTypeByName(typename)
    command.Handle = handle
    return command

def getContentInfo(ctype, attributes=0, properties=()):
    info = uno.createUnoStruct('com.sun.star.ucb.ContentInfo')
    info.Type = ctype
    info.Attributes = attributes
    info.Properties = properties
    return info

def getMimeType(ctx, stream):
    mimetype = 'application/octet-stream'
    detection = ctx.ServiceManager.createInstance('com.sun.star.document.TypeDetection')
    descriptor = (getPropertyValue('InputStream', stream), )
    format, dummy = detection.queryTypeByDescriptor(descriptor, True)
    if detection.hasByName(format):
        properties = detection.getByName(format)
        for property in properties:
            if property.Name == "MediaType":
                mimetype = property.Value
    return mimetype

def getParametersRequest(source, connection, message):
    r = ParametersRequest()
    r.Message = message
    r.Context = source
    r.Classification = uno.Enum('com.sun.star.task.InteractionClassification', 'QUERY')
    r.Connection = connection
    return r

def getInteractiveAugmentedIOException(message, source, classification, code, arguments):
    e = InteractiveAugmentedIOException()
    e.Message = message
    e.Context = source
    e.Classification = uno.Enum('com.sun.star.task.InteractionClassification', classification)
    e.Code = uno.Enum('com.sun.star.ucb.IOErrorCode', code)
    e.Arguments = arguments
    return e

def notifyContentListener(ctx, content, action, identifier=None):
    if action == INSERTED:
        identifier = content.getIdentifier()
        parent = identifier.getParent()
        parent.notify(getContentEvent(action, content, identifier))
    elif action == DELETED:
        identifier = content.getIdentifier()
        content.notify(getContentEvent(action, content, identifier))
    elif action == EXCHANGED:
        content.notify(getContentEvent(action, content, identifier))

def executeContentCommand(content, name, argument, environment):
    command = getCommand(name, argument)
    return content.execute(command, 0, environment)

def getExceptionMessage(logger, code, extension, *args):
    title = logger.resolveString(code, extension)
    message = logger.resolveString(code + 1, *args)
    return title, message

def showWarning(ctx, message, title):
    box = uno.Enum('com.sun.star.awt.MessageBoxType', 'ERRORBOX')
    args = {'Box': box, 'Button': 1, 'Title': title, 'Message': message}
    executeDispatch(ctx, '%s:ShowWarning' % g_scheme, **args)

# Private method
def _checkConfiguration(ctx, source, logger, warn):
    oauth2 = getOAuth2Version(ctx)
    driver = getExtensionVersion(ctx, g_jdbcid)
    if oauth2 is None:
        title, msg = getExceptionMessage(logger, 801, g_oauth2ext, g_oauth2ext, g_extension)
        if warn:
            showWarning(ctx, msg, title)
        raise IllegalIdentifierException(msg, source)
    if not checkVersion(oauth2, g_oauth2ver):
        title, msg = getExceptionMessage(logger, 803, g_oauth2ext, oauth2, g_oauth2ext, g_oauth2ver)
        if warn:
            showWarning(ctx, msg, title)
        raise IllegalIdentifierException(msg, source)
    if driver is None:
        title, msg = getExceptionMessage(logger, 801, g_jdbcext, g_jdbcext, g_extension)
        if warn:
            showWarning(ctx, msg, title)
        raise IllegalIdentifierException(msg, source)
    if not checkVersion(driver, g_jdbcver):
        title, msg = getExceptionMessage(logger, 803, g_jdbcext, driver, g_jdbcext, g_jdbcver)
        if warn:
            showWarning(ctx, msg, title)
        raise IllegalIdentifierException(msg, source)

def _getDataSourceConnection(ctx, url, new, infos=None):
    if new:
        infos = getDriverInfos(ctx, url, g_drvinfos)
    return getDataSourceConnection(ctx, url, '', '', new, infos)

def _checkConnection(ctx, source, connection, logger, new, warn):
    version = connection.getMetaData().getDriverVersion()
    if not checkVersion(version, g_version):
        connection.close()
        title, msg = getExceptionMessage(logger, 811, g_jdbcext, version, g_version)
        if warn:
            showWarning(ctx, msg, title)
        raise IllegalIdentifierException(msg, source)
    service = 'com.sun.star.sdb.Connection'
    interface = 'com.sun.star.sdbcx.XGroupsSupplier'
    if new and not _checkConnectionApi(connection, service, interface):
        connection.close()
        title, msg = getExceptionMessage(logger, 813, g_jdbcext, service, interface)
        if warn:
            showWarning(ctx, msg, title)
        raise IllegalIdentifierException(msg, source)

def _checkConnectionApi(connection, service, interface):
    return connection.supportsService(service) and hasInterface(connection, interface)

def _getContentProperties(content, properties):
    namedvalues = []
    for name in properties:
        namedvalues.append(getProperty(name))
    command = getCommand('getPropertyValues', tuple(namedvalues))
    return content.execute(command, 0, None)

def _getPropertyChangeEvent(source, name, oldvalue, newvalue, further=False, handle=-1):
    event = uno.createUnoStruct('com.sun.star.beans.PropertyChangeEvent')
    event.Source = source
    event.PropertyName = name
    event.Further = further
    event.PropertyHandle = handle
    event.OldValue = oldvalue
    event.NewValue = newvalue
    return event


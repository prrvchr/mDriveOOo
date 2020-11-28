#!
# -*- coding: utf-8 -*-

'''
    Copyright (c) 2020 https://prrvchr.github.io

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the Software
    is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
    OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import uno

from com.sun.star.sdb import ParametersRequest
from com.sun.star.connection import NoConnectException
from com.sun.star.ucb import InteractiveAugmentedIOException
from com.sun.star.ucb.ConnectionMode import ONLINE
from com.sun.star.ucb.ConnectionMode import OFFLINE

from unolib import createService
from unolib import getProperty
from unolib import getPropertyValue
from unolib import getNamedValueSet


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
        elif name in ('Size', 'Loaded'):
            call.setLong(index, value)
        index += 1
    return index

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

def getCommandInfo(name, unotype=None, handle=-1):
    command = uno.createUnoStruct('com.sun.star.ucb.CommandInfo')
    command.Name = name
    if unotype:
        command.ArgType = unotype
    command.Handle = handle
    return command

def getContentInfo(ctype, attributes=0, properties=()):
    info = uno.createUnoStruct('com.sun.star.ucb.ContentInfo')
    info.Type = ctype
    info.Attributes = attributes
    info.Properties = properties
    return info

def getUrl(ctx, identifier):
    url = uno.createUnoStruct('com.sun.star.util.URL')
    url.Complete = identifier
    transformer = createService(ctx, 'com.sun.star.util.URLTransformer')
    success, url = transformer.parseStrict(url)
    if success:
        identifier = transformer.getPresentation(url, True)
    return identifier

def getUri(ctx, url):
    factory = createService(ctx, 'com.sun.star.uri.UriReferenceFactory')
    uri = factory.parse(url)
    return uri

def getUcb(ctx, arguments=('Local', 'Office')):
    name = 'com.sun.star.ucb.UniversalContentBroker'
    return ctx.ServiceManager.createInstanceWithArguments(name, (arguments, ))

def getUcp(ctx, scheme):
    return getUcb(ctx).queryContentProvider('%s://' % scheme)

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

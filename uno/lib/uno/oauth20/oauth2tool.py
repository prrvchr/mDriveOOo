#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-24 https://prrvchr.github.io                                  ║
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

from ..unotool import createService
from ..unotool import getExtensionVersion

from .configuration import g_service
from .configuration import g_identifier
from .configuration import g_chunk

from string import Formatter
from string import Template
from urllib import parse
import base64
import json
import ijson


def getRequest(ctx, url=None, name=None):
    if url and name:
        request = createService(ctx, g_service, url, name)
    else:
        request = createService(ctx, g_service)
    return request

def getOAuth2(ctx, url='', name=''):
    if url and name:
        oauth2 = createService(ctx, g_service, url, name)
    else:
        oauth2 = createService(ctx, g_service)
    return oauth2

def getOAuth2Version(ctx):
    version = getExtensionVersion(ctx, g_identifier)
    return version

def setResquestParameter(arguments, request, parameter):
    method = request.getByName('Method')
    if method:
        parameter.Method = method
    url = request.getByName('Url')
    if url:
        parameter.Url = Template(url).safe_substitute(arguments)
    data = request.getByName('Data')
    if data and data in arguments:
        parameter.Data = uno.ByteSequence(arguments[data])
    args = request.getByName('Arguments')
    if args:
        items = json.loads(args)
        setItemsIdentifier(items, arguments)
        parameter.fromJson(json.dumps(items))

def setParametersArguments(parameters, arguments, key=None):
    for name in sorted(parameters.getElementNames()):
        parameter = parameters.getByName(name)
        key = _setParameterArguments(parameter, arguments)
    return key

def getParserItems(request):
    keys = {}
    items = {}
    triggers = {}
    collectors = {}
    responses = request.getByName('Responses')
    if responses:
        getKey = lambda x: (x[0], x[1], x[2] if len(x) > 2 else None)
        for name in responses.getElementNames():
            response = responses.getByName(name)
            item = response.getByName('Item')
            if item and len(item) == 2:
                trigger = response.getByName('Trigger')
                if not trigger:
                    items[item] = name
                elif len(trigger) > 1:
                    keys[name] = item
                    triggers[getKey(trigger)] = name
                    collector = response.getByName('Collector')
                    if collector:
                        if len(collector) > 1:
                            collectors[getKey(collector)] = name
    return keys, items, triggers, collectors

def getResponseResults(items, response):
    results = {}
    events = ijson.sendable_list()
    parser = ijson.parse_coro(events)
    iterator = response.iterContent(g_chunk, False)
    while iterator.hasMoreElements():
        parser.send(iterator.nextElement().value)
        for event in events:
            items.parse(results, *event)
        del events[:]
    parser.close()
    return results

def setItemsIdentifier(items, arguments, prefix='${', suffix='}'):
    identifiers = {prefix + k + suffix: k for k in arguments.keys()}
    _setItemsIdentifier(items, arguments, identifiers)

def _setParameterArguments(parameter, arguments):
    key = parameter.getByName('Name')
    template = parameter.getByName('Template')
    command = parameter.getByName('Command')
    if template:
        _setArgumentTemplate(key, arguments, template)
    if command and key in arguments:
        method = command[0]
        value = arguments[key]
        if method == 'encodeURI':
            safe = _getArgumentCommand(command, "~@#$&()*!+=:;,?/'")
            arguments[key] = parse.quote(value, safe=safe)
        elif method == 'encodeURIComponent':
            safe = _getArgumentCommand(command, "~()*!'")
            arguments[key] = parse.quote(value, safe=safe)
        elif method == 'base64URL':
            arguments[key] = base64.urlsafe_b64encode(value)
        elif method == 'base64':
            arguments[key] = base64.b64encode(value)
        elif method == 'decode':
            encoding = _getArgumentCommand(command, 'utf-8')
            errors = _getArgumentCommand(command, 'strict', 2)
            arguments[key] = value.decode(encoding=encoding, errors=errors)
        elif method == 'encode':
            encoding = _getArgumentCommand(command, 'utf-8')
            errors = _getArgumentCommand(command, 'strict', 2)
            arguments[key] = value.encode(encoding=encoding, errors=errors)
        elif method == 'replace':
            arg1 = _getArgumentCommand(command, '')
            arg2 = _getArgumentCommand(command, '', 2)
            arg3 = int(_getArgumentCommand(command, -1, 3))
            arguments[key] = value.replace(arg1, arg2, arg3)
        elif method == 'strip':
            arguments[key] = value.strip(_getArgumentCommand(command))
        elif method == 'rstrip':
            arguments[key] = value.rstrip(_getArgumentCommand(command))
        elif method == 'lstrip':
            arguments[key] = value.lstrip(_getArgumentCommand(command))
    return setParametersArguments(parameter.getByName('Parameters'), arguments, key)

def _setArgumentTemplate(key, arguments, template):
    for identifier in Formatter().parse(template):
        if identifier[1] in arguments:
            arguments[key] = Template(template).safe_substitute(arguments)
            break

def _getArgumentCommand(command, default=None, index=1):
    return command[index] if len(command) > index else default

def _setItemsIdentifier(items, arguments, identifiers):
    for key, value in items.items():
        if isinstance(value, dict):
            _setItemsIdentifier(value, arguments, identifiers)
        elif isinstance(value, list):
            _setItemsList(value, arguments, identifiers)
        elif value in identifiers:
            items[key] = arguments[identifiers[value]]

def _setItemsList(values, arguments, identifiers):
    for i, value in enumerate(values):
        if isinstance(value, dict):
            _setItemsIdentifier(value, arguments, identifiers)
        elif isinstance(value, list):
            _setItemsList(value, arguments, identifiers)
        elif value in identifiers:
            values[i] = arguments[identifiers[value]]


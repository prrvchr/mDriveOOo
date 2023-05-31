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

from com.sun.star.rest.ParameterType import JSON
from com.sun.star.rest.ParameterType import REDIRECT

from com.sun.star.rest.HTTPStatusCode import ACCEPTED

from .providerbase import ProviderBase

from .dbtool import currentUnoDateTime
from .dbtool import currentDateTimeInTZ

from .unotool import getResourceLocation

from .configuration import g_identifier
from .configuration import g_scheme
from .configuration import g_provider
from .configuration import g_host
from .configuration import g_url
from .configuration import g_userfields
from .configuration import g_drivefields
from .configuration import g_itemfields
from .configuration import g_chunk
from .configuration import g_pages
from .configuration import g_folder
from .configuration import g_office
from .configuration import g_link
from .configuration import g_doc_map

from . import ijson
import traceback


class Provider(ProviderBase):
    def __init__(self, ctx, folder, link, logger):
        self._ctx = ctx
        self._folder = folder
        self._link = link
        self._logger = logger
        self.Scheme = g_scheme
        self.SourceURL = getResourceLocation(ctx, g_identifier, g_scheme)
        self._folders = []

    @property
    def Name(self):
        return g_provider
    @property
    def Host(self):
        return g_host
    @property
    def BaseUrl(self):
        return g_url
    @property
    def UploadUrl(self):
        return g_upload
    @property
    def Office(self):
        return g_office
    @property
    def Document(self):
        return g_doc_map
    @property
    def DateTimeFormat(self):
        return '%Y-%m-%dT%H:%M:%S.%fZ'
    @property
    def Folder(self):
        return self._folder
    @property
    def Link(self):
        return self._link

    def getFirstPullRoots(self, user):
        return (user.RootId, )

    def initUser(self, database, user, token):
        # FIXME: Some APIs like Microsoft oneDrive allow to have the token during the firstPull
        #token = self.getUserToken(user)
        if database.updateToken(user.Id, token):
            user.setToken(token)

    def getUser(self, source, request, name):
        user = self._getUser(source, request, name)
        root = self._getRoot(source, request, name)
        return user, root

    def parseRootFolder(self, parameter, content):
        return self.parseItems(content.User.Request, parameter)

    def parseItems(self, request, parameter):
        while parameter.hasNextPage():
            response = request.execute(parameter)
            if not response.Ok:
                break
            events = ijson.sendable_list()
            parser = ijson.parse_coro(events)
            iterator = response.iterContent(g_chunk, False)
            while iterator.hasMoreElements():
                parser.send(iterator.nextElement().value)
                for prefix, event, value in events:
                    if (prefix, event) == ('@odata.deltaLink', 'string'):
                        parameter.SyncToken = value
                    elif (prefix, event) == ('@odata.nextLink', 'string'):
                        parameter.setNextPage('', value, REDIRECT)
                    elif (prefix, event) == ('value.item', 'start_map'):
                        itemid = name = None
                        created = modified = currentUnoDateTime()
                        mimetype = g_folder
                        size = 0
                        addchild = canrename = True
                        trashed = readonly = versionable = False
                        parents = []
                    elif (prefix, event) == ('value.item.id', 'string'):
                        itemid = value
                    elif (prefix, event) == ('value.item.name', 'string'):
                        name = value
                    elif (prefix, event) == ('value.item.createdDateTime', 'string'):
                        created = self.parseDateTime(value)
                    elif (prefix, event) == ('value.item.lastModifiedDateTime', 'string'):
                        modified = self.parseDateTime(value)
                    elif (prefix, event) == ('value.item.file.mimeType', 'string'):
                        mimetype = value
                    elif (prefix, event) == ('value.item.trashed', 'boolean'):
                        trashed = value
                    elif (prefix, event) == ('value.item.size', 'string'):
                        size = int(value)
                    elif (prefix, event) == ('value.item.parentReference.id', 'string'):
                        parents.append(value)
                    elif (prefix, event) == ('value.item', 'end_map'):
                        yield itemid, name, created, modified, mimetype, size, trashed, True, True, False, False, None, parents
                del events[:]
            parser.close()
            response.close()

    def parseChanges(self, request, parameter):
        while parameter.hasNextPage():
            response = request.execute(parameter)
            if not response.Ok:
                break
            events = ijson.sendable_list()
            parser = ijson.parse_coro(events)
            iterator = response.iterContent(g_chunk, False)
            while iterator.hasMoreElements():
                parser.send(iterator.nextElement().value)
                for prefix, event, value in events:
                    if (prefix, event) == ('@odata.nextLink', 'string'):
                        parameter.setNextPage('', value, REDIRECT)
                    elif (prefix, event) == ('@odata.deltaLink', 'string'):
                        parameter.SyncToken = value
                    elif (prefix, event) == ('value.item', 'start_map'):
                        itemid = name = modified = None
                        trashed = False
                    elif (prefix, event) == ('value.item.removed', 'boolean'):
                        trashed = value
                    elif (prefix, event) == ('value.item.fileId', 'string'):
                        itemid = value
                    elif (prefix, event) == ('value.item.time', 'string'):
                        modified = self.parseDateTime(value)
                    elif (prefix, event) == ('value.item.file.name', 'string'):
                        name = value
                    elif (prefix, event) == ('value.item', 'end_map'):
                        pass
                        #yield itemid, trashed, name, modified
                del events[:]
            parser.close()
            response.close()

    def getDocumentLocation(self, content):
        url = None
        parameter = self.getRequestParameter(content.User.Request, 'getDocumentLocation', content)
        response = content.User.Request.execute(parameter)
        print("Provider.getDocumentContent() Status: %s - IsOk: %s - Reason: %s" % (response.StatusCode, response.Ok, response.Reason))
        if response.Ok and response.hasHeader('Location'):
            url = response.getHeader('Location')
        response.close()
        print("Provider.getDocumentContent() Url: %s" % url)
        return url

    def mergeNewFolder(self, response, user, item):
        return user.DataBase.updateNewItemId(item, self._parseNewFolder(response))

    def _parseNewFolder(self, response):
        newid = created = modified = None
        events = ijson.sendable_list()
        parser = ijson.parse_coro(events)
        iterator = response.iterContent(g_chunk, False)
        while iterator.hasMoreElements():
            parser.send(iterator.nextElement().value)
            for prefix, event, value in events:
                if (prefix, event) == ('id', 'string'):
                    newid = value
                elif (prefix, event) == ('createdDateTime', 'string'):
                    created = self.parseDateTime(value)
                elif (prefix, event) == ('lastModifiedDateTime', 'string'):
                    modified = self.parseDateTime(value)
            del events[:]
        parser.close()
        response.close()
        return newid, created, modified

    def _getUser(self, source, request, name):
        parameter = self.getRequestParameter(request, 'getUser')
        response = request.execute(parameter)
        if not response.Ok:
            msg = self._logger.resolveString(403, name)
            raise IllegalIdentifierException(msg, source)
        user = self._parseUser(response)
        response.close()
        return user

    def _getRoot(self, source, request, name):
        parameter = self.getRequestParameter(request, 'getRoot')
        response = request.execute(parameter)
        if not response.Ok:
            msg = self._logger.resolveString(403, name)
            raise IllegalIdentifierException(msg, source)
        root = self._parseRoot(response)
        response.close()
        return root

    def _parseUser(self, response):
        userid = name = displayname = None
        events = ijson.sendable_list()
        parser = ijson.parse_coro(events)
        iterator = response.iterContent(g_chunk, False)
        while iterator.hasMoreElements():
            parser.send(iterator.nextElement().value)
            for prefix, event, value in events:
                if (prefix, event) == ('id', 'string'):
                    userid = value
                elif (prefix, event) == ('userPrincipalName', 'string'):
                    name = value
                elif (prefix, event) == ('displayName', 'string'):
                    displayname = value
            del events[:]
        parser.close()
        return userid, name, displayname

    def _parseRoot(self, response):
        events = ijson.sendable_list()
        parser = ijson.parse_coro(events)
        iterator = response.iterContent(g_chunk, False)
        while iterator.hasMoreElements():
            parser.send(iterator.nextElement().value)
            for prefix, event, value in events:
                if (prefix, event) == ('id', 'string'):
                    rootid = value
                elif (prefix, event) == ('name', 'string'):
                    name = value
                elif (prefix, event) == ('createdDateTime', 'string'):
                    created = self.parseDateTime(value)
                elif (prefix, event) == ('lastModifiedDateTime', 'string'):
                    modified = self.parseDateTime(value)
            del events[:]
        parser.close()
        return rootid, name, created, modified, g_folder, False, True, False, False, False

    def parseUploadLocation(self, response):
        url =  None
        if response.Ok:
            events = ijson.sendable_list()
            parser = ijson.parse_coro(events)
            iterator = response.iterContent(g_chunk, False)
            while iterator.hasMoreElements():
                parser.send(iterator.nextElement().value)
                for prefix, event, value in events:
                    if (prefix, event) == ('uploadUrl', 'string'):
                        url = value
                del events[:]
            parser.close()
        response.close()
        return url

    def updateItemId(self, database, oldid, response):
        if response is not None:
            if response.Ok:
                newid = self._parseNewId(response)
                if newid and oldid != newid:
                    database.updateItemId(newid, oldid)
                return True
            response.close()
        return False

    def _parseNewId(self, response):
        newid = None
        events = ijson.sendable_list()
        parser = ijson.parse_coro(events)
        iterator = response.iterContent(g_chunk, False)
        while iterator.hasMoreElements():
            parser.send(iterator.nextElement().value)
            for prefix, event, value in events:
                if (prefix, event) == ('id', 'string'):
                    newid = value
            del events[:]
        parser.close()
        response.close()
        return newid

    def updateDrive(self, database, user, token):
        if database.updateToken(user.get('UserId'), token):
            user['Token'] = token

    def getRequestParameter(self, request, method, data=None):
        parameter = request.getRequestParameter(method)
        parameter.Url = self.BaseUrl
        if method == 'getUser':
            parameter.Url += '/me'
            parameter.setQuery('select', g_userfields)

        elif method == 'getRoot':
            parameter.Url += '/me/drive/root'
            parameter.setQuery('select', g_drivefields)

        elif method == 'getItem':
            parameter.Url += '/me/drive/items/'+ data.Id
            parameter.setQuery('select', g_itemfields)

        elif method == 'getFirstPull':
            parameter.Url += '/me/drive/root/delta'
            parameter.setQuery('select', g_itemfields)

        elif method == 'getPull':
            parameter.Url = data.Token
            print("Provider. Name: %s - Url: %s" % (parameter.Name, parameter.Url))

        elif method == 'getFolderContent':
            parameter.Url += '/me/drive/items/%s/children' % data.Id
            parameter.setQuery('select', g_itemfields)
            parameter.setQuery('top', g_pages)

        elif method == 'getDocumentLocation':
            parameter.Url += '/me/drive/items/%s/content' % data.Id
            print("Provider.getRequestParameter() Name: %s - Url: %s" % (parameter.Name, parameter.Url))
            parameter.NoRedirect = True

        elif method == 'getDocumentContent':
            parameter.Url = data
            parameter.NoAuth = True

        elif method == 'updateTitle':
            parameter.Method = 'PATCH'
            parameter.Url += '/me/drive/items/' + data.Id
            parameter.setJson('name', data.get('name'))

        elif method == 'updateTrashed':
            parameter.Method = 'DELETE'
            parameter.Url += '/me/drive/items/' + data.Id

        elif method == 'updateParents':
            parameter.Method = 'PATCH'
            parameter.Url += '/files/' + data.get('Id')
            toadd = data.get('ParentToAdd')
            toremove = data.get('ParentToRemove')
            if len(toadd) > 0:
                parameter.setJson('addParents', ','.join(toadd))
            if len(toremove) > 0:
                parameter.setJson('removeParents', ','.join(toremove))

        elif method == 'createNewFolder':
            parameter.Method = 'POST'
            parameter.Url += '/me/drive/items/%s/children' % data.get('ParentId')
            parameter.setJson('name', data.get('Title'))
            parameter.setJson('folder', None)
            parameter.setJson('@microsoft.graph.conflictBehavior', 'replace')
            print("Provider.createNewFolder() Parameter.Json: '%s'" % parameter.Json)

        elif method in ('getUploadLocation', 'getNewUploadLocation'):
            parameter.Method = 'POST'
            parameter.Url += '/me/drive/items/%s:/%s:/createUploadSession' % (data.get('ParentId'), data.get('Title'))
            parameter.setNesting('item/folder', None)
            parameter.setNesting('item/@odata.type', 'microsoft.graph.driveItemUploadableProperties')
            parameter.setNesting('item/@microsoft.graph.conflictBehavior', 'replace')
            parameter.setNesting('item/name', data.get('Title'))
            print("Provider.getUploadLocation() Parameter.Json: '%s'" % parameter.Json)

        elif method == 'getUploadStream':
            parameter.Method = 'PUT'
            parameter.Url = data
            parameter.NoAuth = True
            parameter.setUpload(ACCEPTED, 'nextExpectedRanges', '([0-9]+)', 0, JSON)

        elif method == 'uploadFile':
            parameter.Method = 'PUT'
            parameter.Url = '/me/drive/items/%s/content' % data.get('ItemId')

        elif method == 'uploadNewFile':
            parameter.Method = 'PUT'
            parameter.Url = '/me/drive/items/%s:/%s:/content' % (data.get('ParentId'), data.get('Title'))
        return parameter


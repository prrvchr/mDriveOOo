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

from com.sun.star.ucb import IllegalIdentifierException

from .ucp import Provider as ProviderBase
from .ucp import g_ucboffice

from .dbtool import currentDateTimeInTZ
from .dbtool import currentUnoDateTime

from .unotool import generateUuid

from .configuration import g_identifier
from .configuration import g_scheme
from .configuration import g_provider
from .configuration import g_host
from .configuration import g_url
from .configuration import g_upload
from .configuration import g_userfields
from .configuration import g_drivefields
from .configuration import g_itemfields
from .configuration import g_chunk
from .configuration import g_pages
from .configuration import g_ucpfolder
from .configuration import g_doc_map

import ijson
import traceback


class Provider(ProviderBase):

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

    def initSharedDocuments(self, user, datetime):
        itemid = generateUuid()
        timestamp = currentUnoDateTime()
        user.DataBase.createSharedFolder(user, itemid, self.SharedFolderName, g_ucpfolder, timestamp, datetime)
        parameter = self.getRequestParameter(user.Request, 'getSharedFolderContent')
        iterator = self._parseSharedFolder(user.Request, parameter, itemid, timestamp)
        user.DataBase.pullItems(iterator, user.Id, datetime, 0)

    def _parseSharedFolder(self, request, parameter, parentid, timestamp):
        parents = [parentid, ]
        trashed = rename = readonly = versionable = False
        addchild = True
        while parameter.hasNextPage():
            response = request.execute(parameter)
            if response.Ok:
                events = ijson.sendable_list()
                parser = ijson.parse_coro(events)
                iterator = response.iterContent(g_chunk, False)
                while iterator.hasMoreElements():
                    parser.send(iterator.nextElement().value)
                    for prefix, event, value in events:
                        if (prefix, event) == ('value.item', 'start_map'):
                            itemid = name = None
                            created = modified = timestamp
                            mimetype = g_ucpfolder
                            link = ''
                            size = 0
                        elif (prefix, event) == ('value.item.remoteItem.id', 'string'):
                            itemid = value
                        elif (prefix, event) == ('value.item.remoteItem.parentReference.driveId', 'string'):
                            link = value
                        elif (prefix, event) == ('value.item.remoteItem.name', 'string'):
                            name = value
                        elif (prefix, event) == ('value.item.remoteItem.size', 'number'):
                            size = value
                        elif (prefix, event) == ('value.item.createdDateTime', 'string'):
                            created = self.parseDateTime(value)
                        elif (prefix, event) == ('value.item.lastModifiedDateTime', 'string'):
                            modified = self.parseDateTime(value)
                        elif (prefix, event) == ('value.item.remoteItem.file.mimeType', 'string'):
                            mimetype = value
                        elif (prefix, event) == ('value.item', 'end_map'):
                            if itemid and name:
                                yield itemid, name, created, modified, mimetype, size, link, trashed, addchild, rename, readonly, versionable, parents, None
                    del events[:]
                parser.close()
            response.close()

    def parseRootFolder(self, parameter, content):
        return self.parseItems(content.User.Request, parameter, content.User.RootId, content.Link)

    def parseItems(self, request, parameter, rootid, link=''):
        readonly = versionable = False
        addchild = rename = True
        while parameter.hasNextPage():
            response = request.execute(parameter)
            if response.Ok:
                timestamp = currentUnoDateTime()
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
                            created = modified = timestamp
                            mimetype = g_ucpfolder
                            size = 0
                            trashed = False
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
                        elif (prefix, event) == ('value.item.size', 'number'):
                            size = value
                        elif (prefix, event) == ('value.item.parentReference.id', 'string'):
                            parents.append(value)
                        elif (prefix, event) == ('value.item', 'end_map'):
                            if itemid and name:
                                yield itemid, name, created, modified, mimetype, size, link, trashed, addchild, rename, readonly, versionable, parents, None
                    del events[:]
                parser.close()
            response.close()

    def parseChanges(self, request, parameter):
        while parameter.hasNextPage():
            response = request.execute(parameter)
            if response.Ok:
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
        parameter = self.getRequestParameter(content.User.Request, 'getDocumentLocation', content)
        response = content.User.Request.execute(parameter)
        print("Provider.getDocumentContent() Status: %s - IsOk: %s - Reason: %s" % (response.StatusCode, response.Ok, response.Reason))
        url = self._parseDocumentLocation(response)
        print("Provider.getDocumentContent() Url: %s" % url)
        return url

    def _parseDocumentLocation(self, response):
        url = None
        if response.Ok and response.hasHeader('Location'):
            url = response.getHeader('Location')
        response.close()
        return url

    def mergeNewFolder(self, user, oldid, response):
        newid = None
        if response.Ok:
            items = self._parseNewFolder(response)
            if all(items):
                newid = user.DataBase.updateNewItemId(oldid, *items)
        else:
            print("Provider.mergeNewFolder() %s" % response.Text)
        response.close()
        return newid

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
                elif (prefix, event) == ('createdDateTime', 'string'):
                    created = self.parseDateTime(value)
                elif (prefix, event) == ('lastModifiedDateTime', 'string'):
                    modified = self.parseDateTime(value)
            del events[:]
        parser.close()
        return rootid, created, modified

    def parseUploadLocation(self, response):
        url =  None
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
        newid = self._parseNewId(response)
        if newid and oldid != newid:
            database.updateItemId(newid, oldid)
            self.updateNewItemId(oldid, newid)
        return newid

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
            parameter.setQuery('$select', g_userfields)

        elif method == 'getRoot':
            parameter.Url += '/me/drive/root'
            parameter.setQuery('$select', g_drivefields)

        elif method == 'getItem':
            parameter.Url += '/me/drive/items/'+ data.Id
            parameter.setQuery('$select', g_itemfields)

        elif method == 'getFirstPull':
            parameter.Url += '/me/drive/root/delta'
            parameter.setQuery('$select', g_itemfields)

        elif method == 'getPull':
            parameter.Url = data.Token
            print("Provider. Name: %s - Url: %s" % (parameter.Name, parameter.Url))

        elif method == 'getSharedFolderContent':
            parameter.Url += '/me/drive/sharedWithMe'

        elif method == 'getFolderContent':
            if data.Link:
                url = '/drives/%s/items/%s/children' % (data.Link, data.Id)
            else:
                url = '/me/drive/items/%s/children' % data.Id
            print("Provider.getFolderContent() Url: %s" % url)
            parameter.Url += url
            parameter.setQuery('$select', g_itemfields)
            parameter.setQuery('$top', g_pages)

        elif method == 'getDocumentLocation':
            if data.Link:
                url = '/drives/%s/items/%s/content' % (data.Link, data.Id)
            else:
                url = '/me/drive/items/%s/content' % data.Id
            parameter.Url += url
            print("Provider.getRequestParameter() Name: %s - Url: %s" % (parameter.Name, parameter.Url))
            parameter.NoRedirect = True

        elif method == 'getDocumentContent':
            parameter.Url = data
            parameter.NoAuth = True

        elif method == 'updateTitle':
            parameter.Method = 'PATCH'
            parameter.Url += '/me/drive/items/' + data.get('Id')
            parameter.setJson('name', data.get('Title'))

        elif method == 'updateTrashed':
            parameter.Method = 'DELETE'
            parameter.Url += '/me/drive/items/' + data.get('Id')

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
            if data.get('Link'):
                url = '/drives/%s/items/%s/children' % (data.get('Link'), data.get('ParentId'))
            else:
                url = '/me/drive/items/%s/children' % data.get('ParentId')
            parameter.Url += url
            parameter.setJson('name', data.get('Title'))
            # FIXME: We need to bee able to construct a JSON object like:
            # FIXME: {folder:{}, } then it's done by a trailing slash...
            parameter.setJson('folder/', None)
            parameter.setJson('@microsoft.graph.conflictBehavior', 'replace')
            print("Provider.createNewFolder() Parameter.Json: '%s'" % parameter.Json)

        elif method == 'getUploadLocation':
            parameter.Method = 'POST'
            if data.get('Link'):
                url = '/drives/%s/items/%s/createUploadSession' % (data.get('Link'), data.get('Id'))
            else:
                url = '/me/drive/items/%s/createUploadSession' % data.get('Id')
            parameter.Url += url
            print("Provider.getUploadLocation() Parameter.Json: '%s'" % parameter.Json)

        elif method == 'getNewUploadLocation':
            parameter.Method = 'POST'
            if data.get('Link'):
                url = '/drives/%s/items/%s:/%s:/createUploadSession' % (data.get('Link'), data.get('ParentId'), data.get('Title'))
            else:
                url = '/me/drive/items/%s:/%s:/createUploadSession' % (data.get('ParentId'), data.get('Title'))
            parameter.Url += url
            parameter.setJson('item/@odata.type', 'microsoft.graph.driveItemUploadableProperties')
            parameter.setJson('item/@microsoft.graph.conflictBehavior', 'replace')
            parameter.setJson('item/name', data.get('Title'))
            print("Provider.getNewUploadLocation() Parameter.Json: '%s'" % parameter.Json)

        elif method == 'getUploadStream':
            parameter.Method = 'PUT'
            parameter.Url = data
            parameter.NoAuth = True
            parameter.setUpload(ACCEPTED, 'nextExpectedRanges', '([0-9]+)', 0, JSON)

        elif method == 'uploadFile':
            parameter.Method = 'PUT'
            if data.get('Link'):
                url = '/drives/%s/items/%s/content' % (data.get('Link'), data.get('Id'))
            else:
                url = '/me/drive/items/%s/content' % data.get('Id')
            parameter.Url += url

        elif method == 'uploadNewFile':
            parameter.Method = 'PUT'
            if data.get('Link'):
                url = '/drives/%s/items/%s:/%s:/content' % (data.get('Link'), data.get('ParentId'), data.get('Title'))
            else:
                url = '/me/drive/items/%s:/%s:/content' % (data.get('ParentId'), data.get('Title'))
            parameter.Url += url
        return parameter


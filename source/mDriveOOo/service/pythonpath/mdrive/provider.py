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

from com.sun.star.logging.LogLevel import INFO

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
    def BaseUrl(self):
        return g_url
    @property
    def Host(self):
        return g_host
    @property
    def Name(self):
        return g_provider
    @property
    def UploadUrl(self):
        return g_upload

    # Must be implemented method
    def getDocumentLocation(self, user, item):
        url = None
        parameter = self.getRequestParameter(user.Request, 'getDocumentLocation', item)
        response = user.Request.execute(parameter)
        if response.Ok and response.hasHeader('Location'):
            url = response.getHeader('Location')
        response.close()
        return url

    def getFirstPullRoots(self, user):
        return (user.RootId, )

    def getUser(self, source, request, name):
        user = self._getUser(source, request)
        user.update(self._getRoot(source, request))
        return user

    def mergeNewFolder(self, user, oldid, response):
        newid = None
        items = self._parseNewFolder(response)
        if all(items):
            newid = user.DataBase.updateNewItemId(user.Id, oldid, *items)
        return newid

    def parseFolder(self, user, data, parameter):
        # XXX: Link may not be present and in this case must be an empty string
        link = data.get('Link', '')
        return self.parseItems(user.Request, parameter, user.RootId, link)

    def parseItems(self, request, parameter, rootid, link=''):
        readonly = versionable = False
        addchild = canrename = True
        path = None
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
                            parents = (rootid, )
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
                            parents = (value, )
                        elif (prefix, event) == ('value.item', 'end_map'):
                            if itemid and name:
                                yield {'Id': itemid,
                                       'Name': name,
                                       'DateCreated': created,
                                       'DateModified': modified,
                                       'MediaType': mimetype,
                                       'Size': size,
                                       'Link': link,
                                       'Trashed': trashed,
                                       'CanAddChild': addchild,
                                       'CanRename': canrename,
                                       'IsReadOnly': readonly,
                                       'IsVersionable': versionable,
                                       'Parents': parents,
                                       'Path': path}
                    del events[:]
                parser.close()
            response.close()

    def parseUploadLocation(self, response):
        url = response.getJson().getString('uploadUrl')
        response.close()
        return url

    def updateItemId(self, user, oldid, response):
        newid = response.getJson().getString('id')
        response.close()
        if oldid != newid:
            user.DataBase.updateItemId(user.Id, newid, oldid)
            self.updateNewItemId(oldid, newid)
        return newid

    # Can be rewrited method
    def initSharedDocuments(self, user, reset, datetime):
        count = download = 0
        folder = {'Id':            user.ShareId,
                  'Name':          self.SharedFolderName,
                  'DateCreated':   user.DateCreated,
                  'DateModified':  user.DateModified,
                  'MediaType':     g_ucpfolder,
                  'Size':          0,
                  'Link':          '',
                  'Trashed':       False,
                  'CanAddChild':   False,
                  'CanRename':     False,
                  'IsReadOnly':    False,
                  'IsVersionable': False,
                  'Parents':       (user.RootId),
                  'Path':          None}
        user.DataBase.mergeItem(user.Id, user.RootId, datetime, folder)
        parameter = self.getRequestParameter(user.Request, 'getSharedFolderContent')
        items = self._parseSharedFolder(user.Request, parameter, user.ShareId)
        for item in user.DataBase.mergeItems(user.Id, user.ShareId, datetime, items):
            count += 1
            if reset:
                download += self.pullFileContent(user, item)
        return count, download, parameter.PageCount

    # Private method
    def _getRoot(self, source, request):
        parameter = self.getRequestParameter(request, 'getRoot')
        response = request.execute(parameter)
        if not response.Ok:
            self.raiseIllegalIdentifierException(source, 571, parameter, reponse)
        root = self._parseRoot(response)
        response.close()
        return root

    def _getUser(self, source, request):
        parameter = self.getRequestParameter(request, 'getUser')
        response = request.execute(parameter)
        if not response.Ok:
            self.raiseIllegalIdentifierException(source, 561, parameter, reponse)
        user = self._parseUser(response)
        response.close()
        return user

    def _parseNewFolder(self, response):
        newid = created = modified = None
        if response.Ok:
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
        return {'RootId': rootid, 'DateCreated': created, 'DateModified': modified}

    def _parseSharedFolder(self, request, parameter, parentid):
        parents = (parentid, )
        timestamp = currentUnoDateTime()
        trashed = canrename = readonly = versionable = False
        addchild = True
        path = None
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
                                yield {'Id': itemid,
                                       'Name': name,
                                       'DateCreated': created,
                                       'DateModified': modified,
                                       'MediaType': mimetype,
                                       'Size': size,
                                       'Link': link,
                                       'Trashed': trashed,
                                       'CanAddChild': addchild,
                                       'CanRename': canrename,
                                       'IsReadOnly': readonly,
                                       'IsVersionable': versionable,
                                       'Parents': parents,
                                       'Path': path}
                    del events[:]
                parser.close()
            response.close()

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
        return {'Id': userid, 'Name': name, 'DisplayName': displayname}

    # Requests get Parameter method
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
            if data.get('Link'):
                url = '/drives/%s/items/%s/children' % (data.get('Link'), data.get('Id'))
            else:
                url = '/me/drive/items/%s/children' % data.get('Id')
            print("Provider.getFolderContent() Url: %s" % url)
            parameter.Url += url
            parameter.setQuery('$select', g_itemfields)
            parameter.setQuery('$top', g_pages)

        elif method == 'getDocumentLocation':
            if data.get('Link'):
                url = '/drives/%s/items/%s/content' % (data.get('Link'), data.get('Id'))
            else:
                url = '/me/drive/items/%s/content' % data.get('Id')
            parameter.Url += url
            print("Provider.getRequestParameter() Name: %s - Url: %s" % (parameter.Name, parameter.Url))
            parameter.NoRedirect = True

        elif method == 'downloadFile':
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


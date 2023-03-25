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

from com.sun.star.ucb.ConnectionMode import OFFLINE

from com.sun.star.auth.RestRequestTokenType import TOKEN_NONE
from com.sun.star.auth.RestRequestTokenType import TOKEN_URL
from com.sun.star.auth.RestRequestTokenType import TOKEN_REDIRECT
from com.sun.star.auth.RestRequestTokenType import TOKEN_QUERY
from com.sun.star.auth.RestRequestTokenType import TOKEN_JSON
from com.sun.star.auth.RestRequestTokenType import TOKEN_SYNC

from onedrive import KeyMap
from onedrive import ProviderBase

from onedrive import toUnoDateTime

from onedrive import g_identifier
from onedrive import g_provider
from onedrive import g_host
from onedrive import g_url
from onedrive import g_userfields
from onedrive import g_drivefields
from onedrive import g_itemfields
from onedrive import g_chunk
from onedrive import g_buffer
from onedrive import g_pages
from onedrive import g_folder
from onedrive import g_office
from onedrive import g_link
from onedrive import g_doc_map

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = '%s.Provider' % g_identifier


class Provider(ProviderBase):
    def __init__(self, ctx):
        self._ctx = ctx
        self.Scheme = ''
        self.Plugin = ''
        self.Link = ''
        self.Folder = ''
        self.SourceURL = ''
        self.SessionMode = OFFLINE
        self._Error = ''
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
    def Chunk(self):
        return g_chunk
    @property
    def Buffer(self):
        return g_buffer
    @property
    def TimeStampPattern(self):
        return '%Y-%m-%dT%H:%M:%S.0'

    def getRequestParameter(self, method, data=None):
        parameter = uno.createUnoStruct('com.sun.star.auth.RestRequestParameter')
        parameter.Name = method
        if method == 'getUser':
            parameter.Method = 'GET'
            parameter.Url = '%s/me' % self.BaseUrl
            parameter.Query = '{"select": "%s"}' % g_userfields
        elif method == 'getItem':
            parameter.Method = 'GET'
            parameter.Url = '%s/me/drive/items/%s' % (self.BaseUrl, data.getValue('Id'))
            parameter.Query = '{"select": "%s"}' % g_itemfields
        elif method == 'getRoot':
            parameter.Method = 'GET'
            parameter.Url = '%s/me/drive/root' % self.BaseUrl
            parameter.Query = '{"select": "%s"}' % g_drivefields
        elif method == 'getFirstPull':
            parameter.Method = 'GET'
            parameter.Url = '%s/me/drive/root/delta' % self.BaseUrl
            parameter.Query = '{"select": "%s"}' % g_itemfields
            token = uno.createUnoStruct('com.sun.star.auth.RestRequestToken')
            token.Type = TOKEN_REDIRECT | TOKEN_SYNC
            token.Field = '@odata.nextLink'
            token.SyncField = '@odata.deltaLink'
            enumerator = uno.createUnoStruct('com.sun.star.auth.RestRequestEnumerator')
            enumerator.Field = 'value'
            enumerator.Token = token
            parameter.Enumerator = enumerator
        elif method == 'getPull':
            parameter.Method = 'GET'
            parameter.Url = data.getValue('Token')
            parameter.Query = '{"select": "%s"}' % g_itemfields
            token = uno.createUnoStruct('com.sun.star.auth.RestRequestToken')
            token.Type = TOKEN_REDIRECT | TOKEN_SYNC
            token.Field = '@odata.nextLink'
            token.SyncField = '@odata.deltaLink'
            enumerator = uno.createUnoStruct('com.sun.star.auth.RestRequestEnumerator')
            enumerator.Field = 'value'
            enumerator.Token = token
            parameter.Enumerator = enumerator
        elif method == 'getFolderContent':
            parameter.Method = 'GET'
            parameter.Url = '%s/me/drive/items/%s/children' % (self.BaseUrl, data.getValue('Id'))
            parameter.Query = '{"select": "%s", "top": "%s"}' % (g_itemfields, g_pages)
            token = uno.createUnoStruct('com.sun.star.auth.RestRequestToken')
            token.Type = TOKEN_REDIRECT
            token.Field = '@odata:nextLink'
            enumerator = uno.createUnoStruct('com.sun.star.auth.RestRequestEnumerator')
            enumerator.Field = 'value'
            enumerator.Token = token
            parameter.Enumerator = enumerator
        elif method == 'getDocumentLocation':
            parameter.Method = 'GET'
            parameter.Url = '%s/me/drive/items/%s/content' % (self.BaseUrl, data.getValue('Id'))
            parameter.NoRedirect = True
        elif method == 'getDocumentContent':
            parameter.Method = 'GET'
            parameter.Url = data.getValue('Location')
            parameter.NoAuth = True
        elif method == 'updateTitle':
            parameter.Method = 'PATCH'
            parameter.Url = '%s/me/drive/items/%s' % (self.BaseUrl, data.getValue('Id'))
            parameter.Json = '{"name": "%s"}' % data.getValue('name')
        elif method == 'updateTrashed':
            parameter.Method = 'DELETE'
            parameter.Url = '%s/me/drive/items/%s' % (self.BaseUrl, data.getValue('Id'))

        elif method == 'updateParents':
            parameter.Method = 'PATCH'
            parameter.Url = '%s/files/%s' % (self.BaseUrl, data.getValue('Id'))
            toadd = data.getValue('ParentToAdd')
            toremove = data.getValue('ParentToRemove')
            if len(toadd) > 0:
                parameter.Json = '{"addParents": %s}' % ','.join(toadd)
            if len(toremove) > 0:
                parameter.Json = '{"removeParents": %s}' % ','.join(toremove)

        elif method == 'createNewFolder':
            parameter.Method = 'POST'
            url = '%s/me/drive/items/%s/children' % (self.BaseUrl, data.getValue('ParentId'))
            parameter.Url = url
            rename = '"@microsoft.graph.conflictBehavior": "replace"'
            parameter.Json = '{"name": "%s", "folder": { }, %s}' % (data.getValue('Title'), rename)
        elif method in ('getUploadLocation', 'getNewUploadLocation'):
            parameter.Method = 'POST'
            url, parent, name = self.BaseUrl, data.getValue('ParentId'), data.getValue('Title')
            parameter.Url = '%s/me/drive/items/%s:/%s:/createUploadSession' % (url, parent, name)
            odata = '"@odata.type": "microsoft.graph.driveItemUploadableProperties"'
            onconflict = '"@microsoft.graph.conflictBehavior": "replace"'
            parameter.Json = '{"item": {%s, %s, "name": "%s"}}' % (odata, onconflict, name)
        elif method == 'getUploadStream':
            parameter.Method = 'PUT'
            parameter.Url = data.getValue('uploadUrl')
            parameter.NoAuth = True
        return parameter

    def getUserId(self, user):
        return user.getValue('id')
    def getUserName(self, user):
        return user.getValue('userPrincipalName')
    def getUserDisplayName(self, user):
        return user.getValue('displayName')

    def getItemParent(self, item, rootid):
        ref = item.getDefaultValue('parentReference', KeyMap())
        parent = ref.getDefaultValue('id', rootid)
        return (parent, )

    def getItemId(self, item):
        return item.getDefaultValue('id', None)
    def getItemTitle(self, item):
        return item.getDefaultValue('name', None)
    def getItemCreated(self, item, timestamp=None):
        created = item.getDefaultValue('createdDateTime', None)
        if created:
            return self.parseDateTime(created)
        return toUnoDateTime(timestamp)
    def getItemModified(self, item, timestamp=None):
        modified = item.getDefaultValue('lastModifiedDateTime', None)
        if modified:
            return self.parseDateTime(modified)
        return toUnoDateTime(timestamp)
    def getItemMediaType(self, item):
        return item.getDefaultValue('file', KeyMap()).getDefaultValue('mimeType', self.Folder)
    def getItemSize(self, item):
        return int(item.getDefaultValue('size', 0))
    def getItemTrashed(self, item):
        return item.getDefaultValue('trashed', False)
    def getItemCanAddChild(self, item):
        return True
    def getItemCanRename(self, item):
        return True
    def getItemIsReadOnly(self, item):
        return False
    def getItemIsVersionable(self, item):
        return False

    def updateDrive(self, database, user, token):
        if database.updateToken(user.getValue('UserId'), token):
            user.setValue('Token', token)
    def setDriveContent1(self, item):
        if self._isFolder(item):
            self._folders.append(self.getItemId(item))

    def getDocumentContent(self, request, content):
        parameter = self.getRequestParameter('getDocumentLocation', content)
        response = request.execute(parameter)
        if response.IsPresent:
            parameter = self.getRequestParameter('getDocumentContent', response.Value)
            return request.getInputStream(parameter, self.Chunk, self.Buffer)
        return None

    def _isFolder(self, item):
        folder = item.getDefaultValue('file', None)
        return folder is None

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(Provider,
                                         g_ImplementationName,
                                        (g_ImplementationName, ))

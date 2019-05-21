#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.ucb.RestRequestTokenType import TOKEN_NONE
from com.sun.star.ucb.RestRequestTokenType import TOKEN_URL
from com.sun.star.ucb.RestRequestTokenType import TOKEN_REDIRECT
from com.sun.star.ucb.RestRequestTokenType import TOKEN_QUERY
from com.sun.star.ucb.RestRequestTokenType import TOKEN_JSON

# clouducp is only available after CloudUcpOOo as been loaded...
try:
    from clouducp import ProviderBase
    from clouducp import KeyMap
except ImportError:
    class ProviderBase():
        pass

from onedrive import g_plugin
from onedrive import g_host
from onedrive import g_url
from onedrive import g_userfields
from onedrive import g_drivefields
from onedrive import g_itemfields
from onedrive import g_pages
from onedrive import g_folder
from onedrive import g_office
from onedrive import g_link
from onedrive import g_doc_map
from onedrive import g_chunk
from onedrive import g_buffer

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = '%s.Provider' % g_plugin


class Provider(ProviderBase):
    def __init__(self, ctx):
        ProviderBase.__init__(self, ctx)

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
    def Folder(self):
        return g_folder
    @property
    def Link(self):
        return g_link
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
        parameter = uno.createUnoStruct('com.sun.star.ucb.RestRequestParameter')
        parameter.Name = method
        if method == 'getUser':
            parameter.Method = 'GET'
            parameter.Url = '%s/me' % self.BaseUrl
            parameter.Query = '{"select": "%s"}' % g_userfields
        elif method == 'getRoot':
            parameter.Method = 'GET'
            parameter.Url = '%s/me/drive/root' % self.BaseUrl
            parameter.Query = '{"select": "%s"}' % g_drivefields
        elif method == 'getItem':
            parameter.Method = 'GET'
            parameter.Url = '%s/me/drive/items/%s' % (self.BaseUrl, data.getValue('Id'))
            parameter.Query = '{"select": "%s"}' % g_itemfields
        elif method == 'getFolderContent':
            parameter.Method = 'GET'
            parameter.Url = '%s/me/drive/items/%s/children' % (self.BaseUrl, data.getValue('Id'))
            parameter.Query = '{"select": "%s", "top": "%s"}' % (g_itemfields, g_pages)
            token = uno.createUnoStruct('com.sun.star.ucb.RestRequestToken')
            token.Type = TOKEN_REDIRECT
            token.Field = '@odata:nextLink'
            enumerator = uno.createUnoStruct('com.sun.star.ucb.RestRequestEnumerator')
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
            parameter.Url = '%s/me/drive/items/%s' % (self.BaseUrl, data.getValue('id'))
            parameter.Json = '{"name": "%s"}' % data.getValue('name')
        elif method == 'updateTrashed':
            parameter.Method = 'DELETE'
            parameter.Url = '%s/me/drive/items/%s' % (self.BaseUrl, data.getValue('id'))
        elif method == 'insertContent':
            parameter.Method = 'POST'
            url = '%s/me/drive/items/%s/children' % (self.BaseUrl, data.getValue('parent'))
            parameter.Url = url
            rename = '"@microsoft.graph.conflictBehavior": "replace"'
            parameter.Json = '{"name": "%s", "folder": { }, %s}' % (data.getValue('name'), rename)

        elif method == 'getUploadLocation':
            parameter.Method = 'POST'
            url, parent, name = self.BaseUrl, data.getValue('parent'), data.getValue('name')
            parameter.Url = '%s/me/drive/items/%s:/%s:/createUploadSession' % (url, parent, name)
            odata = '"@odata.type": "microsoft.graph.driveItemUploadableProperties"'
            onconflict = '"@microsoft.graph.conflictBehavior": "replace"'
            parameter.Json = '{"item": {%s, %s, "name": "%s"}}' % (odata, onconflict, name)
        elif method == 'getUploadStream':
            parameter.Method = 'PUT'
            parameter.Url = data.getValue('uploadUrl')
            parameter.NoAuth = True
            parameter.Optional = 'id'
        return parameter

    def getUserId(self, user):
        return user.getValue('id')
    def getUserName(self, user):
        return user.getValue('userPrincipalName')
    def getUserDisplayName(self, user):
        return user.getValue('displayName')

    def getItemParent(self, item, rootid):
        return item.getDefaultValue('parentReference', KeyMap()).getDefaultValue('id', rootid)

    def getItemId(self, item):
        return item.getDefaultValue('id', None)
    def getItemName(self, item):
        return item.getDefaultValue('name', None)
    def getItemCreated(self, item, timestamp=None):
        if timestamp:
            created = item.getDefaultValue('createdDateTime', timestamp)
            created = created[:21]
        else:
            created = item.getValue('createdDateTime')
        return created
    def getItemModified(self, item, timestamp=None):
        if timestamp:
            modified = item.getDefaultValue('lastModifiedDateTime', timestamp)
            modified = modified[:21]
        else:
            modified = item.getValue('lastModifiedDateTime')
        return modified
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

    def getDocumentContent(self, content):
        parameter = self.getRequestParameter('getDocumentLocation', content)
        response = self.Request.execute(parameter)
        if response.IsPresent:
            parameter = self.getRequestParameter('getDocumentContent', response.Value)
            return self.Request.getInputStream(parameter, self.Chunk, self.Buffer)
        return None

    def getUploadParameter(self, identifier, new):
        parameter = self.getRequestParameter('getUploadLocation', identifier)
        response = self.Request.execute(parameter)
        if response.IsPresent:
            return self.getRequestParameter('getUploadStream', response.Value)
        return None

    def getUpdateParameter(self, identifier, new, key):
        if new:
             parameter = self.getRequestParameter('insertContent', identifier)
        elif key == 'Title':
            parameter = self.getRequestParameter('updateTitle', identifier)
        elif key == 'Trashed':
            parameter = self.getRequestParameter('updateTrashed', identifier)
        return parameter

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

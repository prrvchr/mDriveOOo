#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.embed import XTransactedObject
from com.sun.star.util import XUpdatable

from unolib import PropertySet
from unolib import getProperty
from unolib import getConfiguration
from unolib import KeyMap

from .configuration import g_identifier
from .configuration import g_refresh_overlap

import time


class OAuth2Setting(unohelper.Base,
                    XTransactedObject,
                    PropertySet):
    def __init__(self, ctx):
        self.ctx = ctx
        self.configuration = getConfiguration(self.ctx, g_identifier, True)
        self.Url = UrlSetting(self.configuration)
        self.revert()

    @property
    def Timeout(self):
        if self.ConnectTimeout and self.ReadTimeout:
            return self.ConnectTimeout, self.ReadTimeout
        elif self.ConnectTimeout:
            return self.ConnectTimeout
        elif self.ReadTimeout:
            return self.ReadTimeout
        return None

    @property
    def Initialized(self):
        return all((self.Url.Scope.Provider.MetaData, self.Url.Scope.Provider.User.IsValid))

    # XTransactedObject
    def commit(self):
        self.configuration.replaceByName('ConnectTimeout', self.ConnectTimeout)
        self.configuration.replaceByName('ReadTimeout', self.ReadTimeout)
        self.configuration.replaceByName('HandlerTimeout', self.HandlerTimeout)
        if self.configuration.hasPendingChanges():
            self.configuration.commitChanges()
    def revert(self):
        self.HandlerTimeout = self.configuration.getByName('HandlerTimeout')
        self.ConnectTimeout = self.configuration.getByName('ConnectTimeout')
        self.ReadTimeout = self.configuration.getByName('ReadTimeout')

    def _getPropertySetInfo(self):
        properties = {}
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['Url'] = getProperty('Url', 'com.sun.star.uno.XInterface', readonly)
        properties['HandlerTimeout'] = getProperty('HandlerTimeout', 'short', transient)
        properties['ConnectTimeout'] = getProperty('ConnectTimeout', 'short', transient)
        properties['ReadTimeout'] = getProperty('ReadTimeout', 'short', transient)
        properties['Timeout'] = getProperty('Timeout', 'any', readonly)
        properties['Initialized'] = getProperty('Initialized', 'boolean', readonly)
        return properties


class UrlSetting(unohelper.Base,
                 PropertySet):
    def __init__(self, configuration):
        self.configuration = configuration
        self.Scope = ScopeSetting(self.configuration)
        self._Id = ''
        self.Urls = self._getUrls()

    @property
    def Id(self):
        return self._Id
    @Id.setter
    def Id(self, id):
        self.Urls = self._getUrls()
        if id in self.Urls:
            self._Id = id
            scope = self.Urls[id]
        else:
            self._Id = ''
            scope = ''
        self.Scope.Id = scope

    @property
    def UrlList(self):
        return tuple(self.Urls.keys())
    @property
    def Initialized(self):
        return self.Id != ''

    def _getUrls(self):
        urls = {}
        url = self.configuration.getByName('Urls')
        for id in url.ElementNames:
            urls[id] = url.getByName(id).getByName('Scope')
        return urls

    def _getPropertySetInfo(self):
        properties = {}
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['Scope'] = getProperty('Scope', 'com.sun.star.uno.XInterface', readonly)
        properties['Id'] = getProperty('Id', 'string', transient)
        properties['UrlList'] = getProperty('UrlList', '[]string', readonly)
        properties['Initialized'] = getProperty('Initialized', 'boolean', readonly)
        return properties


class ScopeSetting(unohelper.Base,
                   PropertySet):
    def __init__(self, configuration):
        self._Id = ''
        self._Scopes = []
        self.configuration = configuration
        self.Provider = ProviderSetting(self.configuration)

    @property
    def Id(self):
        return self._Id
    @Id.setter
    def Id(self, id):
        scopes = self.configuration.getByName('Scopes')
        if scopes.hasByName(id):
            self._Id = id
            s = scopes.getByName(id)
            self._Scopes = s.getByName('Values')
            provider = s.getByName('Provider')
        else:
            self._Id = ''
            self._Scopes = []
            provider = ''
        self.Provider.Id = provider

    @property
    def Authorized(self):
        authorized = len(self._Scopes) > 0
        for scope in self._Scopes:
            if scope not in self.Provider.User.Scopes:
                authorized = False
                break
        return authorized

    def _getPropertySetInfo(self):
        properties = {}
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['Provider'] = getProperty('Provider', 'com.sun.star.uno.XInterface', readonly)
        properties['Id'] = getProperty('Id', 'string', transient)
        properties['Authorized'] = getProperty('Authorized', 'boolean', readonly)
        return properties


class ProviderSetting(unohelper.Base,
                      XTransactedObject,
                      PropertySet):
    def __init__(self, configuration):
        self.configuration = configuration
        self.User = UserSetting(self.configuration)
        self.MetaData = None

    @property
    def Id(self):
        return self.User._ProviderId
    @Id.setter
    def Id(self, id):
        self.User._ProviderId = id
        self.MetaData = self._getMetaData(id)

    def _getMetaData(self, id):
        metadata = None
        providers = self.configuration.getByName('Providers')
        if providers.hasByName(id):
            provider = providers.getByName(id)
            metadata = KeyMap()
            metadata.insertValue('ClientSecret', provider.getByName('ClientSecret'))
            metadata.insertValue('ClientId', provider.getByName('ClientId'))
            metadata.insertValue('TokenUrl', provider.getByName('TokenUrl'))
            metadata.insertValue('TokenParameters', provider.getByName('TokenParameters'))
        return metadata

    def _getPropertySetInfo(self):
        properties = {}
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        properties['User'] = getProperty('User', 'com.sun.star.uno.XInterface', readonly)
        properties['MetaData'] = getProperty('MetaData', 'com.sun.star.auth.XRestKeyMap', readonly)
        return properties


class UserSetting(unohelper.Base,
                  XTransactedObject,
                  PropertySet):
    def __init__(self, configuration):
        self.configuration = configuration
        self._Id = ''
        self._ProviderId = ''
        self._TimeStamp = 0
        self.Scopes = ()
        self.AccessToken = ''
        self.RefreshToken = ''
        self.NeverExpires = False

    @property
    def Id(self):
        return self._Id
    @Id.setter
    def Id(self, id):
        self._Id = id
        self.revert()
    @property
    def HasExpired(self):
        if self.NeverExpires:
            return False
        now = int(time.time())
        expire  = max(0, self._TimeStamp - now)
        return expire < g_refresh_overlap
    @property
    def MetaData(self):
        metadata = KeyMap()
        metadata.insertValue('AccessToken', self.AccessToken)
        metadata.insertValue('RefreshToken', self.RefreshToken)
        metadata.insertValue('NeverExpires', self.NeverExpires)
        metadata.insertValue('TimeStamp', self._TimeStamp)
        metadata.insertValue('Scopes', self.Scopes)
        return metadata
    @MetaData.setter
    def MetaData(self, data):
        self.AccessToken = data.getValue('AccessToken')
        self.RefreshToken = data.getValue('RefreshToken')
        self.NeverExpires = data.getValue('NeverExpires')
        self._TimeStamp = data.getValue('TimeStamp')
        self.Scopes = data.getValue('Scopes')
        self.commit()
    @property
    def IsValid(self):
        return all((self._ProviderId, self.Id, self.AccessToken, self.RefreshToken, self.Scopes))

    # XTransactedObject
    def commit(self):
        providers = self.configuration.getByName('Providers')
        if providers.hasByName(self._ProviderId):
            provider = providers.getByName(self._ProviderId)
            users = provider.getByName('Users')
            if users.hasByName(self.Id):
                user = users.getByName(self.Id)
                user.replaceByName('AccessToken', self.AccessToken)
                user.replaceByName('RefreshToken', self.RefreshToken)
                user.replaceByName('NeverExpires', self.NeverExpires)
                user.replaceByName('TimeStamp', self._TimeStamp)
                arguments = ('Scopes', uno.Any('[]string', self.Scopes))
                uno.invoke(user, 'replaceByName', arguments)
                if self.configuration.hasPendingChanges():
                    self.configuration.commitChanges()
    def revert(self):
        accesstoken = ''
        refreshtoken = ''
        neverexpires = False
        timestamp = 0
        scopes = ()
        providers = self.configuration.getByName('Providers')
        if providers.hasByName(self._ProviderId):
            provider = providers.getByName(self._ProviderId)
            users = provider.getByName('Users')
            if users.hasByName(self.Id):
                user = users.getByName(self.Id)
                accesstoken = user.getByName('AccessToken')
                refreshtoken = user.getByName('RefreshToken')
                neverexpires = user.getByName('NeverExpires')
                timestamp = user.getByName('TimeStamp')
                scopes = user.getByName('Scopes')
        self.AccessToken = accesstoken
        self.RefreshToken = refreshtoken
        self.NeverExpires = neverexpires
        self._TimeStamp = timestamp
        self.Scopes = scopes

    def _getPropertySetInfo(self):
        properties = {}
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['Id'] = getProperty('Id', 'string', transient)
        properties['AccessToken'] = getProperty('AccessToken', 'string', readonly)
        properties['HasExpired'] = getProperty('HasExpired', 'boolean', readonly)
        properties['IsValid'] = getProperty('IsValid', 'boolean', readonly)
        properties['Scopes'] = getProperty('Scopes', '[]string', readonly)
        properties['MetaData'] = getProperty('MetaData', 'com.sun.star.auth.XRestKeyMap', transient)
        return properties

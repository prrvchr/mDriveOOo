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


class WizardSetting(unohelper.Base,
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
    def UrlList(self):
        names = []
        for key, value in self.Url.Urls.items():
            if value['State'] < 8:
                names.append(key)
        return tuple(names)

    # XTransactedObject
    def commit(self):
        self.configuration.replaceByName('ConnectTimeout', self.ConnectTimeout)
        self.configuration.replaceByName('ReadTimeout', self.ReadTimeout)
        self.configuration.replaceByName('HandlerTimeout', self.HandlerTimeout)
        self.Url.commit()
        self.Url.Scope.commit()
        self.Url.Scope.Provider.commit()
        self.Url.Scope.Provider.User.commit()
    def revert(self):
        self.HandlerTimeout = self.configuration.getByName('HandlerTimeout')
        self.ConnectTimeout = self.configuration.getByName('ConnectTimeout')
        self.ReadTimeout = self.configuration.getByName('ReadTimeout')

    def _getPropertySetInfo(self):
        properties = {}
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['Url'] = getProperty('Url', 'com.sun.star.uno.XInterface', readonly)
        properties['UrlList'] = getProperty('UrlList', '[]string', readonly)
        properties['HandlerTimeout'] = getProperty('HandlerTimeout', 'short', transient)
        properties['ConnectTimeout'] = getProperty('ConnectTimeout', 'short', transient)
        properties['ReadTimeout'] = getProperty('ReadTimeout', 'short', transient)
        properties['Timeout'] = getProperty('Timeout', 'any', readonly)
        properties['Logger'] = getProperty('Logger', 'com.sun.star.logging.XLogger', readonly)
        return properties


class UrlSetting(unohelper.Base,
                 XTransactedObject,
                 PropertySet):
    def __init__(self, configuration):
        self.configuration = configuration
        self.Scope = ScopeSetting(self.configuration)
        self._Id = ''
        self.Urls = {}
        self.revert()

    @property
    def Id(self):
        return self._Id
    @Id.setter
    def Id(self, id):
        self._Id = id
        if id and id not in self.Urls:
            self.Urls[id] = {'Scope': '', 'State': 2}
        scope = ''
        if id in self.Urls:
            scope = self.Urls[id]['Scope']
            if self.Urls[id]['State'] > 7:
                self.Urls[id]['State'] = 2
        self.Scope.Id = scope
        provider = ''
        if scope in self.Scope.Scopes:
            provider = self.Scope.Scopes[scope]['Provider']
        self.Scope.Provider.Id = provider
    @property
    def ProviderName(self):
        return self.Scope.Provider.Id
    @ProviderName.setter
    def ProviderName(self, id):
        self.Scope.Provider.Id = id
        if id and id not in self.Scope.Provider.Providers:
            self.Scope.Provider.Providers[id] = {'ClientId': '',
                                                 'ClientSecret': '',
                                                 'AuthorizationUrl': '',
                                                 'AuthorizationParameters': '{}',
                                                 'TokenUrl': '',
                                                 'TokenParameters': '{}',
                                                 'CodeChallenge': True,
                                                 'CodeChallengeMethod': 'S256',
                                                 'HttpHandler': True,
                                                 'RedirectAddress': 'localhost',
                                                 'RedirectPort': 8080,
                                                 'State': 2}
        elif id in self.Scope.Provider.Providers:
            if self.Scope.Provider.Providers[id]['State'] > 7:
                self.Scope.Provider.Providers[id]['State'] = 2
    @property
    def ProviderList(self):
        names = []
        for key, value in self.Scope.Provider.Providers.items():
            if value['State'] < 8:
                names.append(key)
        return tuple(names)
    @property
    def ScopeName(self):
        return self.Scope.Id
    @ScopeName.setter
    def ScopeName(self, id):
        self.Scope.Id = id
        if id and id not in self.Scope.Scopes:
            self.Scope.Scopes[id] = {'Provider': self.Scope.Provider.Id,
                                     'Values': [],
                                     'State': 2}
        elif id in self.Scope.Scopes:
            if self.Scope.Scopes[id]['State'] > 7:
                self.Scope.Scopes[id]['State'] = 2
        if id and self.Id in self.Urls:
            self.Urls[self.Id]['Scope'] = id
            self.State = 4
    @property
    def ScopeList(self):
        names = []
        for key, value in self.Scope.Scopes.items():
            if value['State'] < 8 and value['Provider'] == self.Scope.Provider.Id:
                names.append(key)
        return tuple(names)
    @property
    def ScopesList(self):
        names = []
        for key, value in self.Scope.Scopes.items():
            if value['State'] < 8:
                names.append(key)
        return tuple(names)
    @property
    def State(self):
        state = 2
        if self.Id in self.Urls:
            state = self.Urls[self.Id]['State']
        return state
    @State.setter
    def State(self, state):
        if self.Id in self.Urls:
            self.Urls[self.Id]['State'] = state

    # XTransactedObject
    def commit(self):
        urls = self.configuration.getByName('Urls')
        for key, value in self.Urls.items():
            if value['State'] < 4:
                continue
            elif value['State'] < 8:
                if not urls.hasByName(key):
                    urls.insertByName(key, urls.createInstance())
                url = urls.getByName(key)
                url.replaceByName('Scope', value['Scope'])
            elif urls.hasByName(key):
                    urls.removeByName(key)
        if self.configuration.hasPendingChanges():
            self.configuration.commitChanges()
    def revert(self):
        self.Urls = {}
        urls = self.configuration.getByName('Urls')
        for id in urls.ElementNames:
            url = urls.getByName(id)
            scope = url.getByName('Scope')
            self.Urls[id] = {'Scope': scope,
                             'State': 1}

    def _getPropertySetInfo(self):
        properties = {}
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['Scope'] = getProperty('Scope', 'com.sun.star.uno.XInterface', readonly)
        properties['Id'] = getProperty('Id', 'string', transient)
        properties['ProviderName'] = getProperty('ProviderName', 'string', transient)
        properties['ProviderList'] = getProperty('ProviderList', '[]string', readonly)
        properties['ScopeName'] = getProperty('ScopeName', 'string', transient)
        properties['ScopeList'] = getProperty('ScopeList', '[]string', readonly)
        properties['ScopesList'] = getProperty('ScopesList', '[]string', readonly)
        properties['State'] = getProperty('State', 'short', transient)
        return properties


class ScopeSetting(unohelper.Base,
                   XTransactedObject,
                   PropertySet):
    def __init__(self, configuration):
        self.configuration = configuration
        self.Provider = ProviderSetting(self.configuration)
        self.Id = ''
        self.Scopes = {}
        self.revert()

    @property
    def Value(self):
        values = list(self.Provider.User.Scopes)
        if self.Id in self.Scopes:
            for value in self.Scopes[self.Id]['Values']:
                if value not in values:
                    values.append(value)
        return ' '.join(values)
    @property
    def Values(self):
        values = []
        if self.Id in self.Scopes:
            values = self.Scopes[self.Id]['Values']
        return tuple(values)
    @Values.setter
    def Values(self, values):
        if self.Id in self.Scopes:
            self.Scopes[self.Id]['Values'] = values
    @property
    def Authorized(self):
        values = self.Values
        authorized = len(values) != 0
        for value in values:
            if value not in self.Provider.User.Scopes:
                authorized = False
                break
        return authorized
    @property
    def State(self):
        state = 2
        if self.Id in self.Scopes:
            state = self.Scopes[self.Id]['State']
        return state
    @State.setter
    def State(self, state):
        if self.Id in self.Scopes:
            self.Scopes[self.Id]['State'] = state

    # XTransactedObject
    def commit(self):
        scopes = self.configuration.getByName('Scopes')
        for key, value in self.Scopes.items():
            if value['State'] < 4:
                continue
            elif value['State'] < 8:
                if not scopes.hasByName(key):
                    scopes.insertByName(key, scopes.createInstance())
                    scopes.getByName(key).replaceByName('Provider', value['Provider'])
                scope = scopes.getByName(key)
#               scope.replaceByName('Value', value['Values'])
                arguments = ('Values', uno.Any('[]string', value['Values']))
                uno.invoke(scope, 'replaceByName', arguments)
            elif scopes.hasByName(key):
                scopes.removeByName(key)
        if self.configuration.hasPendingChanges():
            self.configuration.commitChanges()
    def revert(self):
        self.Scopes = {}
        scopes = self.configuration.getByName('Scopes')
        for id in scopes.ElementNames:
            scope = scopes.getByName(id)
            self.Scopes[id] = {'Provider': scope.getByName('Provider'),
                               'Values': scope.getByName('Values'),
                               'State': 1}

    def _getPropertySetInfo(self):
        properties = {}
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['Provider'] = getProperty('Provider', 'com.sun.star.uno.XInterface', readonly)
        properties['Id'] = getProperty('Id', 'string', transient)
        properties['Value'] = getProperty('Value', 'string', readonly)
        properties['Values'] = getProperty('Values', '[]string', transient)
        properties['Authorized'] = getProperty('Authorized', 'boolean', readonly)
        properties['State'] = getProperty('State', 'short', transient)
        return properties


class ProviderSetting(unohelper.Base,
                      XTransactedObject,
                      PropertySet):
    def __init__(self, configuration):
        self.configuration = configuration
        self.User = UserSetting(self.configuration)
        self.redirect = 'urn:ietf:wg:oauth:2.0:oob'
        self.Providers = {}
        self.revert()

    @property
    def Id(self):
        return self.User.ProviderId
    @Id.setter
    def Id(self, id):
        self.User.ProviderId = id
    @property
    def ClientId(self):
        id = ''
        if self.Id in self.Providers:
            id = self.Providers[self.Id]['ClientId']
        return id
    @ClientId.setter
    def ClientId(self, id):
        if self.Id in self.Providers:
            self.Providers[self.Id]['ClientId'] = id
    @property
    def ClientSecret(self):
        secret = ''
        if self.Id in self.Providers:
            secret = self.Providers[self.Id]['ClientSecret']
        return secret
    @ClientSecret.setter
    def ClientSecret(self, secret):
        if self.Id in self.Providers:
            self.Providers[self.Id]['ClientSecret'] = secret
    @property
    def AuthorizationUrl(self):
        url = ''
        if self.Id in self.Providers:
            url = self.Providers[self.Id]['AuthorizationUrl']
        return url
    @AuthorizationUrl.setter
    def AuthorizationUrl(self, url):
        if self.Id in self.Providers:
            self.Providers[self.Id]['AuthorizationUrl'] = url
    @property
    def AuthorizationParameters(self):
        parameters = '{}'
        if self.Id in self.Providers:
            parameters = self.Providers[self.Id]['AuthorizationParameters']
        return parameters
    @AuthorizationParameters.setter
    def AuthorizationParameters(self, parameters):
        if self.Id in self.Providers and \
           self.Providers[self.Id]['AuthorizationParameters'] != parameters:
            self.Providers[self.Id]['AuthorizationParameters'] = parameters
            self.State = 4
    @property
    def TokenUrl(self):
        url = ''
        if self.Id in self.Providers:
            url = self.Providers[self.Id]['TokenUrl']
        return url
    @TokenUrl.setter
    def TokenUrl(self, url):
        if self.Id in self.Providers:
            self.Providers[self.Id]['TokenUrl'] = url
    @property
    def TokenParameters(self):
        parameters = '{}'
        if self.Id in self.Providers:
            parameters = self.Providers[self.Id]['TokenParameters']
        return parameters
    @TokenParameters.setter
    def TokenParameters(self, parameters):
        if self.Id in self.Providers and self.Providers[self.Id]['TokenParameters'] != parameters:
            self.Providers[self.Id]['TokenParameters'] = parameters
            self.State = 4
    @property
    def CodeChallenge(self):
        enabled = True
        if self.Id in self.Providers:
            enabled = self.Providers[self.Id]['CodeChallenge']
        return enabled
    @CodeChallenge.setter
    def CodeChallenge(self, enabled):
        if self.Id in self.Providers:
            self.Providers[self.Id]['CodeChallenge'] = enabled
    @property
    def CodeChallengeMethod(self):
        method = 'S256'
        if self.Id in self.Providers:
            method = self.Providers[self.Id]['CodeChallengeMethod']
        return method
    @CodeChallengeMethod.setter
    def CodeChallengeMethod(self, method):
        if self.Id in self.Providers:
            self.Providers[self.Id]['CodeChallengeMethod'] = method
    @property
    def HttpHandler(self):
        enabled = True
        if self.Id in self.Providers:
            enabled = self.Providers[self.Id]['HttpHandler']
        return enabled
    @HttpHandler.setter
    def HttpHandler(self, enabled):
        if self.Id in self.Providers and self.Providers[self.Id]['HttpHandler'] != enabled:
            self.Providers[self.Id]['HttpHandler'] = enabled
            self.State = 4
    @property
    def RedirectAddress(self):
        address = 'localhost'
        if self.Id in self.Providers:
            address =  self.Providers[self.Id]['RedirectAddress']
        return address
    @RedirectAddress.setter
    def RedirectAddress(self, address):
        if self.Id in self.Providers and self.Providers[self.Id]['RedirectAddress'] != address:
            self.Providers[self.Id]['RedirectAddress'] = address
            self.State = 4
    @property
    def RedirectPort(self):
        port = 8080
        if self.Id in self.Providers:
            port = self.Providers[self.Id]['RedirectPort']
        return port
    @RedirectPort.setter
    def RedirectPort(self, port):
        if self.Id in self.Providers and self.Providers[self.Id]['RedirectPort'] != port:
            self.Providers[self.Id]['RedirectPort'] = port
            self.State = 4
    @property
    def RedirectUri(self):
        if self.HttpHandler:
            uri = 'http://%s:%s/' % (self.RedirectAddress, self.RedirectPort)
        else:
            uri = self.redirect
        return uri
    @property
    def MetaData(self):
        metadata = KeyMap()
        metadata.insertValue('ClientSecret', self.ClientSecret)
        metadata.insertValue('ClientId', self.ClientId)
        metadata.insertValue('TokenUrl', self.TokenUrl)
        metadata.insertValue('TokenParameters', self.TokenParameters)
        return metadata
    @property
    def State(self):
        state = 2
        if self.Id in self.Providers:
            state = self.Providers[self.Id]['State']
        return state
    @State.setter
    def State(self, state):
        if self.Id in self.Providers:
            self.Providers[self.Id]['State'] = state
            if state == 8:
                for scope in self.Scope.Scopes.values():
                    if scope['Provider'] == self.Id:
                        scope['State'] = 8

    # XTransactedObject
    def commit(self):
        providers = self.configuration.getByName('Providers')
        for key, value in self.Providers.items():
            if value['State'] < 4:
                continue
            elif value['State'] < 8:
                if not providers.hasByName(key):
                    providers.insertByName(key, providers.createInstance())
                provider = providers.getByName(key)
                provider.replaceByName('ClientId', value['ClientId'])
                provider.replaceByName('ClientSecret', value['ClientSecret'])
                provider.replaceByName('AuthorizationUrl', value['AuthorizationUrl'])
                provider.replaceByName('AuthorizationParameters', value['AuthorizationParameters'])
                provider.replaceByName('TokenUrl', value['TokenUrl'])
                provider.replaceByName('TokenParameters', value['TokenParameters'])
                provider.replaceByName('CodeChallenge', value['CodeChallenge'])
                provider.replaceByName('CodeChallengeMethod', value['CodeChallengeMethod'])
                provider.replaceByName('HttpHandler', value['HttpHandler'])
                provider.replaceByName('RedirectAddress', value['RedirectAddress'])
                provider.replaceByName('RedirectPort', value['RedirectPort'])
            elif providers.hasByName(key):
                providers.removeByName(key)
        if self.configuration.hasPendingChanges():
            self.configuration.commitChanges()
    def revert(self):
        self.Providers = {}
        providers = self.configuration.getByName('Providers')
        for id in providers.ElementNames:
            provider = providers.getByName(id)
            self.Providers[id] = {'ClientId': provider.getByName('ClientId'),
                                  'ClientSecret': provider.getByName('ClientSecret'),
                                  'AuthorizationUrl': provider.getByName('AuthorizationUrl'),
                                  'AuthorizationParameters': provider.getByName('AuthorizationParameters'),
                                  'TokenUrl': provider.getByName('TokenUrl'),
                                  'TokenParameters': provider.getByName('TokenParameters'),
                                  'CodeChallenge': provider.getByName('CodeChallenge'),
                                  'CodeChallengeMethod': provider.getByName('CodeChallengeMethod'),
                                  'HttpHandler': provider.getByName('HttpHandler'),
                                  'RedirectAddress': provider.getByName('RedirectAddress'),
                                  'RedirectPort': provider.getByName('RedirectPort'),
                                  'State': 1}

    def _getPropertySetInfo(self):
        properties = {}
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['User'] = getProperty('User', 'com.sun.star.uno.XInterface', readonly)
        properties['ClientId'] = getProperty('ClientId', 'string', transient)
        properties['ClientSecret'] = getProperty('ClientSecret', 'string', transient)
        properties['AuthorizationUrl'] = getProperty('AuthorizationUrl', 'string', transient)
        properties['AuthorizationParameters'] = getProperty('AuthorizationParameters', 'string', transient)
        properties['TokenUrl'] = getProperty('TokenUrl', 'string', transient)
        properties['TokenParameters'] = getProperty('TokenParameters', 'string', transient)
        properties['CodeChallenge'] = getProperty('CodeChallenge', 'boolean', transient)
        properties['CodeChallengeMethod'] = getProperty('CodeChallengeMethod', 'string', transient)
        properties['HttpHandler'] = getProperty('HttpHandler', 'boolean', transient)
        properties['RedirectAddress'] = getProperty('RedirectAddress', 'string', transient)
        properties['RedirectPort'] = getProperty('RedirectPort', 'short', transient)
        properties['RedirectUri'] = getProperty('RedirectUri', 'string', readonly)
        properties['State'] = getProperty('State', 'short', transient)
        properties['MetaData'] = getProperty('MetaData', 'com.sun.star.auth.XRestKeyMap', readonly)
        return properties


class UserSetting(unohelper.Base,
                  XUpdatable,
                  XTransactedObject,
                  PropertySet):
    def __init__(self, configuration):
        self.configuration = configuration
        self._Id = ''
        self._ProviderId = ''
        self.revert()

    @property
    def Id(self):
        return self._Id
    @Id.setter
    def Id(self, id):
        self._Id = id
        self.update()
    @property
    def ProviderId(self):
        return self._ProviderId
    @ProviderId.setter
    def ProviderId(self, id):
        self._ProviderId = id
        self.update()
    @property
    def HasExpired(self):
        return False if self.NeverExpires else self.ExpiresIn < g_refresh_overlap
    @property
    def ExpiresIn(self):
        now = int(time.time())
        return g_refresh_overlap if self.NeverExpires else max(0, self._TimeStamp - now)
    @ExpiresIn.setter
    def ExpiresIn(self, second):
        now = int(time.time())
        self._TimeStamp = second + now
    @property
    def Scope(self):
        return ' '.join(self._Scopes)
    @Scope.setter
    def Scope(self, scope):
        self._Scopes = scope.split(' ')
    @property
    def Scopes(self):
        return tuple(self._Scopes)
    @property
    def MetaData(self):
        metadata = KeyMap()
        metadata.insertValue('AccessToken', self.AccessToken)
        metadata.insertValue('RefreshToken', self.RefreshToken)
        metadata.insertValue('NeverExpires', self.NeverExpires)
        metadata.insertValue('TimeStamp', self._TimeStamp)
        metadata.insertValue('Scopes', tuple(self._Scopes))
        return metadata

    # XUpdatable
    def update(self):
        accesstoken = ''
        refreshtoken = ''
        neverexpires = False
        timestamp = 0
        scopes = []
        providers = self.configuration.getByName('Providers')
        if providers.hasByName(self.ProviderId):
            provider = providers.getByName(self.ProviderId)
            users = provider.getByName('Users')
            if users.hasByName(self.Id):
                user = users.getByName(self.Id)
                accesstoken = user.getByName('AccessToken')
                refreshtoken = user.getByName('RefreshToken')
                neverexpires = user.getByName('NeverExpires')
                timestamp = user.getByName('TimeStamp')
                scopes = list(user.getByName('Scopes'))
        self.AccessToken = accesstoken
        self.RefreshToken = refreshtoken
        self.NeverExpires = neverexpires
        self._TimeStamp = timestamp
        self._Scopes = scopes

    # XTransactedObject
    def commit(self):
        providers = self.configuration.getByName('Providers')
        if providers.hasByName(self.ProviderId):
            provider = providers.getByName(self.ProviderId)
            users = provider.getByName('Users')
            if not users.hasByName(self.Id):
                users.insertByName(self.Id, users.createInstance())
            user = users.getByName(self.Id)
            user.replaceByName('AccessToken', self.AccessToken)
            user.replaceByName('RefreshToken', self.RefreshToken)
            user.replaceByName('NeverExpires', self.NeverExpires)
            user.replaceByName('TimeStamp', self._TimeStamp)
            # user.replaceByName('Scopes', self._Scopes)
            arguments = ('Scopes', uno.Any('[]string', self.Scopes))
            uno.invoke(user, 'replaceByName', arguments)
            if self.configuration.hasPendingChanges():
                self.configuration.commitChanges()
    def revert(self):
        self.AccessToken = ''
        self.RefreshToken = ''
        self.NeverExpires = False
        self._TimeStamp = 0
        self._Scopes = []

    def _getPropertySetInfo(self):
        properties = {}
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['Id'] = getProperty('Id', 'string', transient)
        properties['ProviderId'] = getProperty('ProviderId', 'string', transient)
        properties['AccessToken'] = getProperty('AccessToken', 'string', transient)
        properties['RefreshToken'] = getProperty('RefreshToken', 'string', transient)
        properties['NeverExpires'] = getProperty('NeverExpires', 'boolean', transient)
        properties['ExpiresIn'] = getProperty('ExpiresIn', 'short', transient)
        properties['HasExpired'] = getProperty('HasExpired', 'boolean', readonly)
        properties['Scopes'] = getProperty('Scopes', '[]string', readonly)
        properties['Scope'] = getProperty('Scope', 'string', transient)
        properties['MetaData'] = getProperty('MetaData', 'com.sun.star.auth.XRestKeyMap', readonly)
        return properties

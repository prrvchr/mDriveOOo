#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.embed import XTransactedObject
from com.sun.star.util import XUpdatable

from unolib import PropertySet
from unolib import getProperty
from unolib import getConfiguration

from .configuration import g_identifier
from .configuration import g_refresh_overlap

import time
import traceback


class OAuth2Configuration(unohelper.Base,
                          XTransactedObject,
                          PropertySet):
    def __init__(self, ctx):
        self.ctx = ctx
        self.configuration = getConfiguration(self.ctx, g_identifier, True)
        self.Url = UrlReader(self.configuration)
        self.ConnectTimeout = self.configuration.getByName('ConnectTimeout')
        self.ReadTimeout = self.configuration.getByName('ReadTimeout')
        self.HandlerTimeout = self.configuration.getByName('HandlerTimeout')

    @property
    def UrlList(self):
        return self.configuration.getByName('Urls').ElementNames
    @property
    def Timeout(self):
        if self.ConnectTimeout and self.ReadTimeout:
            return self.ConnectTimeout, self.ReadTimeout
        elif self.ConnectTimeout:
            return self.ConnectTimeout
        elif self.ReadTimeout:
            return self.ReadTimeout
        return None

    # XTransactedObject
    def commit(self):
        self.configuration.replaceByName('ConnectTimeout', self.ConnectTimeout)
        self.configuration.replaceByName('ReadTimeout', self.ReadTimeout)
        self.configuration.replaceByName('HandlerTimeout', self.HandlerTimeout)
        if self.configuration.hasPendingChanges():
            self.configuration.commitChanges()
    def revert(self):
        self.ConnectTimeout = self.configuration.getByName('ConnectTimeout')
        self.ReadTimeout = self.configuration.getByName('ReadTimeout')
        self.HandlerTimeout = self.configuration.getByName('HandlerTimeout')

    def _getPropertySetInfo(self):
        properties = {}
        maybevoid = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.MAYBEVOID')
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['Url'] = getProperty('Url', 'com.sun.star.uno.XInterface', readonly)
        properties['UrlList'] = getProperty('UrlList', '[]string', readonly)
        properties['ConnectTimeout'] = getProperty('ConnectTimeout', 'short', transient)
        properties['ReadTimeout'] = getProperty('ReadTimeout', 'short', transient)
        properties['HandlerTimeout'] = getProperty('HandlerTimeout', 'short', transient)
        properties['Timeout'] = getProperty('Timeout', 'any', readonly)
        return properties


class UrlReader(unohelper.Base,
                PropertySet):
    def __init__(self, configuration):
        self.configuration = configuration
        self.Scope = ScopeReader(self.configuration)
        self._Id = ''

    @property
    def Id(self):
        return self._Id
    @Id.setter
    def Id(self, id):
        self._Id = id
        urls = self.configuration.getByName('Urls')
        if urls.hasByName(self.Id):
            scope = urls.getByName(self.Id).getByName('Scope')
            self.Scope.Id = scope

    def _getPropertySetInfo(self):
        properties = {}
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['Scope'] = getProperty('Scope', 'com.sun.star.uno.XInterface', readonly)
        properties['Id'] = getProperty('Id', 'string', transient)
        return properties


class ScopeReader(unohelper.Base,
                  PropertySet):
    def __init__(self, configuration):
        self.configuration = configuration
        self.Provider = ProviderReader(self.configuration)
        self._Id = ''
        self._Values = []

    @property
    def Id(self):
        return self._Id
    @Id.setter
    def Id(self, id):
        self._Id = id
        values = []
        provider = ''
        scopes = self.configuration.getByName('Scopes')
        if scopes.hasByName(self.Id):
            scope = scopes.getByName(self.Id)
            values = list(scope.getByName('Values'))
            provider = scope.getByName('Provider')
        self._Values = values
        self.Provider.Id = provider

    @property
    def Value(self):
        values = list(self.Provider.User.Scopes)
        for value in self._Values:
            if value not in values:
                values.append(value)
        return ' '.join(values)
    @property
    def Authorized(self):
        authorized = len(self._Values) != 0
        for value in self._Values:
            if value not in self.Provider.User.Scopes:
                authorized = False
                break
        return authorized

    def _getPropertySetInfo(self):
        properties = {}
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['Provider'] = getProperty('Provider', 'com.sun.star.uno.XInterface', readonly)
        properties['Id'] = getProperty('Id', 'string', transient)
        properties['Value'] = getProperty('Value', 'string', readonly)
        properties['Authorized'] = getProperty('Authorized', 'boolean', readonly)
        return properties


class ProviderReader(unohelper.Base,
                     PropertySet):
    def __init__(self, configuration):
        self.configuration = configuration
        self.User = UserReader(self.configuration)
        self.ClientId = ''
        self.ClientSecret = ''
        self.AuthorizationUrl = ''
        self.AuthorizationParameters = '{}'
        self.TokenUrl = ''
        self.TokenParameters = '{}'
        self.CodeChallenge = True
        self.HttpHandler = True
        self.RedirectAddress = 'localhost'
        self.RedirectPort = 8080
        self.redirect = 'urn:ietf:wg:oauth:2.0:oob'

    @property
    def Id(self):
        return self.User.ProviderId
    @Id.setter
    def Id(self, id):
        self.User.ProviderId = id
        clientid = ''
        clientsecret = ''
        authorizationurl = ''
        authorizationparameters = '{}'
        tokenurl = ''
        tokenparameters = '{}'
        codechallenge = True
        httphandler = True
        redirectaddress = 'localhost'
        redirectport = 8080
        providers = self.configuration.getByName('Providers')
        if providers.hasByName(self.Id):
            provider = providers.getByName(self.Id)
            clientid = provider.getByName('ClientId')
            clientsecret = provider.getByName('ClientSecret')
            authorizationurl = provider.getByName('AuthorizationUrl')
            authorizationparameters = provider.getByName('AuthorizationParameters')
            tokenurl = provider.getByName('TokenUrl')
            tokenparameters = provider.getByName('TokenParameters')
            codechallenge = provider.getByName('CodeChallenge')
            httphandler = provider.getByName('HttpHandler')
            redirectaddress = provider.getByName('RedirectAddress')
            redirectport = provider.getByName('RedirectPort')
        self.ClientId = clientid
        self.ClientSecret = clientsecret
        self.AuthorizationUrl = authorizationurl
        self.AuthorizationParameters = authorizationparameters
        self.TokenUrl = tokenurl
        self.TokenParameters = tokenparameters
        self.CodeChallenge = codechallenge
        self.HttpHandler = httphandler
        self.RedirectAddress = redirectaddress
        self.RedirectPort = redirectport

    @property
    def RedirectUri(self):
        if self.HttpHandler:
            uri = 'http://%s:%s/' % (self.RedirectAddress, self.RedirectPort)
        else:
            uri = self.redirect
        return uri

    def _getPropertySetInfo(self):
        properties = {}
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['User'] = getProperty('User', 'com.sun.star.uno.XInterface', readonly)
        properties['Id'] = getProperty('Id', 'string', transient)
        properties['ClientId'] = getProperty('ClientId', 'string', readonly)
        properties['ClientSecret'] = getProperty('ClientSecret', 'string', readonly)
        properties['AuthorizationUrl'] = getProperty('AuthorizationUrl', 'string', readonly)
        properties['AuthorizationParameters'] = getProperty('AuthorizationParameters', 'string', readonly)
        properties['TokenUrl'] = getProperty('TokenUrl', 'string', readonly)
        properties['TokenParameters'] = getProperty('TokenParameters', 'string', readonly)
        properties['CodeChallenge'] = getProperty('CodeChallenge', 'boolean', readonly)
        properties['HttpHandler'] = getProperty('HttpHandler', 'boolean', readonly)
        properties['RedirectAddress'] = getProperty('RedirectAddress', 'string', readonly)
        properties['RedirectPort'] = getProperty('RedirectPort', 'short', readonly)
        properties['RedirectUri'] = getProperty('RedirectUri', 'string', readonly)
        return properties


class UserReader(unohelper.Base,
                 XUpdatable,
                 XTransactedObject,
                 PropertySet):
    def __init__(self, configuration):
        self.configuration = configuration
        self._Id = ''
        self._ProviderId = ''
        self.AccessToken = ''
        self.RefreshToken = ''
        self.NeverExpires = False
        self._TimeStamp = 0
        self._Scopes = []

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
        return g_refresh_overlap if self.NeverExpires else max(0, self._TimeStamp - int(time.time()))
    @ExpiresIn.setter
    def ExpiresIn(self, second):
        self._TimeStamp = second + int(time.time())
    @property
    def Scope(self):
        return ' '.join(self._Scopes)
    @Scope.setter
    def Scope(self, scope):
        self._Scopes = scope.split(' ')
    @property
    def Scopes(self):
        return tuple(self._Scopes)

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
        properties['Scopes'] = getProperty('Scopes', '[]string', transient)
        properties['Scope'] = getProperty('Scope', 'string', transient)
        return properties

#!
# -*- coding: utf-8 -*-

#from __futur__ import absolute_import

import uno

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from unolib import KeyMap
from unolib import NoOAuth2
from unolib import getCurrentLocale

print("oauth2tools.py 1")
from .requests.compat import urlencode
print("oauth2tools.py 2")

import json
import base64
import hashlib
import time

import traceback


def getActivePath(configuration):
    if configuration.Url.Scope.Authorized:
        activepath = 2
    elif configuration.Url.Scope.Provider.HttpHandler:
        activepath = 0
    else:
        activepath = 1
    return activepath

def getAuthorizationStr(ctx, configuration, uuid):
    main = configuration.Url.Scope.Provider.AuthorizationUrl
    parameters = _getUrlArguments(ctx, configuration, uuid)
    return '%s?%s' % (main, parameters)

def checkUrl(ctx, configuration, uuid):
    transformer = ctx.ServiceManager.createInstance('com.sun.star.util.URLTransformer')
    url = uno.createUnoStruct('com.sun.star.util.URL')
    url.Complete = getAuthorizationStr(ctx, configuration, uuid)
    success, url = transformer.parseStrict(url)
    return success

def openUrl(ctx, url, option=''):
    service = 'com.sun.star.system.SystemShellExecute'
    ctx.ServiceManager.createInstance(service).execute(url, option, 0)

def getAuthorizationUrl(ctx, configuration, uuid):
    main = configuration.Url.Scope.Provider.AuthorizationUrl
    parameters = urlencode(_getUrlParameters(ctx, configuration, uuid))
    return '%s?%s' % (main, parameters)

def updatePageTokenUI(window, configuration, strings):
    enabled = configuration.Url.Scope.Authorized
    if enabled:
        scope = configuration.Url.Scope.Provider.User.Scope
        refresh = configuration.Url.Scope.Provider.User.RefreshToken
        access = configuration.Url.Scope.Provider.User.AccessToken
        expire = configuration.Url.Scope.Provider.User.ExpiresIn
    else:
        scope = strings.resolveString('PageWizard5.Label2.Label')
        refresh = strings.resolveString('PageWizard5.Label4.Label')
        access = strings.resolveString('PageWizard5.Label6.Label')
        expire = strings.resolveString('PageWizard5.Label8.Label')
    window.getControl('Label2').Text = scope
    window.getControl('Label4').Text = refresh
    window.getControl('Label6').Text = access
    window.getControl('Label8').Text = expire
    window.getControl('CommandButton1').Model.Enabled = enabled
    window.getControl('CommandButton2').Model.Enabled = enabled
    window.getControl('CommandButton3').Model.Enabled = enabled

def _getUrlArguments(ctx, configuration, uuid):
    arguments = []
    parameters = _getUrlParameters(ctx, configuration, uuid)
    for key, value in parameters.items():
        arguments.append('%s=%s' % (key, value))
    return '&'.join(arguments)

def _getUrlParameters(ctx, configuration, uuid):
    parameters = _getUrlBaseParameters(configuration, uuid)
    optional = _getUrlOptionalParameters(ctx, configuration)
    option = configuration.Url.Scope.Provider.AuthorizationParameters
    parameters = _parseParameters(parameters, optional, option)
    return parameters

def _getUrlBaseParameters(configuration, uuid):
    parameters = {}
    parameters['response_type'] = 'code'
    parameters['client_id'] = configuration.Url.Scope.Provider.ClientId
    parameters['state'] = uuid
    if configuration.Url.Scope.Provider.HttpHandler:
        parameters['redirect_uri'] = configuration.Url.Scope.Provider.RedirectUri
    if configuration.Url.Scope.Provider.CodeChallenge:
        method = configuration.Url.Scope.Provider.CodeChallengeMethod
        parameters['code_challenge_method'] = method
        parameters['code_challenge'] = _getCodeChallenge(uuid + uuid, method)
    return parameters

def _getUrlOptionalParameters(ctx, configuration):
    parameters = {}
    parameters['scope'] = configuration.Url.Scope.Value
    parameters['client_secret'] = configuration.Url.Scope.Provider.ClientSecret
    parameters['current_user'] = configuration.Url.Scope.Provider.User.Id
    parameters['current_language'] = getCurrentLocale(ctx).Language
    return parameters

def _getCodeChallenge(code, method):
    if method == 'S256':
        code = hashlib.sha256(code.encode('utf-8')).digest()
        padding = {0:0, 1:2, 2:1}[len(code) % 3]
        challenge = base64.urlsafe_b64encode(code).decode('utf-8')
        code = challenge[:len(challenge)-padding]
    return code

def getTokenParameters(setting, code, codeverifier):
    parameters = _getTokenBaseParameters(setting, code, codeverifier)
    optional = _getTokenOptionalParameters(setting)
    option = setting.Url.Scope.Provider.TokenParameters
    parameters = _parseParameters(parameters, optional, option)
    return parameters

def getResponseFromRequest(session, url, data, timeout):
    response = {}
    error = None
    with session as s:
        try:
            with s.post(url, data=data, timeout=timeout, auth=NoOAuth2()) as r:
                r.raise_for_status()
                response = r.json()
        except Exception as e:
            error = e
    return response, error

def registerTokenFromResponse(configuration, response):
    token = uno.createUnoStruct('com.sun.star.beans.Optional<com.sun.star.auth.XRestKeyMap>')
    token = getTokenFromResponse(response, token)
    return saveTokenToConfiguration(configuration, token)

def saveTokenToConfiguration(configuration, token):
    if token.IsPresent:
        if token.Value.hasValue('RefreshToken'):
            refresh = token.Value.getValue('RefreshToken')
            configuration.Url.Scope.Provider.User.RefreshToken = refresh
        if token.Value.hasValue('AccessToken'):
            access = token.Value.getValue('AccessToken')
            configuration.Url.Scope.Provider.User.AccessToken = access
        if token.Value.hasValue('NeverExpires'):
            never = token.Value.getValue('NeverExpires')
            configuration.Url.Scope.Provider.User.NeverExpires = never
        if token.Value.hasValue('ExpiresIn'):
            expires = token.Value.getValue('ExpiresIn')
            configuration.Url.Scope.Provider.User.ExpiresIn = expires
        scope = configuration.Url.Scope.Value
        configuration.Url.Scope.Provider.User.Scope = scope
        configuration.Url.Scope.Provider.User.commit()
    return token.IsPresent

def getRefreshToken(session, provider, user, timeout):
    token = uno.createUnoStruct('com.sun.star.beans.Optional<com.sun.star.auth.XRestKeyMap>')
    url = provider.getValue('TokenUrl')
    data = getRefreshParameters(provider, user)
    response, error = getResponseFromRequest(session, url, data, timeout)
    if error is None:
        token = getTokenFromResponse(response, token)
    return token, error

def getTokenFromResponse(response, token):
    token.Value = KeyMap()
    refresh = response.get('refresh_token', None)
    expires = response.get('expires_in', None)
    access = response.get('access_token', None)
    if refresh:
        token.Value.insertValue('RefreshToken', refresh)
    if expires:
        timestamp = int(time.time()) + expires
        token.Value.insertValue('ExpiresIn', expires)
        token.Value.insertValue('TimeStamp', timestamp)
    if access:
        token.Value.insertValue('AccessToken', access)
        token.Value.insertValue('NeverExpires', expires is None)
    token.IsPresent = any((refresh, expires, access))
    return token

def _getTokenBaseParameters(setting, code, codeverifier):
    parameters = {}
    parameters['code'] = code
    parameters['grant_type'] = 'authorization_code'
    parameters['client_id'] = setting.Url.Scope.Provider.ClientId
    if setting.Url.Scope.Provider.HttpHandler:
        parameters['redirect_uri'] = setting.Url.Scope.Provider.RedirectUri
    if setting.Url.Scope.Provider.CodeChallenge:
        parameters['code_verifier'] = codeverifier
    return parameters

def _getTokenOptionalParameters(setting):
    parameters = {}
    parameters['scope'] = setting.Url.Scope.Value
    parameters['client_secret'] = setting.Url.Scope.Provider.ClientSecret
    return parameters

def getRefreshParameters(provider, user):
    parameters = _getRefreshBaseParameters(provider, user)
    optional = _getRefreshOptionalParameters(provider, user)
    option = provider.getValue('TokenParameters')
    parameters = _parseParameters(parameters, optional, option)
    return parameters

def _getRefreshBaseParameters(provider, user):
    parameters = {}
    parameters['refresh_token'] = user.getValue('RefreshToken')
    parameters['grant_type'] = 'refresh_token'
    parameters['client_id'] = provider.getValue('ClientId')
    return parameters

def _getRefreshOptionalParameters(provider, user):
    parameters = {}
    parameters['scope'] = ' '.join(user.getValue('Scopes'))
    parameters['client_secret'] = provider.getValue('ClientSecret')
    return parameters

def _parseParameters(base, optional, required):
    for key, value in json.loads(required).items():
        if value is None:
            if key in base:
                del base[key]
            elif key in optional:
                base[key] = optional[key]
        elif value in optional:
            base[key] = optional[value]
        else:
            base[key] = value
    return base

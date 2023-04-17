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

from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.ucb.ConnectionMode import OFFLINE
from com.sun.star.ucb.ConnectionMode import ONLINE

from .dataparser import DataParser

from .unotool import getConnectionMode
from .unotool import getUrl

from .dbtool import getSqlException

from .logger import getLogger

from .configuration import g_host
from .configuration import g_url
from .configuration import g_page
from .configuration import g_member
from .configuration import g_errorlog
from .configuration import g_basename

import json


class Provider(unohelper.Base):
    def __init__(self, ctx, scheme, server):
        self._ctx = ctx
        self._scheme = scheme
        self._server = server
        self._url = '/.well-known/carddav'
        self._headers = ('1', 'access-control', 'addressbook')
        self._status = 'HTTP/1.1 404 Not Found'
        self._Error = ''
        self.SessionMode = OFFLINE

    @property
    def Host(self):
        return self._server
    @property
    def BaseUrl(self):
        return self._scheme + self._server

    def isOnLine(self):
        return getConnectionMode(self._ctx, self.Host) != OFFLINE
    def isOffLine(self):
        offline = getConnectionMode(self._ctx, self.Host) != ONLINE
        print("Provider.isOffLine() %s" % offline)
        return offline

    def getNewUserId(self, request, server, name, pwd):
        url = self._scheme + self._server + self._url
        redirect, url = self._getDiscoveryUrl(request, name, pwd, url)
        print("Provider.getNewUserId() 1 %s" % url)
        if redirect:
            scheme, server = self._getUrlParts(url)
            redirect, url = self._getDiscoveryUrl(request, name, pwd, url)
        path = self._getUserUrl(request, name, pwd, url)
        if path is None:
            #TODO: Raise SqlException with correct message!
            raise self.getSqlException(1004, 1108, 'getNewUserId', 'Server: %s Bad password: %s!' % (server, pwd))
        if not self._supportAddressbook(request, name, pwd, path):
            #TODO: Raise SqlException with correct message!
            raise self.getSqlException(1004, 1108, 'getNewUserId', '%s has no support of CardDAV!' % server)
        print("Provider.getNewUserId() 2 %s" % path)
        userid = self._getAddressbooksUrl(request, name, pwd, path)
        print("Provider.getNewUserId() 3 %s" % userid)
        if userid is None:
            #TODO: Raise SqlException with correct message!
            raise self.getSqlException(1004, 1108, 'getNewUserId', 'Server: %s Bad password: %s!' % (server, pwd))
        return userid

    def initAddressbooks(self, database, user, request):
        if self.isOnLine():
            addressbooks = self._getAllAddressbook(request, user.Name, user.Password, user.Path)
            if not addressbooks:
                #TODO: Raise SqlException with correct message!
                print("User.initAddressbooks() 1 %s" % (addressbooks, ))
                raise self.getSqlException(1004, 1108, 'initAddressbooks', '%s has no support of CardDAV!' % user.Server)
            if user.Addressbooks.initAddressbooks(database, user.Id, addressbooks):
                database.initAddressbooks()

    def _getUrlParts(self, location):
        url = getUrl(self._ctx, location)
        self._scheme = url.Protocol
        self._server = url.Server
        return self._scheme, self._server

    def _getDiscoveryUrl(self, request, user, password, url):
        parameter = self._getRequestParameter('getUrl', user, password, url)
        response = request.getResponse(parameter, None)
        if not response.Ok or not response.IsRedirect:
            response.close()
            #TODO: Raise SqlException with correct message!
            raise self.getSqlException(1006, 1107, 'getDiscoveryUrl()', '%s Response not Ok' % url)
        location = response.getHeader('Location')
        response.close()
        if not location:
            #TODO: Raise SqlException with correct message!
            raise self.getSqlException(1006, 1107, 'getDiscoveryUrl()', '%s url is None' % url)
        redirect = location.endswith(self._url)
        return redirect, location

    def _getUserUrl(self, request, user, password, url):
        data = '''\
<?xml version="1.0"?>
<d:propfind xmlns:d="DAV:">
  <d:prop>
    <d:current-user-principal />
  </d:prop>
</d:propfind>
'''
        parameter = self._getRequestParameter('getUser', user, password, url, data)
        parser = DataParser(parameter.Name)
        response = request.getResponse(parameter, parser)
        if not response.Ok:
            response.close()
            raise self.getSqlException(1006, 1107, 'getUserUrl()', user)
        url = response.Data
        response.close()
        return url

    def _supportAddressbook(self, request, user, password, url):
        parameter = self._getRequestParameter('hasAddressbook', user, password, url)
        response = request.getResponse(parameter, None)
        if not response.Ok:
            response.close()
            #TODO: Raise SqlException with correct message!
            raise self.getSqlException(1006, 1107, 'supportAddressbook()', user)
        headers = response.getHeader('DAV')
        response.close()
        for headers in self._headers:
            if headers not in headers:
                return False
        return True

    def _getAddressbooksUrl(self, request, user, password, url):
        data = '''\
<?xml version="1.0"?>
<d:propfind xmlns:d="DAV:">
  <d:prop>
    <card:addressbook-home-set xmlns:card="urn:ietf:params:xml:ns:carddav" />
  </d:prop>
</d:propfind>
'''
        parameter = self._getRequestParameter('getAddressbooksUrl', user, password, url, data)
        parser = DataParser(parameter.Name)
        response = request.getResponse(parameter, parser)
        if not response.Ok:
            response.close()
            raise self.getSqlException(1006, 1107, 'getAddressbooksUrl()', user)
        url = response.Data
        response.close()
        return url

    def getDefaultAddressbook(self, request, user, password, url):
        data = '''\
<?xml version="1.0"?>
<d:propfind xmlns:d="DAV:">
  <d:prop>
    <d:displayname />
    <cs:getctag xmlns:cs="http://calendarserver.org/ns/" />
    <d:sync-token />
    <d:resourcetype>
        <card:addressbook xmlns:card="urn:ietf:params:xml:ns:carddav" />
    </d:resourcetype>
  </d:prop>
</d:propfind>
'''
        parameter = self._getRequestParameter('getDefaultAddressbook', user, password, url, data)
        parser = DataParser(parameter.Name)
        response = request.getResponse(parameter, parser)
        if not response.Ok:
            response.close()
            #TODO: Raise SqlException with correct message!
            raise self.getSqlException(1006, 1107, 'getDefaultAddressbook()', user)
        path, name, tag, token = response.Data
        response.close()
        return path, name, tag, token

    def _getAllAddressbook(self, request, user, password, url):
        data = '''\
<?xml version="1.0"?>
<d:propfind xmlns:d="DAV:">
  <d:prop>
    <d:displayname />
    <cs:getctag xmlns:cs="http://calendarserver.org/ns/" />
    <d:sync-token />
    <d:resourcetype>
        <card:addressbook xmlns:card="urn:ietf:params:xml:ns:carddav" />
    </d:resourcetype>
  </d:prop>
</d:propfind>
'''
        parameter = self._getRequestParameter('getAllAddressbook', user, password, url, data)
        parser = DataParser(parameter.Name)
        response = request.getResponse(parameter, parser)
        if not response.Ok:
            response.close()
            #TODO: Raise SqlException with correct message!
            raise self.getSqlException(1006, 1107, 'getAllAddressbook()', user)
        addressbooks = response.Data
        response.close()
        return addressbooks
        #return path, name, tag, token

    def getAddressbookUrl(self, request, addressbook, user, password, url):
        data = '''\
<?xml version="1.0"?>
<d:propfind xmlns:d="DAV:">
  <d:prop>
    <d:displayname />
    <cs:getctag xmlns:cs="http://calendarserver.org/ns/" />
    <d:sync-token />
    <d:resourcetype>
        <card:addressbook xmlns:card="urn:ietf:params:xml:ns:carddav" />
    </d:resourcetype>
  </d:prop>
</d:propfind>
'''
        parameter = self._getRequestParameter('getAddressbookUrl', user, password, url, data)
        parser = DataParser(parameter.Name, addressbook)
        response = request.getResponse(parameter, parser)
        if not response.Ok:
            response.close()
            #TODO: Raise SqlException with correct message!
            raise self.getSqlException(1006, 1107, 'getAddressbookUrl()', user)
        path, name, tag, token = response.Data
        response.close()
        return path, name, tag, token

    def getAddressbook(self, request, addressbook, user, password, url):
        data = '''\
<?xml version="1.0"?>
<d:propfind xmlns:d="DAV:">
  <d:prop>
    <d:displayname />
    <cs:getctag xmlns:cs="http://calendarserver.org/ns/" />
    <d:sync-token />
    <d:resourcetype>
        <card:addressbook xmlns:card="urn:ietf:params:xml:ns:carddav" />
    </d:resourcetype>
  </d:prop>
</d:propfind>
'''
        parameter = self._getRequestParameter('getAddressbook', user, password, url, data)
        parser = DataParser(parameter.Name, addressbook)
        response = request.getResponse(parameter, parser)
        if not response.Ok:
            response.close()
            #TODO: Raise SqlException with correct message!
            raise self.getSqlException(1006, 1107, 'getAddressbook()', user)
        isopen = response.Data == url
        response.close()
        return isopen

    def getAddressbookCards(self, request, user, password, url):
        data = '''\
<?xml version="1.0"?>
<card:addressbook-query xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
  <d:prop>
    <d:getetag />
    <card:address-data />
  </d:prop>
</card:addressbook-query>
'''
        parameter = self._getRequestParameter('getAddressbookCards', user, password, url, data)
        parser = DataParser(parameter.Name)
        response = request.getResponse(parameter, parser)
        if not response.Ok:
            response.close()
            #TODO: Raise SqlException with correct message!
            raise self.getSqlException(1006, 1107, 'getAddressbookCards()', user)
        cards = response.Data
        response.close()
        return cards

    def getModifiedCardByToken(self, request, user, password, url, token):
        data = '''\
<?xml version="1.0"?>
<d:sync-collection xmlns:d="DAV:">
  <d:sync-token>%s</d:sync-token>
  <d:sync-level>1</d:sync-level>
  <d:prop>
    <d:getetag />
  </d:prop>
</d:sync-collection>
''' % token
        parameter = self._getRequestParameter('getModifiedCardByToken', user, password, url, data)
        parser = DataParser(parameter.Name, self._status)
        response = request.getResponse(parameter, parser)
        if not response.Ok:
            response.close()
            #TODO: Raise SqlException with correct message!
            raise self.getSqlException(1006, 1107, 'getModifiedCardByToken()', user)
        data = response.Data
        response.close()
        return data

    def getModifiedCard(self, request, user, password, url, urls):
        data = '''\
<?xml version="1.0"?>
<card:addressbook-multiget xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
  <d:prop>
    <d:getetag />
    <card:address-data />
  </d:prop>
  <d:href>%s</d:href>
</card:addressbook-multiget>
''' % '</d:href><d:href>'.join(urls)
        parameter = self._getRequestParameter('getAddressbookCards', user, password, url, data)
        parser = DataParser(parameter.Name)
        response = request.getResponse(parameter, parser)
        if not response.Ok:
            response.close()
            #TODO: Raise SqlException with correct message!
            raise self.getSqlException(1006, 1107, 'getModifiedCard()', user)
        cards = response.Data
        response.close()
        return cards

    def _getRequestParameter(self, method, user, password, url=None, data=None):
        parameter = uno.createUnoStruct('com.sun.star.auth.RestRequestParameter')
        parameter.Name = method
        if method == 'getUrl':
            parameter.Url = url
            parameter.Method = 'PROPFIND'
            parameter.Auth = (user, password)
            parameter.Header = '{"Content-Type": "application/xml; charset=utf-8", "Depth": "0"}'
            parameter.NoRedirect = True
        elif method == 'getUser':
            parameter.Url = url
            parameter.Method = 'PROPFIND'
            parameter.Auth = (user, password)
            parameter.Data = data
            parameter.Header = '{"Content-Type": "application/xml; charset=utf-8", "Depth": "0"}'
        elif method == 'hasAddressbook':
            parameter.Url = self.BaseUrl + url
            parameter.Method = 'OPTIONS'
            parameter.Auth = (user, password)
        elif method == 'getAddressbooksUrl':
            parameter.Url = self.BaseUrl + url
            parameter.Method = 'PROPFIND'
            parameter.Auth = (user, password)
            parameter.Data = data
            parameter.Header = '{"Content-Type": "application/xml; charset=utf-8", "Depth": "0"}'
        elif method == 'getDefaultAddressbook':
            parameter.Url = self.BaseUrl + url
            parameter.Method = 'PROPFIND'
            parameter.Auth = (user, password)
            parameter.Data = data
            parameter.Header = '{"Content-Type": "application/xml; charset=utf-8", "Depth": "1"}'

        elif method == 'getAllAddressbook':
            parameter.Url = self.BaseUrl + url
            parameter.Method = 'PROPFIND'
            parameter.Auth = (user, password)
            parameter.Data = data
            parameter.Header = '{"Content-Type": "application/xml; charset=utf-8", "Depth": "1"}'



        elif method == 'getAddressbookUrl':
            parameter.Url = self.BaseUrl + url
            parameter.Method = 'PROPFIND'
            parameter.Auth = (user, password)
            parameter.Data = data
            parameter.Header = '{"Content-Type": "application/xml; charset=utf-8", "Depth": "1"}'
        elif method == 'getAddressbook':
            parameter.Url = self.BaseUrl + url
            parameter.Method = 'PROPFIND'
            parameter.Auth = (user, password)
            parameter.Data = data
            parameter.Header = '{"Content-Type": "application/xml; charset=utf-8", "Depth": "1"}'
        elif method == 'getAddressbookCards':
            parameter.Url = self.BaseUrl + url
            parameter.Method = 'REPORT'
            parameter.Auth = (user, password)
            parameter.Data = data
            parameter.Header = '{"Content-Type": "application/xml; charset=utf-8", "Depth": "1"}'
        elif method == 'getModifiedCardByToken':
            parameter.Url = self.BaseUrl + url
            parameter.Method = 'REPORT'
            parameter.Auth = (user, password)
            parameter.Data = data
            parameter.Header = '{"Content-Type": "application/xml; charset=utf-8"}'
        return parameter

    def _checkAddressbookHeader(self, headers):
        for headers in self._headers:
            if headers not in headers:
                return False
        return True

    def getSqlException(self, state, code, method, *args):
        logger = getLogger(self._ctx, g_errorlog, g_basename)
        state = logger.resolveString(state)
        msg = logger.resolveString(code, *args)
        logger.logp(SEVERE, g_basename, method, msg)
        error = getSqlException(state, code, msg, self)
        return error


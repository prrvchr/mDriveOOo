#!
# -*- coding: utf_8 -*-

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

from com.sun.star.task import XInteractionRequest
from com.sun.star.task import XInteractionAbort
from com.sun.star.auth import XInteractionUserName
from com.sun.star.auth import OAuth2Request


# Wrapper to make callable OAuth2Service
class NoOAuth2(object):
    def __call__(self, request):
        return request


# Wrapper to make callable OAuth2Service
class OAuth2OOo(NoOAuth2):
    def __init__(self, oauth2):
        self.oauth2 = oauth2

    def __call__(self, request):
        request.headers['Authorization'] = self.oauth2.getToken('Bearer %s')
        return request


class InteractionAbort(unohelper.Base,
                       XInteractionAbort):

    # XInteractionAbort
    def select(self):
        pass


class InteractionUserName(unohelper.Base,
                          XInteractionUserName):
    def __init__(self):
        self._username = ''
        self._token = ''

    # XInteractionUserName
    def setUserName(self, name):
        self._username = name

    def getUserName(self):
        return self._username

    def setToken(self, token):
        self._token = token

    def getToken(self):
        return self._token

    def select(self):
        pass


class InteractionRequest(unohelper.Base,
                         XInteractionRequest):
    def __init__(self, source, url, user, format, message):
        self._request = self._getRequest(source, url, user, format, message)
        self._abort = InteractionAbort()
        self._continue = InteractionUserName()

    # XInteractionRequest
    def getRequest(self):
        return self._request

    def getContinuations(self):
        return (self._abort, self._continue)

    def _getRequest(self, context, url, user, format, message):
        request = OAuth2Request()
        classification = 'com.sun.star.task.InteractionClassification'
        request.Classification = uno.Enum(classification, 'QUERY')
        request.Context = context
        request.ResourceUrl = url
        request.UserName = user
        request.Format = format
        request.Message = message
        return request

#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.task import ClassifiedInteractionRequest
from com.sun.star.task import XInteractionAbort

from com.sun.star.auth import XOAuth2Request
from com.sun.star.auth import XInteractionUserName


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
    def __init__(self, result):
        self.result = result
        self.username = ''

    # XInteractionSupplyParameters
    def setUserName(self, name):
        self.username = name
    def select(self):
        self.result.Value = self.username
        self.result.IsPresent = True


class InteractionRequest(unohelper.Base,
                         XOAuth2Request):
    def __init__(self, source, name, message, response):
        self.source = source
        self.name = name
        self.message = message
        self.response = response

    # XOAuth2Request
    def getProviderName(self):
        return self.name
    def getRequest(self):
        request = ClassifiedInteractionRequest()
        request.Classification = uno.Enum('com.sun.star.task.InteractionClassification', 'QUERY')
        request.Context = self.source
        request.Message = self.message
        return request
    def getContinuations(self):
        continuations = (InteractionAbort(), InteractionUserName(self.response))
        return continuations

#!
# -*- coding: utf_8 -*-

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
    def __init__(self, result):
        self.result = result
        self.username = ''

    # XInteractionUserName
    def setUserName(self, name):
        self.username = name
    def select(self):
        self.result.Value = self.username
        self.result.IsPresent = True


class InteractionRequest(unohelper.Base,
                         XInteractionRequest):
    def __init__(self, url, source, message, response):
        self.url = url
        self.source = source
        self.message = message
        self.response = response

    # XInteractionRequest
    def getRequest(self):
        request = OAuth2Request()
        classification = 'com.sun.star.task.InteractionClassification'
        request.Classification = uno.Enum(classification, 'QUERY')
        request.ResourceUrl = self.url
        request.Context = self.source
        if self.message is not None:
            request.Message = self.message
        return request
    def getContinuations(self):
        continuations = (InteractionAbort(), InteractionUserName(self.response))
        return continuations

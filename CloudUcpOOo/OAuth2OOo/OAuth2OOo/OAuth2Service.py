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

from com.sun.star.lang import XServiceInfo
from com.sun.star.lang import XInitialization
from com.sun.star.task import XInteractionHandler2
from com.sun.star.auth import XOAuth2Service
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE
from com.sun.star.ucb.ConnectionMode import OFFLINE
from com.sun.star.ucb.ConnectionMode import ONLINE
from com.sun.star.ui.dialogs.ExecutableDialogResults import OK
from com.sun.star.ui.dialogs.ExecutableDialogResults import CANCEL

from com.sun.star.frame.FrameSearchFlag import GLOBAL

from com.sun.star.uno import Exception as UnoException
from com.sun.star.auth import OAuth2Request

from unolib import OAuth2OOo
from unolib import NoOAuth2
from unolib import KeyMap
from unolib import getStringResource
from unolib import createService
from unolib import getConfiguration
from unolib import getDialog
from unolib import getInterfaceTypes
from unolib import getParentWindow

from oauth2 import Request
from oauth2 import Enumeration
from oauth2 import Enumerator
from oauth2 import Iterator
from oauth2 import InputStream
from oauth2 import Uploader
from oauth2 import DialogHandler
from oauth2 import getSessionMode
from oauth2 import execute
from oauth2 import OAuth2Setting
from oauth2 import Wizard
from oauth2 import WizardController
from oauth2 import getRefreshToken
from oauth2 import logMessage
from oauth2 import g_identifier
from oauth2 import g_extension
from oauth2 import g_oauth2
from oauth2 import g_wizard_paths
from oauth2 import g_wizard_page
from oauth2 import g_refresh_overlap
from oauth2 import requests

import time

import traceback

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = g_oauth2


class OAuth2Service(unohelper.Base,
                    XServiceInfo,
                    XInitialization,
                    XInteractionHandler2,
                    XOAuth2Service):
    def __init__(self, ctx):
        self.ctx = ctx
        self.configuration = getConfiguration(self.ctx, g_identifier, True)
        self.Setting = OAuth2Setting(self.ctx)
        version = self._getSSLVersion()
        self.Session = self._getSession(version)
        self._Url = ''
        self._Provider = KeyMap()
        self._Users = None
        self._UserName = ''
        self._User = KeyMap()
        self._parent = None
        self._Warnings = []
        self._Error = None
        self.Error = ''
        self.stringResource = getStringResource(self.ctx, g_identifier, 'OAuth2OOo')
        self._SessionMode = OFFLINE
        #self._checkSSL()

    @property
    def ResourceUrl(self):
        return self.Setting.Url.Id
    @property
    def ProviderName(self):
        return self.Setting.Url.Scope.Provider.Id
    @property
    def UserName(self):
        return self.Setting.Url.Scope.Provider.User.Id
    @property
    def Timeout(self):
        return self.Setting.Timeout

    # XInitialization
    def initialize(self, properties):
        print("OAuth2Service.initialize() 1")
        for property in properties:
            print("OAuth2Service.initialize() 2")
            if property.Name == 'Parent':
                self._parent = property.Value
                print("OAuth2Service.initialize() 3 %s" % self._parent)

    # XInteractionHandler2, XInteractionHandler
    def handle(self, interaction):
        self.handleInteractionRequest(interaction)
    def handleInteractionRequest(self, interaction):
        # TODO: interaction.getRequest() does not seem to be functional under LibreOffice !!!
        # TODO: throw error AttributeError: "args"
        # TODO: on File "/usr/lib/python3/dist-packages/uno.py"
        # TODO: at line 525 in "_uno_struct__setattr__"
        # TODO: as a workaround we must set an "args" attribute of type "sequence<any>" to
        # TODO: IDL file of com.sun.star.auth.OAuth2Request Exception who is normally returned...
        print("OAuth2Service.handleInteractionRequest() 1")
        request = interaction.getRequest()
        mri = createService(self.ctx, 'mytools.Mri')
        if mri:
            print("OAuth2Service.handleInteractionRequest() 2")
            mri.inspect(interaction)
        url = request.ResourceUrl
        user = request.UserName
        if user != '':
            approved = self._getToken(interaction, url, user, request.Format)
        else:
            approved = self._showUserDialog(interaction, url, request.Message)
        return approved

    def _getToken(self, interaction, url, user, format):
        self.initializeSession(url, user)
        token = self.getToken(format)
        status = 1 if token != '' else 0
        continuation = interaction.getContinuations()[status]
        if status:
            continuation.setToken(token)
        continuation.select()
        return status == 1

    def _showUserDialog(self, interaction, url, message):
        provider = self._getProviderNameFromUrl(url)
        dialog = getDialog(self.ctx, g_extension, 'UserDialog', DialogHandler(), self._parent)
        self._initUserDialog(dialog, provider, message)
        status = dialog.execute()
        approved = status == OK
        continuation = interaction.getContinuations()[status]
        if approved:
            continuation.setUserName(self._getUserName(dialog))
        continuation.select()
        dialog.dispose()
        return approved

    def _initUserDialog(self, dialog, provider, message):
        title = self.stringResource.resolveString('UserDialog.Title')
        label = self.stringResource.resolveString('UserDialog.Label1.Label')
        dialog.setTitle(title % provider)
        dialog.getControl('Label1').Text = label % message

    def _getUserName(self, dialog):
        return dialog.getControl('TextField1').Model.Text


    # XOAuth2Service
    def getWarnings(self):
        if self._Warnings:
            return self._Warnings.pop(0)
        return None
    def clearWarnings(self):
        self._Warnings = []

    def isOnLine(self):
        return self._SessionMode != OFFLINE
    def isOffLine(self, host):
        self._SessionMode = getSessionMode(self.ctx, host)
        return self._SessionMode != ONLINE

    def initializeUrl(self, url):
        self.Setting.Url.Id = url
        return self.Setting.Url.Initialized

    def _getProviderNameFromUrl(self, url):
        self.Setting.Url.Id = url
        if self.Setting.Url.Initialized:
            return self.ProviderName
        return ''

    def initializeSession(self, url, name):
        self.Setting.Url.Id = url
        self.Setting.Url.Scope.Provider.User.Id = name
        return self.Setting.Initialized

    def getKeyMap(self):
        return KeyMap()

    def getSessionMode(self, host):
        return getSessionMode(self.ctx, host)

    def getAuthorization(self, url, username, close=True, parent=None):
        authorized = False
        msg = "Wizard Loading ..."
        print("OAuth2Service.getAuthorization() 1")
        wizard = Wizard(self.ctx, g_wizard_page, True, parent)
        print("OAuth2Service.getAuthorization() 2")
        controller = WizardController(self.ctx, wizard, self.Session, url, username, close)
        print("OAuth2Service.getAuthorization() 3")
        arguments = (g_wizard_paths, controller)
        print("OAuth2Service.getAuthorization() 4")
        wizard.initialize(arguments)
        msg += " Done ..."
        #wizard.DialogWindow.toFront()
        print("OAuth2Service.getAuthorization() 5")
        if wizard.execute() == OK:
            msg +=  " Retrieving Authorization Code ..."
            if controller.Error:
                msg += " ERROR: cant retrieve Authorization Code: %s" % controller.Error
            else:
                msg += " Done"
                authorized = self.initializeSession(controller.ResourceUrl, controller.UserName)
        else:
            msg +=  " ERROR: Wizard as been aborted"
            controller.Server.cancel()
        wizard.DialogWindow.dispose()
        logMessage(self.ctx, INFO, msg, 'OAuth2Service', 'getAuthorization()')
        return authorized

    def getToken(self, format=''):
        level = INFO
        msg = "Request Token ... "
        if not self._isAuthorized():
            level = SEVERE
            msg += "ERROR: Cannot InitializeSession()..."
            token = ''
        elif self.Setting.Url.Scope.Provider.User.HasExpired:
            provider = self.Setting.Url.Scope.Provider.MetaData
            user = self.Setting.Url.Scope.Provider.User
            token, self._Error = getRefreshToken(self.Session, provider, user.MetaData, self.Timeout)
            if token.IsPresent:
                user.MetaData = token.Value
                token = user.AccessToken
                msg += "Refresh needed ... Done"
            else:
                level = SEVERE
                msg += "ERROR: Cannot RefreshToken()..."
                token = ''
        else:
            token = self.Setting.Url.Scope.Provider.User.AccessToken
            msg += "Get from configuration ... Done"
        logMessage(self.ctx, level, msg, 'OAuth2Service', 'getToken()')
        if format:
            token = format % token
        return token

    def execute(self, parameter):
        response, error = execute(self.Session, parameter, self.Timeout)
        if error:
            logMessage(self.ctx, SEVERE, error, 'OAuth2Service', 'execute()')
            self._Warnings.append(self._getException(error))
        return response

    def getRequest(self, parameter, parser):
        return Request(self.Session, parameter, self.Timeout, parser)

    def getIterator(self, parameter, parser):
        return Iterator(self.Session, self.Timeout, parameter, parser)

    def getEnumeration(self, parameter, parser):
        return Enumeration(self.Session, parameter, self.Timeout, parser)

    def getEnumerator(self, parameter):
        return Enumerator(self.ctx, self.Session, parameter, self.Timeout)

    def getInputStream(self, parameter, chunk, buffer):
        return InputStream(self.ctx, self.Session, parameter, chunk, buffer, self.Timeout)

    def getUploader(self, chunk, url, user):
        return Uploader(self.ctx, self.Session, chunk, url, user.callBack, self.Timeout)

    def _getSession(self, version):
        print("OAuth2Service._getSession() 1 %s" % version)
        session = None
        #if sys.version_info[0] < 3:
        #    requests.packages.urllib3.disable_warnings()
        if version is not None:
            #if version < 'OpenSSL 1.0.0':
            #    print("OAuth2Service._getSession() 2 %s" % version)
            #    monkey.patch()
            #    print("OAuth2Service._getSession() 3 %s" % version)
            session = requests.Session()
            session.auth = OAuth2OOo(self)
            session.codes = requests.codes
        return session

    def _getSSLVersion(self):
        try:
            import ssl
        except ImportError:
            self.Error = "Can't load module: 'ssl.py'. Your Python SSL configuration is broken..."
            version = None
        else:
            version = ssl.OPENSSL_VERSION
            print("OAuth2Service._getSSLVersion() %s" % version)
        return version

    def _isAuthorized(self):
        print("OAuth2Service._isAuthorized() 1")
        if self.Setting.Initialized and self.Setting.Url.Scope.Authorized:
            return True
        print("OAuth2Service._isAuthorized() 2")
        msg = "OAuth2 initialization ... AuthorizationCode needed ..."
        parent = getParentWindow(self.ctx) if self._parent is None else self._parent
        print("OAuth2Service._isAuthorized() 3")
        if self.getAuthorization(self.ResourceUrl, self.UserName, True, parent):
            print("OAuth2Service._isAuthorized() 4")
            msg += " Done"
            logMessage(self.ctx, INFO, msg, 'OAuth2Service', '_isAuthorized()')
            return True
        msg += " ERROR: Wizard Aborted!!!"
        logMessage(self.ctx, SEVERE, msg, 'OAuth2Service', '_isAuthorized()')
        print("OAuth2Service._isAuthorized() 5")
        return False

    def _getToolkit(self):
        return createService(self.ctx, 'com.sun.star.awt.Toolkit')

    def _isDocument(self, frame):
        controller = frame.getController()
        return controller.getModel() is not None

    def _getException(self, message):
        error = UnoException()
        error.Message = message
        error.Context = self
        return error

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(OAuth2Service,
                                         g_ImplementationName,
                                        (g_ImplementationName,))

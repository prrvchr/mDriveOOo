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

from com.sun.star.ui.dialogs import XWizardPage
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from unolib import PropertySet
from unolib import createService
from unolib import getContainerWindow
from unolib import getProperty
from unolib import getStringResource

from .logger import logMessage

from .oauth2tools import getActivePath
from .oauth2tools import getAuthorizationStr
from .oauth2tools import getAuthorizationUrl
from .oauth2tools import checkUrl
from .oauth2tools import openUrl
from .oauth2tools import updatePageTokenUI

from .configuration import g_identifier
from .configuration import g_extension
from .configuration import g_wizard_paths

import traceback


class WizardPage(unohelper.Base,
                 PropertySet,
                 XWizardPage):
    def __init__(self, ctx, configuration, id, window, uuid, result):
        try:
            msg = "PageId: %s ..." % id
            self.ctx = ctx
            self.Configuration = configuration
            self.PageId = id
            self.Window = window
            self.Uuid = uuid
            self.AuthorizationCode = result
            self.FirstLoad = True
            self._server = None
            self._stringResource = getStringResource(self.ctx, g_identifier, g_extension)
            if id == 1:
                self._initPage1()
            elif id == 3:
                self._initPage3()
            msg += " Done"
            logMessage(self.ctx, INFO, msg, 'WizardPage', '__init__()')
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, 'WizardPage', '__init__()')

    def _initPage1(self):
        username = self.Configuration.Url.Scope.Provider.User.Id
        self.Window.getControl('TextField1').Text = username
        control = self.Window.getControl('ComboBox1')
        control.Model.StringItemList = self.Configuration.UrlList
        providers = self.Configuration.Url.ProviderList
        self.Window.getControl('ComboBox2').Model.StringItemList = providers
        control.Text = self.Configuration.Url.Id

    def _initPage3(self):
        pass

    # XWizardPage Methods
    def activatePage(self):
        #self.Window.setVisible(False)
        msg = "PageId: %s ..." % self.PageId
        if self.PageId == 1:
            pass
            #username = self.Configuration.Url.Scope.Provider.User.Id
            #self.Window.getControl('TextField1').Text = username
            #control = self.Window.getControl('ComboBox1')
            #control.Model.StringItemList = self.Configuration.UrlList
            #providers = self.Configuration.Url.ProviderList
            #self.Window.getControl('ComboBox2').Model.StringItemList = providers
            #control.Text = self.Configuration.Url.Id
        elif self.PageId == 2:
            url = getAuthorizationStr(self.ctx, self.Configuration, self.Uuid)
            self.Window.getControl('TextField1').Text = url
        elif self.PageId == 3:
            url = getAuthorizationUrl(self.ctx, self.Configuration, self.Uuid)
            openUrl(self.ctx, url)
        elif self.PageId == 4:
            url = getAuthorizationUrl(self.ctx, self.Configuration, self.Uuid)
            openUrl(self.ctx, url)
        elif self.PageId == 5:
            username = self.Configuration.Url.Scope.Provider.User.Id
            provider = self.Configuration.Url.ProviderName
            title = self._stringResource.resolveString('PageWizard5.FrameControl1.Label')
            self.Window.getControl('FrameControl1').Model.Label = title % (username, provider)
            updatePageTokenUI(self.Window, self.Configuration, self._stringResource)
        #self.Window.setVisible(True)
        msg += " Done"
        logMessage(self.ctx, INFO, msg, 'WizardPage', 'activatePage()')

    def commitPage(self, reason):
        msg = "PageId: %s ..." % self.PageId
        forward = uno.getConstantByName('com.sun.star.ui.dialogs.WizardTravelType.FORWARD')
        backward = uno.getConstantByName('com.sun.star.ui.dialogs.WizardTravelType.BACKWARD')
        finish = uno.getConstantByName('com.sun.star.ui.dialogs.WizardTravelType.FINISH')
        #self.Window.setVisible(False)
        if self.PageId == 1 and reason == forward:
            pass
        elif self.PageId == 2:
            pass
        elif self.PageId == 3:
            pass
        elif self.PageId == 4:
            code = self.Window.getControl('TextField1').Text
            self.AuthorizationCode.Value = code
            self.AuthorizationCode.IsPresent = True
        msg += " Done"
        logMessage(self.ctx, INFO, msg, 'WizardPage', 'commitPage()')
        return True

    def canAdvance(self):
        advance = True
        if self.PageId == 1:
            advance = self.Window.getControl('TextField1').Text != ''
            advance &= self.Window.getControl('CommandButton2').Model.Enabled
            advance &= self.Window.getControl('CommandButton5').Model.Enabled
            advance &= self.Window.getControl('CommandButton8').Model.Enabled
        elif self.PageId == 2:
            advance = checkUrl(self.ctx, self.Configuration, self.Uuid)
            advance &= bool(self.Window.getControl('CheckBox1').Model.State)
        elif self.PageId == 3:
            advance = self.AuthorizationCode.IsPresent
            advance = True
        elif self.PageId == 4:
            advance = self.Window.getControl('TextField1').Text != ''
        return advance

    def _getPropertySetInfo(self):
        properties = {}
        interface = 'com.sun.star.uno.XInterface'
        optional = 'com.sun.star.beans.Optional<string>'
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['Configuration'] = getProperty('Configuration', interface, readonly)
        properties['PageId'] = getProperty('PageId', 'short', readonly)
        properties['Window'] = getProperty('Window', 'com.sun.star.awt.XWindow', readonly)
        properties['Uuid'] = getProperty('Uuid', 'string', readonly)
        properties['AuthorizationCode'] = getProperty('AuthorizationCode', optional, transient)
        properties['FirstLoad'] = getProperty('FirstLoad', 'boolean', transient)
        return properties

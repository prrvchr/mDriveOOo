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

from com.sun.star.awt import XContainerWindowEventHandler
from com.sun.star.ui.dialogs.ExecutableDialogResults import OK
from com.sun.star.ui.dialogs.ExecutableDialogResults import CANCEL

from unolib import PropertySet
from unolib import getDialog
from unolib import createMessageBox
from unolib import createService
from unolib import getCurrentLocale
from unolib import getProperty
from unolib import getStringResource

from .dialoghandler import DialogHandler

print("wizardhandler.py 1")
from .oauth2tools import getActivePath
from .oauth2tools import openUrl
from .oauth2tools import updatePageTokenUI
from .oauth2tools import getRefreshToken
from .oauth2tools import saveTokenToConfiguration
print("wizardhandler.py 2")
from .configuration import g_identifier

from .logger import logMessage

import traceback

class WizardHandler(unohelper.Base,
                    XContainerWindowEventHandler):
    def __init__(self, ctx, session, configuration, wizard):
        self.ctx = ctx
        self.session = session
        self.Configuration = configuration
        self.Wizard = wizard
        self._stringResource = getStringResource(self.ctx, g_identifier, 'OAuth2OOo')
        #mri = self.ctx.ServiceManager.createInstance('mytools.Mri')
        #mri.inspect(self.Wizard)

    # XContainerWindowEventHandler
    def callHandlerMethod(self, window, event, method):
        try:
            handled = False
            if method == 'Add':
                item = event.Source.Model.Tag
                id = self._addItem(window, item)
                if item == 'Url' or item == 'Value':
                    handled = self._updateWindow(window, method, item, id)
                else:
                    handled = self._showDialog(window, method, item, id)
            elif method == 'Edit':
                item = event.Source.Model.Tag
                handled = self._showDialog(window, method, item)
            elif method == 'Remove':
                item = event.Source.Model.Tag
                if item == 'RemoveToken':
                    handled = self._updateUI(window, event.Source)
                else:
                    handled = self._showDialog(window, method, item)
            elif method == 'Changed':
                handled = self._updateUI(window, event.Source)
            elif method == 'Clicked':
                handled = self.callHandlerMethod(window, event, 'Edit')
            elif method == 'LoadUrl':
                handled = self._loadUrl(window, event.Source)
            elif method == 'StateChange':
                handled = self._updateUI(window, event.Source)
            elif method == 'TextChange':
                handled = self._updateUI(window, event.Source)
            elif method == 'PerformAction':
                handled = True
            elif method == 'Refresh':
                handled = self._updateUI(window, event.Source)
            elif method == 'Reset':
                handled = self._updateUI(window, event.Source)
            return handled
        except Exception as e:
            print("WizardHandler.callHandlerMethod() ERROR: %s - %s" % (e, traceback.print_exc()))
    def getSupportedMethodNames(self):
        return ('Add', 'Edit', 'Remove', 'Refresh', 'Reset', 'Changed', 'Clicked', 'LoadUrl',
                'StateChange', 'TextChange', 'PerformAction')

    def _loadUrl(self, window, control):
        name = control.Model.Name
        url = self._stringResource.resolveString('PageWizard2.%s.Url' % name)
        openUrl(self.ctx, url)

    def _addItem(self, window, item):
        if item == 'Url':
            id = window.getControl('ComboBox1').getText()
            self.Configuration.Url.Id = id
        elif item == 'Provider':
            id = window.getControl('ComboBox2').getText()
            self.Configuration.Url.ProviderName = id
        elif item == 'Scope':
            id = window.getControl('ComboBox3').getText()
            self.Configuration.Url.ScopeName = id
        return id

    def _showDialog(self, window, method, item, id=''):
        print("WizardHandler._showDialog() %s - %s" % (method, item))
        dialog = self._getDialog(window, method, item)
        if method != 'Remove':
            self._initDialog(dialog, method, item, id)
        if dialog.execute():
            self._saveData(window, dialog, method, item, id)
            print("WizardHandler._showDialog() %s - %s - %s" % (method, item, id))
            self._updateWindow(window, method, item, id)
        else:
            # TODO: need delete AddItem
            pass
        dialog.dispose()
        return True

    def _getDialog(self, window, method, item):
        if method != 'Remove':
            print("WizardHandler._getDialog() %s - %s" % (method, item))
            xdl = '%sDialog' % item
            handler = DialogHandler()
            dialog = getDialog(self.ctx, 'OAuth2OOo', xdl, handler, window.Peer)
        else:
            title = self._stringResource.resolveString('MessageBox.Title')
            message = self._stringResource.resolveString('MessageBox.Message')
            dialog = createMessageBox(window.Peer, message, title)
        return dialog

    def _initDialog(self, dialog, method, item, id):
        if item == 'Provider':
            if not id:
                id = self.Configuration.Url.ProviderName
            title = self._stringResource.resolveString('ProviderDialog.Title')
            dialog.setTitle(title % id)
            title = self._stringResource.resolveString('ProviderDialog.FrameControl1.Label')
            print("WizardHandler._initDialog() Provider")
            dialog.getControl('FrameControl1').Model.Label = title % id
            if method == 'Edit':
                clientid = self.Configuration.Url.Scope.Provider.ClientId
                dialog.getControl('TextField1').setText(clientid)
                authurl = self.Configuration.Url.Scope.Provider.AuthorizationUrl
                dialog.getControl('TextField2').setText(authurl)
                tokenurl = self.Configuration.Url.Scope.Provider.TokenUrl
                dialog.getControl('TextField3').setText(tokenurl)
                clientsecret = self.Configuration.Url.Scope.Provider.ClientSecret
                dialog.getControl('TextField4').setText(clientsecret)
                authparameters = self.Configuration.Url.Scope.Provider.AuthorizationParameters
                dialog.getControl('TextField5').setText(authparameters)
                tokenparameters = self.Configuration.Url.Scope.Provider.TokenParameters
                dialog.getControl('TextField6').setText(tokenparameters)
                # CodeChallengeMethod is 'S256' by default in ProviderDialog.xdl
                if self.Configuration.Url.Scope.Provider.CodeChallengeMethod == 'plain':
                    dialog.getControl('OptionButton2').State = 1
                # CodeChallenge is enabled by default in ProviderDialog.xdl
                if not self.Configuration.Url.Scope.Provider.CodeChallenge:
                    control = dialog.getControl('CheckBox1')
                    control.State = 0
                    self._updateUI(dialog, control)
                address = self.Configuration.Url.Scope.Provider.RedirectAddress
                dialog.getControl('TextField7').Text = address
                port = self.Configuration.Url.Scope.Provider.RedirectPort
                dialog.getControl('NumericField1').Value = port
                # HttpHandler is enabled by default in ProviderDialog.xdl
                if not self.Configuration.Url.Scope.Provider.HttpHandler:
                    control = dialog.getControl('OptionButton4')
                    control.State = 1
                    self._updateUI(dialog, control)
        elif item == 'Scope':
            if not id:
                id = self.Configuration.Url.ScopeName
            print("WizardHandler._initDialog() Scope: %s" % (id, ))
            title = self._stringResource.resolveString('ScopeDialog.Title')
            dialog.setTitle(title % id)
            title = self._stringResource.resolveString('ScopeDialog.FrameControl1.Label')
            dialog.getControl('FrameControl1').Model.Label = title % id
            if method == 'Edit':
                values = self.Configuration.Url.Scope.Values
                dialog.getControl('ListBox1').Model.StringItemList = values
                print("WizardHandler._initDialog() Scope: %s" % (values, ))

    def _saveData(self, window, dialog, method, item, id):
        if method == 'Remove':
            if item == 'Url':
                self.Configuration.Url.State = 8
            elif item == 'Provider':
                self.Configuration.Url.Scope.Provider.State = 8
            elif item == 'Scope':
                self.Configuration.Url.Scope.State = 8
        else:
            if item == 'Provider':
                clientid = dialog.getControl('TextField1').Text
                self.Configuration.Url.Scope.Provider.ClientId = clientid
                authurl = dialog.getControl('TextField2').Text
                self.Configuration.Url.Scope.Provider.AuthorizationUrl = authurl
                tokenurl = dialog.getControl('TextField3').Text
                self.Configuration.Url.Scope.Provider.TokenUrl = tokenurl
                challenge = bool(dialog.getControl('CheckBox1').State)
                self.Configuration.Url.Scope.Provider.CodeChallenge = challenge
                method = 'S256' if dialog.getControl('OptionButton1').State else 'plain'
                self.Configuration.Url.Scope.Provider.CodeChallengeMethod = method
                clientsecret = dialog.getControl('TextField4').Text
                self.Configuration.Url.Scope.Provider.ClientSecret = clientsecret
                authparameters = dialog.getControl('TextField5').Text
                self.Configuration.Url.Scope.Provider.AuthorizationParameters = authparameters
                tokenparameters = dialog.getControl('TextField6').Text
                self.Configuration.Url.Scope.Provider.TokenParameters = tokenparameters
                address = dialog.getControl('TextField7').Text
                self.Configuration.Url.Scope.Provider.RedirectAddress = address
                port = int(dialog.getControl('NumericField1').Value)
                self.Configuration.Url.Scope.Provider.RedirectPort = port
                enabled = bool(dialog.getControl('OptionButton3').State)
                print("WizardHandler._saveData() Provider %s" % enabled)
                self.Configuration.Url.Scope.Provider.HttpHandler = enabled
                self.Configuration.Url.Scope.Provider.State = 4
                self.Wizard.activatePath(0 if enabled else 1, True)
                self.Wizard.updateTravelUI()
            elif item == 'Scope':
                values = dialog.getControl('ListBox1').Model.StringItemList
                self.Configuration.Url.Scope.Values = values
                self.Configuration.Url.Scope.State = 4

    def _updateWindow(self, window, method, item, id):
        if method != 'Edit':
            if item == 'Url':
                urls = self.Configuration.UrlList
                control = window.getControl('ComboBox1')
                control.Model.StringItemList = urls
                control.setText(id)
            elif item == 'Provider':
                providers = self.Configuration.Url.ProviderList
                control = window.getControl('ComboBox2')
                control.Model.StringItemList = providers
                control.setText(id)
            elif item == 'Scope':
                scopes = self.Configuration.Url.ScopeList
                control = window.getControl('ComboBox3')
                control.Model.StringItemList = scopes
                control.setText(id)
        return True

    def _updateControl(self, window, control, selection=''):
        item = control.Model.Tag
        if not selection:
            print("WizardHandler._updateControl() ******************************************")
            selection = control.SelectedText
        if item == 'Url':
            self.Configuration.Url.Id = selection
            provider = self.Configuration.Url.ProviderName
            scope = self.Configuration.Url.ScopeName
            window.getControl('ComboBox2').Text = provider
            window.getControl('ComboBox3').Text = scope
        elif item == 'Provider':
            self.Configuration.Url.ProviderName = selection
            scopes = window.getControl('ComboBox3')
            scopes.Model.StringItemList = self.Configuration.Url.ScopeList
            scopes.Text = ''
        elif item == 'Scope':
            self.Configuration.Url.ScopeName = selection
        return True

    def _isSelected(self, control, item=''):
        item = item if item else control.Text
        # TODO: OpenOffice dont return a empty <tuple> but a <ByteSequence instance ''> on
        # ComboBox.Model.StringItemList if StringItemList is empty!!!
        # items = control.Model.StringItemList
        items = control.Model.StringItemList if control.ItemCount else ()
        return item in items

    def _isEdited(self, control, item=''):
        item = item if item else control.Text
        # TODO: OpenOffice dont return a empty <tuple> but a <ByteSequence instance ''> on
        # ComboBox.Model.StringItemList if StringItemList is empty!!!
        # items = control.Model.StringItemList
        items = control.Model.StringItemList if control.ItemCount else ()
        return item != '' and item not in items

    def _updateUI(self, window, control):
        try:
            item = control.Model.Tag
            if item == 'User':
                user = control.Text
                enabled = user != ''
                self.Configuration.Url.Scope.Provider.User.Id = user
                self.Wizard.activatePath(getActivePath(self.Configuration), enabled)
                self.Wizard.updateTravelUI()
            elif item == 'Url':
                url = control.Text
                enabled = self._isSelected(control, url)
                if enabled:
                    self._updateControl(window, control, url)
                    window.getControl('CommandButton1').Model.Enabled = False
                    window.getControl('CommandButton2').Model.Enabled = True
                else:
                    canadd = url != ''
                    canadd &= self._isSelected(window.getControl('ComboBox2'))
                    canadd &= self._isSelected(window.getControl('ComboBox3'))
                    window.getControl('CommandButton1').Model.Enabled = canadd
                    window.getControl('CommandButton2').Model.Enabled = False
                title = self._stringResource.resolveString('PageWizard1.FrameControl2.Label')
                window.getControl('FrameControl2').Model.Label = title % url
                self.Wizard.activatePath(getActivePath(self.Configuration), enabled)
                self.Wizard.updateTravelUI()
            elif item == 'Provider':
                provider = control.Text
                enabled = self._isSelected(control, provider)
                if enabled:
                    self._updateControl(window, control, provider)
                    canadd = self._isEdited(window.getControl('ComboBox1'))
                    canadd &= self._isSelected(window.getControl('ComboBox3'))
                    window.getControl('CommandButton1').Model.Enabled = canadd
                    window.getControl('CommandButton3').Model.Enabled = False
                    window.getControl('CommandButton4').Model.Enabled = True
                    window.getControl('CommandButton5').Model.Enabled = True
                else:
                    canadd = provider != ''
                    canadd &= self._isEdited(window.getControl('ComboBox3'))
                    window.getControl('CommandButton1').Model.Enabled = False
                    window.getControl('CommandButton3').Model.Enabled = canadd
                    window.getControl('CommandButton4').Model.Enabled = False
                    window.getControl('CommandButton5').Model.Enabled = False
                    scopes = window.getControl('ComboBox3')
                    scopes.Model.StringItemList = ()
                    scopes.Text = ''
                self.Wizard.activatePath(getActivePath(self.Configuration), enabled)
                self.Wizard.updateTravelUI()
            elif item == 'Scope':
                scope = control.Text
                enabled = self._isSelected(control, scope)
                if enabled:
                    self._updateControl(window, control, scope)
                    canadd = self._isEdited(window.getControl('ComboBox1'))
                    canadd &= self._isSelected(window.getControl('ComboBox2'))
                    window.getControl('CommandButton1').Model.Enabled = canadd
                    window.getControl('CommandButton6').Model.Enabled = False
                    window.getControl('CommandButton7').Model.Enabled = True
                    window.getControl('CommandButton8').Model.Enabled = True
                else:
                    canadd = scope != ''
                    canadd &= window.getControl('ComboBox2').Text != ''
                    window.getControl('CommandButton1').Model.Enabled = False
                    window.getControl('CommandButton6').Model.Enabled = canadd
                    canadd &= self._isEdited(window.getControl('ComboBox2'))
                    window.getControl('CommandButton3').Model.Enabled = canadd
                    window.getControl('CommandButton7').Model.Enabled = False
                    window.getControl('CommandButton8').Model.Enabled = False
                self.Wizard.activatePath(getActivePath(self.Configuration), enabled)
                self.Wizard.updateTravelUI()
            elif item == 'AcceptPolicy':
                self.Wizard.updateTravelUI()
            elif item == 'AuthorizationCode':
                enabled = window.getControl('TextField1').Text != ''
                finish = uno.getConstantByName('com.sun.star.ui.dialogs.WizardButton.FINISH')
                self.Wizard.enableButton(finish, enabled)
                self.Wizard.updateTravelUI()
            elif item == 'RefreshToken':
                if self.Configuration.Url.Scope.Provider.User.HasExpired:
                    provider = self.Configuration.Url.Scope.Provider.MetaData
                    user = self.Configuration.Url.Scope.Provider.User.MetaData
                    timeout = self.Configuration.Timeout
                    token, error = getRefreshToken(self.session, provider, user, timeout)
                    if error is None:
                        saveTokenToConfiguration(self.Configuration, token)
                updatePageTokenUI(window, self.Configuration, self._stringResource)
            elif item == 'RemoveToken':
                user = self.Configuration.Url.Scope.Provider.User
                user.Scope = ''
                user.commit()
                updatePageTokenUI(window, self.Configuration, self._stringResource)
            elif item == 'ResetToken':
                user = self.Configuration.Url.Scope.Provider.User
                user.ExpiresIn = 0
                user.commit()
                updatePageTokenUI(window, self.Configuration, self._stringResource)
            return True
        except Exception as e:
            print("WizardHandler._updateUI() ERROR: %s - %s" % (e, traceback.print_exc()))

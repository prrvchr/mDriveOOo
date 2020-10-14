#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.lang import XServiceInfo
from com.sun.star.awt import XContainerWindowEventHandler
from com.sun.star.awt import XDialogEventHandler
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from unolib import createService
from unolib import getFileSequence
from unolib import getStringResource
from unolib import getNamedValueSet
from unolib import getConfiguration
from unolib import getInteractionHandler
from unolib import InteractionRequest
from unolib import getUserNameFromHandler
from unolib import getDialog

from oauth2 import getLoggerUrl
from oauth2 import getLoggerSetting
from oauth2 import setLoggerSetting
from oauth2 import clearLogger
from oauth2 import logMessage
from oauth2 import g_identifier
from oauth2 import g_oauth2

import traceback

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = '%s.OptionsDialog' % g_identifier


class OptionsDialog(unohelper.Base,
                    XServiceInfo,
                    XContainerWindowEventHandler,
                    XDialogEventHandler):
    def __init__(self, ctx):
        try:
            self.ctx = ctx
            self.stringResource = getStringResource(self.ctx, g_identifier, 'OAuth2OOo', 'OptionsDialog')
            self.service = createService(self.ctx, g_oauth2)
            logMessage(self.ctx, INFO, "Loading ... Done", 'OptionsDialog', '__init__()')
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, 'OptionsDialog', '__init__()')

    # XContainerWindowEventHandler, XDialogEventHandler
    def callHandlerMethod(self, dialog, event, method):
        handled = False
        if method == 'external_event':
            if event == 'ok':
                self._saveSetting(dialog)
                handled = True
            elif event == 'back':
                self._loadSetting(dialog)
                handled = True
            elif event == 'initialize':
                self._loadSetting(dialog)
                handled = True
        elif method == 'TextChanged':
            self._doTextChanged(dialog, event.Source)
            handled = True
        elif method == 'SelectionChanged':
            self._doSelectionChanged(dialog, event.Source)
            handled = True
        elif method == 'Connect':
            self._doConnect(dialog)
            handled = True
        elif method == 'Remove':
            self._doRemove(dialog)
            handled = True
        elif method == 'Reset':
            self._doReset(dialog)
            handled = True
        elif method == 'AutoClose':
            handled = True
        elif method == 'ToggleLogger':
            enabled = event.Source.State == 1
            self._toggleLogger(dialog, enabled)
            handled = True
        elif method == 'EnableViewer':
            self._toggleViewer(dialog, True)
            handled = True
        elif method == 'DisableViewer':
            self._toggleViewer(dialog, False)
            handled = True
        elif method == 'ViewLog':
            self._viewLog(dialog)
            handled = True
        elif method == 'ClearLog':
            self._clearLog(dialog)
            handled = True
        return handled
    def getSupportedMethodNames(self):
        return ('external_event', 'TextChanged', 'SelectionChanged', 'Connect', 'Remove', 'Reset',
                'AutoClose', 'ToggleLogger', 'EnableViewer', 'DisableViewer', 'ViewLog', 'ClearLog')

    def _doTextChanged(self, dialog, control):
        enabled = control.Text != ''
        dialog.getControl('CommandButton2').Model.Enabled = True

    def _doSelectionChanged(self, dialog, control):
        enabled = control.SelectedText != ''
        dialog.getControl('CommandButton2').Model.Enabled = enabled

    def _doConnect(self, dialog):
        try:
            user = ''
            print("OptionDialog._doConnect() 1")
            url = dialog.getControl('ComboBox2').SelectedText
            if url != '':
                message = "Authentication needed!!!"
                if self.service.initializeUrl(url):
                    print("OptionDialog._doConnect() 2 %s" % url)
                    user = getUserNameFromHandler(self.ctx, url, self, message)
            autoclose = bool(dialog.getControl('CheckBox2').State)
            print("OptionDialog._doConnect() 3 %s - %s - %s" % (user, url, autoclose))
            enabled = self.service.getAuthorization(url, user, autoclose, dialog.getPeer())
            print("OptionDialog._doConnect() 4")
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, "OptionsDialog", "_doConnect()")

    def _loadSetting(self, dialog):
        try:
            dialog.getControl('NumericField1').setValue(self.service.Setting.ConnectTimeout)
            dialog.getControl('NumericField2').setValue(self.service.Setting.ReadTimeout)
            dialog.getControl('NumericField3').setValue(self.service.Setting.HandlerTimeout)
            dialog.getControl('ComboBox2').Model.StringItemList = self.service.Setting.Url.UrlList
            self._loadLoggerSetting(dialog)
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, "OptionsDialog", "_loadSetting()")

    def _saveSetting(self, dialog):
        try:
            self._saveLoggerSetting(dialog)
            self.service.Setting.ConnectTimeout = int(dialog.getControl('NumericField1').getValue())
            self.service.Setting.ReadTimeout = int(dialog.getControl('NumericField2').getValue())
            self.service.Setting.HandlerTimeout = int(dialog.getControl('NumericField3').getValue())
            self.service.Setting.commit()
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, "OptionsDialog", "_saveSetting()")

    def _toggleLogger(self, dialog, enabled):
        dialog.getControl('Label1').Model.Enabled = enabled
        dialog.getControl('ListBox1').Model.Enabled = enabled
        dialog.getControl('OptionButton1').Model.Enabled = enabled
        control = dialog.getControl('OptionButton2')
        control.Model.Enabled = enabled
        self._toggleViewer(dialog, enabled and control.State)

    def _toggleViewer(self, dialog, enabled):
        dialog.getControl('CommandButton1').Model.Enabled = enabled

    def _viewLog(self, window):
        dialog = getDialog(self.ctx, 'OAuth2OOo', 'LogDialog', self, window.Peer)
        url = getLoggerUrl(self.ctx)
        dialog.Title = url
        self._setDialogText(dialog, url)
        dialog.execute()
        dialog.dispose()

    def _clearLog(self, dialog):
        try:
            clearLogger()
            logMessage(self.ctx, INFO, "ClearingLog ... Done", 'OptionsDialog', '_doClearLog()')
            url = getLoggerUrl(self.ctx)
            self._setDialogText(dialog, url)
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, "OptionsDialog", "_doClearLog()")

    def _setDialogText(self, dialog, url):
        length, sequence = getFileSequence(self.ctx, url)
        dialog.getControl('TextField1').Text = sequence.value.decode('utf-8')

    def _loadLoggerSetting(self, dialog):
        enabled, index, handler = getLoggerSetting(self.ctx)
        dialog.getControl('CheckBox1').State = int(enabled)
        dialog.getControl('ListBox1').selectItemPos(index, True)
        dialog.getControl('OptionButton%s' % handler).State = 1
        self._toggleLogger(dialog, enabled)

    def _saveLoggerSetting(self, dialog):
        enabled = bool(dialog.getControl('CheckBox1').State)
        index = dialog.getControl('ListBox1').getSelectedItemPos()
        handler = dialog.getControl('OptionButton1').State
        setLoggerSetting(self.ctx, enabled, index, handler)

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(OptionsDialog,
                                         g_ImplementationName,
                                        (g_ImplementationName,))

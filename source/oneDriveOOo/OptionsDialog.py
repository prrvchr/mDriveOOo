#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.lang import XServiceInfo
from com.sun.star.awt import XContainerWindowEventHandler
from com.sun.star.awt import XDialogEventHandler
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from onedrive import createService
from onedrive import getFileSequence
from onedrive import getStringResource
from onedrive import getResourceLocation
from onedrive import getConfiguration
from onedrive import getDialog

from onedrive import getLoggerUrl
from onedrive import getLoggerSetting
from onedrive import setLoggerSetting
from onedrive import clearLogger
from onedrive import logMessage

from onedrive import g_scheme
from onedrive import g_extension
from onedrive import g_identifier

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
            self.stringResource = getStringResource(self.ctx, g_identifier, g_extension, 'OptionsDialog')
            print("PyOptionsDialog.__init__() 1")
        except Exception as e:
            print("PyOptionsDialog.__init__().Error: %s - %s" % (e, traceback.print_exc()))

    def __del__(self):
        #self.Connection.close()
        print("PyOptionsDialog.__del__()***********************")

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
        elif method == 'ViewDataSource':
            self._doViewDataSource(dialog)
            handled = True
        return handled
    def getSupportedMethodNames(self):
        return ('external_event', 'ToggleLogger', 'EnableViewer', 'DisableViewer',
                'ViewLog', 'ClearLog', 'ViewDataSource')

    def _loadSetting(self, dialog):
        self._loadLoggerSetting(dialog)

    def _saveSetting(self, dialog):
        self._saveLoggerSetting(dialog)

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
        dialog = getDialog(self.ctx, g_extension, 'LogDialog', self, window.Peer)
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

    def _doViewDataSource(self, dialog):
        try:
            path = getResourceLocation(self.ctx, g_identifier, 'hsqldb')
            url = '%s/%s.odb' % (path, g_scheme)
            desktop = self.ctx.ServiceManager.createInstance('com.sun.star.frame.Desktop')
            desktop.loadComponentFromURL(url, '_default', 0, ())
            #mri = self.ctx.ServiceManager.createInstance('mytools.Mri')
            #mri.inspect(connection)
            print("PyOptionsDialog._doConnect() 2")
        except Exception as e:
            print("PyOptionsDialog._doConnect().Error: %s - %s" % (e, traceback.print_exc()))

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(OptionsDialog,                             # UNO object class
                                         g_ImplementationName,                      # Implementation name
                                        (g_ImplementationName,))                    # List of implemented services

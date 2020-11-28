#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.ui.dialogs import XWizardController
from com.sun.star.awt import XCallback
from com.sun.star.lang import IllegalArgumentException
from com.sun.star.ui.dialogs.ExecutableDialogResults import OK
from com.sun.star.ui.dialogs.ExecutableDialogResults import CANCEL
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from unolib import PropertySet
from unolib import createService
from unolib import generateUuid
from unolib import getCurrentLocale
from unolib import getProperty
from unolib import getStringResource
from unolib import getContainerWindow
from unolib import getDialogUrl
print("wizardcontroller.py 1")
from .wizardhandler import WizardHandler
print("wizardcontroller.py 2")
from .wizardserver import WizardServer
from .wizardpage import WizardPage
from .wizardsetting import WizardSetting

from .logger import logMessage

from .oauth2tools import getActivePath
from .oauth2tools import getTokenParameters
from .oauth2tools import getResponseFromRequest
from .oauth2tools import registerTokenFromResponse

from .configuration import g_identifier
from .configuration import g_extension

import traceback


class WizardController(unohelper.Base,
                       PropertySet,
                       XWizardController,
                       XCallback):
    def __init__(self, ctx, wizard, session, url, username, autoclose):
        self.ctx = ctx
        self._provider = createService(self.ctx, 'com.sun.star.awt.ContainerWindowProvider')
        self.Session = session
        self.Configuration = WizardSetting(self.ctx)
        self.ResourceUrl = url
        self.UserName = username
        self.AutoClose = autoclose
        self._pages = [1]
        self.AuthorizationCode = uno.createUnoStruct('com.sun.star.beans.Optional<string>')
        self.Server = WizardServer(self.ctx)
        self.Uuid = generateUuid()
        self._wizard = wizard
        self.Error = ''
        self._stringResource = getStringResource(self.ctx, g_identifier, 'OAuth2OOo')
        self._handler = WizardHandler(ctx, session, self.Configuration, wizard)
        path = getActivePath(self.Configuration)
        print("WizardController.__init__() %s" % path)
        self._wizard.activatePath(path, True)
        #service = 'com.sun.star.awt.ContainerWindowProvider'
        #self.provider = self.ctx.ServiceManager.createInstanceWithContext(service, self.ctx)
        #mri = self.ctx.ServiceManager.createInstance('mytools.Mri')
        #mri.inspect(self._wizard)

    @property
    def ResourceUrl(self):
        return self.Configuration.Url.Id
    @ResourceUrl.setter
    def ResourceUrl(self, url):
        self.Configuration.Url.Id = url
    @property
    def UserName(self):
        return self.Configuration.Url.Scope.Provider.User.Id
    @UserName.setter
    def UserName(self, name):
        self.Configuration.Url.Scope.Provider.User.Id = name
    @property
    def ActivePath(self):
        return getActivePath(self.Configuration)
    @property
    def CodeVerifier(self):
        return self.Uuid + self.Uuid

    # XCallback
    def notify(self, percent):
        msg = "WizardController.notify() %s" % percent
        logMessage(self.ctx, INFO, msg, 'WizardController', 'notify()')
        page = self._wizard.getCurrentPage()
        if page.PageId == 3:
            if page.Window:
                page.Window.getControl('ProgressBar1').Value = percent
            if percent == 100:
                self._wizard.updateTravelUI()
                if self.AuthorizationCode.IsPresent:
                    self._registerTokens()
                    if self.AutoClose:
                        logMessage(self.ctx, INFO, "WizardController.notify() 2", 'WizardController', 'notify()')
                        self._wizard.DialogWindow.endDialog(OK)
                        logMessage(self.ctx, INFO, "WizardController.notify() 3", 'WizardController', 'notify()')
                    else:
                        logMessage(self.ctx, INFO, "WizardController.notify() 4", 'WizardController', 'notify()')
                        self._wizard.travelNext()
                        logMessage(self.ctx, INFO, "WizardController.notify() 5", 'WizardController', 'notify()')

    # XWizardController
    def createPage(self, parent, id):
        try:
            msg = "PageId: %s ..." % id
            url = getDialogUrl(g_extension, 'PageWizard%s' % id)
            window = self._provider.createContainerWindow(url, 'NotUsed', parent, self._handler)
            page = WizardPage(self.ctx,
                              self.Configuration,
                              id,
                              window,
                              self.Uuid,
                              self.AuthorizationCode)
            msg += " Done"
            logMessage(self.ctx, INFO, msg, 'WizardController', 'createPage()')
            return page
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, 'WizardController', 'createPage()')

    def getPageTitle(self, id):
        title = self._stringResource.resolveString('PageWizard%s.Step' % id)
        return title
    def canAdvance(self):
        return self._wizard.getCurrentPage().canAdvance()
    def onActivatePage(self, id):
        try:
            msg = "PageId: %s..." % id
            title = self._stringResource.resolveString('PageWizard%s.Title' % id)
            self._wizard.setTitle(title)
            backward = uno.getConstantByName('com.sun.star.ui.dialogs.WizardButton.PREVIOUS')
            forward = uno.getConstantByName('com.sun.star.ui.dialogs.WizardButton.NEXT')
            if id == 1:
                pass
            elif id == 2:
                pass
                #if self.Shortened:
                #    self._wizard.activatePath(getActivePath(self.Configuration), False)
            elif id == 3:
                self.Server.addCallback(self, self.Configuration)
                self._wizard.enableButton(backward, False)
                self._wizard.enableButton(forward, False)
                for page in (1,2,5):
                    self._wizard.enablePage(page, False)
            elif id == 4:
                self._wizard.enableButton(backward, False)
                self._wizard.enableButton(forward, False)
                for page in (1,2,5):
                    self._wizard.enablePage(page, False)
            elif id == 5:
                path = getActivePath(self.Configuration)
                self._wizard.activatePath(path, True)
            msg += " Done"
            logMessage(self.ctx, INFO, msg, 'WizardController', 'onActivatePage()')
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, 'WizardController', 'onActivatePage()')

    def onDeactivatePage(self, id):
        try:
            if id == 1:
                pass
                #path = getActivePath(self.Configuration)
                #self._wizard.activatePath(path, True)
                #self._wizard.updateTravelUI()
            elif id == 4 and self.AuthorizationCode.IsPresent:
                pass
                #self._registerTokens()
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            logMessage(self.ctx, SEVERE, msg, 'WizardController', 'onDeactivatePage()')
    def confirmFinish(self):
        return True

    def _registerTokens(self):
        result = False
        code = self.AuthorizationCode.Value
        url = self.Configuration.Url.Scope.Provider.TokenUrl
        data = getTokenParameters(self.Configuration, code, self.CodeVerifier)
        msg = "Make Http Request: %s?%s" % (url, data)
        logMessage(self.ctx, INFO, msg, 'WizardController', '_registerTokens()')
        timeout = self.Configuration.Timeout
        response, error = getResponseFromRequest(self.Session, url, data, timeout)
        result = registerTokenFromResponse(self.Configuration, response)
        if result:
            self.Configuration.commit()
        return result

    def _getPropertySetInfo(self):
        properties = {}
        interface = 'com.sun.star.uno.XInterface'
        optional = 'com.sun.star.beans.Optional<string>'
        bound = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.BOUND')
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['Wizard'] = getProperty('Wizard', 'com.sun.star.ui.dialogs.XWizard', readonly)
        properties['ResourceUrl'] = getProperty('ResourceUrl', 'string', transient)
        properties['UserName'] = getProperty('UserName', 'string', transient)
        properties['AutoClose'] = getProperty('AutoClose', 'boolean', readonly)
        properties['ActivePath'] = getProperty('ActivePath', 'short', readonly)
        properties['AuthorizationCode'] = getProperty('AuthorizationCode', optional, bound)
        properties['Uuid'] = getProperty('Uuid', 'string', readonly)
        properties['CodeVerifier'] = getProperty('CodeVerifier', 'string', readonly)
        properties['Configuration'] = getProperty('Configuration', interface, readonly)
        properties['Server'] = getProperty('Server', interface, bound | readonly)
        properties['Error'] = getProperty('Error', 'string', transient)
#        properties['Handler'] = getProperty('Handler', interface, readonly)
        return properties

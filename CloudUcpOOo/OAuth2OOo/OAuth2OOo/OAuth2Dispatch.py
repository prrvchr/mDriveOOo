#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.lang import XServiceInfo
from com.sun.star.lang import XInitialization
from com.sun.star.frame import XDispatchProvider
from com.sun.star.frame import XDispatch

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from oauth2 import logMessage
from oauth2 import getMessage

from oauth2 import g_identifier

import traceback

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = '%s.OAuth2DispatchProvider' % g_identifier


class OAuth2DispatchProvider(unohelper.Base,
                             XServiceInfo,
                             XInitialization,
                             XDispatchProvider):
    def __init__(self, ctx):
        self.ctx = ctx
        self._frame = None
        logMessage(self.ctx, INFO, "Loading ... Done", 'OAuth2DispatchProvider', '__init__()')

    # XInitialization
    def initialize(self, args):
        if len(args) > 0:
            print("OAuth2DispatchProvider.initialize()")
            self._frame = args[0]

    # XDispatchProvider
    def queryDispatch(self, url, frame, flags):
        if url.Protocol != 'oauth2:':
            print("OAuth2DispatchProvider.queryDispatch() 1 %s" % url.Protocol)
            return None
        print("OAuth2DispatchProvider.queryDispatch()2")
        dispatch = OAuth2Dispatch(self.ctx, self._frame)
        return dispatch
    def queryDispatches(self, requests):
        dispatches = []
        for r in requests:
            dispatches.append(self.queryDispatch(r.FeatureURL, r.FrameName, r.SearchFlags))
        return tuple(dispatches)

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(OAuth2DispatchProvider,                    # UNO object class
                                         g_ImplementationName,                      # Implementation name
                                        (g_ImplementationName,))                    # List of implemented services


class OAuth2Dispatch(unohelper.Base,
                     XDispatch):
    def __init__(self, ctx, frame):
        self.ctx = ctx
        self._listeners = []
        if frame is not None:
            self._parent = frame.getContainerWindow()
            print("OAuth2Dispatch.__init__()")
        else:
            self._parent = None
            print("OAuth2Dispatch.__init__() not parent set!!!!!!")
        logMessage(self.ctx, INFO, "Loading ... Done", 'OAuth2Dispatch', '__init__()')

    # XDispatch
    def dispatch(self, url, arguments):
        kwargs = {arg.Name: arg.Value for arg in arguments}
            print("OAuth2Dispatch.dispatch() 1 %s" % (kwargs, ))
        self._showWizard(kwargs)
    def addStatusListener(self, listener, url):
        print("OAuth2Dispatch.addStatusListener()")
    def removeStatusListener(self, listener, url):
        print("OAuth2Dispatch.removeStatusListener()")

    def _showWizard(self, kwargs):
        try:
            print("_showWizard()")
            msg = "Wizard Loading ..."
            wizard = Wizard(self.ctx, g_wizard_page, True, self._parent)
            controller = WizardController(self.ctx, wizard, self._model)
            arguments = (g_wizard_paths, controller)
            wizard.initialize(arguments)
            msg += " Done ..."
            if wizard.execute() == OK:
                msg +=  " Retrieving SMTP configuration OK..."
            else:
                msg +=  " ERROR: Wizard as been aborted"
            wizard.DialogWindow.dispose()
            wizard.DialogWindow = None
            print(msg)
            logMessage(self.ctx, INFO, msg, 'OAuth2Dispatch', '_showWizard()')
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            print(msg)

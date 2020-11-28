#!
# -*- coding: utf-8 -*-

from .configuration import g_extension
from .configuration import g_identifier
from .configuration import g_oauth2
from .configuration import g_wizard_paths
from .configuration import g_wizard_page
from .configuration import g_refresh_overlap

print("oauth2.__init__.py 1")
import traceback
try:
    import _cffi_backend as backend
    #from cryptography.hazmat.bindings._openssl import ffi, lib
except Exception as e:
    msg = "Error: %s - %s" % (e, traceback.print_exc())
    print(msg)
print("oauth2.__init__.py 2")

from .oauth2setting import OAuth2Setting
from .wizard import Wizard
print("oauth2.__init__.py 3")
from .wizardcontroller import WizardController
print("oauth2.__init__.py 4")
from .request import Request
from .request import Enumeration
from .request import Enumerator
from .request import Iterator
from .request import InputStream
from .request import Uploader
from .request import getSessionMode
from .request import getConnectionMode
from .request import execute

from .oauth2tools import getActivePath
from .oauth2tools import getRefreshToken
from .oauth2tools import getAuthorizationStr
from .oauth2tools import checkUrl
from .oauth2tools import openUrl

from .dialoghandler import DialogHandler

from .logger import getLoggerSetting
from .logger import getLoggerUrl
from .logger import setLoggerSetting
from .logger import clearLogger
from .logger import logMessage
from .logger import getMessage

from . import requests

#!
# -*- coding: utf-8 -*-

from .configuration import g_identifier
from .configuration import g_oauth2
from .configuration import g_logger
from .configuration import g_wizard_paths
from .configuration import g_wizard_page
from .configuration import g_refresh_overlap

from .oauth2setting import OAuth2Setting
from .wizard import Wizard
from .wizardcontroller import WizardController

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

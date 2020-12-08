#!
# -*- coding: utf-8 -*-

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

from .configuration import g_extension
from .configuration import g_identifier
from .configuration import g_oauth2
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

#try:
#    import ssl
#    print("oauth2.__init__.py 1")
#except ImportError:
#    try:
#        from . import ssl
#        print("oauth2.__init__.py 2")
#    except ImportError:
#        ssl = None
#        print("oauth2.__init__.py 3")

from . import requests

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

from .keymap import KeyMap

from .unolib import InteractionHandler
from .unolib import Initialization
from .unolib import PropertySet
from .unolib import PropertySetInfo
from .unolib import PropertiesChangeNotifier
from .unolib import PropertySetInfoChangeNotifier

from .unotools import createMessageBox
from .unotools import createService
from .unotools import getContainerWindow
from .unotools import getProperty
from .unotools import getPropertyValue
from .unotools import getPropertyValueSet
from .unotools import getResourceLocation
from .unotools import getCurrentLocale
from .unotools import getFileSequence
from .unotools import getConfiguration
from .unotools import getSimpleFile
from .unotools import getStringResource
from .unotools import generateUuid
from .unotools import getNamedValue
from .unotools import getNamedValueSet
from .unotools import getSimpleFile
from .unotools import getInteractionHandler
from .unotools import getDialog
from .unotools import getDialogUrl
from .unotools import getDateTime
from .unotools import getInterfaceTypes
from .unotools import hasInterface
from .unotools import parseDateTime
from .unotools import unparseDateTime
from .unotools import unparseTimeStamp
from .unotools import getConnectionMode
from .unotools import getRequest
from .unotools import getOAuth2
from .unotools import getParentWindow
from .unotools import getUrl
from .unotools import getExceptionMessage

from .unocore import PropertyContainer

from .oauth2config import g_oauth2

from .oauth2lib import InteractionRequest
from .oauth2lib import NoOAuth2
from .oauth2lib import OAuth2OOo

from .oauth2core import getOAuth2UserName
from .oauth2core import getOAuth2Token

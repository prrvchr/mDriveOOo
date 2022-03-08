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

import traceback
try:

    from .contentprovider import ContentProvider
    from .datasource import DataSource
    from .user import User
    from .identifier import Identifier
    from .providerbase import ProviderBase
    from .content import Content

    from .contentcore import executeContentCommand
    from .contentcore import getPropertiesValues
    from .contentcore import setPropertiesValues

    from .contentlib import CommandInfo
    from .contentlib import CommandInfoChangeNotifier
    from .contentlib import InteractionRequestParameters
    from .contentlib import Row
    from .contentlib import DynamicResultSet

    from .contenttools import getUcb
    from .contenttools import getUcp
    from .contenttools import getUri
    from .contenttools import getMimeType
    from .contenttools import getCommandInfo
    from .contenttools import getContentEvent
    from .contenttools import getContentInfo
    from .contenttools import propertyChange

    from .dbtool import registerDataSource
    from .dbtool import executeQueries
    from .dbtool import getDataBaseConnection
    from .dbtool import getKeyMapFromResult
    from .dbtool import getSequenceFromResult

    from .unolib import KeyMap

    from .unotool import createService
    from .unotool import getFileSequence
    from .unotool import getStringResource
    from .unotool import getResourceLocation
    from .unotool import getConfiguration
    from .unotool import getDialog

    from .dbqueries import getSqlQuery

    from .logger import getLoggerSetting
    from .logger import getLoggerUrl
    from .logger import setLoggerSetting
    from .logger import clearLogger
    from .logger import logMessage
    from .logger import getMessage

    from .configuration import g_provider
    from .configuration import g_scheme
    from .configuration import g_extension
    from .configuration import g_identifier
    from .configuration import g_host
    from .configuration import g_url
    from .configuration import g_upload

    from .configuration import g_userkeys
    from .configuration import g_userfields
    from .configuration import g_drivekeys
    from .configuration import g_drivefields
    from .configuration import g_itemkeys
    from .configuration import g_itemfields

    from .configuration import g_chunk
    from .configuration import g_buffer
    from .configuration import g_pages

    from .configuration import g_office
    from .configuration import g_folder
    from .configuration import g_link
    from .configuration import g_doc_map

except Exception as e:
    print("clouducp.__init__() ERROR: %s - %s" % (e, traceback.print_exc()))

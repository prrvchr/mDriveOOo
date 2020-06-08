#!
# -*- coding: utf-8 -*-

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

    from .dbtools import registerDataSource
    from .dbtools import executeQueries
    from .dbtools import getDataSourceLocation
    from .dbtools import getDataSourceInfo
    from .dbtools import getDataSourceJavaInfo
    from .dbtools import getDataBaseConnection
    from .dbtools import getKeyMapFromResult
    from .dbtools import getSequenceFromResult

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

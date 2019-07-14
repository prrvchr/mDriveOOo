#!
# -*- coding: utf-8 -*-

from .configuration import g_oauth2
from .configuration import g_doc_map
from .configuration import g_folder
from .configuration import g_host
from .configuration import g_link
from .configuration import g_office
from .configuration import g_plugin
from .configuration import g_provider
from .configuration import g_scheme
from .configuration import g_url
from .configuration import g_upload
from .configuration import g_userkeys
from .configuration import g_userfields
from .configuration import g_drivekeys
from .configuration import g_drivefields
from .configuration import g_itemkeys
from .configuration import g_itemfields
from .configuration import g_pages
from .configuration import g_chunk
from .configuration import g_buffer

from .logger import getLogger
from .logger import getLoggerSetting
from .logger import setLoggerSetting
from .logger import getLoggerUrl
from .logger import isLoggerEnabled

from .unotools import getFileSequence
from .unotools import getStringResource
from .unotools import getResourceLocation

from .contenttools import getUcp

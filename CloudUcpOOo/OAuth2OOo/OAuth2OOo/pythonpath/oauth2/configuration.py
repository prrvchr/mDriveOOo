#!
# -*- coding: utf_8 -*-

# OAuth2 configuration
g_extension = 'OAuth2OOo'
g_identifier = 'com.gmail.prrvchr.extensions.%s' % g_extension
g_logger = '%s.Logger' % g_identifier
g_oauth2 = '%s.OAuth2Service' % g_identifier

g_advance_to = 0 # 0 to disable
g_wizard_paths = ((1, 2, 3, 5), (1, 2, 4, 5), (1, 5))
g_refresh_overlap = 10 # must be positive, in second

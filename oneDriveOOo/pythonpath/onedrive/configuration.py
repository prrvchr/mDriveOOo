#!
# -*- coding: utf-8 -*-

# Provider configuration
g_scheme = 'vnd.microsoft-apps'
g_extension = 'oneDriveOOo'
g_identifier = 'com.gmail.prrvchr.extensions.%s' % g_extension
g_logger = '%s.Logger' % g_identifier

g_provider = 'Microsoft'
g_host = 'graph.microsoft.com'
g_version = 'v1.0' # v1.0 or beta
g_url = 'https://%s/%s' % (g_host, g_version)
g_upload = '%s/me/drive/items/%%s:/%%s:/createUploadSession' % g_url

g_userkeys = ('id','userPrincipalName','displayName')
g_userfields = ','.join(g_userkeys)
g_drivekeys = ('id','createdDateTime','lastModifiedDateTime','name')
g_drivefields = ','.join(g_drivekeys)
g_itemkeys = ('file','size','parentReference')
g_itemfields = '%s,%s' % (g_drivefields, ','.join(g_itemkeys))
g_pages = 100

# If your app splits a file into multiple byte ranges, the size of each byte range MUST be
# a multiple of 320 KiB (327,680 bytes). Using a fragment size that does not divide evenly
# by 320 KiB will result in errors committing some files
g_chunk = 327680  # Http request maximum data size, must be a multiple of 'g_buffer'
g_buffer = 32768  # InputStream (Downloader) maximum 'Buffers' size

g_office = 'application/vnd.oasis.opendocument'
g_folder = 'application/vnd.microsoft-apps.folder'
g_link = 'application/vnd.microsoft-apps.link'
g_doc_map = {'application/vnd.microsoft-apps.document':     'application/vnd.oasis.opendocument.text',
             'application/vnd.microsoft-apps.spreadsheet':  'application/x-vnd.oasis.opendocument.spreadsheet',
             'application/vnd.microsoft-apps.presentation': 'application/vnd.oasis.opendocument.presentation',
             'application/vnd.microsoft-apps.drawing':      'application/pdf'}

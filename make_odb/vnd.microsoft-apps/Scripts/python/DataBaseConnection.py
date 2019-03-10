#!
# -*- coding: utf_8 -*-

import uno


g_class = 'org.hsqldb.jdbc.JDBCDriver'
g_jar = 'hsqldb.jar'
g_protocol = 'jdbc:hsqldb:'
g_path = 'hsqldb/'
g_scheme = 'vnd.microsoft-apps'
g_options = ';default_schema=true;hsqldb.default_table_type=cached;get_column_name=false;ifexists=true'


def setDataBaseConnection(*arg):
    doc = XSCRIPTCONTEXT.getDocument()
    location = _getDocumentLocation(doc)
    doc.DataSource.Settings.JavaDriverClass = g_class
    doc.DataSource.Settings.JavaDriverClassPath = location + g_path + g_jar
    doc.DataSource.URL = g_protocol + location + g_path + g_scheme + g_options

def _getDocumentLocation(doc):
    ctx = uno.getComponentContext()
    url = uno.createUnoStruct('com.sun.star.util.URL')
    url.Complete = doc.URL
    dummy, url = ctx.ServiceManager.createInstanceWithContext('com.sun.star.util.URLTransformer', ctx).parseStrict(url)
    return url.Protocol + url.Path


g_exportedScripts = (setDataBaseConnection, )

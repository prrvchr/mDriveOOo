#!
# -*- coding: utf-8 -*-

# DataSource configuration
g_protocol = 'jdbc:hsqldb:'
g_path = 'hsqldb'
g_jar = 'hsqldb.jar'
g_class = 'org.hsqldb.jdbcDriver'
g_options = ';default_schema=true;hsqldb.default_table_type=cached;get_column_name=false;ifexists=false'
g_shutdown = ';shutdown=true'
g_csv = '%s.csv;fs=|;ignore_first=true;encoding=UTF-8;quoted=true'
g_version = '2.5.0'

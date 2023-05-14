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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from .configuration import g_member
from .configuration import g_errorlog

from .logger import getLogger
g_basename = 'dbqueries'


def getSqlQuery(ctx, name, format=None):

# Create Text Table Queries
    if name == 'createTableTables':
        c1 = '"Table" INTEGER NOT NULL PRIMARY KEY'
        c2 = '"Name" VARCHAR(100) NOT NULL'
        c3 = '"Identity" INTEGER DEFAULT NULL'
        c4 = '"View" BOOLEAN DEFAULT TRUE'
        c5 = '"Versioned" BOOLEAN DEFAULT FALSE'
        k1 = 'CONSTRAINT "UniqueTablesName" UNIQUE("Name")'
        c = (c1, c2, c3, c4, c5, k1)
        query = 'CREATE TEXT TABLE IF NOT EXISTS "Tables"(%s)' % ','.join(c)

    elif name == 'createTableColumns':
        c1 = '"Column" INTEGER NOT NULL PRIMARY KEY'
        c2 = '"Name" VARCHAR(100) NOT NULL'
        k1 = 'CONSTRAINT "UniqueColumnsName" UNIQUE("Name")'
        c = (c1, c2, k1)
        query = 'CREATE TEXT TABLE IF NOT EXISTS "Columns"(%s)' % ','.join(c)

    elif name == 'createTableTableColumn':
        c1 = '"Table" INTEGER NOT NULL'
        c2 = '"Column" INTEGER NOT NULL'
        c3 = '"Type" VARCHAR(100) NOT NULL'
        c4 = '"Default" VARCHAR(100) DEFAULT NULL'
        c5 = '"Options" VARCHAR(100) DEFAULT NULL'
        c6 = '"Primary" BOOLEAN NOT NULL'
        c7 = '"Unique" BOOLEAN NOT NULL'
        c8 = '"ForeignTable" INTEGER DEFAULT NULL'
        c9 = '"ForeignColumn" INTEGER DEFAULT NULL'
        k1 = 'PRIMARY KEY("Table","Column")'
        k2 = 'CONSTRAINT "ForeignTablesTable" FOREIGN KEY("Table") REFERENCES '
        k2 += '"Tables"("Table") ON DELETE CASCADE ON UPDATE CASCADE'
        k3 = 'CONSTRAINT "ForeignColumnsColumn" FOREIGN KEY("Column") REFERENCES '
        k3 += '"Columns"("Column") ON DELETE CASCADE ON UPDATE CASCADE'
        c = (c1, c2, c3, c4, c5, c6, c7, c8, c9, k1, k2, k3)
        query = 'CREATE TEXT TABLE IF NOT EXISTS "TableColumn"(%s)' % ','.join(c)

    elif name == 'createTableResources':
        c1 = '"Resource" INTEGER NOT NULL PRIMARY KEY'
        c2 = '"Path" VARCHAR(100) NOT NULL'
        c3 = '"Name" VARCHAR(100) DEFAULT NULL'
        c4 = '"View" VARCHAR(100) DEFAULT NULL'
        c5 = '"Method" SMALLINT DEFAULT NULL'
        c = (c1, c2, c3, c4, c5)
        query = 'CREATE TEXT TABLE IF NOT EXISTS "Resources"(%s)' % ','.join(c)

    elif name == 'createTableProperties':
        c1 = '"Property" INTEGER NOT NULL PRIMARY KEY'
        c2 = '"Resource" INTEGER NOT NULL'
        c3 = '"Path" VARCHAR(100) NOT NULL'
        c4 = '"Name" VARCHAR(100) DEFAULT NULL'
        k1 = 'CONSTRAINT "ForeignResourcesResource" FOREIGN KEY("Resource") REFERENCES '
        k1 += '"Resources"("Resource") ON DELETE CASCADE ON UPDATE CASCADE'
        c = (c1, c2, c3, c4, k1)
        query = 'CREATE TEXT TABLE IF NOT EXISTS "Properties"(%s)' % ','.join(c)

    elif name == 'createTableTypes':
        c1 = '"Type" INTEGER NOT NULL PRIMARY KEY'
        c2 = '"Path" VARCHAR(100) NOT NULL'
        c3 = '"Name" VARCHAR(100) DEFAULT NULL'
        c = (c1, c2, c3)
        query = 'CREATE TEXT TABLE IF NOT EXISTS "Types"(%s)' % ','.join(c)

    elif name == 'createTablePropertyType':
        c1 = '"Property" INTEGER NOT NULL'
        c2 = '"Type" INTEGER NOT NULL'
        k1 = 'CONSTRAINT "ForeignPropertiesProperty" FOREIGN KEY("Property") REFERENCES '
        k1 += '"Properties"("Property") ON DELETE CASCADE ON UPDATE CASCADE'
        k2 = 'CONSTRAINT "ForeignTypesType" FOREIGN KEY("Type") REFERENCES '
        k2 += '"Types"("Type") ON DELETE CASCADE ON UPDATE CASCADE'
        c = (c1, c2, k1, k2)
        query = 'CREATE TEXT TABLE IF NOT EXISTS "PropertyType"(%s)' % ','.join(c)

    elif name == 'setTableSource':
        query = 'SET TABLE "%s" SOURCE "%s"' % format

    elif name == 'setTableHeader':
        query = 'SET TABLE "%s" SOURCE HEADER "%s"' % format

    elif name == 'setTableReadOnly':
        query = 'SET TABLE "%s" READONLY TRUE' % format

# Create Cached Table Options
    elif name == 'getPrimayKey':
        query = 'PRIMARY KEY(%s)' % ','.join(format)

    elif name == 'getUniqueConstraint':
        query = 'CONSTRAINT "Unique%(Table)s%(Column)s" UNIQUE("%(Column)s")' % format

    elif name == 'getForeignConstraint':
        q = 'CONSTRAINT "Foreign%(Table)s%(Column)s" FOREIGN KEY("%(Column)s") REFERENCES '
        q += '"%(ForeignTable)s"("%(ForeignColumn)s") ON DELETE CASCADE ON UPDATE CASCADE'
        query = q % format

# Create Cached Table Queries
    elif name == 'createTable':
        query = 'CREATE CACHED TABLE IF NOT EXISTS "%s"(%s)' % format

    elif name == 'getPeriodColumns':
        query = '"RowStart" TIMESTAMP(6) WITH TIME ZONE GENERATED ALWAYS AS ROW START,'
        query += '"RowEnd" TIMESTAMP(6) WITH TIME ZONE GENERATED ALWAYS AS ROW END,'
        query += 'PERIOD FOR SYSTEM_TIME("RowStart","RowEnd")'

    elif name == 'getSystemVersioning':
        query = ' WITH SYSTEM VERSIONING'

# Create Dynamic View Queries
    elif name == 'getAddressBookView':
        query = '''\
CREATE VIEW "%(View)s" ("%(Columns)s") AS SELECT %(Select)s FROM "Card" %(Table)s
''' % format

    elif name == 'createCardColumnsView':
        query = 'CREATE VIEW "Book" (%(Columns)s) AS SELECT %(Select)s FROM %(Table)s' % format

    elif name == 'createView':
        query = 'CREATE VIEW "%s"(%s) AS SELECT %s FROM %s' % format

    elif name == 'getPrimaryColumnName':
        query = 'Resource'

    elif name == 'getBookmarkColumnName':
        query = 'Bookmark'

    elif name == 'getBookmarkColumn':
        query = 'ROW_NUMBER() OVER() AS "Bookmark"'

    elif name == 'getAddressBookTable':
        query = '''"Peoples"
JOIN "Connections" ON "Peoples"."People"="Connections"."People"
JOIN "Groups" ON "Connections"."Group"="Groups"."Group" AND "Groups"."GroupSync"=FALSE
JOIN "Peoples" AS P ON "Groups"."People"=P."People"
'''

    elif name == 'getAddressBookPredicate':
        query = '''WHERE P."Account"=CURRENT_USER OR CURRENT_USER='SA' ORDER BY "Peoples"."People"'''

    elif name == 'createBookView':
        view = '''\
CREATE VIEW IF NOT EXISTS "%(Name)s" AS
  SELECT "%(ViewName)s".*, "%(UserTable)s"."%(UserColumn)s" FROM "%(ViewName)s" 
  JOIN "%(CardTable)s" ON "%(ViewName)s"."%(CardColumn)s"="%(CardTable)s"."%(CardColumn)s" 
  JOIN "%(BookCardTable)s" ON "%(CardTable)s"."%(CardColumn)s"="%(BookCardTable)s"."%(CardColumn)s" 
  JOIN "%(BookTable)s" ON "%(BookCardTable)s"."%(BookColumn)s"="%(BookTable)s"."%(BookColumn)s" 
  JOIN "%(UserTable)s" ON "%(BookTable)s"."%(UserColumn)s"="%(UserTable)s"."%(UserColumn)s";
'''
        query = view % format

    elif name == 'createUserBook':
        synonym = '''\
CREATE VIEW IF NOT EXISTS "%(Schema)s"."%(Name)s" AS
  SELECT %(Public)s."%(View)s".* FROM %(Public)s."%(View)s" 
  WHERE %(Public)s."%(View)s"."%(UserColumn)s" = "%(UserId)s";
'''

        query = synonym % format

    elif name == 'createAddressbookView':
        view = '''\
CREATE VIEW IF NOT EXISTS "%(Schema)s"."%(Name)s" AS
  SELECT %(Public)s."%(View)s".* FROM %(Public)s."%(View)s"
  JOIN %(Public)s."Cards" ON %(Public)s."%(View)s"."Card"=%(Public)s."Cards"."Card"
  JOIN %(Public)s."BookCards" ON %(Public)s."Cards"."Card"=%(Public)s."BookCards"."Card"
  JOIN %(Public)s."Books" ON %(Public)s."BookCards"."Book"=%(Public)s."Books"."Book"
  WHERE %(Public)s."Books"."Book"=%(Book)s
  ORDER BY %(Public)s."%(View)s"."Created";
GRANT SELECT ON "%(Schema)s"."%(Name)s" TO "%(User)s";
'''
        query = view % format

    elif name == 'createGroupView':
        view = '''\
CREATE VIEW IF NOT EXISTS "%(Schema)s"."%(Name)s" AS
  SELECT %(Public)s."%(View)s".* FROM %(Public)s."%(View)s"
  JOIN %(Public)s."GroupCards" ON %(Public)s."%(View)s"."Card"=%(Public)s."GroupCards"."Card"
  JOIN %(Public)s."Groups" ON %(Public)s."GroupCards"."Group"=%(Public)s."Groups"."Group"
  WHERE %(Public)s."Groups"."Group"=%(Group)s
  ORDER BY %(Public)s."%(View)s"."Created";
GRANT SELECT ON "%(Schema)s"."%(Name)s" TO "%(User)s";
'''
        query = view % format

    elif name == 'deleteView':
        query = 'DROP VIEW IF EXISTS "%(Schema)s"."%(OldName)s";' % format

# Create User and Schema Query
    elif name == 'createUser':
        q = """CREATE USER "%(User)s" PASSWORD '%(Password)s'"""
        q += ' ADMIN;' if format.get('Admin', False) else ';'
        query = q % format

    elif name == 'createUserSchema':
        query = 'CREATE SCHEMA "%(Schema)s" AUTHORIZATION "%(User)s";' % format

    elif name == 'setUserSchema':
        query = 'ALTER USER "%(User)s" SET INITIAL SCHEMA "%(Schema)s";' % format

    elif name == 'setUserPassword':
        query = """ALTER USER "%(User)s" SET PASSWORD '%(Password)s'""" % format

# Get last IDENTITY value that was inserted into a table by the current session
    elif name == 'getIdentity':
        query = 'CALL IDENTITY();'

# Get Users and Privileges Query
    elif name == 'getUsers':
        query = 'SELECT * FROM INFORMATION_SCHEMA.SYSTEM_USERS'
    elif name == 'getPrivileges':
        query = 'SELECT * FROM INFORMATION_SCHEMA.TABLE_PRIVILEGES'
    elif name == 'changePassword':
        query = "SET PASSWORD '%s'" % format

# Select Queries
    # DataBase creation Select Queries
    elif name == 'getTableNames':
        query = 'SELECT "Name" FROM "Tables" ORDER BY "Table";'

    elif name == 'getTables':
        s1 = '"T"."Table" AS "TableId"'
        s2 = '"C"."Column" AS "ColumnId"'
        s3 = '"T"."Name" AS "Table"'
        s4 = '"C"."Name" AS "Column"'
        s5 = '"TC"."Type"'
        s6 = '"TC"."Default"'
        s7 = '"TC"."Options"'
        s8 = '"TC"."Primary"'
        s9 = '"TC"."Unique"'
        s10 = '"TC"."ForeignTable" AS "ForeignTableId"'
        s11 = '"TC"."ForeignColumn" AS "ForeignColumnId"'
        s12 = '"T2"."Name" AS "ForeignTable"'
        s13 = '"C2"."Name" AS "ForeignColumn"'
        s14 = '"T"."View"'
        s15 = '"T"."Versioned"'
        s = (s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14,s15)
        f1 = '"Tables" AS "T"'
        f2 = 'JOIN "TableColumn" AS "TC" ON "T"."Table" = "TC"."Table"'
        f3 = 'JOIN "Columns" AS "C" ON "TC"."Column" = "C"."Column"'
        f4 = 'LEFT JOIN "Tables" AS "T2" ON "TC"."ForeignTable" = "T2"."Table"'
        f5 = 'LEFT JOIN "Columns" AS "C2" ON "TC"."ForeignColumn" = "C2"."Column"'
        w = '"T"."Name" = ?'
        f = (f1, f2, f3, f4, f5)
        p = (', '.join(s), ' '.join(f), w)
        query = 'SELECT %s FROM %s WHERE %s' % p


    elif name == 'getViewNames':
        query = 'SELECT "Name" FROM "Tables" WHERE "View"=TRUE ORDER BY "Table"'

    elif name == 'getViews':
        s1 = '"T1"."Table" AS "TableId"'
        s2 = '"TL"."Label" AS "LabelId"'
        s3 = '"TT"."Type" AS "TypeId"'
        s4 = '"T1"."Name" AS "Table"'
        s5 = '"L"."Name" AS "Label"'
        s6 = '"T"."Name" AS "Type"'
        s7 = 'CONCAT(COALESCE("T"."Name",\'\'),COALESCE("TL"."View","L"."Name")) AS "View"'
        s8 = '"T2"."Name" AS "PrimaryTable"'
        s9 = '"C"."Name" AS "PrimaryColumn"'
        s = (s1,s2,s3,s4,s5,s6,s7,s8,s9)
        f1 = '"Tables" AS "T1", "Tables" AS "T2"'
        f2 = 'JOIN "TableLabel" AS "TL" ON "T1"."Table"="TL"."Table"'
        f3 = 'JOIN "Labels" AS "L" ON "TL"."Label"="L"."Label"'
        f4 = 'LEFT JOIN "TableType" AS "TT" ON "T1"."Table"="TT"."Table"'
        f5 = 'LEFT JOIN "Types" AS "T" ON "TT"."Type"="T"."Type"'
        f6 = 'JOIN "Columns" AS "C" ON "T2"."Identity"="C"."Column"'
        w = '"T2"."Identity"=1 AND "T1"."Name"=? '
        f = (f1, f2, f3, f4, f5, f6)
        p = (','.join(s), ' '.join(f), w)
        query = 'SELECT %s FROM %s WHERE %s ORDER BY "TableId","LabelId","TypeId"' % p

    elif name == 'getFieldNames':
        query = '''\
SELECT F."Name" FROM "Fields" AS F 
  JOIN "Tables" AS T ON F."Column"=T."Table" AND F."Table"='Tables' 
  WHERE T."View"=TRUE 
UNION 
SELECT "Name" FROM "Fields" WHERE "Table"='Loop' AND "Column"=1;'''

    elif name == 'getDefaultType':
        s1 = '"Tables"."Name" AS "Table"'
        s2 = '"Types"."Name" AS "Type"'
        s = (s1, s2)
        f1 = '"Tables"'
        f2 = 'JOIN "TableType" ON "Tables"."Table"="TableType"."Table"'
        f3 = 'JOIN "Types" ON "TableType"."Type"="Types"."Type"'
        w = '"TableType"."Default"=TRUE'
        f = (f1, f2 , f3 )
        p = (','.join(s), ' '.join(f), w)
        query = 'SELECT %s FROM %s WHERE %s' % p

    elif name == 'getFieldsMap':
        s1 = '"F"."Name" AS "Value"'
        s2 = 'COALESCE("Tables"."Name","Columns"."Name","Labels"."Name","Fields"."Name") AS "Name"'
        s3 = '"F"."Type"'
        s4 = '"F"."Table"'
        s = (s1, s2, s3, s4)
        f1 = '"Fields" AS "F"'
        f2 = 'LEFT JOIN "Tables" ON "F"."Table"=%s AND "F"."Column"="Tables"."Table"'
        f3 = 'LEFT JOIN "Columns" ON "F"."Table"=%s AND "F"."Column"="Columns"."Column"'
        f4 = 'LEFT JOIN "Labels" ON "F"."Table"=%s AND "F"."Column"="Labels"."Label"'
        f5 = 'LEFT JOIN "Fields" ON "F"."Table"=%s AND "F"."Field"="Fields"."Field"'
        f = (f1, f2 % "'Tables'", f3 % "'Columns'", f4 % "'Labels'", f5 % "'Loop'")
        p = (','.join(s), ' '.join(f))
        query = 'SELECT %s FROM %s WHERE "F"."Method"=? ORDER BY "F"."Field"' % p

    elif name == 'getPrimaryTable':
        s = 'COALESCE("Tables"."Name","Columns"."Name","Labels"."Name","Fields"."Name") AS "Name"'
        f1 = '"Fields" AS "F"'
        f2 = 'LEFT JOIN "Tables" ON "F"."Table"=%s AND "F"."Column"="Tables"."Table"'
        f3 = 'LEFT JOIN "Columns" ON "F"."Table"=%s AND "F"."Column"="Columns"."Column"'
        f4 = 'LEFT JOIN "Labels" ON "F"."Table"=%s AND "F"."Column"="Labels"."Label"'
        f5 = 'LEFT JOIN "Fields" ON "F"."Table"=%s AND "F"."Field"="Fields"."Field"'
        f = (f1, f2 % "'Tables'", f3 % "'Columns'", f4 % "'Labels'", f5 % "'Loop'")
        w = '"F"."Type"=%s AND "F"."Table"=%s' % ("'Primary'","'Tables'")
        p = (s, ' '.join(f), w)
        query = 'SELECT %s FROM %s WHERE %s' % p


    elif name == 'getUpdatedGroup':
        query = 'SELECT "Resource" FROM "Groups" FOR SYSTEM_TIME AS OF CURRENT_TIMESTAMP - 1 YEAR'

# Update Queries
    elif name == 'updateAddressbookToken':
        query = 'UPDATE "Books" SET "Token"=?,"Modified"=DEFAULT WHERE "Book"=?'

    elif name == 'updateUser1':
        query = 'UPDATE "Users" SET "Scheme"=?,"Password"=? WHERE "User"=?'

    elif name == 'updateUserScheme':
        query = 'UPDATE "Users" SET "Scheme"=? WHERE "User"=?'

    elif name == 'updateUserPassword':
        query = 'UPDATE "Users" SET "Password"=? WHERE "User"=?'


    elif name == 'updatePeoples':
        query = 'UPDATE "Peoples" SET "TimeStamp"=? WHERE "Resource"=?'

    elif name == 'updatePeopleSync':
        query = 'UPDATE "Peoples" SET "PeopleSync"=?,"TimeStamp"=? WHERE "People"=?'

    elif name == 'updateGroupSync':
        query = 'UPDATE "Peoples" SET "GroupSync"=?,"TimeStamp"=? WHERE "People"=?'

# Get DataBase Version Query
    elif name == 'getVersion':
        query = 'Select DISTINCT DATABASE_VERSION() as "HSQL Version" From INFORMATION_SCHEMA.SYSTEM_TABLES'

# Create Trigger Query
    elif name == 'createTriggerGroupInsert':
        query = """\
CREATE TRIGGER "GroupInsert" AFTER INSERT ON "Groups"
  REFERENCING NEW ROW AS "NewRow"
  FOR EACH ROW
  BEGIN ATOMIC
    CALL "GroupView" ("NewRow"."Name", "NewRow"."Group")
  END"""

    elif name == 'selectUpdatedGroup':
        c1 = '?||"Resource" AS "Resource"'
        c2 = '"Group"'
        c3 = '"Name"'
        q = '\
SELECT %s FROM "Groups" WHERE "GroupSync"=FALSE AND "People"=? AND "Resource"<>?'
        query = q % ','.join((c1, c2, c3))

    elif name == 'truncatGroup':
        q = """\
TRUNCATE TABLE "Groups" VERSIONING TO TIMESTAMP'%(TimeStamp)s'"""
        query = q % format

# Insert Queries
    elif name == 'insertSuperUser':
        q = """\
INSERT INTO "Users" ("Uri","Scheme","Server","Path","Name") VALUES ('%s','%s','%s','%s','%s');
"""
        query = q % format

    elif name == 'insertSuperAdressbook':
        query = """\
INSERT INTO "Books" ("User","Uri","Name","Tag","Token") VALUES (0,'/','admin','#','#');
"""

    elif name == 'insertSuperGroup':
        query = """\
INSERT INTO "Groups" ("Book","Uri","Name") VALUES (0,'/','#');
"""

# Create Procedure Query
    elif name == 'createSelectGroup':
        query = """\
CREATE PROCEDURE "SelectGroup"(IN "Prefix" VARCHAR(50),
                               IN "PeopleId" INTEGER,
                               IN "ResourceName" VARCHAR(100))
  SPECIFIC "SelectGroup_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE "StartTime","EndTime","Format" VARCHAR(30);
    DECLARE "TmpTime" TIMESTAMP(6);
    DECLARE "Result" CURSOR WITH RETURN FOR
      SELECT "Prefix"||"Resource" FROM "Groups" FOR SYSTEM_TIME FROM 
      TO_TIMESTAMP('%(Start)s','%(Format)s') TO TO_TIMESTAMP('%(End)s','%(Format)s')
      WHERE "People"="PeopleId" AND "Resource"<>"ResourceName" FOR READ ONLY;
    SET "Time" = LOCALTIMESTAMP(6);
    SET "TmpTime" = "Time" - 10 MINUTE;
    SET "Format" = 'YYYY-MM-DDTHH24:MI:SS.FFFZ';
    SET "EndTime" = TO_CHAR("Time","Format");
    SET "StartTime" = TO_CHAR("TmpTime","Format");
    SET "Time" = "EndTime";
    OPEN "Result";
  END"""

    elif name == 'createSelectUser':
        query = """\
CREATE PROCEDURE "SelectUser"(IN SERVER VARCHAR(128),
                              IN NAME VARCHAR(128))
  SPECIFIC "SelectUser_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE RSLT CURSOR WITH RETURN FOR
      SELECT U."User",U."Uri",U."Scheme",U."Server",U."Path",U."Name",
        ARRAY_AGG(A."Book" ORDER BY A."Book") AS "Aids",
        ARRAY_AGG(A."Uri" ORDER BY A."Book") AS "Uris",
        ARRAY_AGG(A."Name" ORDER BY A."Book") AS "Names",
        ARRAY_AGG(A."Tag" ORDER BY A."Book") AS "Tags",
        ARRAY_AGG(A."Token" ORDER BY A."Book") AS "Tokens"
      FROM "Users" AS U
      LEFT JOIN "Books" AS A ON U."User"=A."User"
      WHERE U."Server"=SERVER AND U."Name"=NAME
      GROUP BY U."User",U."Uri",U."Scheme",U."Server",U."Path",U."Name"
    FOR READ ONLY;
    OPEN RSLT;
  END"""

    elif name == 'createInsertUser':
        query = """\
CREATE PROCEDURE "InsertUser"(IN URI VARCHAR(256),
                              IN SCHEME VARCHAR(128),
                              IN SERVER VARCHAR(128),
                              IN PATH VARCHAR(128),
                              IN NAME VARCHAR(128),
                              IN ADDRESSBOOK VARCHAR(128))
  SPECIFIC "InsertUser_1"
  MODIFIES SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE PK1 INTEGER DEFAULT NULL;
    DECLARE RSLT CURSOR WITH RETURN FOR
      SELECT U."User",U."Uri",U."Scheme",U."Server",U."Path",U."Name",
        ARRAY_AGG(A."Book" ORDER BY A."Book") AS "Aids",
        ARRAY_AGG(A."Uri" ORDER BY A."Book") AS "Uris",
        ARRAY_AGG(A."Name" ORDER BY A."Book") AS "Names",
        ARRAY_AGG(A."Tag" ORDER BY A."Book") AS "Tags",
        ARRAY_AGG(A."Token" ORDER BY A."Book") AS "Tokens"
      FROM "Users" AS U
      LEFT JOIN "Books" AS A ON U."User"=A."User"
      WHERE U."Server"=SERVER AND U."Name"=NAME
      GROUP BY U."User",U."Uri",U."Scheme",U."Server",U."Path",U."Name"
    FOR READ ONLY;
    INSERT INTO "Users" ("Uri","Scheme","Server","Path","Name") VALUES (URI,SCHEME,SERVER,PATH,NAME);
    IF ADDRESSBOOK IS NOT NULL THEN
      INSERT INTO "Books" ("User","Uri","Name","Tag") VALUES (IDENTITY(),'/',ADDRESSBOOK,'#');
    END IF;
    OPEN RSLT;
  END"""

    elif name == 'createSelectAddressbook':
        query = """\
CREATE PROCEDURE "SelectAddressbook"(IN UID INTEGER,
                                     IN AID INTEGER,
                                     IN NAME VARCHAR(128))
  SPECIFIC "SelectAddressbook_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE RSLT CURSOR WITH RETURN FOR
      SELECT A."Book", A."Uri" AS "Path", A."Name",A."Tag",
      A."Token" AS "AdrSync",
      A."Created"=A."Modified" AS "New"
      FROM "Users" AS U
      JOIN "Books" AS A ON U."User"=A."User"
      WHERE U."User"=UID AND (A."Book"=AID OR
        (((NAME IS NULL AND A."Book"=U."Default") OR
        (NAME IS NOT NULL AND A."Name"=NAME))))
      FOR READ ONLY;
    OPEN RSLT;
  END"""

    elif name == 'createInsertBook':
        query = """\
CREATE PROCEDURE "InsertBook"(IN UID INTEGER,
                              IN URI VARCHAR(256),
                              IN NAME VARCHAR(128),
                              IN TAG VARCHAR(128),
                              IN TOKEN VARCHAR(128),
                              OUT AID INTEGER)
  SPECIFIC "InsertBook_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    INSERT INTO "Books" ("User","Uri","Name","Tag","Token") VALUES (UID,URI,NAME,TAG,TOKEN);
    SET AID = IDENTITY();
  END"""

    elif name == 'createUpdateAddressbookName':
        query = """\
CREATE PROCEDURE "UpdateAddressbookName"(IN AID INTEGER,
                                         IN NAME VARCHAR(128))
  SPECIFIC "UpdateAddressbookName_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    UPDATE "Books" SET "Name"=NAME WHERE "Book"=AID;
  END"""

    elif name == 'createMergeCardData':
        query = """\
CREATE PROCEDURE "MergeCardData"(IN Labels VARCHAR(60) ARRAY,
                                 IN DateTime TIMESTAMP(6),
                                 IN Card INTEGER,
                                 IN Prefix VARCHAR(20),
                                 IN Label VARCHAR(20),
                                 IN Suffixes VARCHAR(20) ARRAY,
                                 IN Data VARCHAR(128))
  SPECIFIC "MergeCardData_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE Index INTEGER DEFAULT 1;
    DECLARE ColumnId INTEGER DEFAULT 0;
    DECLARE Suffix VARCHAR(20) DEFAULT '';
    WHILE Index <= CARDINALITY(Suffixes) DO 
      SET Suffix = Suffix || Suffixes[Index];
      SET Index = Index + 1;
    END WHILE;
    SET ColumnId = POSITION_ARRAY(Prefix || Label || Suffix IN Labels);
    IF ColumnId > 0 THEN
      MERGE INTO "CardValues" USING (VALUES(Card,ColumnId,Data,DateTime)) 
        AS vals(w,x,y,z) ON "CardValues"."Card"=vals.w AND "CardValues"."Column"=vals.x
          WHEN MATCHED THEN UPDATE SET "Value"=vals.y, "Modified"=vals.z 
          WHEN NOT MATCHED THEN INSERT ("Card","Column","Value","Created","Modified")
             VALUES vals.w,vals.x,vals.y,vals.z,vals.z;
    END IF;
  END"""

    elif name == 'createMergeCard':
        query = """\
CREATE PROCEDURE "MergeCard"(IN Book INTEGER,
                             IN Uri VARCHAR(256),
                             IN Tag VARCHAR(128),
                             IN Deleted BOOLEAN,
                             IN Data VARCHAR(10000))
  SPECIFIC "MergeCard_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE Card INTEGER DEFAULT NULL;
    IF Deleted THEN
      DELETE FROM "Cards" WHERE "Uri"=Uri;
    ELSE
      MERGE INTO "Cards" USING (VALUES(Uri,Tag,Data))
        AS vals(x,y,z) ON "Cards"."Uri"=vals.x
          WHEN MATCHED THEN UPDATE SET "Tag"=vals.y,"Data"=vals.z
          WHEN NOT MATCHED THEN INSERT ("Uri","Tag","Data")
            VALUES vals.x,vals.y,vals.z;
      SELECT "Card" INTO Card FROM "Cards" WHERE "Uri"=Uri;
      IF Card IS NOT NULL THEN
        MERGE INTO "BookCards" USING (VALUES(Book,Card))
          AS vals(y,z) ON "Book"=vals.y AND "Card"=vals.z
            WHEN NOT MATCHED THEN INSERT ("Book","Card")
              VALUES vals.y,vals.z;
      END IF;
    END IF;
  END"""

    elif name == 'createDeleteCard':
        query = """\
CREATE PROCEDURE "DeleteCard"(IN URIS VARCHAR(256) ARRAY)
  SPECIFIC "DeleteCard_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DELETE FROM "Cards" WHERE "Uri" IN (UNNEST(URIS));
  END"""

    elif name == 'createGetLastAddressbookSync':
        query = """\
CREATE PROCEDURE "GetLastAddressbookSync"(OUT FIRST TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "GetLastAddressbookSync_1"
  READS SQL DATA
  BEGIN ATOMIC
    DECLARE TMP TIMESTAMP(6) WITH TIME ZONE;
    SELECT "Created" INTO TMP FROM "Books" WHERE "Book"=0;
    SET FIRST = TMP;
  END"""

    elif name == 'createSelectChangedAddressbooks':
        query = """\
CREATE PROCEDURE "SelectChangedAddressbooks"(IN UID INTEGER,
                                             IN FIRST TIMESTAMP(6) WITH TIME ZONE,
                                             IN LAST TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "SelectChangedAddressbooks_1"
  MODIFIES SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE RSLT CURSOR WITH RETURN FOR
      (SELECT CAST(U."User" AS VARCHAR(9)) AS "User", 
              A1."Book", NULL AS "Name", A1."Name" AS "OldName", 
              'Deleted' AS "Query", A1."RowEnd" AS "Order"
      FROM "Books" FOR SYSTEM_TIME AS OF FIRST AS A1
      JOIN "Users" AS U ON A1."User"=U."User"
      LEFT JOIN "Books" FOR SYSTEM_TIME AS OF LAST AS A2
        ON A1."Book" = A2."Book"
      WHERE A1."Book"!=0 AND A2."Book" IS NULL AND U."User"=UID)
      UNION
      (SELECT CAST(U."User" AS VARCHAR(9)) AS "User", 
              A2."Book", A2."Name", NULL AS "OldName", 
              'Inserted' AS "Query", A2."RowStart" AS "Order"
      FROM "Books" FOR SYSTEM_TIME AS OF LAST AS A2
      JOIN "Users" AS U ON A2."User"=U."User"
      LEFT JOIN "Books" FOR SYSTEM_TIME AS OF FIRST AS A1
        ON A2."Book"=A1."Book"
      WHERE A2."Book"!=0 AND  A1."Book" IS NULL AND U."User"=UID)
      UNION
      (SELECT CAST(U."User" AS VARCHAR(9)) AS "User", 
              A2."Book", A2."Name", A1."Name" AS "OldName", 
              'Updated' AS "Query", A1."RowEnd" AS "Order"
      FROM "Books" FOR SYSTEM_TIME AS OF LAST AS A2
      JOIN "Users" AS U ON A2."User"=U."User"
      INNER JOIN "Books" FOR SYSTEM_TIME FROM FIRST TO LAST AS A1
        ON A2."Book"=A1."Book" AND A2."RowStart"=A1."RowEnd"
      WHERE A2."Book"!=0 AND U."User"=UID)
      ORDER BY "Order"
      FOR READ ONLY;
    OPEN RSLT;
  END"""

    elif name == 'createUpdateAddressbook':
        query = """\
CREATE PROCEDURE "UpdateAddressbook"(IN LAST TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "UpdateAddressbook_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    UPDATE "Books" SET "Created"=LAST WHERE "Book"=0;
  END"""

    elif name == 'createGetLastGroupSync':
        query = """\
CREATE PROCEDURE "GetLastGroupSync"(OUT FIRST TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "GetLastGroupSync_1"
  READS SQL DATA
  BEGIN ATOMIC
    DECLARE TMP TIMESTAMP(6) WITH TIME ZONE;
    SELECT "Created" INTO TMP FROM "Groups" WHERE "Group"=0;
    SET FIRST = TMP;
  END"""

    elif name == 'createSelectChangedGroups':
        query = """\
CREATE PROCEDURE "SelectChangedGroups"(IN FIRST TIMESTAMP(6) WITH TIME ZONE,
                                       IN LAST TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "SelectChangedGroups_1"
  MODIFIES SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE RSLT CURSOR WITH RETURN FOR
      (SELECT CAST(U."User" AS VARCHAR(9)) AS "User", 
              REPLACE(U."Name",'.','-') AS "Schema", 
              G1."Group", NULL AS "Name", G1."Name" AS "OldName", 
              'Deleted' AS "Query", G1."RowEnd" AS "Order"
      FROM "Groups" FOR SYSTEM_TIME AS OF FIRST AS G1
      JOIN "Books" AS A ON G1."Book"=A."Book"
      JOIN "Users" AS U ON A."User"=U."User"
      LEFT JOIN "Groups" FOR SYSTEM_TIME AS OF LAST AS G2
        ON G1."Group" = G2."Group"
      WHERE G1."Group"!=0 AND G2."Group" IS NULL)
      UNION
      (SELECT CAST(U."User" AS VARCHAR(9)) AS "User", 
              REPLACE(U."Name",'.','-') AS "Schema", 
              G2."Group", G2."Name", NULL AS "OldName", 
              'Inserted' AS "Query", G2."RowStart" AS "Order"
      FROM "Groups" FOR SYSTEM_TIME AS OF LAST AS G2
      JOIN "Books" AS A ON G2."Book"=A."Book"
      JOIN "Users" AS U ON A."User"=U."User"
      LEFT JOIN "Groups" FOR SYSTEM_TIME AS OF FIRST AS G1
        ON G2."Group"=G1."Group"
      WHERE G2."Group"!=0 AND  G1."Group" IS NULL)
      UNION
      (SELECT CAST(U."User" AS VARCHAR(9)) AS "User", 
              REPLACE(U."Name",'.','-') AS "Schema", 
              G2."Group", G2."Name", G1."Name" AS "OldName", 
              'Updated' AS "Query", G1."RowEnd" AS "Order"
      FROM "Groups" FOR SYSTEM_TIME AS OF LAST AS G2
      JOIN "Books" AS A ON G2."Book"=A."Book"
      JOIN "Users" AS U ON A."User"=U."User"
      INNER JOIN "Groups" FOR SYSTEM_TIME FROM FIRST TO LAST AS G1
        ON G2."Group"=G1."Group" AND G2."RowStart"=G1."RowEnd"
      WHERE G2."Group"!=0)
      ORDER BY "Order"
      FOR READ ONLY;
    OPEN RSLT;
  END"""

    elif name == 'createUpdateGroup':
        query = """\
CREATE PROCEDURE "UpdateGroup"(IN LAST TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "UpdateGroup_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    UPDATE "Groups" SET "Created"=LAST WHERE "Group"=0;
  END"""

    elif name == 'createGetLastUserSync':
        query = """\
CREATE PROCEDURE "GetLastUserSync"(OUT FIRST TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "GetLastUserSync_1"
  READS SQL DATA
  BEGIN ATOMIC
    DECLARE TMP TIMESTAMP(6) WITH TIME ZONE;
    SELECT "Created" INTO TMP FROM "Users" WHERE "User"=0;
    SET FIRST = TMP;
  END"""

    elif name == 'createSelectChangedCards':
        query = """\
CREATE PROCEDURE "SelectChangedCards"(IN FIRST TIMESTAMP(6) WITH TIME ZONE,
                                      IN LAST TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "SelectChangedCards_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE RSLT CURSOR WITH RETURN FOR
      (SELECT U."User",C1."Card",'Deleted' AS "Query",NULL AS "Data",C1."RowEnd" AS "Order"
      FROM "Cards" FOR SYSTEM_TIME AS OF FIRST AS C1
      JOIN "BookCards" AS BC ON C1."Card"=BC."Card"
      JOIN "Books" AS B ON BC."Book"=B."Book"
      JOIN "Users" AS U ON B."User"=U."User"
      LEFT JOIN "Cards" FOR SYSTEM_TIME AS OF LAST AS C2
        ON C1."Card" = C2."Card"
      WHERE C2."Card" IS NULL)
      UNION
      (SELECT U."User",C2."Card",'Inserted' AS "Query",C2."Data",C2."RowStart" AS "Order"
      FROM "Cards" FOR SYSTEM_TIME AS OF LAST AS C2
      JOIN "BookCards" AS BC ON C2."Card"=BC."Card"
      JOIN "Books" AS B ON BC."Book"=B."Book"
      JOIN "Users" AS U ON B."User"=U."User"
      LEFT JOIN "Cards" FOR SYSTEM_TIME AS OF FIRST AS C1
        ON C2."Card"=C1."Card"
      WHERE C1."Card" IS NULL)
      UNION
      (SELECT U."User",C2."Card",'Updated' AS "Query",C2."Data",C1."RowEnd" AS "Order"
      FROM "Cards" FOR SYSTEM_TIME AS OF LAST AS C2
      JOIN "BookCards" AS BC ON C2."Card"=BC."Card"
      JOIN "Books" AS B ON BC."Book"=B."Book"
      JOIN "Users" AS U ON B."User"=U."User"
      INNER JOIN "Cards" FOR SYSTEM_TIME FROM FIRST TO LAST AS C1
        ON C2."Card"=C1."Card" AND C2."RowStart"=C1."RowEnd")
      ORDER BY "Order"
      FOR READ ONLY;
    OPEN RSLT;
  END"""

    elif name == 'createUpdateUser':
        query = """\
CREATE PROCEDURE "UpdateUser"(IN LAST TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "UpdateUser_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    UPDATE "Users" SET "Created"=LAST WHERE "User"=0;
  END"""

    elif name == 'createSelectCardProperties':
        query = """\
CREATE PROCEDURE "SelectCardProperties"()
  SPECIFIC "SelectCardProperties_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE RSLT CURSOR WITH RETURN FOR
      SELECT
        R."Name" AS "PropertyName", 
        R."Path" AS "PropertyGetter", 
        R."View" IS NULL AS "IsGroup", 
        PT."Property" IS NOT NULL AS "IsTyped",
        ARRAY_AGG(DISTINCT JSON_OBJECT(P."Path": P."Name"))
      FROM "Resources" AS R 
      INNER JOIN "Properties" AS P ON R."Resource"=P."Resource" 
      LEFT JOIN "PropertyType" AS PT ON P."Property"=PT."Property" 
      GROUP BY R."Name", R."Path", "IsGroup", "IsTyped" 
      FOR READ ONLY;
    OPEN RSLT;
  END"""

    # The getColumnIds query allows to obtain all the columns available from parser properties.
    elif name == 'createSelectColumnIds':
        query = """\
CREATE PROCEDURE "SelectColumnIds"()
  SPECIFIC "SelectColumnIds_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE Rslt CURSOR WITH RETURN FOR 
      SELECT ARRAY_AGG(R."Name" || P."Path" || COALESCE(T."Path",'') 
                       ORDER BY R."Resource", P."Property", T."Type")
      FROM "Resources" AS R 
      INNER JOIN "Properties" AS P ON R."Resource"=P."Resource" 
      LEFT JOIN "PropertyType" AS PT ON P."Property"=PT."Property" 
      LEFT JOIN "Types" AS T ON PT."Type"=T."Type" 
      WHERE P."Name" IS NOT NULL 
      FOR READ ONLY;
    OPEN Rslt;
  END"""

    # The getColumns query allows to obtain all the columns available from parser properties.
    elif name == 'createSelectColumns':
        query = """\
CREATE PROCEDURE "SelectColumns"()
  SPECIFIC "SelectColumns_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE Rslt CURSOR WITH RETURN FOR 
      SELECT ROWNUM() AS "ColumnId", 
        COALESCE(T."Name",'') || P."Name" AS "ColumnName", 
        R."View" AS "ViewName" 
      FROM "Resources" AS R 
      INNER JOIN "Properties" AS P ON R."Resource"=P."Resource" 
      LEFT JOIN "PropertyType" AS PT ON P."Property"=PT."Property" 
      LEFT JOIN "Types" AS T ON PT."Type"=T."Type" 
      WHERE P."Name" IS NOT NULL 
      ORDER BY R."Resource", P."Property", T."Type" 
      FOR READ ONLY;
    OPEN Rslt;
  END"""

    # The getPaths query allows to obtain all the JSON paths of the simple properties (untyped)
    elif name == 'createSelectPaths':
        query = """\
CREATE PROCEDURE "SelectPaths"()
  SPECIFIC "SelectPaths_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE Rslt CURSOR WITH RETURN FOR 
      SELECT R."Path", R."Name", P."Path", P."Name" 
      FROM "Resources" AS R 
      INNER JOIN "Properties" AS P ON R."Resource"=P."Resource" 
      LEFT JOIN "PropertyType" AS PT ON P."Property"=PT."Property" 
      WHERE PT."Property" IS NULL AND P."Name" IS NOT NULL 
      FOR READ ONLY;
    OPEN Rslt;
  END"""

    # The getLits query allows to obtain all the JSON paths of the simple list properties (untyped)
    elif name == 'createSelectLists':
        query = """\
CREATE PROCEDURE "SelectLists"()
  SPECIFIC "SelectLists_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE Rslt CURSOR WITH RETURN FOR 
      SELECT R."Path", R."Name", R."Name" 
      FROM "Resources" AS R
      WHERE R."View" IS NULL 
      FOR READ ONLY;
    OPEN Rslt;
  END"""

    # The getMaps query allows to start and stop buffers (tmp var) when parsing typed properties
    elif name == 'createSelectMaps':
        query = """\
CREATE PROCEDURE "SelectMaps"()
  SPECIFIC "SelectMaps_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE Rslt CURSOR WITH RETURN FOR 
      SELECT R."Path", R."Name", 
        ARRAY_AGG(DISTINCT P."Path") 
      FROM "Resources" AS R 
      INNER JOIN "Properties" AS P ON R."Resource"=P."Resource" 
      INNER JOIN "PropertyType" AS PT ON P."Property"=PT."Property" 
      GROUP BY R."Path", R."Name"
      FOR READ ONLY;
    OPEN Rslt;
  END"""

    # The getTypes query allows to obtain the right label (column) for typed properties
    elif name == 'createSelectTypes':
        query = """\
CREATE PROCEDURE "SelectTypes"()
  SPECIFIC "SelectTypes_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE Rslt CURSOR WITH RETURN FOR 
      SELECT R."Path", R."Name", P."Path", 
      ARRAY_AGG(JSON_OBJECT(T."Path" || P2."Path": COALESCE(T."Name", '') || P2."Name")) 
      FROM "Resources" AS R 
      INNER JOIN "Properties" AS P ON R."Resource"=P."Resource" 
      INNER JOIN "Resources" AS R2 ON R."Resource"=R2."Resource" 
      INNER JOIN "Properties" AS P2 ON R2."Resource"=P2."Resource" 
      INNER JOIN "PropertyType" AS PT ON P2."Property"=PT."Property" 
      INNER JOIN "Types" AS T ON PT."Type"=T."Type" 
      WHERE P."Name" IS NULL AND P2."Name" IS NOT NULL 
      GROUP BY R."Path", R."Name", P."Path" 
      FOR READ ONLY;
    OPEN Rslt;
  END"""

    # The getTmps query allows to get the path for the typed properties
    elif name == 'createSelectTmps':
        query = """\
CREATE PROCEDURE "SelectTmps"()
  SPECIFIC "SelectTmps_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE Rslt CURSOR WITH RETURN FOR 
      SELECT R."Path", R."Name", P."Path"
      FROM "Resources" AS R 
      INNER JOIN "Properties" AS P ON R."Resource"=P."Resource" 
      INNER JOIN "PropertyType" AS PT ON P."Property"=PT."Property" 
      GROUP BY R."Path", R."Name", P."Path" 
      FOR READ ONLY;
    OPEN Rslt;
  END"""

    elif name == 'createSelectFields':
        query = """\
CREATE PROCEDURE "SelectFields"()
  SPECIFIC "SelectFields_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE Rslt CURSOR WITH RETURN FOR 
      SELECT COALESCE(R."Name", P."Path") 
      FROM "Resources" AS R 
      LEFT JOIN "Properties" AS P ON R."Resource"=P."Resource" AND R."Name" IS NULL 
      FOR READ ONLY;
    OPEN Rslt;
  END"""

    elif name == 'createSelectGroups':
        query = """\
CREATE PROCEDURE "SelectGroups"(IN Aid Integer)
  SPECIFIC "SelectGroups_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE Rslt CURSOR WITH RETURN FOR 
      SELECT "Group", "Uri" FROM "Groups" WHERE "Book"=Aid ORDER BY "Group" 
      FOR READ ONLY;
    OPEN Rslt;
  END"""

    elif name == 'createMergeGroup':
        query = """\
CREATE PROCEDURE "MergeGroup"(IN AID VARCHAR(100),
                              IN URI VARCHAR(100),
                              IN DELETED BOOLEAN,
                              IN NAME VARCHAR(100),
                              IN DATETIME TIMESTAMP(6))
  SPECIFIC "MergeGroup_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    IF DELETED THEN
      DELETE FROM "Groups" WHERE "Book"=AID AND "Uri"=URI;
    ELSE
      MERGE INTO "Groups" USING (VALUES(AID,URI,NAME,DATETIME))
        AS vals(w,x,y,z) ON "Book"=vals.w AND "Uri"=vals.x
          WHEN MATCHED THEN UPDATE
            SET "Name"=vals.y, "Modified"=vals.z
          WHEN NOT MATCHED THEN INSERT ("Book","Uri","Name","Created","Modified")
            VALUES vals.w, vals.x, vals.y, vals.z, vals.z;
    END IF;
  END"""

    elif name == 'createSelectAddressbookColumns1':
        query = """\
CREATE PROCEDURE "SelectAddressbookColumns"()
  SPECIFIC "SelectAddressbookColumns_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE RSLT CURSOR WITH RETURN FOR
      SELECT ROWNUM() AS "ColumnId",
        C."Value" AS "PropertyName",
        C."View" AS "ViewName",
        C."Getter" AS "PropertyGetter",
        P."Getter" AS "ParameterGetter",
        C."Method",
        COALESCE(GROUP_CONCAT(T."Column" ORDER BY T."Order" SEPARATOR ''),'') ||
        COALESCE(PP."Column",'') AS "ColumnName",
        ARRAY_AGG(T."Value") AS "TypeValues"
      FROM "Properties" AS C
      JOIN "PropertyParameter" AS PP ON C."Property"=PP."Property"
      JOIN "Parameters" AS P ON PP."Parameter"=P."Parameter"
      LEFT JOIN "PropertyType" AS PT ON C."Property"=PT."Property"
      LEFT JOIN "Types" AS T ON PT."Type"=T."Type"
      GROUP BY C."Value",C."View",C."Getter",P."Getter",C."Method",PP."Column",PT."Group"
      FOR READ ONLY;
    OPEN RSLT;
  END"""

    elif name == 'createMergeGroupMembers':
        query = """\
CREATE PROCEDURE "MergeGroupMembers"(IN Gid INTEGER,
                                     DateTime TIMESTAMP(6),
                                     IN Members VARCHAR(100) ARRAY)
  SPECIFIC "MergeGroupMembers_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE Index INTEGER DEFAULT 1;
    DECLARE Cid INTEGER DEFAULT 1;
    DELETE FROM "GroupCards" WHERE "Group"=Gid; 
    WHILE Index <= CARDINALITY(Members) DO 
      SELECT "Card" INTO Cid FROM "Cards" WHERE "Uri"=Members[Index];
      IF Cid IS NOT NULL THEN
        MERGE INTO "GroupCards" USING (VALUES(Gid,Cid,DateTime))
          AS vals(x,y,z) ON "Group"=vals.x AND "Card"=vals.y
            WHEN MATCHED THEN UPDATE SET "Modified"=vals.z
            WHEN NOT MATCHED THEN INSERT ("Group","Card","Modified")
              VALUES vals.x,vals.y,vals.z;
      END IF;
      SET Index = Index + 1;
    END WHILE;
  END"""


    elif name == 'createMergeCardValue':
        query = """\
CREATE PROCEDURE "MergeCardValue"(IN AID INTEGER,
                                  IN CID INTEGER,
                                  IN DATA VARCHAR(128))
  SPECIFIC "MergeCardValue_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    MERGE INTO "CardValues" USING (VALUES(AID,CID,DATA))
      AS vals(x,y,z) ON "Card"=vals.x AND "Column"=vals.y
        WHEN MATCHED THEN UPDATE SET "Value"=vals.z
        WHEN NOT MATCHED THEN INSERT ("Card","Column","Value")
          VALUES vals.x,vals.y,vals.z;
  END"""

    elif name == 'createSelectCardGroup':
        query = """\
CREATE PROCEDURE "SelectCardGroup"()
  SPECIFIC "SelectCardGroup_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE RSLT CURSOR WITH RETURN FOR
      SELECT U."User", 
        ARRAY_AGG(JSON_OBJECT(G."Name": G."Group")) 
      FROM "Users" AS U 
      INNER JOIN "Books" AS A ON U."User"=A."User" 
      INNER JOIN "Groups" AS G ON A."Book"=G."Book" 
      WHERE U."User"!=0 
      GROUP BY U."User" 
      FOR READ ONLY;
    OPEN RSLT;
  END"""

    elif name == 'createInitGroups':
        query = """\
CREATE PROCEDURE "InitGroups"(IN Book INTEGER,
                              IN Uris VARCHAR(128) ARRAY,
                              IN Names VARCHAR(128) ARRAY,
                              OUT ViewToRemove VARCHAR(512),
                              OUT ViewToAdd VARCHAR(512))
  SPECIFIC "InitGroups_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE Index INTEGER DEFAULT 1;
    DECLARE TmpToRemove VARCHAR(512);
    DECLARE TmpToAdd VARCHAR(512);
    SELECT JSON_ARRAYAGG(JSON_OBJECT('OldName': "Name")) INTO TmpToRemove FROM "Groups" WHERE "Book"=Book AND "Uri" NOT IN(UNNEST(Uris));
    DELETE FROM "Groups" WHERE "Book"=Book AND "Uri" NOT IN(UNNEST(Uris));
    WHILE Index <= CARDINALITY(Uris) DO
      MERGE INTO "Groups" USING (VALUES(Book,Uris[Index],Names[Index])) 
        AS vals(x,y,z) ON "Groups"."Book"=vals.x AND "Groups"."Uri"=vals.y
          WHEN NOT MATCHED THEN INSERT ("Book","Uri","Name")
             VALUES vals.x,vals.y,vals.z;
      SET Index = Index + 1;
    END WHILE;
    SELECT JSON_ARRAYAGG(JSON_OBJECT('Name': "Name", 'Group':"Group")) INTO TmpToAdd FROM "Groups" WHERE "Book"=Book AND "Uri" IN(UNNEST(Uris));
    SET ViewToRemove = TmpToRemove;
    SET ViewToAdd = TmpToAdd;
  END"""

    elif name == 'createInsertGroup':
        query = """\
CREATE PROCEDURE "InsertGroup"(IN AID INTEGER,
                               IN URI VARCHAR(128),
                               IN NAME VARCHAR(128),
                               OUT GID INTEGER)
  SPECIFIC "InsertGroup_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    INSERT INTO "Groups" ("Book","Uri","Name") VALUES (AID,URI,NAME);
    SET GID = IDENTITY();
  END"""

    elif name == 'createMergeCardGroup':
        query = """\
CREATE PROCEDURE "MergeCardGroup"(IN Cid INTEGER,
                                  IN Gid INTEGER)
  SPECIFIC "MergeCardGroup_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DELETE FROM "GroupCards" WHERE "Card"=Cid;
    INSERT INTO "GroupCards" ("Group","Card") VALUES (Gid,Cid);
  END"""

    elif name == 'createMergeCardGroups':
        query = """\
CREATE PROCEDURE "MergeCardGroups"(IN Book INTEGER,
                                   IN Card INTEGER,
                                   IN Names VARCHAR(100) ARRAY)
  SPECIFIC "MergeCardGroups_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE Index INTEGER DEFAULT 1;
    DECLARE GroupId INTEGER DEFAULT NULL;
    DELETE FROM "GroupCards" WHERE "Card"=Card;
    WHILE Index <= CARDINALITY(Names) DO
      SELECT "Group" INTO GroupId FROM "Groups" WHERE "Book"=Book AND "Name"=Names[Index];
      IF GroupId IS NOT NULL THEN
        INSERT INTO "GroupCards" ("Group","Card") VALUES (GroupId,Card);
      END IF;
      SET Index = Index + 1;
    END WHILE;
  END"""

    elif name == 'createGetPeopleIndex':
        query = """\
CREATE FUNCTION "GetPeopleIndex"("Prefix" VARCHAR(50),"ResourceName" VARCHAR(100))
  RETURNS INTEGER
  SPECIFIC "GetPeopleIndex_1"
  READS SQL DATA
  RETURN (SELECT "People" FROM "Peoples" WHERE "Prefix"||"Resource"="ResourceName");
"""

    elif name == 'createGetLabelIndex':
        query = """\
CREATE FUNCTION "GetLabelIndex"("LabelName" VARCHAR(100))
  RETURNS INTEGER
  SPECIFIC "GetLabelIndex_1"
  READS SQL DATA
  RETURN (SELECT "Label" FROM "Labels" WHERE "Name"="LabelName");
"""

    elif name == 'createGetTypeIndex':
        query = """\
CREATE PROCEDURE "GetTypeIndex"(IN "TableName" VARCHAR(100),
                                IN "TypeName" VARCHAR(100),
                                OUT "TypeId" INTEGER)
  SPECIFIC "GetTypeIndex_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE "TypeIndex" INTEGER DEFAULT NULL;
    SET "TypeIndex" = SELECT "Type" FROM "Types" WHERE "Name"="TypeName";
    IF "TypeIndex" IS NULL THEN
      SET "TypeIndex" = SELECT "Type" FROM "TableType" JOIN "Tables"
        ON "TableType"."Table"="Tables"."Table"
          WHERE "TableType"."Default"=TRUE AND "Tables"."Name"="TableName";
      IF "TypeIndex" IS NULL THEN 
        INSERT INTO "Types" ("Name","Value") VALUES ("TypeName","TypeName");
        SET "TypeIndex" = IDENTITY();
      END IF;
    END IF;
    SET "TypeId" = "TypeIndex";
  END"""

    elif name == 'createMergePeople':
        query = """\
CREATE PROCEDURE "MergePeople"(IN "Prefix" VARCHAR(50),
                               IN "ResourceName" VARCHAR(100),
                               IN "GroupId" INTEGER,
                               IN "Time" TIMESTAMP(6),
                               IN "Deleted" BOOLEAN)
  SPECIFIC "MergePeople_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE "PeopleResource" VARCHAR(100);
    SET "PeopleResource" = REPLACE("ResourceName", "Prefix");
    IF "Deleted"=TRUE THEN
      DELETE FROM "Peoples" WHERE "Resource"="PeopleResource";
    ELSEIF NOT EXISTS(SELECT "People" FROM "Peoples" WHERE "Resource"="PeopleResource") THEN 
      INSERT INTO "Peoples" ("Resource","TimeStamp") VALUES ("PeopleResource","Time");
      INSERT INTO "Connections" ("Group","People","TimeStamp") VALUES ("GroupId",IDENTITY(),"Time");
    END IF;
  END"""

    elif name == 'createUnTypedDataMerge':
        q = """\
CREATE PROCEDURE "Merge%(Table)s"(IN "Prefix" VARCHAR(50),
                                  IN "ResourceName" VARCHAR(100),
                                  IN "LabelName" VARCHAR(100),
                                  IN "Value" VARCHAR(100),
                                  IN "Time" TIMESTAMP(6))
  SPECIFIC "Merge%(Table)s_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE "PeopleIndex","LabelIndex" INTEGER DEFAULT NULL;
    SET "PeopleIndex" = "GetPeopleIndex"("Prefix","ResourceName");
    SET "LabelIndex" = "GetLabelIndex"("LabelName");
    MERGE INTO "%(Table)s" USING
      (VALUES("PeopleIndex","LabelIndex","Value","Time")) AS vals(w,x,y,z)
      ON "%(Table)s"."People"=vals.w AND "%(Table)s"."Label"=vals.x
        WHEN MATCHED THEN UPDATE SET "Value"=vals.y, "TimeStamp"=vals.z
        WHEN NOT MATCHED THEN INSERT ("People","Label","Value","TimeStamp")
          VALUES vals.w, vals.x, vals.y, vals.z;
  END"""
        query = q % format

    elif name == 'createTypedDataMerge':
        q = """\
CREATE PROCEDURE "Merge%(Table)s"(IN "Prefix" VARCHAR(50),
                                  IN "ResourceName" VARCHAR(100),
                                  IN "LabelName" VARCHAR(100),
                                  IN "Value" VARCHAR(100),
                                  IN "Time" TIMESTAMP(6),
                                  IN "Table" VARCHAR(50),
                                  IN "TypeName" VARCHAR(100))
  SPECIFIC "Merge%(Table)s_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE "PeopleIndex","TypeIndex","LabelIndex" INTEGER DEFAULT NULL;
    SET "PeopleIndex" = "GetPeopleIndex"("Prefix","ResourceName");
    CALL "GetTypeIndex"("Table","TypeName","TypeIndex");
    SET "LabelIndex" = "GetLabelIndex"("LabelName");
    MERGE INTO "%(Table)s" USING
      (VALUES("PeopleIndex","TypeIndex","LabelIndex","Value","Time")) AS vals(v,w,x,y,z)
      ON "%(Table)s"."People"=vals.v AND "%(Table)s"."Type"=vals.w AND "%(Table)s"."Label"=vals.x
        WHEN MATCHED THEN UPDATE SET "Value"=vals.y, "TimeStamp"=vals.z
        WHEN NOT MATCHED THEN INSERT ("People","Type","Label","Value","TimeStamp")
          VALUES vals.v, vals.w, vals.x, vals.y, vals.z;
  END"""
        query = q % format

    elif name == 'createMergeConnection':
        q = """\
CREATE PROCEDURE "MergeConnection"(IN "GroupPrefix" VARCHAR(50),
                                   IN "PeoplePrefix" VARCHAR(50),
                                   IN "ResourceName" VARCHAR(100),
                                   IN "Time" TIMESTAMP(6),
                                   IN "Separator" VARCHAR(1),
                                   IN "MembersList" VARCHAR(15000))
  SPECIFIC "MergeConnection_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE "Index" INTEGER DEFAULT 1;
    DECLARE "Pattern" VARCHAR(5) DEFAULT '[^$]+';
    DECLARE "GroupId", "PeopleId" INTEGER;
    DECLARE "GroupResource", "PeopleResource" VARCHAR(100);
    DECLARE "MembersArray" VARCHAR(100) ARRAY[%s];
    SET "GroupResource" = REPLACE("ResourceName", "GroupPrefix");
    SELECT "Group" INTO "GroupId" FROM "Groups" WHERE "Resource"="GroupResource";
    DELETE FROM "Connections" WHERE "Group"="GroupId";
    SET "Pattern" = REPLACE("Pattern", '$', "Separator");
    SET "MembersArray" = REGEXP_SUBSTRING_ARRAY("MembersList", "Pattern");
    WHILE "Index" <= CARDINALITY("MembersArray") DO
      SET "PeopleResource" = REPLACE("MembersArray"["Index"], "PeoplePrefix");
      SELECT "People" INTO "PeopleId" FROM "Peoples" WHERE "Resource"="PeopleResource";
      INSERT INTO "Connections" ("Group","People","TimeStamp")
        VALUES ("GroupId","PeopleId","Time");
      SET "Index" = "Index" + 1;
    END WHILE;
    UPDATE "Groups" SET "GroupSync"=TRUE WHERE "Group"="GroupId";
  END"""
        query = q % g_member

# Get Procedure Query
    elif name == 'selectUser':
        query = 'CALL "SelectUser"(?,?)'
    elif name == 'insertUser':
        query = 'CALL "InsertUser"(?,?,?,?,?,?)'
    elif name == 'selectAddressbook':
        query = 'CALL "SelectAddressbook"(?,?,?)'
    elif name == 'insertBook':
        query = 'CALL "InsertBook"(?,?,?,?,?,?)'
    elif name == 'updateAddressbookName':
        query = 'CALL "UpdateAddressbookName"(?,?)'
    elif name == 'mergeCard':
        query = 'CALL "MergeCard"(?,?,?,?,?)'
    elif name == 'mergeCardValue':
        query = 'CALL "MergeCardValue"(?,?,?)'
    elif name == 'mergeGroupMembers':
        query = 'CALL "MergeGroupMembers"(?,?,?)'
    elif name == 'deleteCard':
        query = 'CALL "DeleteCard"(?)'
    elif name == 'getColumns':
        query = 'CALL "SelectColumns"()'
    elif name == 'getColumnIds':
        query = 'CALL "SelectColumnIds"()'
    elif name == 'getPaths':
        query = 'CALL "SelectPaths"()'
    elif name == 'getLists':
        query = 'CALL "SelectLists"()'
    elif name == 'getTypes':
        query = 'CALL "SelectTypes"()'
    elif name == 'getMaps':
        query = 'CALL "SelectMaps"()'
    elif name == 'getTmps':
        query = 'CALL "SelectTmps"()'
    elif name == 'getFields':
        query = 'CALL "SelectFields"()'
    elif name == 'getGroups':
        query = 'CALL "SelectGroups"(?)'
    elif name == 'selectChangedAddressbooks':
        query = 'CALL "SelectChangedAddressbooks"(?,?,?)'
    elif name == 'selectChangedGroups':
        query = 'CALL "SelectChangedGroups"(?,?)'
    elif name == 'getLastAddressbookSync':
        query = 'CALL "GetLastAddressbookSync"(?)'
    elif name == 'getLastGroupSync':
        query = 'CALL "GetLastGroupSync"(?)'
    elif name == 'updateAddressbook':
        query = 'CALL "UpdateAddressbook"(?)'
    elif name == 'updateGroup':
        query = 'CALL "UpdateGroup"(?)'
    elif name == 'getLastUserSync':
        query = 'CALL "GetLastUserSync"(?)'
    elif name == 'getChangedCards':
        query = 'CALL "SelectChangedCards"(?,?)'
    elif name == 'updateUser':
        query = 'CALL "UpdateUser"(?)'
    elif name == 'getSessionId':
        query = 'CALL SESSION_ID()'


    elif name == 'getCardGroup':
        query = 'CALL "SelectCardGroup"()'
    elif name == 'initGroups':
        query = 'CALL "InitGroups"(?,?,?,?,?)'
    elif name == 'insertGroup':
        query = 'CALL "InsertGroup"(?,?,?,?)'
    elif name == 'mergeCardGroup':
        query = 'CALL "MergeCardGroup"(?,?)'
    elif name == 'mergeCardGroups':
        query = 'CALL "MergeCardGroups"(?,?,?)'


    elif name == 'mergePeople':
        query = 'CALL "MergePeople"(?,?,?,?,?)'
    elif name == 'mergeGroup':
        query = 'CALL "MergeGroup"(?,?,?,?,?)'
    elif name == 'mergeConnection':
        query = 'CALL "MergeConnection"(?,?,?,?,?,?)'
    elif name == 'mergePeopleData':
        if format['Type'] is None:
            q = 'CALL "Merge%(Table)s"(?,?,?,?,?)'
        else:
            q = 'CALL "Merge%(Table)s"(?,?,?,?,?,?,?)'
        query = q % format

# Logging Changes Queries
    elif name == 'loggingChanges':
        if format:
            query = 'SET FILES LOG TRUE'
        else:
            query = 'SET FILES LOG FALSE'

# Saves Changes Queries
    elif name == 'saveChanges':
        if format:
            query = 'CHECKPOINT DEFRAG'
        else:
            query = 'CHECKPOINT'

# ShutDown Queries
    elif name == 'shutdown':
        if format:
            query = 'SHUTDOWN COMPACT;'
        else:
            query = 'SHUTDOWN;'

    elif name == 'shutdownCompact':
        query = 'SHUTDOWN COMPACT;'

# Queries don't exist!!!
    else:
        logger = getLogger(ctx, g_errorlog, g_basename)
        logger.logprb(SEVERE, g_basename, 'getSqlQuery()', 101, name)
        query = None
    return query

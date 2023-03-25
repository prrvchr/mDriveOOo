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

from .dbconfig import g_csv

from .logger import getLogger

from .configuration import g_errorlog

g_basename = 'dbqueries'


def getSqlQuery(ctx, name, format=None):


# Create Static Table Queries
    if name == 'createTableTables':
        c1 = '"Table" INTEGER NOT NULL PRIMARY KEY'
        c2 = '"Name" VARCHAR(100) NOT NULL'
        c3 = '"Identity" INTEGER DEFAULT NULL'
        c4 = '"View" BOOLEAN DEFAULT TRUE'
        c5 = '"Versioned" BOOLEAN DEFAULT FALSE'
        k1 = 'CONSTRAINT "UniqueTablesName" UNIQUE("Name")'
        c = (c1, c2, c3, c4, c5, k1)
        query = 'CREATE TEXT TABLE "Tables"(%s);' % ','.join(c)
    elif name == 'createTableColumns':
        c1 = '"Column" INTEGER NOT NULL PRIMARY KEY'
        c2 = '"Name" VARCHAR(100) NOT NULL'
        k1 = 'CONSTRAINT "UniqueColumnsName" UNIQUE("Name")'
        c = (c1, c2, k1)
        query = 'CREATE TEXT TABLE "Columns"(%s);' % ','.join(c)
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
        k2 = 'CONSTRAINT "ForeignTableColumnTable" FOREIGN KEY("Table") REFERENCES '
        k2 += '"Tables"("Table") ON DELETE CASCADE ON UPDATE CASCADE'
        k3 = 'CONSTRAINT "ForeignTableColumnColumn" FOREIGN KEY("Column") REFERENCES '
        k3 += '"Columns"("Column") ON DELETE CASCADE ON UPDATE CASCADE'
        c = (c1, c2, c3, c4, c5, c6, c7, c8, c9, k1, k2, k3)
        query = 'CREATE TEXT TABLE "TableColumn"(%s);' % ','.join(c)
    elif name == 'createTableSettings':
        c1 = '"Id" INTEGER NOT NULL PRIMARY KEY'
        c2 = '"Name" VARCHAR(100) NOT NULL'
        c3 = '"Value1" VARCHAR(100) NOT NULL'
        c4 = '"Value2" VARCHAR(100) DEFAULT NULL'
        c5 = '"Value3" VARCHAR(100) DEFAULT NULL'
        c = (c1, c2, c3, c4, c5)
        p = ','.join(c)
        query = 'CREATE TEXT TABLE "Settings"(%s);' % p
    elif name == 'setTableSource':
        query = 'SET TABLE "%s" SOURCE "%s"' % (format, g_csv % format)
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
        query = 'CREATE CACHED TABLE "%s"(%s)' % format

    elif name == 'getPeriodColumns':
        query = '"RowStart" TIMESTAMP GENERATED ALWAYS AS ROW START,'
        query += '"RowEnd" TIMESTAMP GENERATED ALWAYS AS ROW END,'
        query += 'PERIOD FOR SYSTEM_TIME("RowStart","RowEnd")'

    elif name == 'getSystemVersioning':
        query = ' WITH SYSTEM VERSIONING'


# Create Function Queries
    elif name == 'createGetTitle':
        query = '''\
CREATE FUNCTION "GetTitle"(IN TITLE VARCHAR(100),
                           IN URN VARCHAR(100),
                           IN SWAP BOOLEAN)
  RETURNS VARCHAR(100)
  SPECIFIC "GetTitle_1"
  CONTAINS SQL
  BEGIN ATOMIC
    IF SWAP THEN
      RETURN COALESCE(URN,TITLE);
    ELSE
      RETURN TITLE;
    END IF;
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetTitle_1" TO "%(Role)s";''' % format

    elif name == 'createGetUniqueName':
        query = '''\
CREATE FUNCTION "GetUniqueName"(IN NAME VARCHAR(100),
                                IN ISFOLDER BOOLEAN,
                                IN NUMBER INTEGER)
  RETURNS VARCHAR(110)
  SPECIFIC "GetUniqueName_1"
  CONTAINS SQL
  BEGIN ATOMIC
    DECLARE HINT VARCHAR(10);
    SET HINT = '%(Prefix)s' || NUMBER || '%(Suffix)s';
    IF ISFOLDER THEN
      RETURN NAME || HINT;
    ELSE
      RETURN INSERT(NAME, LENGTH(NAME) - POSITION('.' IN REVERSE(NAME)) + 1, 0, HINT);
    END IF;
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetUniqueName_1" TO "%(Role)s";''' % format

# Create Cached View Queries
    elif name == 'createChildView':
        query = '''\
CREATE VIEW "Child" ("UserId", "ItemId", "ParentId", "Title") AS SELECT 
  I."UserId", I."ItemId", P."ItemId", I."Title" 
  FROM "Items" AS I 
  JOIN "Parents" AS P ON I."ItemId"=P."ChildId";
GRANT SELECT ON "Child" TO "%(Role)s";''' % format

    elif name == 'createTwinView':
        query = '''\
CREATE VIEW "Twin" ("ParentId", "Title", "Idx") AS SELECT 
  P."ItemId", I."Title", ARRAY_AGG(I."ItemId" ORDER BY I."DateCreated", I."DateModified") 
  FROM "Items" AS I 
  JOIN "Parents" AS "P" ON "I"."ItemId"="P"."ChildId" 
  GROUP BY P."ItemId", I."Title" 
  HAVING COUNT(*) > 1;
GRANT SELECT ON "Twin" TO "%(Role)s";''' % format

    elif name == 'createUriView':
        query = '''\
CREATE VIEW "Uri" ("ItemId", "ParentId", "Title", "Length", "Position") AS SELECT 
  C."ItemId", T."ParentId", T."Title", CARDINALITY(T."Idx"), POSITION_ARRAY(C."ItemId" IN T."Idx") 
  FROM "Twin" AS T 
  JOIN "Child" AS C ON T."Title"=C."Title" AND T."ParentId"=C."ParentId";
GRANT SELECT ON "Uri" TO "%(Role)s";''' % format

    elif name == 'createItemView':
        query = '''\
CREATE VIEW "Item" ("ItemId", "ContentType", "IsFolder", "IsLink", "IsDocument") AS SELECT 
  I."ItemId", 
  CASE WHEN I."MediaType" IN (S."Value2",S."Value3") THEN I."MediaType" ELSE S."Value1" END, 
  I."MediaType"="S"."Value2", 
  I."MediaType"="S"."Value3", 
  I."MediaType"!="S"."Value2" AND I."MediaType"!="S"."Value3" 
  FROM "Settings" AS S, "Items" AS I 
  WHERE S."Name"='ContentType';
GRANT SELECT ON "Item" TO "%(Role)s";''' % format

    elif name == 'createTitleView':
        query = '''\
CREATE VIEW "Title" ("ItemId", "Title", "Position") AS SELECT 
  U."ItemId", "GetUniqueName"(U."Title", I."IsFolder", U."Position"), U."Position" 
  FROM "Uri" AS U 
  INNER JOIN "Item" AS I ON U."ItemId"=I."ItemId" 
  WHERE U."Position" > 1;
GRANT SELECT ON "Title" TO "%(Role)s";''' % format

    elif name == 'createChildrenView':
        query = '''\
CREATE VIEW "Children" ("UserId", "ItemId", "ParentId", "Title", "Uri", "DateCreated", "DateModified", "IsFolder", "Size", "Loaded") AS SELECT
  I."UserId", C."ItemId", C."ParentId", I."Title", COALESCE(T."Title",I."Title"), I."DateCreated", I."DateModified",
  I2."IsFolder", I."Size", I."Loaded" 
  FROM "Items" AS I 
  INNER JOIN "Item" AS I2 ON I."ItemId"=I2."ItemId" 
  INNER JOIN "Child" AS C ON I2."ItemId"=C."ItemId" 
  LEFT JOIN "Title" AS T ON C."ItemId"=T."ItemId";
GRANT SELECT ON "Children" TO "%(Role)s";''' % format

    elif name == 'createPathView':
        query = '''\
CREATE VIEW "Path" AS WITH RECURSIVE TREE ("ItemId", "Path") AS (
    SELECT "RootId", '%(Scheme)s' || '://' || "UserName" 
    FROM "Users"
  UNION ALL 
    SELECT C2."ItemId", "Path" || '%(Separator)s' || C2."Uri"
    FROM "Children" C2
    JOIN TREE T on T."ItemId" = C2."ParentId"
  )
  SELECT "ItemId", "Path"
  FROM TREE;
GRANT SELECT ON "Path" TO "%(Role)s";''' % format

    elif name == 'createUpdateView':
        query = '''\
(SELECT I."ItemId", 3 AS "ChangeAction", I."RowEnd" AS "TimeStamp" 
  FROM "Items"FOR SYSTEM_TIME AS OF FIRST AS I 
  LEFT JOIN "Items" FOR SYSTEM_TIME AS OF LAST AS I2 ON I."ItemId" = I2."ItemId" 
  WHERE I2."ItemId" IS NULL)
UNION ALL
(SELECT I2."ItemId", 1 AS "ChangeAction", I2."RowStart" AS "TimeStamp"
  FROM "Items" FOR SYSTEM_TIME AS OF LAST AS I2
  INNER JOIN "Path" AS P ON I2."ItemId"=P."ItemId" 
  LEFT JOIN "Items" FOR SYSTEM_TIME AS OF FIRST AS I ON P."ItemId"=I."ItemId"
  WHERE I."ItemId" IS NULL)
UNION ALL
(SELECT I2."ItemId", 2 AS "Action", I."RowEnd" AS "TimeStamp"
  FROM "Items" FOR SYSTEM_TIME AS OF LAST AS I2
  INNER JOIN "Items" FOR SYSTEM_TIME FROM FIRST TO LAST AS I
    ON I2."ItemId"=I."ItemId" AND I2."RowStart"=I."RowEnd")
ORDER BY "TimeStamp"

'''

# Create User
    elif name == 'createUser':
        q = """\
CREATE USER "%(User)s" PASSWORD '%(Password)s'"""
        if format.get('Admin', False):
            q += ' ADMIN'
        query = q % format

    elif name == 'createRole':
        query = 'CREATE ROLE "%(Role)s";' % format

    elif name == 'grantRole':
        query = 'GRANT "%(Role)s" TO "%(User)s";' % format

    elif name == 'grantPrivilege':
        query = 'GRANT %(Privilege)s ON TABLE "%(Table)s" TO "%(Role)s";' % format

    elif name == 'setSession':
        query = "SET SESSION AUTHORIZATION '%s'" % format

# Select Queries
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
        f2 = 'JOIN "TableColumn" AS "TC" ON "T"."Table"="TC"."Table"'
        f3 = 'JOIN "Columns" AS "C" ON "TC"."Column"="C"."Column"'
        f4 = 'LEFT JOIN "Tables" AS "T2" ON "TC"."ForeignTable"="T2"."Table"'
        f5 = 'LEFT JOIN "Columns" AS "C2" ON "TC"."ForeignColumn"="C2"."Column"'
        w = '"T"."Name"=?'
        f = (f1, f2, f3, f4, f5)
        p = (','.join(s), ' '.join(f), w)
        query = 'SELECT %s FROM %s WHERE %s;' % p

    elif name == 'getContentType':
        query = """\
SELECT "Value2" "Folder","Value3" "Link" FROM "Settings" WHERE "Name"='ContentType';"""

    elif name == 'getUser':
        query = '''\
SELECT U."UserId", U."RootId", U."Token", I."Title" "RootName" 
FROM "Users" AS U 
INNER JOIN "Items" AS I ON U."RootId" = I."ItemId" 
WHERE U."UserName" = ?;'''

    elif name == 'getChildren':
        query = '''\
SELECT C."Uri" AS Title, C."Size", C."DateModified", C."DateCreated", C."IsFolder", 
P."Path" AS "TargetURL", FALSE "IsHidden", FALSE "IsVolume", 
FALSE "IsRemote", FALSE "IsRemoveable", FALSE "IsFloppy", FALSE "IsCompactDisc" 
FROM "Children" AS C
INNER JOIN "Path" AS P ON C."ItemId"=P."ItemId" 
WHERE C."ParentId" = ? AND (C."IsFolder" = TRUE OR C."Loaded" >= ?);'''

    elif name == 'getChildId':
        query = '''\
SELECT "ItemId" FROM "Children" WHERE "ParentId" = ? AND "Uri" = ?;'''

    elif name == 'getNewIdentifier':
        query = 'SELECT "ItemId" FROM "Identifiers" WHERE "UserId" = ? ORDER BY "TimeStamp","ItemId" LIMIT 1;'

    elif name == 'countNewIdentifier':
        query = 'SELECT COUNT("ItemId") "Ids" FROM "Identifiers" WHERE "UserId" = ?;'

    elif name == 'hasTitle':
        query = 'SELECT COUNT("Title") > 0 FROM "Child" WHERE "UserId" = ? AND "ParentId" = ? AND "Title" = ?;'

    elif name == 'getToken':
        query = 'SELECT "Token" FROM "Users" WHERE "UserId" = ?;'

# Insert Queries
    elif name == 'insertUser':
        query = 'INSERT INTO "Users" ("UserName", "DisplayName", "RootId", "TimeStamp", "UserId") VALUES (?,?,?,?,?);'

    elif name == 'insertNewIdentifier':
        query = 'INSERT INTO "Identifiers"("UserId","ItemId")VALUES(?,?);'

# Update Queries
    elif name == 'updateToken':
        query = 'UPDATE "Users" SET "Token"=? WHERE "UserId"=?;'

    elif name == 'updateUserTimeStamp':
        query = 'UPDATE "Users" SET "TimeStamp"=? WHERE "UserId"=?;'

    elif name == 'updateUsersTimeStamp':
        query = 'UPDATE "Users" SET "TimeStamp"=?;'

    elif name == 'updateTitle':
        query = 'UPDATE "Items" SET "TimeStamp"=?, "Title"=? WHERE "ItemId"=?;'

    elif name == 'updateSize':
        query = 'UPDATE "Items" SET "TimeStamp"=?, "Size"=? WHERE "ItemId"=?;'

    elif name == 'updateTrashed':
        query = 'UPDATE "Items" SET "TimeStamp"=?, "Trashed"=? WHERE "ItemId"=?;'

    elif name == 'updateCapabilities':
        query = 'UPDATE "Capabilities" SET "TimeStamp"=? WHERE "UserId"=? AND "ItemId"=?;'

    elif name == 'updateLoaded':
        query = 'UPDATE "Items" SET "Loaded"=? WHERE "ItemId"=?;'

    elif name == 'updateItemId':
        query = 'UPDATE "Items" SET "ItemId"=? WHERE "ItemId"=?;'

# Delete Queries
    elif name == 'deleteNewIdentifier':
        query = 'DELETE FROM "Identifiers" WHERE "UserId"=? AND "ItemId"=?;'

# Create Procedure Query
    elif name == 'createGetIdentifier':
        query = '''\
CREATE PROCEDURE "GetIdentifier"(IN URI VARCHAR(500),
                                 IN ROOTID VARCHAR(100),
                                 OUT ITEMID VARCHAR(100),
                                 OUT ISROOT BOOLEAN)
  SPECIFIC "GetIdentifier_1"
  READS SQL DATA
  BEGIN ATOMIC
    DECLARE ITEM VARCHAR(100);
    SET ITEM = SELECT "ItemId" FROM "Path" WHERE "Path" = URI;
    SET ITEMID = ITEM;
    SET ISROOT = ITEM = ROOTID;
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetIdentifier_1" TO "%(Role)s";''' % format

    elif name == 'createGetRoot':
        query = '''\
CREATE PROCEDURE "GetRoot"(IN USERID VARCHAR(100))
  SPECIFIC "GetRoot_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE "Result" CURSOR WITH RETURN FOR
      SELECT I."ItemId" "Id", I."ItemId" "ParentId", P."Path" "ParentURI", I."ItemId" "ObjectId", 
      I."Title", I."Title" "TitleOnServer", I."DateCreated", I."DateModified", 
      I2."ContentType", I."MediaType", I."Size", I."Trashed", TRUE "IsRoot", I2."IsFolder", I2."IsDocument", 
      C."CanAddChild", C."CanRename", C."IsReadOnly", C."IsVersionable", I."Loaded", '' "CasePreservingURL" 
      FROM "Users" AS U 
      INNER JOIN "Items" AS I ON U."RootId"=I."ItemId" 
      INNER JOIN "Item" AS I2 ON I."ItemId"=I2."ItemId" 
      INNER JOIN "Capabilities" AS C ON I."ItemId"=C."ItemId" 
      INNER JOIN "Path" AS P ON C."ItemId"=P."ItemId"
      WHERE U."UserId" = USERID FOR READ ONLY;
    OPEN "Result";
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetRoot_1" TO "%(Role)s";''' % format

    elif name == 'createGetItem':
        query = '''\
CREATE PROCEDURE "GetItem"(IN ITEMID VARCHAR(100),
                           IN SWAP BOOLEAN)
  SPECIFIC "GetItem_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE "Result" CURSOR WITH RETURN FOR
      SELECT I."ItemId" "Id", P."ItemId" "ParentId", P2."Path" "ParentURI", I."ItemId" "ObjectId", 
       "GetTitle"(I."Title",T."Title",SWAP) "Title", "GetTitle"(I."Title",T."Title",SWAP) "TitleOnServer",
       I."DateCreated", I."DateModified", I2."ContentType", I."MediaType", I."Size", I."Trashed", 
       FALSE "IsRoot", I2."IsFolder", I2."IsDocument", C."CanAddChild", C."CanRename", 
       C."IsReadOnly", C."IsVersionable", I."Loaded", '' "CasePreservingURL" 
      FROM "Items" AS I 
      INNER JOIN "Item" AS I2 ON I."ItemId"=I2."ItemId" 
      INNER JOIN "Capabilities" AS C ON I."ItemId"=C."ItemId" 
      INNER JOIN "Parents" AS P ON I."ItemId"=P."ChildId" 
      INNER JOIN "Path" AS P2 ON P."ItemId"=P2."ItemId" 
      LEFT JOIN "Title" AS T ON I."ItemId"=T."ItemId" 
      WHERE I."ItemId" = ITEMID FOR READ ONLY;
    OPEN "Result";
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetItem_1" TO "%(Role)s";''' % format

    elif name == 'createGetNewTitle':
        query = '''\
CREATE PROCEDURE "GetNewTitle"(IN TITLE VARCHAR(100),
                               IN PARENTID VARCHAR(100),
                               IN ISFOLDER BOOLEAN,
                               OUT NEWTITLE VARCHAR(100))
  SPECIFIC "GetNewTitle_1"
  READS SQL DATA
  BEGIN ATOMIC
    DECLARE NUMBER INTEGER;
    DECLARE NEWNAME VARCHAR(100);
    SELECT COUNT("Title") INTO NUMBER FROM "Child" WHERE "Title" = TITLE AND "ParentId" = PARENTID;
    IF NUMBER > 0 THEN
      SET NEWNAME = "GetUniqueName"(TITLE, ISFOLDER, NUMBER + 1);
    ELSE
      SET NEWNAME = TITLE;
    END IF;
    SET NEWTITLE = NEWNAME;
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetNewTitle_1" TO "%(Role)s";''' % format

# Get the user timestamp of the oldest replication
    elif name == 'createGetUserTimeStamp':
        query = '''\
CREATE PROCEDURE "GetUserTimeStamp"(OUT TS TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "GetUserTimeStamp_1"
  READS SQL DATA
  BEGIN ATOMIC
    DECLARE TMP TIMESTAMP(6) WITH TIME ZONE;
    SELECT MIN("TimeStamp") INTO TMP FROM "Users";
    SET TS = TMP;
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetUserTimeStamp_1" TO "%(Role)s";''' % format

# System Time Period Procedure Queries
    elif name == 'createGetPushItems':
        query = '''\
CREATE PROCEDURE "GetPushItems"(IN USERID VARCHAR(100),
                                IN "Start" TIMESTAMP(6) WITH TIME ZONE,
                                IN "Stop" TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "GetPushItems_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE "Result" CURSOR WITH RETURN FOR
      -- com.sun.star.ucb.ChangeAction.INSERT
      (SELECT I."ItemId", 1 AS "ChangeAction", I."RowStart" AS "TimeStamp" 
        FROM "Items" FOR SYSTEM_TIME FROM "Start" TO "Stop" AS I 
        LEFT JOIN "Items" FOR SYSTEM_TIME AS OF "Start" AS I2 
          ON I."ItemId" = I2."ItemId" 
        WHERE I2."ItemId" IS NULL AND I."UserId" = USERID) 
      UNION
      (SELECT "ItemId", SUM("ChangeAction"), MAX("TimeStamp") FROM (
        -- com.sun.star.ucb.ChangeAction.UPDATE
        SELECT I."ItemId", 2 AS "ChangeAction", MAX(I."RowEnd") AS "TimeStamp" 
          FROM "Items" FOR SYSTEM_TIME FROM "Start" TO "Stop" AS I 
          INNER JOIN "Items" FOR SYSTEM_TIME FROM "Start" TO "Stop" AS I2 
            ON I."ItemId" = I2."ItemId" AND I2."RowStart" = I."RowEnd" 
          WHERE I."UserId" = USERID GROUP BY "ItemId", "ChangeAction" 
       UNION
        -- com.sun.star.ucb.ChangeAction.MOVE
        SELECT P."ChildId" AS "ItemId", 4 AS "ChangeAction", MAX(I."RowEnd") AS "TimeStamp" 
          FROM "Parents" FOR SYSTEM_TIME FROM "Start" TO "Stop" AS P 
          INNER JOIN "Items" AS I ON P."ChildId" = I."ItemId"
          INNER JOIN "Parents" FOR SYSTEM_TIME FROM "Start" TO "Stop" AS P2 
            ON P."ChildId" = P2."ChildId" AND P2."RowStart"=P."RowEnd" 
          WHERE I."UserId" = USERID GROUP BY "ChildId", "ChangeAction") 
      GROUP BY "ItemId")
      UNION
      -- com.sun.star.ucb.ChangeAction.DELETE
      (SELECT I."ItemId", 8 AS "ChangeAction", I."RowEnd" AS "TimeStamp" 
        FROM "Items" FOR SYSTEM_TIME AS OF "Start" AS I 
        LEFT JOIN "Items" FOR SYSTEM_TIME FROM "Start" TO "Stop" AS I2 
          ON I."ItemId" = I2."ItemId" 
        WHERE I2."ItemId" IS NULL AND I."UserId" = USERID) 
      ORDER BY "TimeStamp" FOR READ ONLY;
    OPEN "Result";
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetPushItems_1" TO "%(Role)s";''' % format

    elif name == 'createGetPushProperties':
        query = '''\
CREATE PROCEDURE "GetPushProperties"(IN USERID VARCHAR(100),
                                     IN ITEMID VARCHAR(100),
                                     IN "Start" TIMESTAMP(6) WITH TIME ZONE,
                                     IN "Stop" TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "GetPushProperties_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE "Result" CURSOR WITH RETURN FOR
      SELECT MAX(I."Title" <> I2."Title") AS "Title", 
        MAX(I."DateModified" <> I2."DateModified") AS "DateModified", 
        MAX(I."Size" <> I2."Size") AS "Size" 
        FROM "Items" FOR SYSTEM_TIME FROM "Start" TO "Stop" AS I 
        INNER JOIN "Items" FOR SYSTEM_TIME FROM "Start" TO "Stop" AS I2 
          ON I."ItemId" = I2."ItemId" AND I2."RowStart" = I."RowEnd" 
        WHERE I."UserId" = USERID AND I."ItemId" = ITEMID FOR READ ONLY;
    OPEN "Result";
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetPushProperties_1" TO "%(Role)s";''' % format

# Get item parent id Procedure Queries
    elif name == 'createGetItemParentIds':
        query = '''\
CREATE PROCEDURE "GetItemParentIds"(IN ITEMID VARCHAR(100),
                                    IN STARTTIME TIMESTAMP(6) WITH TIME ZONE,
                                    IN STOPTIME TIMESTAMP(6) WITH TIME ZONE,
                                    OUT OLDPARENT VARCHAR(100) ARRAY,
                                    OUT NEWPARENT VARCHAR(100) ARRAY)
  SPECIFIC "GetItemParentIds_1"
  READS SQL DATA
  BEGIN ATOMIC
    DECLARE OLDIDS VARCHAR(100) ARRAY;
    DECLARE NEWIDS VARCHAR(100) ARRAY;
    SELECT ARRAY_AGG("ItemId" ORDER BY "TimeStamp") INTO OLDIDS 
      FROM "Parents" FOR SYSTEM_TIME AS OF STARTTIME 
      WHERE "ChildId" = ITEMID GROUP BY "ChildId";
    SELECT ARRAY_AGG("ItemId" ORDER BY "TimeStamp") INTO NEWIDS 
      FROM "Parents" FOR SYSTEM_TIME AS OF STOPTIME 
      WHERE "ChildId" = ITEMID GROUP BY "ChildId";
    SET OLDPARENT = OLDIDS;
    SET NEWPARENT = NEWIDS;
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetItemParentIds_1" TO "%(Role)s";''' % format

# System Time Period Procedure Queries
    elif name == 'createGetSyncItems1':
        query = '''\
CREATE PROCEDURE "GetSyncItems"(IN "Start" TIMESTAMP(6) WITH TIME ZONE,
                                IN "Stop" TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "GetSyncItems_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE "Result" CURSOR WITH RETURN FOR
      (SELECT U."UserName", I."ItemId", 3 AS "ChangeAction", I."RowEnd" AS "TimeStamp" 
        FROM "Items" FOR SYSTEM_TIME AS OF "Start" AS I 
        INNER JOIN "Users" AS U ON I."UserId"=U."UserId" 
        LEFT JOIN "Items" FOR SYSTEM_TIME AS OF "Stop" AS I2 
          ON I."ItemId" = I2."ItemId" 
        WHERE I2."ItemId" IS NULL)
      UNION
      (SELECT U."UserName", I2."ItemId", 1 AS "ChangeAction", I2."RowStart" AS "TimeStamp"
        FROM "Items" FOR SYSTEM_TIME AS OF "Stop" AS I2
        INNER JOIN "Users" AS U ON I2."UserId"=U."UserId" 
        LEFT JOIN "Items" FOR SYSTEM_TIME AS OF "Start" AS I 
          ON I."ItemId"=I2."ItemId"
        WHERE I."ItemId" IS NULL)
      UNION
      (SELECT U."UserName", I2."ItemId", 2 AS "ChangeAction", I."RowEnd" AS "TimeStamp"
        FROM "Items" FOR SYSTEM_TIME AS OF "Stop" AS I2
        INNER JOIN "Users" AS U ON I2."UserId"=U."UserId" 
        INNER JOIN "Items" FOR SYSTEM_TIME FROM "Start" TO "Stop" AS I 
          ON I2."ItemId"=I."ItemId" AND I2."RowStart"=I."RowEnd")
      ORDER BY "UserName", "TimeStamp" FOR READ ONLY;
    OPEN "Result";
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetSyncItems_1" TO "%(Role)s";''' % format



    elif name == 'createGetSyncItems2':
        query = '''\
CREATE PROCEDURE "GetSyncItems"(IN "Start" TIMESTAMP(6) WITH TIME ZONE,
                                IN "Stop" TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "GetSyncItems_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE "Result" CURSOR WITH RETURN FOR
    SELECT "UserName", "Id", "Title", "DateCreated", "DateModified", "MediaType", "Size", "Trashed",
        GROUP_CONCAT("ParentId" SEPARATOR '","') "ParentId", "TimeStamp", "TitleUpdated", "SizeUpdated",
        "TrashedUpdated", EVERY("AtRoot") "AtRoot" FROM
    ((SELECT  "Users"."UserName" "UserName", "Items"."ItemId" "Id", "Items"."Title",
        "Items"."DateCreated", "Items"."DateModified", "Items"."MediaType", "Items"."Size",
        "Items"."Trashed", "Parents"."ItemId" "ParentId",
        "Before"."TimeStamp" "TimeStamp",
        "Items"."Title" <> "Before"."Title" "TitleUpdated",
        "Items"."Size" <> "Before"."Size" AND "Before"."Size" = 0 "SizeUpdated",
        "Items"."Trashed" <> "Before"."Trashed" "TrashedUpdated",
        "Users"."RootId" = "Parents"."ItemId" "AtRoot" FROM "Items"
    INNER JOIN "Capabilities" FOR SYSTEM_TIME AS OF "Stop" AS "Current" ON "Items"."ItemId" = "Current"."ItemId"
    INNER JOIN "Parents" ON "Current"."UserId" = "Parents"."UserId" AND "Current"."ItemId" = "Parents"."ChildId"
    INNER JOIN "Users" ON "Parents"."UserId" = "Users"."UserId" 
    INNER JOIN "Capabilities" FOR SYSTEM_TIME FROM "Start" TO "Stop" AS "Previous" ON "Current"."UserId" = "Previous"."UserId"
     AND "Current"."ItemId" = "Previous"."ItemId" AND "Current"."RowStart" = "Previous"."RowEnd"
    LEFT JOIN "Items" FOR SYSTEM_TIME FROM "Start" TO "Stop" AS "After" ON "Previous"."ItemId" = "After"."ItemId"
    LEFT JOIN "Items" FOR SYSTEM_TIME FROM "Start" TO "Stop" AS "Before" ON "After"."ItemId" = "Before"."ItemId" AND "After"."RowStart" = "Before"."RowEnd")
    UNION 
    (SELECT "Users"."UserName" "UserName", "Items"."ItemId" "Id", "Items"."Title",
        "Items"."DateCreated", "Items"."DateModified", "Items"."MediaType", "Items"."Size",
        "Items"."Trashed", "Parents"."ItemId" "ParentId",
        "Previous"."TimeStamp" "TimeStamp", TRUE "TitleUpdated", TRUE "SizeUpdated", TRUE "TrashedUpdated",
        "Users"."RootId" = "Parents"."ItemId" "AtRoot" FROM "Items"
    INNER JOIN "Capabilities" FOR SYSTEM_TIME AS OF "Stop" AS "Current" ON "Items"."ItemId" = "Current"."ItemId"
    INNER JOIN "Parents" ON "Current"."UserId" = "Parents"."UserId" AND "Current"."ItemId" = "Parents"."ChildId"
    INNER JOIN "Users" ON "Parents"."UserId" = "Users"."UserId" 
    LEFT JOIN "Capabilities" FOR SYSTEM_TIME AS OF "Start" AS "Previous" ON "Current"."UserId" = "Previous"."UserId" AND "Current"."ItemId" = "Previous"."ItemId"
    WHERE "Previous"."UserId" IS NULL AND "Previous"."ItemId" IS NULL))
    GROUP BY "UserName", "Id", "Title", "DateCreated", "DateModified", "MediaType",
        "Size", "Trashed", "TimeStamp", "TitleUpdated", "SizeUpdated", "TrashedUpdated"
    ORDER BY "TimeStamp" FOR READ ONLY;
    OPEN "Result";
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetSyncItems_1" TO "%(Role)s";''' % format


    elif name == 'createMergeItem':
        query = '''\
CREATE PROCEDURE "MergeItem"(IN "UserId" VARCHAR(100),
                             IN "Loaded" SMALLINT,
                             IN "TimeStamp" TIMESTAMP(6) WITH TIME ZONE,
                             IN "ItemId" VARCHAR(100),
                             IN "Title" VARCHAR(100),
                             IN "DateCreated" TIMESTAMP(6),
                             IN "DateModified" TIMESTAMP(6),
                             IN "MediaType" VARCHAR(100),
                             IN "Size" BIGINT,
                             IN "Trashed" BOOLEAN,
                             IN "CanAddChild" BOOLEAN,
                             IN "CanRename" BOOLEAN,
                             IN "IsReadOnly" BOOLEAN,
                             IN "IsVersionable" BOOLEAN,
                             IN "Parents" VARCHAR(100) ARRAY)
  SPECIFIC "MergeItem_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE "Index" INTEGER DEFAULT 1;
    MERGE INTO "Items" USING (VALUES("UserId","ItemId","Title","DateCreated","DateModified", 
                                     "MediaType","Size","Trashed","Loaded","TimeStamp")) 
      AS vals(k,r,s,t,u,v,w,x,y,z) ON "Items"."ItemId"=vals.r 
        WHEN MATCHED THEN 
          UPDATE SET "Title"=vals.s, "DateCreated"=vals.t, "DateModified"=vals.u, "MediaType"=vals.v, 
                     "Size"=vals.w, "Trashed"=vals.x, "Loaded"=vals.y, "TimeStamp"=vals.z 
        WHEN NOT MATCHED THEN 
          INSERT ("UserId","ItemId","Title","DateCreated","DateModified", 
                  "MediaType","Size","Trashed","Loaded","TimeStamp") 
          VALUES vals.k, vals.r, vals.s, vals.t, vals.u, vals.v, vals.w, vals.x, vals.y, vals.z; 
    MERGE INTO "Capabilities" USING (VALUES("UserId","ItemId","CanAddChild","CanRename", 
                                            "IsReadOnly","IsVersionable","TimeStamp")) 
      AS vals(t,u,v,w,x,y,z) ON "Capabilities"."UserId"=vals.t AND "Capabilities"."ItemId"=vals.u 
        WHEN MATCHED THEN 
          UPDATE SET "CanAddChild"=vals.v, "CanRename"=vals.w, "IsReadOnly"=vals.x, 
                     "IsVersionable"=vals.y, "TimeStamp"=vals.z 
        WHEN NOT MATCHED THEN 
          INSERT ("UserId","ItemId","CanAddChild","CanRename","IsReadOnly", 
                  "IsVersionable","TimeStamp")
          VALUES vals.t, vals.u, vals.v, vals.w, vals.x, vals.y, vals.z;
    DELETE FROM "Parents" WHERE "ChildId"="ItemId" AND "ItemId" NOT IN (UNNEST("Parents"));
    -- A resource can have several parents in any case Google allows it...
    WHILE "Index" <= CARDINALITY("Parents") DO
      MERGE INTO "Parents" USING (VALUES("ItemId","Parents"["Index"],"TimeStamp")) 
        AS vals(x,y,z) ON "Parents"."ChildId"=vals.x AND "Parents"."ItemId"=vals.y 
          WHEN NOT MATCHED THEN 
            INSERT ("ChildId","ItemId","TimeStamp") 
            VALUES vals.x, vals.y, vals.z;
      SET "Index" = "Index" + 1;
    END WHILE;
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "MergeItem_1" TO "%(Role)s";''' % format

    elif name == 'createInsertItem':
        query = '''\
CREATE PROCEDURE "InsertItem"(IN USERID VARCHAR(100),
                              IN LOADED SMALLINT,
                              IN DATETIME TIMESTAMP(6) WITH TIME ZONE,
                              IN ITEMID VARCHAR(100),
                              IN TITLE VARCHAR(100),
                              IN CREATED TIMESTAMP(6),
                              IN MODIFIED TIMESTAMP(6),
                              IN MEDIATYPE VARCHAR(100),
                              IN SIZE BIGINT,
                              IN TRASHED BOOLEAN,
                              IN ADDCHILD BOOLEAN,
                              IN CANRENAME BOOLEAN,
                              IN READONLY BOOLEAN,
                              IN ISVERSIONABLE BOOLEAN,
                              IN PARENT VARCHAR(100),
                              OUT URI VARCHAR(500),
                              OUT BASENAME VARCHAR(100))
  SPECIFIC "InsertItem_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE PATH VARCHAR(500);
    DECLARE NAME VARCHAR(100);
    INSERT INTO "Items" ("UserId","ItemId","Title","DateCreated","DateModified","MediaType",
      "Size","Trashed","Loaded","TimeStamp") VALUES (USERID,ITEMID,TITLE,CREATED,MODIFIED,
      MEDIATYPE,SIZE,TRASHED,LOADED,DATETIME);
    INSERT INTO "Capabilities" ("UserId","ItemId","CanAddChild","CanRename","IsReadOnly",
      "IsVersionable","TimeStamp") VALUES (USERID,ITEMID,ADDCHILD,CANRENAME,READONLY,
      ISVERSIONABLE,DATETIME);
    INSERT INTO "Parents" ("ChildId","ItemId","TimeStamp") VALUES (ITEMID,
      PARENT,DATETIME);
    SELECT P."Path", COALESCE(T."Title", I."Title") "Title" INTO PATH, NAME
    FROM "Items" AS I 
    INNER JOIN "Path" AS P ON I."ItemId"=P."ItemId" 
    LEFT JOIN "Title" AS T ON I."ItemId"=T."ItemId" 
    WHERE I."ItemId"=ITEMID;
    SET URI = PATH;
    SET BASENAME = NAME;
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "InsertItem_1" TO "%(Role)s";''' % format

# Get Procedure Query
    elif name == 'getIdentifier':
        query = 'CALL "GetIdentifier"(?,?,?,?)'
    elif name == 'getRoot':
        query = 'CALL "GetRoot"(?)'
    elif name == 'getItem':
        query = 'CALL "GetItem"(?,?)'
    elif name == 'getNewTitle':
        query = 'CALL "GetNewTitle"(?,?,?,?)'
    elif name == 'getUserTimeStamp':
        query = 'CALL "GetUserTimeStamp"(?)'
    elif name == 'getPushItems':
        query = 'CALL "GetPushItems"(?,?,?)'
    elif name == 'getPushProperties':
        query = 'CALL "GetPushProperties"(?,?,?,?)'
    elif name == 'getItemParentIds':
        query = 'CALL "GetItemParentIds"(?,?,?,?,?)'
    elif name == 'mergeItem':
        query = 'CALL "MergeItem"(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
    elif name == 'insertItem':
        query = 'CALL "InsertItem"(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'

# Get DataBase Version Query
    elif name == 'getVersion':
        query = 'Select DISTINCT DATABASE_VERSION() as "HSQL Version" From INFORMATION_SCHEMA.SYSTEM_TABLES;'

# ShutDown Queries
    elif name == 'shutdown':
        query = 'SHUTDOWN;'
    elif name == 'shutdownCompact':
        query = 'SHUTDOWN COMPACT;'

# Queries don't exist!!!
    else:
        logger = getLogger(ctx, g_errorlog, g_basename)
        logger.logp(SEVERE, g_basename, 'getSqlQuery()', 101, name)
        query = None
    return query

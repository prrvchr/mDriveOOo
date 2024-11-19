#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-24 https://prrvchr.github.io                                  ║
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

from .logger import getLogger

from .configuration import g_defaultlog

g_basename = 'dbqueries'


def getSqlQuery(ctx, name, format=None):

# Select Queries
    if name == 'getUser':
        query = 'SELECT "UserId", "UserName", "RootId", "ShareId", "Token", "DateCreated", "DateModified", "TimeStamp" FROM "Users" WHERE "UserName" = ?;'

    elif name == 'getChildren':
        query = 'SELECT %(Columns)s FROM %(Children)s AS C WHERE C."UserId" = ? AND C."Path" = ? AND (C."IsFolder" = TRUE OR ABS(C."ConnectionMode") >= ?);' % format

    elif name == 'getChildId':
        query = 'SELECT "ItemId" FROM "Children" WHERE "ParentId" = ? AND "Path" = ? AND "Title" = ?;'

    elif name == 'getNewIdentifier':
        query = 'SELECT "ItemId" FROM "Identifiers" WHERE "UserId" = ? ORDER BY "TimeStamp","ItemId" LIMIT 1;'

    elif name == 'countNewIdentifier':
        query = 'SELECT COUNT("ItemId") "Ids" FROM "Identifiers" WHERE "UserId" = ?;'

    elif name == 'hasTitle':
        query = 'SELECT COUNT("Name") > 0 FROM "Child" WHERE "UserId" = ? AND "ParentId" = ? AND "Name" = ?;'

# Insert Queries
    elif name == 'insertNewIdentifier':
        query = 'INSERT INTO "Identifiers"("UserId", "ItemId") VALUES (?, ?);'

# Update Queries
    elif name == 'updateToken':
        query = 'UPDATE "Users" SET "Token" = ? WHERE "UserId" = ?;'

    elif name == 'updateName':
        query = 'UPDATE "Items" SET "TimeStamp" = ?, "Name" = ?, "SyncMode" = 2 WHERE "UserId" = ? AND "ItemId" = ?;'

    elif name == 'updateSize':
        query = 'UPDATE "Items" SET "TimeStamp" = ?, "Size" = ?, "DateModified" = ?, "SyncMode" = 2 WHERE "UserId" = ? AND "ItemId" = ?;'

    elif name == 'updateTrashed':
        query = 'UPDATE "Items" SET "TimeStamp" = ?, "Trashed" = ?, "SyncMode" = 2 WHERE "UserId" = ? AND "ItemId" = ?;'

    elif name == 'updateConnectionMode':
        query = 'UPDATE "Items" SET "ConnectionMode" = ? WHERE "UserId" = ? AND "ItemId" = ?;'

    elif name == 'updateItemId':
        query = 'UPDATE "Items" SET "ItemId" = ? WHERE "UserId" = ? AND "ItemId" = ?;'

    elif name == 'updateTimeStamp':
        query = 'UPDATE "Users" SET "TimeStamp" = ? WHERE "UserId" = ?;'

# Delete Queries
    elif name == 'deleteNewIdentifier':
        query = 'DELETE FROM "Identifiers" WHERE "UserId" = ? AND "ItemId" = ?;'

# Call Procedure Query
    elif name == 'getItem':
        query = 'CALL "GetItem"(?,?,?)'
    elif name == 'updatePushItems':
        query = 'CALL "UpdatePushItems"(?,?,?)'
    elif name == 'getPushItems':
        query = 'CALL "GetPushItems"(?,?,?)'
    elif name == 'getPushProperties':
        query = 'CALL "GetPushProperties"(?,?,?,?)'
    elif name == 'getItemParentIds':
        query = 'CALL "GetItemParentIds"(?,?,?,?,?)'
    elif name == 'insertUser':
        query = 'CALL "InsertUser"(?,?,?,?,?,?,?,?)'
    elif name == 'mergeItem':
        query = 'CALL "MergeItem"(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
    elif name == 'insertItem':
        query = 'CALL "InsertItem"(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
    elif name == 'updateNewItemId':
        query = 'CALL "UpdateNewItemId"(?,?,?,?,?)'

# ShutDown Queries
    elif name == 'shutdown':
        query = 'SHUTDOWN;'
    elif name == 'shutdownCompact':
        query = 'SHUTDOWN COMPACT;'

# Create View Command called by dbinit.py
    elif name == 'getChildViewCommand':
        query = '''\
SELECT I."UserId", P."ParentId", I."ItemId", I."Name", I."DateCreated", I."DateModified"
  FROM %(Items)s AS I
  INNER JOIN %(Parents)s AS P ON I."ItemId" = P."ItemId"
  WHERE I."Trashed" = FALSE;''' % format

    elif name == 'getTwinViewCommand':
        query = '''\
SELECT C."UserId", C."ParentId", C."Name", ARRAY_AGG(C."ItemId" ORDER BY C."DateCreated", C."DateModified") AS "Indexes"
  FROM %(Child)s AS C
  GROUP BY C."UserId", C."ParentId", C."Name"
  HAVING COUNT(*) > 1;''' % format

    elif name == 'getDuplicateViewCommand':
        query = '''\
SELECT T."UserId", T."ParentId", C."ItemId", "GetUniqueName"(T."Name", POSITION_ARRAY(C."ItemId" IN T."Indexes")) AS "Name"
  FROM %(Twin)s AS T
  JOIN %(Child)s AS C ON T."Name" = C."Name" AND T."ParentId" = C."ParentId";''' % format

    elif name == 'getPathViewCommand':
        query = '''\
WITH RECURSIVE TREE ("UserId", "ParentId", "ItemId", "Name", "Path", "Title") AS
  (
    SELECT U."UserId", U."RootId", C."ItemId", C."Name", CAST('%(Separator)s' AS VARCHAR(1024)), COALESCE(D."Name", C."Name")
    FROM %(Users)s AS U
    INNER JOIN %(Child)s AS C ON U."UserId" = C."UserId" AND U."RootId" = C."ParentId"
    LEFT JOIN %(Duplicate)s AS D ON C."UserId" = D."UserId" AND C."ParentId" = D."ParentId" AND C."ItemId" = D."ItemId"
  UNION
    SELECT C1."UserId", C1."ParentId", C1."ItemId", C1."Name", T."Path" || T."Title" || '%(Separator)s', COALESCE(D1."Name", C1."Name")
    FROM %(Child)s AS C1
    INNER JOIN TREE AS T ON T."UserId" = C1."UserId" AND T."ItemId" = C1."ParentId"
    LEFT JOIN %(Duplicate)s AS D1 ON C1."UserId" = D1."UserId" AND C1."ParentId" = D1."ParentId" AND C1."ItemId" = D1."ItemId"
  )
  SELECT "UserId", "ParentId", "ItemId", "Name", "Path", "Title" FROM TREE;''' % format

    elif name == 'getChildrenViewCommand':
        query = '''\
SELECT C."UserId", C."ItemId", C."ParentId", P."Name", P."Path",
       P."Title", I."Link", I."DateCreated", I."DateModified",
       "GetIsFolder"(I."MediaType") AS "IsFolder", I."MediaType",
       I."Size", I."ConnectionMode"
  FROM %(Path)s AS P
  INNER JOIN %(Child)s AS C ON P."ItemId" = C."ItemId" AND P."ParentId" = C."ParentId"
  INNER JOIN %(Items)s AS I ON C."ItemId" = I."ItemId";''' % format

# Create Function Queries called by dbinit.py
    elif name == 'createGetIsFolder':
        query = '''\
CREATE FUNCTION "GetIsFolder"(IN MIMETYPE VARCHAR(100))
  RETURNS BOOLEAN
  SPECIFIC "GetIsFolder_1"
  CONTAINS SQL
  BEGIN ATOMIC
    RETURN MIMETYPE = '%(UcpFolder)s';
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetIsFolder_1" TO "%(Role)s";''' % format

    elif name == 'createGetContentType':
        query = '''\
CREATE FUNCTION "GetContentType"(IN ISFOLDER BOOLEAN)
  RETURNS VARCHAR(100)
  SPECIFIC "GetContentType_1"
  CONTAINS SQL
  BEGIN ATOMIC
    IF ISFOLDER THEN
      RETURN '%(UcbFolder)s';
    ELSE
      RETURN '%(UcbFile)s';
    END IF;
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetContentType_1" TO "%(Role)s";''' % format

    elif name == 'createGetUniqueName':
        query = '''\
CREATE FUNCTION "GetUniqueName"(IN NAME VARCHAR(100),
                                IN NUMBER INTEGER)
  RETURNS VARCHAR(110)
  SPECIFIC "GetUniqueName_1"
  CONTAINS SQL
  BEGIN ATOMIC
    DECLARE HINT VARCHAR(10);
    DECLARE DOT BIGINT DEFAULT 0;
    SET DOT = POSITION('.' IN REVERSE(NAME));
    SET HINT = '%(Prefix)s' || NUMBER || '%(Suffix)s';
    IF DOT != 0 AND DOT < 5 THEN
      RETURN INSERT(NAME, CHAR_LENGTH(NAME) - DOT + 1, 0, HINT);
    ELSE
      RETURN NAME || HINT;
    END IF;
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetUniqueName_1" TO "%(Role)s";''' % format

# Create Procedure Query called by dbinit.py
    elif name == 'createUpdateNewItemId':
        query = '''\
CREATE PROCEDURE "UpdateNewItemId"(IN USERID VARCHAR(320),
                                   IN OLDID VARCHAR(256),
                                   IN NEWID VARCHAR(256),
                                   IN CREATED TIMESTAMP(6),
                                   IN MODIFIED TIMESTAMP(6))
  SPECIFIC "UpdateNewItemId_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    UPDATE "Items" SET "ItemId" = NEWID, "DateCreated" = CREATED, "DateModified" = MODIFIED WHERE "UserId" = USERID AND "ItemId" = OLDID;
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "UpdateNewItemId_1" TO "%(Role)s";''' % format

    elif name == 'createGetItem':
        query = '''\
CREATE PROCEDURE "GetItem"(IN USERID VARCHAR(320),
                           IN URI VARCHAR(1024),
                           IN ISPATH BOOLEAN)
  SPECIFIC "GetItem_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE "Result" CURSOR WITH RETURN FOR
      SELECT C."ItemId" AS "Id", C."Path", C."ParentId", C."Name",
       C."Title", C."DateCreated", C."DateModified", C."MediaType",
       "GetContentType"(C."IsFolder") AS "ContentType", C."Size", C."Link",
       FALSE AS "Trashed", FALSE AS "IsRoot", C."IsFolder", NOT C."IsFolder"
       AS "IsDocument", C."ConnectionMode", C."ItemId" AS "ObjectId",
       C1."CanAddChild", C1."CanRename", C1."IsReadOnly", C1."IsVersionable",
       FALSE AS "IsHidden", FALSE AS "IsVolume", C."ConnectionMode" < 0 AS "IsRemote",
       FALSE AS "IsRemoveable", FALSE AS "IsFloppy", FALSE AS "IsCompactDisc"
      FROM "Children" AS C
      INNER JOIN "Capabilities" AS C1 ON C."ItemId" = C1."ItemId" 
      WHERE C."UserId" = USERID AND
            ((ISPATH AND C."Path" || C."Title" = URI) OR
             (NOT ISPATH AND C."ItemId" = URI))
      FOR READ ONLY;
    OPEN "Result";
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetItem_1" TO "%(Role)s";''' % format

    elif name == 'createInsertUser':
        query = '''\
CREATE PROCEDURE "InsertUser"(IN USERID VARCHAR(320),
                              IN USERNAME VARCHAR(100),
                              IN DISPLAYNAME VARCHAR(100),
                              IN ROOTID VARCHAR(256),
                              IN SHAREID VARCHAR(256),
                              IN DATECREATED TIMESTAMP(6),
                              IN DATEMODIFIED TIMESTAMP(6),
                              IN DATETIME TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "InsertUser_1"
  MODIFIES SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE RSLT CURSOR WITH RETURN FOR
      SELECT "UserId", "UserName", "RootId", "ShareId", "Token", "DateCreated", "DateModified", "TimeStamp"
      FROM "Users"
      WHERE "UserName" = USERNAME FOR READ ONLY;
    INSERT INTO "Users" ("UserId", "UserName", "DisplayName", "RootId", "ShareId", "DateCreated", "DateModified", "TimeStamp") 
                 VALUES (USERID, USERNAME, DISPLAYNAME, ROOTID, SHAREID, DATECREATED, DATEMODIFIED, DATETIME);
    OPEN RSLT;
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "InsertUser_1" TO "%(Role)s";''' % format

    elif name == 'createUpdatePushItems':
        query = '''\
CREATE PROCEDURE "UpdatePushItems"(IN USERID VARCHAR(320),
                                   IN ITEMS VARCHAR(256) ARRAY,
                                   OUT DATETIME TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "UpdatePushItems_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE TS TIMESTAMP(6) WITH TIME ZONE;
    IF CARDINALITY(ITEMS) > 0 THEN
        UPDATE "Items" SET "SyncMode" = 0 WHERE "UserId" = USERID AND "ItemId" IN (UNNEST(ITEMS));
        SELECT MAX("RowStart") INTO TS FROM "Items" FOR SYSTEM_TIME AS OF CURRENT_TIMESTAMP(6)
        WHERE "UserId" = USERID AND "ItemId" IN (UNNEST(ITEMS));
    END IF;
    SET DATETIME = TS;
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "UpdatePushItems_1" TO "%(Role)s";''' % format

# System Time Period Procedure Queries
    elif name == 'createGetPushItems':
        query = '''\
CREATE PROCEDURE "GetPushItems"(IN USERID VARCHAR(320),
                                IN STARTTIME TIMESTAMP(6) WITH TIME ZONE,
                                IN STOPTIME TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "GetPushItems_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE "Result" CURSOR WITH RETURN FOR
      -- com.sun.star.ucb.ChangeAction.INSERT
      (SELECT I."ItemId" AS "Id", 1 AS "ChangeAction", I."RowStart" AS "TimeStamp" 
        FROM "Items" FOR SYSTEM_TIME FROM STARTTIME TO STOPTIME AS I 
        LEFT JOIN "Items" FOR SYSTEM_TIME FROM STARTTIME TO STOPTIME AS I2 
          ON I."ItemId" = I2."ItemId" AND I."RowStart" = I2."RowEnd" 
        WHERE I2."ItemId" IS NULL AND I."SyncMode" = 1 AND I."UserId" = USERID) 
      UNION
      (SELECT "Id", SUM("ChangeAction"), MAX("TimeStamp") FROM (
        -- com.sun.star.ucb.ChangeAction.UPDATE
        SELECT I."ItemId" AS "Id", 2 AS "ChangeAction", MAX(I."RowEnd") AS "TimeStamp" 
          FROM "Items" FOR SYSTEM_TIME FROM STARTTIME TO STOPTIME AS I 
          INNER JOIN "Items" FOR SYSTEM_TIME FROM STARTTIME TO STOPTIME AS I2 
            ON I."ItemId" = I2."ItemId" AND I2."RowStart" = I."RowEnd" 
          WHERE I2."SyncMode" = 2 AND I."UserId" = USERID GROUP BY "ItemId", "ChangeAction" 
       UNION
        -- com.sun.star.ucb.ChangeAction.MOVE
        SELECT P."ItemId" AS "Id", 4 AS "ChangeAction", MAX(I."RowEnd") AS "TimeStamp" 
          FROM "Parents" FOR SYSTEM_TIME FROM STARTTIME TO STOPTIME AS P 
          INNER JOIN "Items" AS I ON P."ItemId" = I."ItemId"
          INNER JOIN "Parents" FOR SYSTEM_TIME FROM STARTTIME TO STOPTIME AS P2 
            ON P."ItemId" = P2."ItemId" AND P2."RowStart" = P."RowEnd" 
          WHERE P2."SyncMode" = 2 AND I."UserId" = USERID GROUP BY "ItemId", "ChangeAction") 
      GROUP BY "Id")
      UNION
      -- com.sun.star.ucb.ChangeAction.DELETE
      (SELECT I."ItemId" AS "Id", 8 AS "ChangeAction", I."RowEnd" AS "TimeStamp" 
        FROM "Items" FOR SYSTEM_TIME AS OF STARTTIME AS I 
        LEFT JOIN "Items" FOR SYSTEM_TIME FROM STARTTIME TO STOPTIME AS I2 
          ON I."ItemId" = I2."ItemId" 
        WHERE I2."ItemId" IS NULL AND I."UserId" = USERID) 
      ORDER BY "TimeStamp" FOR READ ONLY;
    OPEN "Result";
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetPushItems_1" TO "%(Role)s";''' % format

    elif name == 'createGetPushProperties':
        query = '''\
CREATE PROCEDURE "GetPushProperties"(IN USERID VARCHAR(320),
                                     IN ITEMID VARCHAR(256),
                                     IN STARTTIME TIMESTAMP(6) WITH TIME ZONE,
                                     IN STOPTIME TIMESTAMP(6) WITH TIME ZONE)
  SPECIFIC "GetPushProperties_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE "Result" CURSOR WITH RETURN FOR
      SELECT 1 AS "Properties", MAX(I."RowEnd") AS "TimeStamp" 
        FROM "Items" FOR SYSTEM_TIME FROM STARTTIME TO STOPTIME AS I 
        INNER JOIN "Items" FOR SYSTEM_TIME FROM STARTTIME TO STOPTIME AS I2 
          ON I."ItemId" = I2."ItemId" AND I2."RowStart" = I."RowEnd" 
        WHERE I."UserId" = USERID AND I."ItemId" = ITEMID 
        AND I2."SyncMode" = 2 AND I."Name" <> I2."Name" GROUP BY "Properties"
      UNION
      SELECT 2 AS "Properties", MAX(I."RowEnd") AS "TimeStamp" 
        FROM "Items" FOR SYSTEM_TIME FROM STARTTIME TO STOPTIME AS I 
        INNER JOIN "Items" FOR SYSTEM_TIME FROM STARTTIME TO STOPTIME AS I2 
          ON I."ItemId" = I2."ItemId" AND I2."RowStart" = I."RowEnd" 
        WHERE I."UserId" = USERID AND I."ItemId" = ITEMID 
        AND I2."SyncMode" = 2 AND (I."Size" <> I2."Size" OR I."DateModified" <> I2."DateModified") 
        GROUP BY "Properties"
      UNION
      SELECT 4 AS "Properties", MAX(I."RowEnd") AS "TimeStamp" 
        FROM "Items" FOR SYSTEM_TIME FROM STARTTIME TO STOPTIME AS I 
        INNER JOIN "Items" FOR SYSTEM_TIME FROM STARTTIME TO STOPTIME AS I2 
          ON I."ItemId" = I2."ItemId" AND I2."RowStart" = I."RowEnd" 
        WHERE I."UserId" = USERID AND I."ItemId" = ITEMID 
        AND I2."SyncMode" = 2 AND I."Trashed" <> I2."Trashed" GROUP BY "Properties"
      ORDER BY "TimeStamp" FOR READ ONLY;
    OPEN "Result";
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetPushProperties_1" TO "%(Role)s";''' % format

# Get item parent id Procedure Queries
    elif name == 'createGetItemParentIds':
        query = '''\
CREATE PROCEDURE "GetItemParentIds"(IN ITEMID VARCHAR(256),
                                    IN STARTTIME TIMESTAMP(6) WITH TIME ZONE,
                                    IN STOPTIME TIMESTAMP(6) WITH TIME ZONE,
                                    OUT OLDPARENT VARCHAR(256) ARRAY,
                                    OUT NEWPARENT VARCHAR(256) ARRAY)
  SPECIFIC "GetItemParentIds_1"
  READS SQL DATA
  BEGIN ATOMIC
    DECLARE OLDIDS VARCHAR(256) ARRAY;
    DECLARE NEWIDS VARCHAR(256) ARRAY;
    SELECT ARRAY_AGG("ParentId" ORDER BY "TimeStamp") INTO OLDIDS 
      FROM "Parents" FOR SYSTEM_TIME AS OF STARTTIME 
      WHERE "ItemId" = ITEMID GROUP BY "ItemId";
    SELECT ARRAY_AGG("ParentId" ORDER BY "TimeStamp") INTO NEWIDS 
      FROM "Parents" FOR SYSTEM_TIME AS OF STOPTIME 
      WHERE "ItemId" = ITEMID GROUP BY "ItemId";
    SET OLDPARENT = OLDIDS;
    SET NEWPARENT = NEWIDS;
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "GetItemParentIds_1" TO "%(Role)s";''' % format

    elif name == 'createMergeItem':
        query = '''\
CREATE PROCEDURE "MergeItem"(IN USERID VARCHAR(320),
                             IN PARENTID VARCHAR(256),
                             IN DATETIME TIMESTAMP(6) WITH TIME ZONE,
                             IN CONNECTIONMODE SMALLINT,
                             IN ITEMID VARCHAR(256),
                             IN NAME VARCHAR(100),
                             IN DATECREATED TIMESTAMP(6),
                             IN DATEMODIFIED TIMESTAMP(6),
                             IN MEDIATYPE VARCHAR(100),
                             IN SIZE BIGINT,
                             IN LINK VARCHAR(256),
                             IN TRASHED BOOLEAN,
                             IN CANADDCHILD BOOLEAN,
                             IN CANRENAME BOOLEAN,
                             IN ISREADONLY BOOLEAN,
                             IN ISVERSIONABLE BOOLEAN,
                             IN PARENTS VARCHAR(256) ARRAY,
                             IN PATH VARCHAR(1024))
  SPECIFIC "MergeItem_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE TMP VARCHAR(256) ARRAY;
    DECLARE PARENT VARCHAR(256);
    DECLARE IDX INTEGER DEFAULT 1;
    MERGE INTO "Items" USING (VALUES(USERID, ITEMID, NAME, DATECREATED, DATEMODIFIED, 
                                     MEDIATYPE, SIZE, LINK, TRASHED, CONNECTIONMODE, DATETIME)) 
      AS vals(p,k,r,s,t,u,v,w,x,y,z) ON  "UserId" = vals.p AND "ItemId" = vals.k 
        WHEN MATCHED THEN 
          UPDATE SET "Name" = vals.r, "DateModified" = vals.t, "MediaType" = vals.u, "Size" = vals.v,
                     "Link" = vals.w, "Trashed" = vals.x, "ConnectionMode" = vals.y, "TimeStamp" = vals.z 
        WHEN NOT MATCHED THEN 
          INSERT ("UserId", "ItemId", "Name", "DateCreated", "DateModified", 
                  "MediaType", "Size", "Link", "Trashed", "ConnectionMode", "TimeStamp") 
          VALUES vals.p, vals.k, vals.r, vals.s, vals.t, vals.u, vals.v, vals.w, vals.x, vals.y, vals.z; 
    MERGE INTO "Capabilities" USING (VALUES(USERID, ITEMID, CANADDCHILD, CANRENAME, 
                                            ISREADONLY, ISVERSIONABLE, DATETIME)) 
      AS vals(t,u,v,w,x,y,z) ON "UserId" = vals.t AND "ItemId" = vals.u 
        WHEN MATCHED THEN 
          UPDATE SET "CanAddChild" = vals.v, "CanRename" = vals.w, "IsReadOnly" = vals.x, 
                     "IsVersionable" = vals.y, "TimeStamp" = vals.z 
        WHEN NOT MATCHED THEN 
          INSERT ("UserId","ItemId","CanAddChild","CanRename","IsReadOnly", 
                  "IsVersionable","TimeStamp")
          VALUES vals.t, vals.u, vals.v, vals.w, vals.x, vals.y, vals.z;
    IF PATH IS NULL THEN
      SET TMP = PARENTS;
    ELSE
      SELECT ARRAY_AGG("ItemId") INTO TMP FROM "Path" WHERE "UserId" = USERID AND "Path" || "Title" = PATH;
    END IF;
    DELETE FROM "Parents" WHERE "ParentId" NOT IN (UNNEST(TMP)) AND "ItemId" = ITEMID;
    WHILE IDX <= CARDINALITY(TMP) DO
      IF EXISTS (SELECT 1 FROM "Items" WHERE "UserId" = USERID AND "ItemId" = TMP[IDX]) THEN
        SET PARENT = TMP[IDX];
      ELSE
        SET PARENT = PARENTID;
      END IF;
      MERGE INTO "Parents" USING (VALUES(USERID, ITEMID, PARENT, DATETIME)) 
        AS vals(w,x,y,z) ON "UserId" = vals.w AND "ItemId" = vals.x AND "ParentId" = vals.y 
          WHEN NOT MATCHED THEN 
            INSERT ("UserId","ItemId","ParentId","TimeStamp") 
            VALUES vals.w, vals.x, vals.y, vals.z;
      SET IDX = IDX + 1;
    END WHILE;
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "MergeItem_1" TO "%(Role)s";''' % format

    elif name == 'createInsertItem':
        query = '''\
CREATE PROCEDURE "InsertItem"(IN USERID VARCHAR(320),
                              IN CONNECTIONMODE SMALLINT,
                              IN DATETIME TIMESTAMP(6) WITH TIME ZONE,
                              IN ITEMID VARCHAR(256),
                              IN NAME VARCHAR(100),
                              IN CREATED TIMESTAMP(6),
                              IN MODIFIED TIMESTAMP(6),
                              IN MEDIATYPE VARCHAR(100),
                              IN SIZE BIGINT,
                              IN LINK VARCHAR(256),
                              IN TRASHED BOOLEAN,
                              IN ADDCHILD BOOLEAN,
                              IN CANRENAME BOOLEAN,
                              IN READONLY BOOLEAN,
                              IN ISVERSIONABLE BOOLEAN,
                              IN PARENTID VARCHAR(256))
  SPECIFIC "InsertItem_1"
  MODIFIES SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE "Result" CURSOR WITH RETURN FOR
      SELECT "Name", "Title", "Path"
      FROM "Path"
      WHERE "UserId" = USERID AND "ParentId" = PARENTID AND "ItemId" = ITEMID
    FOR READ ONLY;
    INSERT INTO "Items" ("UserId", "ItemId", "Name", "DateCreated", "DateModified", "MediaType",
                         "Size", "Link", "Trashed", "ConnectionMode", "SyncMode", "TimeStamp")
                 VALUES (USERID, ITEMID, NAME, CREATED, MODIFIED, MEDIATYPE,
                         SIZE, LINK, TRASHED, CONNECTIONMODE, 1, DATETIME);
    INSERT INTO "Capabilities" ("UserId", "ItemId", "CanAddChild", "CanRename",
                                "IsReadOnly", "IsVersionable", "TimeStamp")
                        VALUES (USERID, ITEMID, ADDCHILD, CANRENAME,
                                READONLY, ISVERSIONABLE, DATETIME);
    INSERT INTO "Parents" ("UserId", "ItemId", "ParentId", "TimeStamp", "SyncMode")
                   VALUES (USERID, ITEMID, PARENTID, DATETIME, 1);
    OPEN "Result";
  END;
GRANT EXECUTE ON SPECIFIC ROUTINE "InsertItem_1" TO "%(Role)s";''' % format

# Queries don't exist!!!
    else:
        logger = getLogger(ctx, g_defaultlog, g_basename)
        logger.logprb(SEVERE, g_basename, 'getSqlQuery', 101, name)
        query = None

    return query


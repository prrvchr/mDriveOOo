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

# Create User and Schema Query
    if name == 'createUserSchema':
        query = 'CREATE SCHEMA "%(Schema)s" AUTHORIZATION "%(Name)s";' % format

    elif name == 'setUserSchema':
        query = 'ALTER USER "%(Name)s" SET INITIAL SCHEMA "%(Schema)s";' % format

# Create Dynamic View Queries
    elif name == 'createUserView':
        view = '''\
CREATE VIEW IF NOT EXISTS "%(Schema)s"."%(View)s" AS
  SELECT %(Public)s."%(CardView)s".* FROM %(Public)s."%(CardView)s"
  INNER JOIN %(Public)s."BookCards" ON %(Public)s."%(CardView)s"."Card"=%(Public)s."BookCards"."Card"
  INNER JOIN %(Public)s."Books" ON %(Public)s."BookCards"."Book"=%(Public)s."Books"."Book"
  WHERE %(Public)s."Books"."User"=%(User)s
  ORDER BY %(Public)s."%(CardView)s"."Created";
GRANT SELECT ON "%(Schema)s"."%(View)s" TO "%(Name)s";
'''
        query = view % format

    elif name == 'createBookView':
        view = '''\
CREATE VIEW IF NOT EXISTS "%(Schema)s"."%(Name)s" AS
  SELECT %(Public)s."%(View)s".* FROM %(Public)s."%(View)s"
  INNER JOIN %(Public)s."BookCards" ON %(Public)s."%(View)s"."Card"=%(Public)s."BookCards"."Card"
  INNER JOIN %(Public)s."Books" ON %(Public)s."BookCards"."Book"=%(Public)s."Books"."Book"
  WHERE %(Public)s."Books"."Book"=%(Book)s
  ORDER BY %(Public)s."%(View)s"."Created";
GRANT SELECT ON "%(Schema)s"."%(Name)s" TO "%(User)s";
'''
        query = view % format

    elif name == 'createGroupView':
        view = '''\
CREATE VIEW IF NOT EXISTS "%(Schema)s"."%(Name)s" AS
  SELECT %(Public)s."%(View)s".* FROM %(Public)s."%(View)s"
  INNER JOIN %(Public)s."GroupCards" ON %(Public)s."%(View)s"."Card"=%(Public)s."GroupCards"."Card"
  INNER JOIN %(Public)s."Groups" ON %(Public)s."GroupCards"."Group"=%(Public)s."Groups"."Group"
  WHERE %(Public)s."Groups"."Group"=%(Group)s
  ORDER BY %(Public)s."%(View)s"."Created";
GRANT SELECT ON "%(Schema)s"."%(Name)s" TO "%(User)s";
'''
        query = view % format

    elif name == 'deleteView':
        query = 'DROP VIEW IF EXISTS "%(Schema)s"."%(OldName)s";' % format

# Select Queries
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

# Update Queries
    elif name == 'updateAddressbookToken':
        query = 'UPDATE "Books" SET "Token"=?,"Modified"=DEFAULT WHERE "Book"=?'

# Insert Queries
    elif name == 'insertSuperUser':
        q = """\
INSERT INTO PUBLIC."Users" ("Uri","Scheme","Server","Path","Name") VALUES ('%s','%s','%s','%s','%s');
"""
        query = q % format

    elif name == 'insertSuperAdressbook':
        query = """\
INSERT INTO PUBLIC."Books" ("User","Uri","Name","Tag","Token") VALUES (0,'/','admin','#','#');
"""

    elif name == 'insertSuperGroup':
        query = """\
INSERT INTO PUBLIC."Groups" ("Book","Uri","Name") VALUES (0,'/','#');
"""

# Create Procedure Query
    elif name == 'createSelectUser':
        query = """\
CREATE PROCEDURE "SelectUser"(IN Server VARCHAR(128),
                              IN Name VARCHAR(128),
                              OUT Id INTEGER,
                              OUT Uri VARCHAR(256),
                              OUT Scheme VARCHAR(128),
                              OUT Path VARCHAR(128))
  SPECIFIC "SelectUser_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE RSLT CURSOR WITH RETURN FOR
      SELECT B."Book",B."Uri",B."Name",B."Tag",B."Token"
      FROM "Books" AS B
      INNER JOIN "Users" AS U ON B."User"=U."User"
      WHERE U."Server"=Server AND U."Name"=Name
    FOR READ ONLY;
      SELECT "User","Uri","Scheme","Path" INTO Id,Uri,Scheme,Path FROM "Users"
      WHERE "Server"=Server AND "Name"=Name;
    OPEN RSLT;
  END"""

    elif name == 'createInsertUser':
        query = """\
CREATE PROCEDURE "InsertUser"(IN Uri VARCHAR(256),
                              IN Scheme VARCHAR(128),
                              IN Server VARCHAR(128),
                              IN Path VARCHAR(128),
                              IN Name VARCHAR(128),
                              OUT Id INTEGER)
  SPECIFIC "InsertUser_1"
  MODIFIES SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE RSLT CURSOR WITH RETURN FOR
      SELECT B."Book",B."Uri",B."Name",B."Tag",B."Token"
      FROM "Books" AS B
      INNER JOIN "Users" AS U ON B."User"=U."User"
      WHERE U."Server"=Server AND U."Name"=Name
    FOR READ ONLY;
    INSERT INTO "Users" ("Uri","Scheme","Server","Path","Name") VALUES (Uri,Scheme,Server,Path,Name);
    SET Id = IDENTITY();
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
                             IN Data VARCHAR(100000))
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
      (SELECT U."Name" AS "User", 
              B1."Book", NULL AS "Name", B1."Name" AS "OldName", 
              'Deleted' AS "Query", B1."RowEnd" AS "Order"
      FROM "Books" FOR SYSTEM_TIME AS OF FIRST AS B1
      JOIN "Users" AS U ON B1."User"=U."User"
      LEFT JOIN "Books" FOR SYSTEM_TIME AS OF LAST AS B2
        ON B1."Book" = B2."Book"
      WHERE B1."Book"!=0 AND B2."Book" IS NULL AND U."User"=UID)
      UNION
      (SELECT U."Name" AS "User", 
              B2."Book", B2."Name", NULL AS "OldName", 
              'Inserted' AS "Query", B2."RowStart" AS "Order"
      FROM "Books" FOR SYSTEM_TIME AS OF LAST AS B2
      JOIN "Users" AS U ON B2."User"=U."User"
      LEFT JOIN "Books" FOR SYSTEM_TIME AS OF FIRST AS B1
        ON B2."Book"=B1."Book"
      WHERE B2."Book"!=0 AND  B1."Book" IS NULL AND U."User"=UID)
      UNION
      (SELECT U."Name" AS "User", 
              B2."Book", B2."Name", B1."Name" AS "OldName", 
              'Updated' AS "Query", B1."RowEnd" AS "Order"
      FROM "Books" FOR SYSTEM_TIME AS OF LAST AS B2
      JOIN "Users" AS U ON B2."User"=U."User"
      INNER JOIN "Books" FOR SYSTEM_TIME FROM FIRST TO LAST AS B1
        ON B2."Book"=B1."Book" AND B2."RowStart"=B1."RowEnd"
      WHERE B2."Book"!=0 AND U."User"=UID)
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
CREATE PROCEDURE "SelectChangedGroups"(IN First TIMESTAMP(6) WITH TIME ZONE,
                                       IN Last TIMESTAMP(6) WITH TIME ZONE,
                                       IN Dot INTEGER)
  SPECIFIC "SelectChangedGroups_1"
  MODIFIES SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE RSLT CURSOR WITH RETURN FOR
      (SELECT U."Name" AS "User", 
              REPLACE(U."Name",'.',CHAR(Dot)) AS "Schema", 
              G1."Group", NULL AS "Name", G1."Name" AS "OldName", 
              'Deleted' AS "Query", G1."RowEnd" AS "Order"
      FROM "Groups" FOR SYSTEM_TIME AS OF First AS G1
      JOIN "Books" AS B ON G1."Book"=B."Book"
      JOIN "Users" AS U ON B."User"=U."User"
      LEFT JOIN "Groups" FOR SYSTEM_TIME AS OF Last AS G2
        ON G1."Group" = G2."Group"
      WHERE G1."Group"!=0 AND G2."Group" IS NULL)
      UNION
      (SELECT U."Name" AS "User", 
              REPLACE(U."Name",'.',CHAR(Dot)) AS "Schema", 
              G2."Group", G2."Name", NULL AS "OldName", 
              'Inserted' AS "Query", G2."RowStart" AS "Order"
      FROM "Groups" FOR SYSTEM_TIME AS OF Last AS G2
      JOIN "Books" AS B ON G2."Book"=B."Book"
      JOIN "Users" AS U ON B."User"=U."User"
      LEFT JOIN "Groups" FOR SYSTEM_TIME AS OF First AS G1
        ON G2."Group"=G1."Group"
      WHERE G2."Group"!=0 AND  G1."Group" IS NULL)
      UNION
      (SELECT U."Name" AS "User", 
              REPLACE(U."Name",'.',CHAR(Dot)) AS "Schema", 
              G2."Group", G2."Name", G1."Name" AS "OldName", 
              'Updated' AS "Query", G1."RowEnd" AS "Order"
      FROM "Groups" FOR SYSTEM_TIME AS OF Last AS G2
      JOIN "Books" AS B ON G2."Book"=B."Book"
      JOIN "Users" AS U ON B."User"=U."User"
      INNER JOIN "Groups" FOR SYSTEM_TIME FROM First TO Last AS G1
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
CREATE PROCEDURE "SelectTypes"(IN COMPOSE BOOLEAN)
  SPECIFIC "SelectTypes_1"
  READS SQL DATA
  DYNAMIC RESULT SETS 1
  BEGIN ATOMIC
    DECLARE Rslt CURSOR WITH RETURN FOR 
      SELECT R."Path", R."Name", P."Path", 
      CASE WHEN COMPOSE THEN 
        ARRAY_AGG(JSON_OBJECT(T."Path" || P2."Path": COALESCE(T."Name", '') || P2."Name")) 
      ELSE
        ARRAY_AGG(JSON_OBJECT(T."Path": COALESCE(T."Name", '') || P2."Name")) 
      END
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
CREATE PROCEDURE "SelectGroups"(IN Aid INTEGER)
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

    elif name == 'createMergeGroupMembers':
        query = """\
CREATE PROCEDURE "MergeGroupMembers"(IN GID INTEGER,
                                     IN DATETIME TIMESTAMP(6),
                                     IN MEMBERS VARCHAR(100) ARRAY)
  SPECIFIC "MergeGroupMembers_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE INDEX INTEGER DEFAULT 1;
    DECLARE CID INTEGER DEFAULT NULL;
    DELETE FROM "GroupCards" WHERE "Group" = GID; 
    WHILE INDEX <= CARDINALITY(MEMBERS) DO 
      SELECT "Card" INTO CID FROM "Cards" WHERE "Uri" = MEMBERS[INDEX];
      IF CID IS NOT NULL THEN
        MERGE INTO "GroupCards" USING (VALUES(GID, CID, DATETIME))
          AS vals(x, y, z) ON "Group" = vals.x AND "Card" = vals.y
            WHEN MATCHED THEN UPDATE SET "Modified" = vals.z
            WHEN NOT MATCHED THEN INSERT ("Group", "Card", "Modified")
              VALUES vals.x, vals.y, vals.z;
      END IF;
      SET INDEX = INDEX + 1;
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
      INNER JOIN "Books" AS B ON U."User"=B."User" 
      INNER JOIN "Groups" AS G ON B."Book"=G."Book" 
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

# Get Procedure Query
    elif name == 'selectUser':
        query = 'CALL "SelectUser"(?,?,?,?,?,?)'
    elif name == 'insertUser':
        query = 'CALL "InsertUser"(?,?,?,?,?,?)'
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
        query = 'CALL "SelectTypes"(?)'
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
        query = 'CALL "SelectChangedGroups"(?,?,?)'
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
    elif name == 'mergeGroup':
        query = 'CALL "MergeGroup"(?,?,?,?,?)'

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

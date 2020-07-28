#!
# -*- coding: utf_8 -*-

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from .dbconfig import g_csv

from .logger import logMessage
from .logger import getMessage


def getSqlQuery(name, format=None):


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
    elif name == 'createTableTableColumn1':
        c1 = '"Table" INTEGER NOT NULL'
        c2 = '"Column" INTEGER NOT NULL'
        c3 = '"TypeName" VARCHAR(100) NOT NULL'
        c4 = '"TypeLenght" SMALLINT DEFAULT NULL'
        c5 = '"Default" VARCHAR(100) DEFAULT NULL'
        c6 = '"Options" VARCHAR(100) DEFAULT NULL'
        c7 = '"Primary" BOOLEAN NOT NULL'
        c8 = '"Unique" BOOLEAN NOT NULL'
        c9 = '"ForeignTable" VARCHAR(100) DEFAULT NULL'
        c10 = '"ForeignColumn" VARCHAR(100) DEFAULT NULL'
        k1 = 'PRIMARY KEY("Table","Column")'
        c = (c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, k1)
        query = 'CREATE TEXT TABLE "TableColumn"(%s);' % ','.join(c)
    elif name == 'createTableTableColumn':
        c1 = '"Table" INTEGER NOT NULL'
        c2 = '"Column" INTEGER NOT NULL'
        c3 = '"TypeName" VARCHAR(100) NOT NULL'
        c4 = '"TypeLenght" SMALLINT DEFAULT NULL'
        c5 = '"Default" VARCHAR(100) DEFAULT NULL'
        c6 = '"Options" VARCHAR(100) DEFAULT NULL'
        c7 = '"Primary" BOOLEAN NOT NULL'
        c8 = '"Unique" BOOLEAN NOT NULL'
        c9 = '"ForeignTable" INTEGER DEFAULT NULL'
        c10 = '"ForeignColumn" INTEGER DEFAULT NULL'
        k1 = 'PRIMARY KEY("Table","Column")'
        k2 = 'CONSTRAINT "ForeignTableColumnTable" FOREIGN KEY("Table") REFERENCES '
        k2 += '"Tables"("Table") ON DELETE CASCADE ON UPDATE CASCADE'
        k3 = 'CONSTRAINT "ForeignTableColumnColumn" FOREIGN KEY("Column") REFERENCES '
        k3 += '"Columns"("Column") ON DELETE CASCADE ON UPDATE CASCADE'
        c = (c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, k1, k2, k3)
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

# Create Cached View Queries
    elif name == 'createChildView':
        c1 = '"UserId"'
        c2 = '"ItemId"'
        c3 = '"ParentId"'
        c4 = '"Title"'
        c = (c1,c2,c3,c4)
        s1 = '"P"."UserId"'
        s2 = '"I"."ItemId"'
        s3 = '"P"."ItemId"'
        s4 = '"I"."Title"'
        s = (s1,s2,s3,s4)
        f1 = '"Items" AS "I"'
        f2 = 'JOIN "Parents" AS "P" ON "I"."ItemId"="P"."ChildId"'
        f = (f1,f2)
        p = (','.join(c), ','.join(s), ' '.join(f))
        query = 'CREATE VIEW "Child" (%s) AS SELECT %s FROM %s;' % p
        query += 'GRANT SELECT ON "Child" TO "%(Role)s";' % format
    elif name == 'createTwinView':
        c1 = '"Idx"'
        c2 = '"ParentId"'
        c3 = '"Title"'
        c = (c1,c2,c3)
        s1 = 'ARRAY_AGG("ItemId" ORDER BY "ItemId")'
        s2 = '"ParentId"'
        s3 = '"Title"'
        s = (s1,s2,s3)
        f =  '"Child"'
        g1 = '"Title"'
        g2 = '"ParentId"'
        g = (g1,g2)
        h = 'COUNT(*) > 1'
        p = (','.join(c), ','.join(s), f, ','.join(g), h)
        query = 'CREATE VIEW "Twin" (%s) AS SELECT %s FROM %s GROUP BY %s HAVING %s;' % p
        query += 'GRANT SELECT ON "Twin" TO "%(Role)s";' % format
    elif name == 'createUriView':
        c1 = '"ItemId"'
        c2 = '"ParentId"'
        c3 = '"Title"'
        c4 = '"Length"'
        c5 = '"Position"'
        c = (c1,c2,c3,c4,c5)
        s1 = '"C"."ItemId"'
        s2 = '"T"."ParentId"'
        s3 = '"T"."Title"'
        s4 = 'CARDINALITY("T"."Idx")'
        s5 = 'POSITION_ARRAY("C"."ItemId" IN "T"."Idx")'
        s = (s1,s2,s3,s4,s5)
        f1 =  '"Twin" AS "T" JOIN "Child" AS "C"'
        f2 = 'ON "T"."Title"="C"."Title" AND "T"."ParentId"="C"."ParentId"'
        f = (f1,f2)
        p = (','.join(c), ','.join(s), ' '.join(f))
        query = 'CREATE VIEW "Uri" (%s) AS SELECT %s FROM %s;' % p
        query += 'GRANT SELECT ON "Uri" TO "%(Role)s";' % format
    elif name == 'createTileView':
        c1 = '"ItemId"'
        c2 = '"ParentId"'
        c3 = '"Title"'
        c = (c1,c2,c3)
        s1 = '"U"."ItemId"'
        s2 = '"U"."ParentId"'
        s3 = 'INSERT("U"."Title", LENGTH("U"."Title") - POSITION(%s IN REVERSE("U"."Title")) + 1,0,CONCAT(%s,"U"."Position"))'
        s = (s1,s2,s3 % ("'.'", "'~'"))
        f =  '"Uri" AS "U"'
        p = (','.join(c), ','.join(s), f)
        query = 'CREATE VIEW "Title" (%s) AS SELECT %s FROM %s;' % p
        query += 'GRANT SELECT ON "Title" TO "%(Role)s";' % format
    elif name == 'createItemView':
        c1 = '"ItemId"'
        c2 = '"ContentType"'
        c3 = '"IsFolder"'
        c4 = '"IsLink"'
        c5 = '"IsDocument"'
        c = (c1,c2,c3,c4,c5)
        s0 = '"I"."MediaType"'
        s1 = '"I"."ItemId"'
        s2 = 'CASE WHEN %s IN ("S"."Value2","S"."Value3") THEN %s ELSE "S"."Value1" END' % (s0, s0)
        s3 = '%s="S"."Value2"' % s0
        s4 = '%s="S"."Value3"' % s0
        s5 = '%s!="S"."Value2" AND %s!="S"."Value3"' % (s0, s0)
        s = (s1,s2,s3,s4,s5)
        f = '"Settings" AS "S","Items" AS "I"'
        w = '"S"."Name"=%s' % "'ContentType'"
        p = (','.join(c), ','.join(s), f, w)
        query = 'CREATE VIEW "Item" (%s) AS SELECT %s FROM %s WHERE %s;' % p
        query += 'GRANT SELECT ON "Item" TO "%(Role)s";' % format
    elif name == 'createChildrenView':
        c1 = '"UserId"'
        c2 = '"ItemId"'
        c3 = '"ParentId"'
        c4 = '"Title"'
        c5 = '"Uri"'
        c6 = '"DateCreated"'
        c7 = '"DateModified"'
        c8= '"IsFolder"'
        c9 = '"Size"'
        c10 = '"Loaded"'
        c = (c1,c2,c3,c4,c5,c6,c7,c8,c9,c10)
        s1 = '"C"."UserId"'
        s2 = '"C"."ItemId"'
        s3 = '"C"."ParentId"'
        s4 = '"I"."Title"'
        s5 = 'COALESCE("T"."Title","I"."Title")'
        s6 = '"I"."DateCreated"'
        s7 = '"I"."DateModified"'
        s8 = '"I1"."IsFolder"'
        s9 = '"I"."Size"'
        s10 = '"I"."Loaded"'
        s = (s1,s2,s3,s4,s5,s6,s7,s8,s9,s10)
        f1 = '"Items" AS "I" '
        f2 = 'INNER JOIN "Item" AS "I1" ON "I"."ItemId"="I1"."ItemId"'
        f3 = 'INNER JOIN "Child" AS "C" ON "I1"."ItemId"="C"."ItemId"'
        f4 = 'LEFT JOIN "Title" AS "T" ON "C"."ItemId"="T"."ItemId" AND "C"."ParentId"="T"."ParentId"'
        f = (f1,f2,f3,f4)
        p = (','.join(c), ','.join(s), ' '.join(f))
        query = 'CREATE VIEW "Children" (%s) AS SELECT %s FROM %s;' % p
        query += 'GRANT SELECT ON "Children" TO "%(Role)s";' % format

# Create User
    elif name == 'createUser':
        q = 'CREATE USER "%(User)s" PASSWORD \'%(Password)s\''
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
    elif name == 'getTableName':
        query = 'SELECT "Name" FROM "Tables" ORDER BY "Table";'
    elif name == 'getTables':
        s1 = '"T"."Table" AS "TableId"'
        s2 = '"C"."Column" AS "ColumnId"'
        s3 = '"T"."Name" AS "Table"'
        s4 = '"C"."Name" AS "Column"'
        s5 = '"TC"."TypeName" AS "Type"'
        s6 = '"TC"."TypeLenght" AS "Lenght"'
        s7 = '"TC"."Default"'
        s8 = '"TC"."Options"'
        s9 = '"TC"."Primary"'
        s10 = '"TC"."Unique"'
        s11 = '"TC"."ForeignTable" AS "ForeignTableId"'
        s12 = '"TC"."ForeignColumn" AS "ForeignColumnId"'
        s13 = '"T2"."Name" AS "ForeignTable"'
        s14 = '"C2"."Name" AS "ForeignColumn"'
        s15 = '"T"."View"'
        s16 = '"T"."Versioned"'
        s = (s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14,s15,s16)
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
        query = 'SELECT "Value2" "Folder","Value3" "Link" FROM "Settings" WHERE "Name"=\'ContentType\';'
    elif name == 'getUserTimeStamp':
        query = 'SELECT "TimeStamp" FROM "Users" WHERE "UserId"=?;'
    elif name == 'getUser':
        c1 = '"U"."UserId"'
        c2 = '"U"."UserName"'
        c3 = '"U"."RootId"'
        c4 = '"U"."Token"'
        c5 = '"I"."Title" "RootName"'
        c = (c1, c2, c3, c4, c5)
        f = '"Users" "U" JOIN "Items" "I" ON "U"."RootId" = "I"."ItemId"'
        p = (','.join(c), f)
        query = 'SELECT %s FROM %s WHERE "U"."UserName" = ?;' % p
    elif name == 'getRoot':
        c1 = '"I"."ItemId" "Id"'
        c2 = '"I"."ItemId" "ObjectId"'
        c3 = '"I"."Title"'
        c4 = '"I"."Title" "TitleOnServer"'
        c5 = '"I"."DateCreated"'
        c6 = '"I"."DateModified"'
        c7 = '"I1"."ContentType"'
        c8 = '"I"."MediaType"'
        c9 = '"I"."Size"'
        c10 = '"I"."Trashed"'
        c11 = 'TRUE "IsRoot"'
        c12 = '"I1"."IsFolder"'
        c13 = '"I1"."IsDocument"'
        c14 = '"C"."CanAddChild"'
        c15 = '"C"."CanRename"'
        c16 = '"C"."IsReadOnly"'
        c17 = '"C"."IsVersionable"'
        c18 = '"I"."Loaded"'
        c19 = '%s "CasePreservingURL"' % "''"
        c20 = 'FALSE "IsHidden"'
        c21 = 'FALSE "IsVolume"'
        c22 = 'FALSE "IsRemote"'
        c23 = 'FALSE "IsRemoveable"'
        c24 = 'FALSE "IsFloppy"'
        c25 = 'FALSE "IsCompactDisc"'
        c = (c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12,c13,c14,c15,c16,c17,c18,c19,c20,c21,c22,c23,c24,c25)
        f1 = '"Items" AS "I"'
        f2 = 'INNER JOIN "Item" AS "I1" ON "I"."ItemId"="I1"."ItemId"'
        f3 = 'INNER JOIN "Capabilities" AS "C" ON "I1"."ItemId"="C"."ItemId"'
        f = (f1,f2,f3)
        p = (','.join(c), ' '.join(f))
        query = 'SELECT %s FROM %s WHERE "C"."UserId" = ? AND "C"."ItemId" = ?;' % p
    elif name == 'getItem':
        c1 = '"I"."ItemId" "Id"'
        c2 = '"I"."ItemId" "ObjectId"'
        c3 = 'COALESCE("T"."Title","I"."Title") "Title"'
        c4 = '"I"."Title" "TitleOnServer"'
        c5 = '"I"."DateCreated"'
        c6 = '"I"."DateModified"'
        c7 = '"I1"."ContentType"'
        c8 = '"I"."MediaType"'
        c9 = '"I"."Size"'
        c10 = '"I"."Trashed"'
        c11 = 'FALSE "IsRoot"'
        c12 = '"I1"."IsFolder"'
        c13 = '"I1"."IsDocument"'
        c14 = '"C"."CanAddChild"'
        c15 = '"C"."CanRename"'
        c16 = '"C"."IsReadOnly"'
        c17 = '"C"."IsVersionable"'
        c18 = '"I"."Loaded"'
        c19 = '%s "CasePreservingURL"' % "''"
        c20 = 'FALSE "IsHidden"'
        c21 = 'FALSE "IsVolume"'
        c22 = 'FALSE "IsRemote"'
        c23 = 'FALSE "IsRemoveable"'
        c24 = 'FALSE "IsFloppy"'
        c25 = 'FALSE "IsCompactDisc"'
        c = (c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12,c13,c14,c15,c16,c17,c18,c19,c20,c21,c22,c23,c24,c25)
        f1 = '"Items" AS "I"'
        f2 = 'INNER JOIN "Item" AS "I1" ON "I"."ItemId"="I1"."ItemId"'
        f3 = 'INNER JOIN "Capabilities" AS "C" ON "I1"."ItemId"="C"."ItemId"'
        f4 = 'INNER JOIN "Child" AS "C1" ON "C"."UserId"="C1"."UserId" AND "C"."ItemId"="C1"."ItemId"'
        f5 = 'LEFT JOIN "Title" AS "T" ON "C1"."ItemId"="T"."ItemId" AND "C1"."ParentId"="T"."ParentId"'
        f = (f1,f2,f3,f4,f5)
        p = (','.join(c), ' '.join(f))
        query = 'SELECT %s FROM %s WHERE "C1"."UserId" = ? AND "C1"."ItemId" = ? AND "C1"."ParentId" = ?;' % p
    elif name == 'getChildren':
        c1 = '"Title"'
        c2 = '"Size"'
        c3 = '"DateModified"'
        c4 = '"DateCreated"'
        c5 = '"IsFolder"'
        c6 = '? || "Uri" "TargetURL"'
        c7 = 'FALSE "IsHidden"'
        c8 = 'FALSE "IsVolume"'
        c9 = 'FALSE "IsRemote"'
        c10 = 'FALSE "IsRemoveable"'
        c11 = 'FALSE "IsFloppy"'
        c12 = 'FALSE "IsCompactDisc"'
        c = (c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12)
        w = '"UserId" = ? AND "ParentId" = ? AND ("IsFolder" = TRUE OR "Loaded" >= ?)'
        p = (','.join(c), w)
        query = 'SELECT %s FROM "Children" WHERE %s;' % p
    elif name == 'getChildId':
        w = '"UserId" = ? AND "ParentId" = ? AND "Uri" = ?'
        query = 'SELECT "ItemId" FROM "Children" WHERE %s;' % w
    elif name == 'getNewIdentifier':
        query = 'SELECT "ItemId" FROM "Identifiers" WHERE "UserId" = ? ORDER BY "TimeStamp","ItemId" LIMIT 1;'
    elif name == 'countNewIdentifier':
        query = 'SELECT COUNT("ItemId") "Ids" FROM "Identifiers" WHERE "UserId" = ?;'
    elif name == 'countChildTitle':
        w = '"UserId" = ? AND "ParentId" = ? AND "Title" = ?'
        query = 'SELECT COUNT("Title") FROM "Child" WHERE %s;' % w
    elif name == 'getToken':
        query = 'SELECT "Token" FROM "Users" WHERE "UserId" = ?;'

# System Time Period Select Queries
    elif name == 'getSyncItems':
        c0 = '"ParentId"'
        c1 = '"UserName"'
        c2 = '"Id"'
        c3 = '"Title"'
        c4 = '"DateCreated"'
        c5 = '"DateModified"'
        c6 = '"MediaType"'
        c7 = '"Size"'
        c8 = '"Trashed"'
        c9 = 'GROUP_CONCAT(%s SEPARATOR \'","\') %s' % (c0, c0)
        c10 = '"TimeStamp"'
        c11 = '"TitleUpdated"'
        c12 = '"SizeUpdated"'
        c13 = '"TrashedUpdated"'
        c14 = 'EVERY("AtRoot") "AtRoot"'
        c15 = '"Users"."RootId" = "Parents"."ItemId" "AtRoot"'
        c101 = '"Users".%s %s' % (c1, c1)
        c102 = '"Items"."ItemId" %s' % c2
        c103 = '"Items".%s' % c3
        c104 = '"Items".%s' % c4
        c105 = '"Items".%s' % c5
        c106 = '"Items".%s' % c6
        c107 = '"Items".%s' % c7
        c108 = '"Items".%s' % c8
        c109 = '"Parents"."ItemId" %s' % c0
        c110 = '"Before".%s %s' % (c10, c10)
        c111 = '"Items".%s <> "Before".%s %s' % (c3, c3, c11)
        c112 = '"Items".%s <>  "Before".%s AND "Before".%s = 0 %s' % (c7, c7, c7, c12)
        c113 = '"Items".%s <>  "Before".%s %s' % (c8,c8, c13)
        c210 = '"Previous".%s %s' % (c10, c10)
        c211 = 'TRUE %s' % c11
        c212 = 'TRUE %s' % c12
        c213 = 'TRUE %s' % c13
        columns0 = ','.join((c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12,c13,c14))
        columns1 = ','.join((c101,c102,c103,c104,c105,c106,c107,c108,c109,c110,c111,c112,c113,c15))
        columns2 = ','.join((c101,c102,c103,c104,c105,c106,c107,c108,c109,c210,c211,c212,c213,c15))
        groups = ','.join((c1,c2,c3,c4,c5,c6,c7,c8,c10,c11,c12,c13))
        query = '''\
SELECT %s FROM
((SELECT %s FROM "Items"
INNER JOIN
"Capabilities" FOR SYSTEM_TIME AS OF ? + SESSION_TIMEZONE() AS "Current"
ON "Items"."ItemId" = "Current"."ItemId"
INNER JOIN
"Parents"
ON "Current"."UserId" = "Parents"."UserId" AND "Current"."ItemId" = "Parents"."ChildId"
INNER JOIN 
"Users" 
ON "Parents"."UserId" = "Users"."UserId" 
INNER JOIN
"Capabilities" FOR SYSTEM_TIME FROM ? + SESSION_TIMEZONE() TO ? + SESSION_TIMEZONE() AS "Previous"
ON "Current"."UserId" = "Previous"."UserId" AND "Current"."ItemId" = "Previous"."ItemId"
AND "Current"."RowStart" = "Previous"."RowEnd"
LEFT JOIN
"Items" FOR SYSTEM_TIME FROM ? + SESSION_TIMEZONE() TO ? + SESSION_TIMEZONE() AS "After"
ON "Previous"."ItemId" = "After"."ItemId"
LEFT JOIN
"Items" FOR SYSTEM_TIME FROM ? + SESSION_TIMEZONE() TO ? + SESSION_TIMEZONE() AS "Before"
ON "After"."ItemId" = "Before"."ItemId" AND "After"."RowStart" = "Before"."RowEnd")
UNION 
(SELECT %s FROM "Items"
INNER JOIN
"Capabilities" FOR SYSTEM_TIME AS OF ? + SESSION_TIMEZONE() AS "Current"
ON "Items"."ItemId" = "Current"."ItemId"
INNER JOIN
"Parents"
ON "Current"."UserId" = "Parents"."UserId" AND "Current"."ItemId" = "Parents"."ChildId"
INNER JOIN 
"Users" 
ON "Parents"."UserId" = "Users"."UserId" 
LEFT JOIN
"Capabilities" FOR SYSTEM_TIME AS OF ? + SESSION_TIMEZONE() AS "Previous"
ON "Current"."UserId" = "Previous"."UserId" AND "Current"."ItemId" = "Previous"."ItemId"
WHERE "Previous"."UserId" IS NULL AND "Previous"."ItemId" IS NULL))
GROUP BY %s
ORDER BY "TimeStamp";''' % (columns0, columns1, columns2, groups)

# Insert Queries
    elif name == 'insertUser':
        c = '"UserName","DisplayName","RootId","TimeStamp","UserId"'
        query = 'INSERT INTO "Users" (%s) VALUES (?,?,?,?,?);' % c
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
CREATE PROCEDURE "GetIdentifier"(IN "UserId" VARCHAR(100),
                                 IN "RootId" VARCHAR(100),
                                 IN "UriPath" VARCHAR(500),
                                 IN "Separator" VARCHAR(1),
                                 OUT "ItemId" VARCHAR(100),
                                 OUT "ParentId" VARCHAR(100),
                                 OUT "BaseUri" VARCHAR(500))
  SPECIFIC "GetIdentifier_1"
  READS SQL DATA
  BEGIN ATOMIC
    DECLARE "Index" INTEGER DEFAULT 1;
    DECLARE "Pattern" VARCHAR(5) DEFAULT '[^$]+';
    DECLARE "Paths" VARCHAR(100) ARRAY[50];
    DECLARE "Length" INTEGER DEFAULT 0;
    DECLARE "Item" VARCHAR(100);
    DECLARE "Parent" VARCHAR(100);
    DECLARE "Uri" VARCHAR(500) DEFAULT '';
    SET "Pattern" = REPLACE("Pattern", '$', "Separator");
    SET "Paths" = REGEXP_SUBSTRING_ARRAY("UriPath", "Pattern");
    SET "Length" = CARDINALITY("Paths");
    IF "Length" = 0 THEN
      SET "Item" = "RootId";
      SET "ParentId" = NULL;
    ELSE
      SET "Parent" = "RootId";
      SET "ParentId" = "RootId";
      loop_label: WHILE "Index" <= "Length" DO
        SET "Item" = NULL;
        SET "Item" = SELECT "ItemId" FROM "Children"
        WHERE "ParentId" = "Parent" AND "Uri" = "Paths"["Index"];
        IF "Item" IS NULL THEN
          LEAVE loop_label;
        ELSE
          IF "Index" = 1 AND "Length" > 1 THEN
            SET "Uri" = "Paths"["Index"];
          ELSEIF "Index" < "Length" THEN
            SET "Uri" = "Uri" || "Separator" || "Paths"["Index"];
          END IF;
          IF "Index" = "Length" - 1 THEN
            SET "ParentId" = "Item";
          END IF;
          SET "Parent" = "Item";
          SET "Index" = "Index" + 1;
        END IF;
      END WHILE loop_label;
    END IF;
    SET "ItemId" = "Item";
    SET "BaseUri" = "Uri";
  END;
  GRANT EXECUTE ON SPECIFIC ROUTINE "GetIdentifier_1" TO "%(Role)s";''' % format

    elif name == 'createMergeItem':
        query = '''\
CREATE PROCEDURE "MergeItem"(IN "UserId" VARCHAR(100),
                             IN "Separator" VARCHAR(1),
                             IN "Loaded" SMALLINT,
                             IN "TimeStamp" TIMESTAMP(6),
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
                             IN "ParentIds" VARCHAR(1000))
  SPECIFIC "MergeItem_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE "Index" INTEGER DEFAULT 1;
    DECLARE "Pattern" VARCHAR(5) DEFAULT '[^$]+';
    DECLARE "Parents" VARCHAR(100) ARRAY[100];
    SET "Pattern" = REPLACE("Pattern", '$', "Separator");
    SET "Parents" = REGEXP_SUBSTRING_ARRAY("ParentIds", "Pattern");
    MERGE INTO "Items" USING (VALUES("ItemId","Title","DateCreated","DateModified",
      "MediaType","Size","Trashed","Loaded","TimeStamp"))
      AS vals(r,s,t,u,v,w,x,y,z) ON "Items"."ItemId"=vals.r
        WHEN MATCHED THEN UPDATE
          SET "Title"=vals.s, "DateCreated"=vals.t, "DateModified"=vals.u, "MediaType"=vals.v,
          "Size"=vals.w, "Trashed"=vals.x, "Loaded"=vals.y, "TimeStamp"=vals.z
        WHEN NOT MATCHED THEN INSERT ("ItemId","Title","DateCreated","DateModified",
        "MediaType","Size","Trashed","Loaded","TimeStamp")
          VALUES vals.r, vals.s, vals.t, vals.u, vals.v, vals.w, vals.x, vals.y, vals.z;
    MERGE INTO "Capabilities" USING (VALUES("UserId","ItemId","CanAddChild","CanRename",
      "IsReadOnly","IsVersionable","TimeStamp"))
      AS vals(t,u,v,w,x,y,z) ON "Capabilities"."UserId"=vals.t AND "Capabilities"."ItemId"=vals.u
        WHEN MATCHED THEN UPDATE
          SET "CanAddChild"=vals.v, "CanRename"=vals.w, "IsReadOnly"=vals.x, "IsVersionable"=vals.y, "TimeStamp"=vals.z
        WHEN NOT MATCHED THEN INSERT ("UserId","ItemId","CanAddChild","CanRename","IsReadOnly",
        "IsVersionable","TimeStamp")
          VALUES vals.t, vals.u, vals.v, vals.w, vals.x, vals.y, vals.z;
    DELETE FROM "Parents" WHERE "UserId"="UserId" AND "ChildId"="ItemId";
    WHILE "Index" <= CARDINALITY("Parents") DO
      INSERT INTO "Parents" ("UserId","ChildId","ItemId","TimeStamp") VALUES ("UserId","ItemId",
      "Parents"["Index"],"TimeStamp");
      SET "Index" = "Index" + 1;
    END WHILE;
  END;
  GRANT EXECUTE ON SPECIFIC ROUTINE "MergeItem_1" TO "%(Role)s";''' % format

    elif name == 'createInsertItem':
        query = '''\
CREATE PROCEDURE "InsertItem"(IN "UserId" VARCHAR(100),
                              IN "Separator" VARCHAR(1),
                              IN "Loaded" SMALLINT,
                              IN "TimeStamp" TIMESTAMP(6),
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
                              IN "ParentIds" VARCHAR(1000))
  SPECIFIC "InsertItem_1"
  MODIFIES SQL DATA
  BEGIN ATOMIC
    DECLARE "Index" INTEGER DEFAULT 1;
    DECLARE "Pattern" VARCHAR(5) DEFAULT '[^$]+';
    DECLARE "Parents" VARCHAR(100) ARRAY[100];
    SET "Pattern" = REPLACE("Pattern", '$', "Separator");
    SET "Parents" = REGEXP_SUBSTRING_ARRAY("ParentIds", "Pattern");
    INSERT INTO "Items" ("ItemId","Title","DateCreated","DateModified","MediaType",
      "Size","Trashed","Loaded","TimeStamp") VALUES ("ItemId","Title","DateCreated","DateModified",
      "MediaType","Size","Trashed","Loaded","TimeStamp");
    INSERT INTO "Capabilities" ("UserId","ItemId","CanAddChild","CanRename","IsReadOnly",
      "IsVersionable","TimeStamp") VALUES ("UserId","ItemId","CanAddChild","CanRename","IsReadOnly",
      "IsVersionable","TimeStamp");
    WHILE "Index" <= CARDINALITY("Parents") DO
      INSERT INTO "Parents" ("UserId","ChildId","ItemId","TimeStamp") VALUES ("UserId","ItemId",
      "Parents"["Index"],"TimeStamp");
      SET "Index" = "Index" + 1;
    END WHILE;
  END;
  GRANT EXECUTE ON SPECIFIC ROUTINE "InsertItem_1" TO "%(Role)s";''' % format

# Get Procedure Query
    elif name == 'getIdentifier':
        query = 'CALL "GetIdentifier"(?,?,?,?,?,?,?)'
    elif name == 'mergeItem':
        query = 'CALL "MergeItem"(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
    elif name == 'insertItem':
        query = 'CALL "InsertItem"(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'

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
        query = None
        msg = "dbqueries.getSqlQuery(): ERROR: Query '%s' not found!!!" % name
        print(msg)
        #logMessage(ctx, SEVERE, msg, 'dbqueries', 'getSqlQuery()')
    return query

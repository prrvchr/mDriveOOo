#!
# -*- coding: utf_8 -*-

from .dbconfig import g_csv


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
        query = 'CREATE TEXT TABLE "Tables"(%s)' % ','.join(c)
    elif name == 'createTableColumns':
        c1 = '"Column" INTEGER NOT NULL PRIMARY KEY'
        c2 = '"Name" VARCHAR(100) NOT NULL'
        k1 = 'CONSTRAINT "UniqueColumnsName" UNIQUE("Name")'
        c = (c1, c2, k1)
        query = 'CREATE TEXT TABLE "Columns"(%s)' % ','.join(c)
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
        query = 'CREATE TEXT TABLE "TableColumn"(%s)' % ','.join(c)
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
        query = 'CREATE TEXT TABLE "TableColumn"(%s)' % ','.join(c)
    elif name == 'createTableSettings':
        c1 = '"Id" INTEGER NOT NULL PRIMARY KEY'
        c2 = '"Name" VARCHAR(100) NOT NULL'
        c3 = '"Value1" VARCHAR(100) NOT NULL'
        c4 = '"Value2" VARCHAR(100) DEFAULT NULL'
        c5 = '"Value3" VARCHAR(100) DEFAULT NULL'
        c = (c1, c2, c3, c4, c5)
        p = ','.join(c)
        query = 'CREATE TEXT TABLE "Settings"(%s)' % p
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

# Create Cached View Queries
    elif name == 'createItemView':
        c1 = '"UserId"'
        c2 = '"ItemId"'
        c3 = '"Title"'
        c4 = '"DateCreated"'
        c5 = '"DateModified"'
        c6 = '"MediaType"'
        c7 = '"ContentType"'
        c8 = '"IsFolder"'
        c9 = '"IsLink"'
        c10 = '"IsDocument"'
        c11 = '"Size"'
        c12 = '"Trashed"'
        c13 = '"Loaded"'
        c14 = '"CanAddChild"'
        c15 = '"CanRename"'
        c16 = '"IsReadOnly"'
        c17 = '"IsVersionable"'
        c18 = '"IsRoot"'
        c19 = '"RootId"'
        c = (c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12,c13,c14,c15,c16,c17,c18,c19)
        s1 = '"U"."UserId"'
        s2 = '"I"."ItemId"'
        s3 = '"I"."Title"'
        s4 = '"I"."DateCreated"'
        s5 = '"I"."DateModified"'
        s6 = '"I"."MediaType"'
        s7 = 'CASE WHEN %s IN ("S"."Value2","S"."Value3") THEN %s ELSE "S"."Value1" END' % (s6, s6)
        s8 = '"I"."MediaType"="S"."Value2"'
        s9 = '"I"."MediaType"="S"."Value3"'
        s10 = '"I"."MediaType"!="S"."Value2" AND "I"."MediaType"!="S"."Value3"'
        s11 = '"I"."Size"'
        s12 = '"I"."Trashed"'
        s13 = '"I"."Loaded"'
        s14 = '"C"."CanAddChild"'
        s15 = '"C"."CanRename"'
        s16 = '"C"."IsReadOnly"'
        s17 = '"C"."IsVersionable"'
        s18 = '"I"."ItemId"="U"."RootId"'
        s19 = '"U"."RootId"'
        s = (s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14,s15,s16,s17,s18,s19)
        f = '"Settings" AS "S","Items" AS "I" JOIN "Capabilities" AS "C" '
        f += 'ON "I"."ItemId"="C"."ItemId" JOIN "Users" AS "U" ON "C"."UserId"="U"."UserId"'
        w = '"S"."Name"=\'ContentType\''
        p = (','.join(c), ','.join(s), f, w)
        query = 'CREATE VIEW "Item" (%s) AS SELECT %s FROM %s WHERE %s' % p
    elif name == 'createChildView':
        c1 = '"UserId"'
        c2 = '"ItemId"'
        c3 = '"ParentId"'
        c4 = '"Title"'
        c5 = '"DateCreated"'
        c6 = '"DateModified"'
        c7= '"IsFolder"'
        c8 = '"Size"'
        c9 = '"IsHidden"'
        c10 = '"IsVolume"'
        c11 = '"IsRemote"'
        c12 = '"IsRemoveable"'
        c13 = '"IsFloppy"'
        c14 = '"IsCompactDisc"'
        c15 = '"Loaded"'
        c = (c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12,c13,c14,c15)
        s1 = '"I"."UserId"'
        s2 = '"I"."ItemId"'
        s3 = '"P"."ItemId"'
        s4 = '"I"."Title"'
        s5 = '"I"."DateCreated"'
        s6 = '"I"."DateModified"'
        s7 = '"I"."IsFolder"'
        s8 = '"I"."Size"'
        s9 = 'FALSE'
        s10 = 'FALSE'
        s11 = 'FALSE'
        s12 = 'FALSE'
        s13 = 'FALSE'
        s14 = 'FALSE'
        s15 = '"I"."Loaded"'
        s = (s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14,s15)
        f = '"Item" AS "I" JOIN "Parents" AS "P" '
        f += 'ON "I"."UserId"="P"."UserId" AND "I"."ItemId"="P"."ChildId"'
        p = (','.join(c), ','.join(s), f)
        query = 'CREATE VIEW "Child" (%s) AS SELECT %s FROM %s' % p
    elif name == 'createSyncView':
        c1 = '"SyncId"'
        c2 = '"UserId"'
        c3 = '"Id"'
        c4 = '"ParentId"'
        c5 = '"Title"'
        c6 = '"DateCreated"'
        c7 = '"DateModified"'
        c8 = '"MediaType"'
        c9 = '"IsFolder"'
        c10 = '"Size"'
        c11 = '"Trashed"'
        c12 = '"Mode"'
        c13 = '"IsRoot"'
        c14 = '"AtRoot"'
        c = (c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12,c13,c14)
        s1 = '"S"."SyncId"'
        s2 = '"S"."UserId"'
        s3 = '"S"."ItemId"'
        s4 = '"S"."ParentId"'
        s5 = '"I"."Title"'
        s6 = '"I"."DateCreated"'
        s7 = '"I"."DateModified"'
        s8 = '"I"."MediaType"'
        s9 = '"I"."IsFolder"'
        s10 = '"I"."Size"'
        s11 = '"I"."Trashed"'
        s12 = '"S"."SyncMode"'
        s13 = '"I"."IsRoot"'
        s14 = '"S"."ParentId"="I"."RootId"'
        s = (s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14)
        f =  '"Synchronizes" AS "S" JOIN "Item" AS "I" '
        f += 'ON "S"."ItemId"="I"."ItemId" AND "S"."UserId"="I"."UserId"'
        p = (','.join(c), ','.join(s), f)
        query = 'CREATE VIEW "Sync" (%s) AS SELECT %s FROM %s' % p

# Select Queries
    elif name == 'getTableName':
        query = 'SELECT "Name" FROM "Tables" ORDER BY "Table"'
    elif name == 'getTables1':
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
        s11 = '"TC"."ForeignTable"'
        s12 = '"TC"."ForeignColumn"'
        s = (s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12)
        f1 = '"Tables" AS "T"'
        f2 = 'JOIN "TableColumn" AS "TC" ON "T"."Table"="TC"."Table"'
        f3 = 'JOIN "Columns" AS "C" ON "TC"."Column"="C"."Column"'
        f = (f1, f2, f3)
        w = '"T"."Name"=?'
        p = (','.join(s), ' '.join(f), w)
        query = 'SELECT %s FROM %s WHERE %s' % p

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
        query = 'SELECT %s FROM %s WHERE %s' % p

    elif name == 'getContentType':
        query = 'SELECT "Value2" "Folder","Value3" "Link" FROM "Settings" WHERE "Name"=\'ContentType\''
    elif name == 'getUser':
        c1 = '"U"."UserId"'
        c2 = '"U"."UserName"'
        c3 = '"U"."RootId"'
        c4 = '"I"."Title" "RootName"'
        c = (c1, c2, c3, c4)
        f = '"Users" "U" JOIN "Items" "I" ON "U"."RootId" = "I"."ItemId"'
        p = (','.join(c), f)
        query = 'SELECT %s FROM %s WHERE "U"."UserName" = ?' % p
    elif name == 'getItem':
        c = []
        c.append('"ItemId" "Id"')
        c.append('"ItemId" "ObjectId"')
        c.append('"Title"')
        c.append('"Title" "TitleOnServer"')
        c.append('"DateCreated"')
        c.append('"DateModified"')
        c.append('"ContentType"')
        c.append('"MediaType"')
        c.append('"Size"')
        c.append('"Trashed"')
        c.append('"IsRoot"')
        c.append('"IsFolder"')
        c.append('"IsDocument"')
        c.append('"CanAddChild"')
        c.append('"CanRename"')
        c.append('"IsReadOnly"')
        c.append('"IsVersionable"')
        c.append('"Loaded"')
        c.append('\'\' "CasePreservingURL"')
        c.append('FALSE "IsHidden"')
        c.append('FALSE "IsVolume"')
        c.append('FALSE "IsRemote"')
        c.append('FALSE "IsRemoveable"')
        c.append('FALSE "IsFloppy"')
        c.append('FALSE "IsCompactDisc"')
        query = 'SELECT %s FROM "Item" WHERE "UserId" = ? AND "ItemId" = ?' % ','.join(c)
    elif name == 'getChildren':
        c0 = '"ItemId"'
        c1 = '"Title"'
        c2 = '"Size"'
        c3 = '"DateModified"'
        c4 = '"DateCreated"'
        c5 = '"IsFolder"'
        c6 = '"TargetURL"'
        c6 = "CASE WHEN %s = TRUE THEN ? || '/' || %s ELSE ? || '/' || %s END %s" % (c5, c0, c1, c6)
        c7 = '"IsHidden"'
        c8 = '"IsVolume"'
        c9 = '"IsRemote"'
        c10 = '"IsRemoveable"'
        c11 = '"IsFloppy"'
        c12 = '"IsCompactDisc"'
        c = (c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12)
        w = '"UserId" = ? AND "ParentId" = ? AND ("IsFolder" = TRUE OR "Loaded" >= ?)'
        p = (','.join(c), w)
        query = 'SELECT %s FROM "Child" WHERE %s' % p
    elif name == 'getChildId':
        w = '"UserId" = ? AND "ParentId" = ? AND "Title" = ?'
        query = 'SELECT "ItemId" FROM "Child" WHERE %s' % w
    elif name == 'getNewIdentifier':
        query = 'SELECT "Id" FROM "Identifiers" WHERE "UserId" = ? ORDER BY "TimeStamp" LIMIT 1'
    elif name == 'countNewIdentifier':
        query = 'SELECT COUNT( "Id" ) "Id" FROM "Identifiers" WHERE "UserId" = ?'
    elif name == 'countChildTitle':
        w = '"UserId" = ? AND "ParentId" = ? AND "Title" = ?'
        query = 'SELECT COUNT( "Title" ) FROM "Child" WHERE %s' % w
    elif name == 'isChildId':
        c = 'CAST(COUNT(1) AS "BOOLEAN") "IsChild"'
        w = '"UserId" = ? AND "ChildId" = ? AND "ItemId" = ?'
        query = 'SELECT %s FROM "Parents" WHERE %s' % (c, w)
    elif name == 'isIdentifier':
        c = 'CAST(COUNT(1) AS "BOOLEAN") "IsIdentifier"'
        query = 'SELECT %s FROM "Items" WHERE "ItemId" = ?' % c
    elif name == 'getItemToSync':
        query = 'SELECT * FROM "Sync" WHERE "UserId" = ? ORDER BY "SyncId"'

# Insert Queries
    elif name == 'insertUser':
        c = '"UserName","DisplayName","RootId","TimeStamp","UserId"'
        query = 'INSERT INTO "Users" (%s) VALUES (?,?,?,?,?)' % c
    elif name == 'insertItem':
        c = '"Title","DateCreated","DateModified","MediaType","Size","Trashed","ItemId"'
        query = 'INSERT INTO "Items" (%s) VALUES (?,?,?,?,?,?,?)' % c
    elif name == 'insertCapability':
        c = '"CanAddChild","CanRename","IsReadOnly","IsVersionable","UserId","ItemId"'
        query = 'INSERT INTO "Capabilities" (%s) VALUES (?,?,?,?,?,?)' % c
    elif name == 'insertParent':
        query = 'INSERT INTO "Parents" ("UserId","ChildId","ItemId") VALUES (?,?,?)'
    elif name == 'insertSyncMode':
        c = '"SyncId","UserId","ItemId","ParentId","SyncMode"'
        query = 'INSERT INTO "Synchronizes" (%s) VALUES (NULL,?,?,?,?)' % c
    elif name == 'insertIdentifier':
        query = 'INSERT INTO "Identifiers"("UserId","Id")VALUES(?,?)'

# Update Queries
    elif name == 'updateItem':
        c = '"Title"=?,"DateCreated"=?,"DateModified"=?,"MediaType"=?,"Size"=?,"Trashed"=?'
        query = 'UPDATE "Items" SET %s WHERE "ItemId"=?' % c
    elif name == 'updateCapability':
        c = '"CanAddChild"=?,"CanRename"=?,"IsReadOnly"=?,"IsVersionable"=?'
        query = 'UPDATE "Capabilities" SET %s WHERE "UserId"=? AND "ItemId"=?' % c
    elif name == 'updateLoaded':
        query = 'UPDATE "Items" SET "Loaded"=? WHERE "ItemId"=?'
    elif name == 'updateTitle':
        query = 'UPDATE "Items" SET "Title"=? WHERE "ItemId"=?'
    elif name == 'updateSize':
        query = 'UPDATE "Items" SET "Size"=? WHERE "ItemId"=?'
    elif name == 'updateTrashed':
        query = 'UPDATE "Items" SET "Trashed"=? WHERE "ItemId"=?'
    elif name == 'updateItemId':
        query = 'UPDATE "Items" SET "ItemId"=? WHERE "ItemId"=?'

# Delete Queries
    elif name == 'deleteParent':
        query = 'DELETE FROM "Parents" WHERE "UserId"=? AND "ChildId"=?'
    elif name == 'deleteSyncMode':
        query = 'DELETE FROM "Synchronizes" WHERE "SyncId"=?'

# Get DataBase Version Query
    elif name == 'getVerion':
        query = 'Select DISTINCT DATABASE_VERSION() as "HSQL Version" From INFORMATION_SCHEMA.SYSTEM_TABLES'

# ShutDown Queries
    elif name == 'shutdown':
        query = 'SHUTDOWN;'
    elif name == 'shutdownCompact':
        query = 'SHUTDOWN COMPACT;'

# Queries don't exist!!!
    else:
        print("dbqueries.getSqlQuery(): ERROR: Query '%s' not found!!!" % name)
    return query

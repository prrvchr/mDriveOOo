#!
# -*- coding: utf_8 -*-

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

import uno
import unohelper

from com.sun.star.sdbc import XDatabaseMetaData2

import traceback


class DatabaseMetaData(unohelper.Base,
                       XDatabaseMetaData2):
    def __init__(self, connection, metadata, protocols, username):
        self._connection = connection
        self._metadata = metadata
        self._protocols = protocols
        self._username = username

    # XDatabaseMetaData2
    def getConnectionInfo(self):
        print("Connection.MetaData.getConnectionInfo()")
        return self._metadata.getConnectionInfo()
    def allProceduresAreCallable(self):
        print("Connection.MetaData.allProceduresAreCallable()")
        return self._metadata.allProceduresAreCallable()
    def allTablesAreSelectable(self):
        print("Connection.MetaData.allTablesAreSelectable()")
        return self._metadata.allTablesAreSelectable()
    def getURL(self):
        print("Connection.MetaData.getURL()")
        return ':'.join(self._protocols)
    def getUserName(self):
        print("Connection.MetaData.getUserName()")
        return self._username
    def isReadOnly(self):
        value = self._metadata.isReadOnly()
        print("Connection.MetaData.isReadOnly() %s" % value)
        return value
    def nullsAreSortedHigh(self):
        value = self._metadata.nullsAreSortedHigh()
        print("Connection.MetaData.nullsAreSortedHigh() %s" % value)
        return value
    def nullsAreSortedLow(self):
        value = self._metadata.nullsAreSortedLow()
        print("Connection.MetaData.nullsAreSortedLow() %s" % value)
        return value
    def nullsAreSortedAtStart(self):
        value = self._metadata.nullsAreSortedAtStart()
        print("Connection.MetaData.nullsAreSortedAtStart() %s" % value)
        return value
    def nullsAreSortedAtEnd(self):
        value = self._metadata.nullsAreSortedAtEnd()
        print("Connection.MetaData.nullsAreSortedAtEnd() %s" % value)
        return value
    def getDatabaseProductName(self):
        print("Connection.MetaData.getDatabaseProductName()")
        return self._metadata.getDatabaseProductName()
    def getDatabaseProductVersion(self):
        print("Connection.MetaData.getDatabaseProductVersion()")
        return self._metadata.getDatabaseProductVersion()
    def getDriverName(self):
        print("Connection.MetaData.getDriverName()")
        return self._metadata.getDriverName()
    def getDriverVersion(self):
        print("Connection.MetaData.getDriverVersion()")
        return self._metadata.getDriverVersion()
    def getDriverMajorVersion(self):
        print("Connection.MetaData.getDriverMajorVersion()")
        return self._metadata.getDriverMajorVersion()
    def getDriverMinorVersion(self):
        print("Connection.MetaData.getDriverMinorVersion()")
        return self._metadata.getDriverMinorVersion()
    def usesLocalFiles(self):
        return self._metadata.usesLocalFiles()
    def usesLocalFilePerTable(self):
        return self._metadata.usesLocalFilePerTable()
    def supportsMixedCaseIdentifiers(self):
        return self._metadata.supportsMixedCaseIdentifiers()
    def storesUpperCaseIdentifiers(self):
        return self._metadata.storesUpperCaseIdentifiers()
    def storesLowerCaseIdentifiers(self):
        return self._metadata.storesLowerCaseIdentifiers()
    def storesMixedCaseIdentifiers(self):
        return self._metadata.storesMixedCaseIdentifiers()
    def supportsMixedCaseQuotedIdentifiers(self):
        return self._metadata.supportsMixedCaseQuotedIdentifiers()
    def storesUpperCaseQuotedIdentifiers(self):
        return self._metadata.storesUpperCaseQuotedIdentifiers()
    def storesLowerCaseQuotedIdentifiers(self):
        return self._metadata.storesLowerCaseQuotedIdentifiers()
    def storesMixedCaseQuotedIdentifiers(self):
        return self._metadata.storesMixedCaseQuotedIdentifiers()
    def getIdentifierQuoteString(self):
        return self._metadata.getIdentifierQuoteString()
    def getSQLKeywords(self):
        return self._metadata.getSQLKeywords()
    def getNumericFunctions(self):
        return self._metadata.getNumericFunctions()
    def getStringFunctions(self):
        return self._metadata.getStringFunctions()
    def getSystemFunctions(self):
        return self._metadata.getSystemFunctions()
    def getTimeDateFunctions(self):
        return self._metadata.getTimeDateFunctions()
    def getSearchStringEscape(self):
        return self._metadata.getSearchStringEscape()
    def getExtraNameCharacters(self):
        return self._metadata.getExtraNameCharacters()
    def supportsAlterTableWithAddColumn(self):
        return self._metadata.supportsAlterTableWithAddColumn()
    def supportsAlterTableWithDropColumn(self):
        return self._metadata.supportsAlterTableWithDropColumn()
    def supportsColumnAliasing(self):
        return self._metadata.supportsColumnAliasing()
    def nullPlusNonNullIsNull(self):
        return self._metadata.nullPlusNonNullIsNull()
    def supportsTypeConversion(self):
        return self._metadata.supportsTypeConversion()
    def supportsConvert(self, fromtype, totype):
        return self._metadata.supportsConvert(fromtype, totype)
    def supportsTableCorrelationNames(self):
        return self._metadata.supportsTableCorrelationNames()
    def supportsDifferentTableCorrelationNames(self):
        return self._metadata.supportsDifferentTableCorrelationNames()
    def supportsExpressionsInOrderBy(self):
        return self._metadata.supportsExpressionsInOrderBy()
    def supportsOrderByUnrelated(self):
        return self._metadata.supportsOrderByUnrelated()
    def supportsGroupBy(self):
        return self._metadata.supportsGroupBy()
    def supportsGroupByUnrelated(self):
        return self._metadata.supportsGroupByUnrelated()
    def supportsGroupByBeyondSelect(self):
        return self._metadata.supportsGroupByBeyondSelect()
    def supportsLikeEscapeClause(self):
        return self._metadata.supportsLikeEscapeClause()
    def supportsMultipleResultSets(self):
        return self._metadata.supportsMultipleResultSets()
    def supportsMultipleTransactions(self):
        return self._metadata.supportsMultipleTransactions()
    def supportsNonNullableColumns(self):
        return self._metadata.supportsNonNullableColumns()
    def supportsMinimumSQLGrammar(self):
        return self._metadata.supportsMinimumSQLGrammar()
    def supportsCoreSQLGrammar(self):
        return self._metadata.supportsCoreSQLGrammar()
    def supportsExtendedSQLGrammar(self):
        return self._metadata.supportsExtendedSQLGrammar()
    def supportsANSI92EntryLevelSQL(self):
        return self._metadata.supportsANSI92EntryLevelSQL()
    def supportsANSI92IntermediateSQL(self):
        return self._metadata.supportsANSI92IntermediateSQL()
    def supportsANSI92FullSQL(self):
        return self._metadata.supportsANSI92FullSQL()
    def supportsIntegrityEnhancementFacility(self):
        return self._metadata.supportsIntegrityEnhancementFacility()
    def supportsOuterJoins(self):
        return self._metadata.supportsOuterJoins()
    def supportsFullOuterJoins(self):
        return self._metadata.supportsFullOuterJoins()
    def supportsLimitedOuterJoins(self):
        return self._metadata.supportsLimitedOuterJoins()
    def getSchemaTerm(self):
        return self._metadata.getSchemaTerm()
    def getProcedureTerm(self):
        return self._metadata.getProcedureTerm()
    def getCatalogTerm(self):
        return self._metadata.getCatalogTerm()
    def isCatalogAtStart(self):
        return self._metadata.isCatalogAtStart()
    def getCatalogSeparator(self):
        return self._metadata.getCatalogSeparator()
    def supportsSchemasInDataManipulation(self):
        return self._metadata.supportsSchemasInDataManipulation()
    def supportsSchemasInProcedureCalls(self):
        return self._metadata.supportsSchemasInProcedureCalls()
    def supportsSchemasInTableDefinitions(self):
        return self._metadata.supportsSchemasInTableDefinitions()
    def supportsSchemasInIndexDefinitions(self):
        return self._metadata.supportsSchemasInIndexDefinitions()
    def supportsSchemasInPrivilegeDefinitions(self):
        return self._metadata.supportsSchemasInPrivilegeDefinitions()
    def supportsCatalogsInDataManipulation(self):
        return self._metadata.supportsCatalogsInDataManipulation()
    def supportsCatalogsInProcedureCalls(self):
        return self._metadata.supportsCatalogsInProcedureCalls()
    def supportsCatalogsInTableDefinitions(self):
        return self._metadata.supportsCatalogsInTableDefinitions()
    def supportsCatalogsInIndexDefinitions(self):
        return self._metadata.supportsCatalogsInIndexDefinitions()
    def supportsCatalogsInPrivilegeDefinitions(self):
        return self._metadata.supportsCatalogsInPrivilegeDefinitions()
    def supportsPositionedDelete(self):
        return self._metadata.supportsPositionedDelete()
    def supportsPositionedUpdate(self):
        return self._metadata.supportsPositionedUpdate()
    def supportsSelectForUpdate(self):
        return self._metadata.supportsSelectForUpdate()
    def supportsStoredProcedures(self):
        print("Connection.MetaData.supportsStoredProcedures() %s" % self._metadata.supportsStoredProcedures())
        return self._metadata.supportsStoredProcedures()
    def supportsSubqueriesInComparisons(self):
        return self._metadata.supportsSubqueriesInComparisons()
    def supportsSubqueriesInExists(self):
        return self._metadata.supportsSubqueriesInExists()
    def supportsSubqueriesInIns(self):
        return self._metadata.supportsSubqueriesInIns()
    def supportsSubqueriesInQuantifieds(self):
        return self._metadata.supportsSubqueriesInQuantifieds()
    def supportsCorrelatedSubqueries(self):
        return self._metadata.supportsCorrelatedSubqueries()
    def supportsUnion(self):
        return self._metadata.supportsUnion()
    def supportsUnionAll(self):
        return self._metadata.supportsUnionAll()
    def supportsOpenCursorsAcrossCommit(self):
        return self._metadata.supportsOpenCursorsAcrossCommit()
    def supportsOpenCursorsAcrossRollback(self):
        return self._metadata.supportsOpenCursorsAcrossRollback()
    def supportsOpenStatementsAcrossCommit(self):
        return self._metadata.supportsOpenStatementsAcrossCommit()
    def supportsOpenStatementsAcrossRollback(self):
        return self._metadata.supportsOpenStatementsAcrossRollback()
    def getMaxBinaryLiteralLength(self):
        return self._metadata.getMaxBinaryLiteralLength()
    def getMaxCharLiteralLength(self):
        return self._metadata.getMaxCharLiteralLength()
    def getMaxColumnNameLength(self):
        return self._metadata.getMaxColumnNameLength()
    def getMaxColumnsInGroupBy(self):
        return self._metadata.getMaxColumnsInGroupBy()
    def getMaxColumnsInIndex(self):
        return self._metadata.getMaxColumnsInIndex()
    def getMaxColumnsInOrderBy(self):
        return self._metadata.getMaxColumnsInOrderBy()
    def getMaxColumnsInSelect(self):
        return self._metadata.getMaxColumnsInSelect()
    def getMaxColumnsInTable(self):
        return self._metadata.getMaxColumnsInTable()
    def getMaxConnections(self):
        return self._metadata.getMaxConnections()
    def getMaxCursorNameLength(self):
        return self._metadata.getMaxCursorNameLength()
    def getMaxIndexLength(self):
        return self._metadata.getMaxIndexLength()
    def getMaxSchemaNameLength(self):
        return self._metadata.getMaxSchemaNameLength()
    def getMaxProcedureNameLength(self):
        return self._metadata.getMaxProcedureNameLength()
    def getMaxCatalogNameLength(self):
        return self._metadata.getMaxCatalogNameLength()
    def getMaxRowSize(self):
        return self._metadata.getMaxRowSize()
    def doesMaxRowSizeIncludeBlobs(self):
        return self._metadata.doesMaxRowSizeIncludeBlobs()
    def getMaxStatementLength(self):
        return self._metadata.getMaxStatementLength()
    def getMaxStatements(self):
        return self._metadata.getMaxStatements()
    def getMaxTableNameLength(self):
        return self._metadata.getMaxTableNameLength()
    def getMaxTablesInSelect(self):
        return self._metadata.getMaxTablesInSelect()
    def getMaxUserNameLength(self):
        return self._metadata.getMaxUserNameLength()
    def getDefaultTransactionIsolation(self):
        return self._metadata.getDefaultTransactionIsolation()
    def supportsTransactions(self):
        return self._metadata.supportsTransactions()
    def supportsTransactionIsolationLevel(self, level):
        return self._metadata.supportsTransactionIsolationLevel(level)
    def supportsDataDefinitionAndDataManipulationTransactions(self):
        return self._metadata.supportsDataDefinitionAndDataManipulationTransactions()
    def supportsDataManipulationTransactionsOnly(self):
        return self._metadata.supportsDataManipulationTransactionsOnly()
    def dataDefinitionCausesTransactionCommit(self):
        return self._metadata.dataDefinitionCausesTransactionCommit()
    def dataDefinitionIgnoredInTransactions(self):
        return self._metadata.dataDefinitionIgnoredInTransactions()
    def getProcedures(self, catalog, schema, procedure):
        print("Connection.MetaData.getProcedures()")
        return self._metadata.getProcedures(catalog, schema, procedure)
    def getProcedureColumns(self, catalog, schema, procedure, column):
        print("Connection.MetaData.getProcedureColumns()")
        return self._metadata.getProcedureColumns(catalog, schema, procedure, column)
    def getTables(self, catalog, schema, table, types):
        print("Connection.MetaData.getTables()")
        return self._metadata.getTables(catalog, schema, table, types)
    def getSchemas(self):
        print("Connection.MetaData.getSchemas()")
        return self._metadata.getSchemas()
    def getCatalogs(self):
        print("Connection.MetaData.getCatalogs()")
        return self._metadata.getCatalogs()
    def getTableTypes(self):
        print("Connection.MetaData.getTableTypes()")
        return self._metadata.getTableTypes()
    def getColumns(self, catalog, schema, table, column):
        print("Connection.MetaData.getColumns()")
        return self._metadata.getColumns(catalog, schema, table, column)
    def getColumnPrivileges(self, catalog, schema, table, column):
        print("Connection.MetaData.getColumnPrivileges()")
        return self._metadata.getColumnPrivileges(catalog, schema, table, column)
    def getTablePrivileges(self, catalog, schema, table):
        print("Connection.MetaData.getTablePrivileges()")
        return self._metadata.getTablePrivileges(catalog, schema, table)
    def getBestRowIdentifier(self, catalog, schema, table, scope, nullable):
        return self._metadata.getBestRowIdentifier(catalog, schema, table, scope, nullable)
    def getVersionColumns(self, catalog, schema, table):
        return self._metadata.getVersionColumns(catalog, schema, table)
    def getPrimaryKeys(self, catalog, schema, table):
        return self._metadata.getPrimaryKeys(catalog, schema, table)
    def getImportedKeys(self, catalog, schema, table):
        return self._metadata.getImportedKeys(catalog, schema, table)
    def getExportedKeys(self, catalog, schema, table):
        return self._metadata.getExportedKeys(catalog, schema, table)
    def getCrossReference(self, catalog, schema, table, foreigncatalog, foreignschema, foreigntable):
        return self._metadata.getCrossReference(catalog, schema, table, foreigncatalog, foreignschema, foreigntable)
    def getTypeInfo(self):
        print("Connection.MetaData.supportsResultSetType()")
        return self._metadata.getTypeInfo()
    def getIndexInfo(self, catalog, schema, table, unique, approximate):
        print("Connection.MetaData.getIndexInfo()")
        return self._metadata.getIndexInfo(catalog, schema, table, unique, approximate)
    def supportsResultSetType(self, settype):
        print("Connection.MetaData.supportsResultSetType()")
        return self._metadata.supportsResultSetType(settype)
    def supportsResultSetConcurrency(self, settype, concurrency):
        print("Connection.MetaData.supportsResultSetConcurrency()")
        return self._metadata.supportsResultSetConcurrency(settype, concurrency)
    def ownUpdatesAreVisible(self, settype):
        return self._metadata.ownUpdatesAreVisible(settype)
    def ownDeletesAreVisible(self, settype):
        return self._metadata.ownDeletesAreVisible(settype)
    def ownInsertsAreVisible(self, settype):
        return self._metadata.ownInsertsAreVisible(settype)
    def othersUpdatesAreVisible(self, settype):
        return self._metadata.othersUpdatesAreVisible(settype)
    def othersDeletesAreVisible(self, settype):
        return self._metadata.othersDeletesAreVisible(settype)
    def othersInsertsAreVisible(self, settype):
        return self._metadata.othersInsertsAreVisible(settype)
    def updatesAreDetected(self, settype):
        return self._metadata.updatesAreDetected(settype)
    def deletesAreDetected(self, settype):
        return self._metadata.deletesAreDetected(settype)
    def insertsAreDetected(self, settype):
        return self._metadata.insertsAreDetected(settype)
    def supportsBatchUpdates(self):
        return self._metadata.supportsBatchUpdates()
    def getUDTs(self, catalog, schema, typename, types):
        print("Connection.MetaData.getUDTs()")
        return self._metadata.getUDTs(catalog, schema, typename, types)
    def getConnection(self):
        print("Connection.MetaData.getConnection()")
        return self._connection

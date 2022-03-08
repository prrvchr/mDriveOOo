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

import unohelper

from com.sun.star.lang import XEventListener

from com.sun.star.sdbc import XDatabaseMetaData2

import traceback


class MetaData(unohelper.Base,
               XDatabaseMetaData2,
               XEventListener):
    def __init__(self, connection, metadata, info, url):
        self._connection = connection
        self._metadata = metadata
        self._info = info
        self._url = url

# XDatabaseMetaData2
    def allProceduresAreCallable(self):
        return self._metadata.allProceduresAreCallable()
    def allTablesAreSelectable(self):
        return self._metadata.allTablesAreSelectable()
    def dataDefinitionCausesTransactionCommit(self):
        return self._metadata.dataDefinitionCausesTransactionCommit()
    def dataDefinitionIgnoredInTransactions(self):
        return self._metadata.dataDefinitionIgnoredInTransactions()
    def deletesAreDetected(self, settype):
        return self._metadata.deletesAreDetected(settype)
    def doesMaxRowSizeIncludeBlobs(self):
        return self._metadata.doesMaxRowSizeIncludeBlobs()
    def getBestRowIdentifier(self, catalog, schema, table, scope, nullable):
        return self._metadata.getBestRowIdentifier(catalog, schema, table, scope, nullable)
    def getCatalogSeparator(self):
        return self._metadata.getCatalogSeparator()
    def getCatalogs(self):
        return self._metadata.getCatalogs()
    def getCatalogTerm(self):
        return self._metadata.getCatalogTerm()
    def getColumnPrivileges(self, catalog, schema, table, column):
        return self._metadata.getColumnPrivileges(catalog, schema, table, column)
    def getColumns(self, catalog, schema, table, column):
        return self._metadata.getColumns(catalog, schema, table, column)
    def getConnection(self):
        # TODO: This wrapping is only there for the following lines:
        return self._connection
    def getConnectionInfo(self):
        # TODO: This wrapping is only there for the following lines:
        return self._info
    def getCrossReference(self, catalog, schema, table, foreigncatalog, foreignschema, foreigntable):
        return self._metadata.getCrossReference(catalog, schema, table, foreigncatalog, foreignschema, foreigntable)
    def getDatabaseProductName(self):
        return self._metadata.getDatabaseProductName()
    def getDatabaseProductVersion(self):
        return self._metadata.getDatabaseProductVersion()
    def getDefaultTransactionIsolation(self):
        return self._metadata.getDefaultTransactionIsolation()
    def getDriverMajorVersion(self):
        return self._metadata.getDriverMajorVersion()
    def getDriverMinorVersion(self):
        return self._metadata.getDriverMinorVersion()
    def getDriverName(self):
        return self._metadata.getDriverName()
    def getDriverVersion(self):
        return self._metadata.getDriverVersion()
    def getExportedKeys(self, catalog, schema, table):
        return self._metadata.getExportedKeys(catalog, schema, table)
    def getExtraNameCharacters(self):
        return self._metadata.getExtraNameCharacters()
    def getIdentifierQuoteString(self):
        return self._metadata.getIdentifierQuoteString()
    def getImportedKeys(self, catalog, schema, table):
        return self._metadata.getImportedKeys(catalog, schema, table)
    def getIndexInfo(self, catalog, schema, table, unique, approximate):
        return self._metadata.getIndexInfo(catalog, schema, table, unique, approximate)
    def getMaxBinaryLiteralLength(self):
        return self._metadata.getMaxBinaryLiteralLength()
    def getMaxCatalogNameLength(self):
        return self._metadata.getMaxCatalogNameLength()
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
    def getMaxProcedureNameLength(self):
        return self._metadata.getMaxProcedureNameLength()
    def getMaxRowSize(self):
        return self._metadata.getMaxRowSize()
    def getMaxSchemaNameLength(self):
        return self._metadata.getMaxSchemaNameLength()
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
    def getNumericFunctions(self):
        return self._metadata.getNumericFunctions()
    def getPrimaryKeys(self, catalog, schema, table):
        return self._metadata.getPrimaryKeys(catalog, schema, table)
    def getProcedureColumns(self, catalog, schema, procedure, column):
        return self._metadata.getProcedureColumns(catalog, schema, procedure, column)
    def getProcedures(self, catalog, schema, procedure):
        return self._metadata.getProcedures(catalog, schema, procedure)
    def getProcedureTerm(self):
        return self._metadata.getProcedureTerm()
    def getSQLKeywords(self):
        return self._metadata.getSQLKeywords()
    def getSchemas(self):
        return self._metadata.getSchemas()
    def getSchemaTerm(self):
        return self._metadata.getSchemaTerm()
    def getSearchStringEscape(self):
        return self._metadata.getSearchStringEscape()
    def getStringFunctions(self):
        return self._metadata.getStringFunctions()
    def getSystemFunctions(self):
        return self._metadata.getSystemFunctions()
    def getTablePrivileges(self, catalog, schema, table):
        return self._metadata.getTablePrivileges(catalog, schema, table)
    def getTables(self, catalog, schema, table, types):
        return self._metadata.getTables(catalog, schema, table, types)
    def getTableTypes(self):
        return self._metadata.getTableTypes()
    def getTimeDateFunctions(self):
        return self._metadata.getTimeDateFunctions()
    def getTypeInfo(self):
        return self._metadata.getTypeInfo()
    def getUDTs(self, catalog, schema, typename, types):
        return self._metadata.getUDTs(catalog, schema, typename, types)
    def getURL(self):
        # TODO: This wrapping is only there for the following lines:
        return self._url
    def getUserName(self):
        return self._metadata.getUserName()
    def getVersionColumns(self, catalog, schema, table):
        return self._metadata.getVersionColumns(catalog, schema, table)
    def insertsAreDetected(self, settype):
        return self._metadata.insertsAreDetected(settype)
    def isCatalogAtStart(self):
        return self._metadata.isCatalogAtStart()
    def isReadOnly(self):
        return self._metadata.isReadOnly()
    def nullPlusNonNullIsNull(self):
        return self._metadata.nullPlusNonNullIsNull()
    def nullsAreSortedAtEnd(self):
        return self._metadata.nullsAreSortedAtEnd()
    def nullsAreSortedAtStart(self):
        return self._metadata.nullsAreSortedAtStart()
    def nullsAreSortedHigh(self):
        return self._metadata.nullsAreSortedHigh()
    def nullsAreSortedLow(self):
        return self._metadata.nullsAreSortedLow()
    def othersDeletesAreVisible(self, settype):
        return self._metadata.othersDeletesAreVisible(settype)
    def othersInsertsAreVisible(self, settype):
        return self._metadata.othersInsertsAreVisible(settype)
    def othersUpdatesAreVisible(self, settype):
        return self._metadata.othersUpdatesAreVisible(settype)
    def ownDeletesAreVisible(self, settype):
        return self._metadata.ownDeletesAreVisible(settype)
    def ownInsertsAreVisible(self, settype):
        return self._metadata.ownInsertsAreVisible(settype)
    def ownUpdatesAreVisible(self, settype):
        return self._metadata.ownUpdatesAreVisible(settype)
    def storesLowerCaseIdentifiers(self):
        return self._metadata.storesLowerCaseIdentifiers()
    def storesLowerCaseQuotedIdentifiers(self):
        return self._metadata.storesLowerCaseQuotedIdentifiers()
    def storesMixedCaseIdentifiers(self):
        return self._metadata.storesMixedCaseIdentifiers()
    def storesMixedCaseQuotedIdentifiers(self):
        return self._metadata.storesMixedCaseQuotedIdentifiers()
    def storesUpperCaseIdentifiers(self):
        return self._metadata.storesUpperCaseIdentifiers()
    def storesUpperCaseQuotedIdentifiers(self):
        return self._metadata.storesUpperCaseQuotedIdentifiers()
    def supportsANSI92EntryLevelSQL(self):
        return self._metadata.supportsANSI92EntryLevelSQL()
    def supportsANSI92FullSQL(self):
        return self._metadata.supportsANSI92FullSQL()
    def supportsANSI92IntermediateSQL(self):
        return self._metadata.supportsANSI92IntermediateSQL()
    def supportsAlterTableWithAddColumn(self):
        return self._metadata.supportsAlterTableWithAddColumn()
    def supportsAlterTableWithDropColumn(self):
        return self._metadata.supportsAlterTableWithDropColumn()
    def supportsBatchUpdates(self):
        return self._metadata.supportsBatchUpdates()
    def supportsCatalogsInDataManipulation(self):
        return self._metadata.supportsCatalogsInDataManipulation()
    def supportsCatalogsInIndexDefinitions(self):
        return self._metadata.supportsCatalogsInIndexDefinitions()
    def supportsCatalogsInPrivilegeDefinitions(self):
        return self._metadata.supportsCatalogsInPrivilegeDefinitions()
    def supportsCatalogsInProcedureCalls(self):
        return self._metadata.supportsCatalogsInProcedureCalls()
    def supportsCatalogsInTableDefinitions(self):
        return self._metadata.supportsCatalogsInTableDefinitions()
    def supportsColumnAliasing(self):
        return self._metadata.supportsColumnAliasing()
    def supportsConvert(self, fromtype, totype):
        return self._metadata.supportsConvert(fromtype, totype)
    def supportsCoreSQLGrammar(self):
        return self._metadata.supportsCoreSQLGrammar()
    def supportsCorrelatedSubqueries(self):
        return self._metadata.supportsCorrelatedSubqueries()
    def supportsDataDefinitionAndDataManipulationTransactions(self):
        return self._metadata.supportsDataDefinitionAndDataManipulationTransactions()
    def supportsDataManipulationTransactionsOnly(self):
        return self._metadata.supportsDataManipulationTransactionsOnly()
    def supportsDifferentTableCorrelationNames(self):
        return self._metadata.supportsDifferentTableCorrelationNames()
    def supportsExpressionsInOrderBy(self):
        return self._metadata.supportsExpressionsInOrderBy()
    def supportsExtendedSQLGrammar(self):
        return self._metadata.supportsExtendedSQLGrammar()
    def supportsFullOuterJoins(self):
        return self._metadata.supportsFullOuterJoins()
    def supportsGroupBy(self):
        return self._metadata.supportsGroupBy()
    def supportsGroupByBeyondSelect(self):
        return self._metadata.supportsGroupByBeyondSelect()
    def supportsGroupByUnrelated(self):
        return self._metadata.supportsGroupByUnrelated()
    def supportsIntegrityEnhancementFacility(self):
        return self._metadata.supportsIntegrityEnhancementFacility()
    def supportsLikeEscapeClause(self):
        return self._metadata.supportsLikeEscapeClause()
    def supportsLimitedOuterJoins(self):
        return self._metadata.supportsLimitedOuterJoins()
    def supportsMinimumSQLGrammar(self):
        return self._metadata.supportsMinimumSQLGrammar()
    def supportsMixedCaseIdentifiers(self):
        return self._metadata.supportsMixedCaseIdentifiers()
    def supportsMixedCaseQuotedIdentifiers(self):
        return self._metadata.supportsMixedCaseQuotedIdentifiers()
    def supportsMultipleResultSets(self):
        return self._metadata.supportsMultipleResultSets()
    def supportsMultipleTransactions(self):
        return self._metadata.supportsMultipleTransactions()
    def supportsNonNullableColumns(self):
        return self._metadata.supportsNonNullableColumns()
    def supportsOpenCursorsAcrossCommit(self):
        return self._metadata.supportsOpenCursorsAcrossCommit()
    def supportsOpenCursorsAcrossRollback(self):
        return self._metadata.supportsOpenCursorsAcrossRollback()
    def supportsOpenStatementsAcrossCommit(self):
        return self._metadata.supportsOpenStatementsAcrossCommit()
    def supportsOpenStatementsAcrossRollback(self):
        return self._metadata.supportsOpenStatementsAcrossRollback()
    def supportsOrderByUnrelated(self):
        return self._metadata.supportsOrderByUnrelated()
    def supportsOuterJoins(self):
        return self._metadata.supportsOuterJoins()
    def supportsPositionedDelete(self):
        return self._metadata.supportsPositionedDelete()
    def supportsPositionedUpdate(self):
        return self._metadata.supportsPositionedUpdate()
    def supportsResultSetConcurrency(self, settype, concurrency):
        return self._metadata.supportsResultSetConcurrency(settype, concurrency)
    def supportsResultSetType(self, settype):
        return self._metadata.supportsResultSetType(settype)
    def supportsSchemasInDataManipulation(self):
        return self._metadata.supportsSchemasInDataManipulation()
    def supportsSchemasInIndexDefinitions(self):
        return self._metadata.supportsSchemasInIndexDefinitions()
    def supportsSchemasInPrivilegeDefinitions(self):
        return self._metadata.supportsSchemasInPrivilegeDefinitions()
    def supportsSchemasInProcedureCalls(self):
        return self._metadata.supportsSchemasInProcedureCalls()
    def supportsSchemasInTableDefinitions(self):
        return self._metadata.supportsSchemasInTableDefinitions()
    def supportsSelectForUpdate(self):
        return self._metadata.supportsSelectForUpdate()
    def supportsStoredProcedures(self):
        return self._metadata.supportsStoredProcedures()
    def supportsSubqueriesInComparisons(self):
        return self._metadata.supportsSubqueriesInComparisons()
    def supportsSubqueriesInExists(self):
        return self._metadata.supportsSubqueriesInExists()
    def supportsSubqueriesInIns(self):
        return self._metadata.supportsSubqueriesInIns()
    def supportsSubqueriesInQuantifieds(self):
        return self._metadata.supportsSubqueriesInQuantifieds()
    def supportsTableCorrelationNames(self):
        return self._metadata.supportsTableCorrelationNames()
    def supportsTransactionIsolationLevel(self, level):
        return self._metadata.supportsTransactionIsolationLevel(level)
    def supportsTransactions(self):
        return self._metadata.supportsTransactions()
    def supportsTypeConversion(self):
        return self._metadata.supportsTypeConversion()
    def supportsUnion(self):
        return self._metadata.supportsUnion()
    def supportsUnionAll(self):
        return self._metadata.supportsUnionAll()
    def updatesAreDetected(self, settype):
        return self._metadata.updatesAreDetected(settype)
    def usesLocalFilePerTable(self):
        return self._metadata.usesLocalFilePerTable()
    def usesLocalFiles(self):
        return self._metadata.usesLocalFiles()

# XEventListener
    def disposing(self, source):
        self._metadata.disposing(source)

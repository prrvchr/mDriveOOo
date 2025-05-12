#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-25 https://prrvchr.github.io                                  ║
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

from com.sun.star.sdb.SQLFilterOperator import EQUAL

from com.sun.star.sdbc.DataType import CHAR
from com.sun.star.sdbc.DataType import VARCHAR
from com.sun.star.sdbc.DataType import LONGVARCHAR

from .gridview import GridView

from .gridhandler import WindowHandler

from ..unotool import createService
from ..unotool import getConfiguration
from ..unotool import getPropertyValue

from ..configuration import g_identifier

import json
from collections import OrderedDict
import traceback


class GridManager():
    def __init__(self, ctx, url, model, window, quote, setting, selection, resources=None, maxi=None, multi=False, factor=5):
        self._quote = quote
        self._factor = factor
        self._datasource = None
        self._table = None
        if resources is None:
            self._resolver = self._resource = None
        else:
            self._resolver, self._resource = resources
        self._setting = setting
        self._config = getConfiguration(ctx, g_identifier, True)
        widths = self._config.getByName(self._getConfigWidthName())
        self._widths = json.loads(widths, object_pairs_hook=OrderedDict)
        orders = self._config.getByName(self._getConfigOrderName())
        self._orders = json.loads(orders)
        self._max = maxi
        self._multi = multi
        self._indexes = {}
        self._types = {}
        self._url = url
        self._headers = {}
        self._properties = {}
        grid = createService(ctx, 'com.sun.star.awt.grid.SortableGridDataModel')
        grid.initialize((model, ))
        self._model = model
        self._view = GridView(ctx, window, WindowHandler(self), grid, selection)

    @property
    def Model(self):
        return self._view.getGrid().Model.GridDataModel
    @property
    def Column(self):
        return self._view.getGrid().Model.ColumnModel

# GridManager getter methods
    def getGridWidth(self):
        return self._view.getGrid().Model.Width

    def hasSelectedRows(self):
        return self._view.hasSelectedRows()

    def getUnsortedIndex(self, index):
        return self.Model.getRowHeading(index)

    def getSelectedRows(self):
        rows = []
        for row in self._view.getSelectedRows():
            rows.append(self.getUnsortedIndex(row))
        return tuple(rows)

    def getSelectedColumn(self, column):
        value = None
        if self._view.hasSelectedRows() and column in self._headers:
            index = tuple(self._headers.keys()).index(column)
            row = self.getUnsortedIndex(self._view.getSelectedRow())
            value = self._model.getCellData(index, row)
        return value

    def getSelectedIdentifier(self, identifier):
        value = None
        if self._view.hasSelectedRows():
            value = self._getRowValue(identifier, self.getUnsortedIndex(self._view.getSelectedRow()))
        return value

    def getGridFilters(self):
        filters = []
        for row in (range(self._model.RowCount)):
            filters.append(self._getRowFilter(row))
        return tuple(filters)

    def getSelectedStructuredFilters(self):
        filters = []
        for row in self._view.getSelectedRows():
            filters.append(self._getRowStructuredFilter(row))
        return tuple(filters)

    def _getRowFilter(self, row):
        filters = []
        for identifier in self._indexes:
            column = self._getQuotedIdentifier(identifier)
            value = self._getQuotedValue(identifier, row)
            filter = '%s = %s' % (column, value)
            filters.append(filter)
        return ' AND '.join(filters)

    def _getRowStructuredFilter(self, index):
        filters = []
        row = self.Model.getRowHeading(index)
        for identifier in self._indexes:
            value = self._getQuotedValue(identifier, row)
            filter = getPropertyValue(identifier, value, 0, EQUAL)
            filters.append(filter)
        return tuple(filters)

    def _getQuotedValue(self, identifier, row):
        value = self._getRowValue(identifier, row)
        if self._types[identifier] in (CHAR, VARCHAR, LONGVARCHAR):
            value = "'%s'" % value.replace("'", "''")
        else:
            value = "%s" % value
        return value

    def _getQuotedIdentifier(self, identifier):
        return "%s%s%s" % (self._quote, identifier, self._quote)

    def _getRowValue(self, identifier, row):
        return self._model.getCellData(self._indexes[identifier], row)

# GridManager setter methods
    def dispose(self):
        self.saveColumnSettings()
        self.Column.dispose()
        self.Model.dispose()

    def setGridVisible(self, enabled):
        self._view.setGridVisible(enabled)

    def addSelectionListener(self, listener):
        self._view.getGrid().addSelectionListener(listener)

    def removeSelectionListener(self, listener):
        self._view.getGrid().removeSelectionListener(listener)

    def showColumns(self, state):
        self._view.showColumns(state)

    def deselectAllRows(self):
        self._view.deselectAllRows()

    def enableColumnSelection(self, enabled):
        self._view.enableColumnSelection(enabled)

    def saveColumnSettings(self):
        self.saveColumnWidths()
        self.saveColumnOrders()

    def saveColumnWidths(self):
        self._saveWidths()
        name = self._getConfigWidthName()
        widths = json.dumps(self._widths)
        self._config.replaceByName(name, widths)
        self._config.commitChanges()

    def saveColumnOrders(self):
        self._saveOrders()
        name = self._getConfigOrderName()
        orders = json.dumps(self._orders)
        self._config.replaceByName(name, orders)
        self._config.commitChanges()

    def setColumn(self, index):
        if index != -1:
            identifier, add, reset = self._view.getSelectedColumn(index)
            if reset:
                modified, identifiers = self._resetColumn()
            else:
                identifiers = [column.Identifier for column in self.Column.getColumns()]
                if add:
                    modified = self._addColumn(identifiers, identifier)
                else:
                    modified = self._removeColumn(identifiers, identifier)
            if modified:
                self._setDefaultWidths()
                self._view.setColumns(self._url, identifiers)

# GridManager private methods
    def _initColumnModel(self, datasource, table=None):
        # TODO: ColumnWidth should be assigned after all columns have 
        # TODO: been added to the GridColumnModel
        self._removeColumns()
        widths = self._getSavedWidths(datasource, table)
        identifiers = self._getIdentifiers(widths)
        if widths:
            for identifier in widths:
                self._createColumn(identifier)
            self._setSavedWidths(widths)
        else:
            for identifier in identifiers:
                self._createColumn(identifier)
            self._setDefaultWidths()
        return identifiers

    def _saveWidths(self):
        widths = self._getColumnWidths()
        if self._multi:
            name = self._getDataSourceName(self._datasource, self._table)
            self._widths[name] = widths
        else:
            self._widths = widths

    def _saveOrders(self):
        orders = self._getColumnOrders()
        if self._multi:
            name = self._getDataSourceName(self._datasource, self._table)
            self._orders[name] = orders
        else:
            self._orders = orders

    def _getDataSourceName(self, datasource, table):
        name = datasource
        if self._multi and table:
            name += '.%s' % table
        return name

    def _resetColumn(self):
        self._removeColumns()
        identifiers = self._getDefaultIdentifiers()
        for identifier in identifiers:
            self._createColumn(identifier)
        return True, identifiers

    def _addColumn(self, identifiers, identifier):
        modified = False
        if identifier not in identifiers:
            if self._createColumn(identifier):
                identifiers.append(identifier)
                modified = True
        return modified

    def _removeColumn(self, identifiers, identifier):
        modified = False
        if identifier in identifiers:
            if self._removeIdentifier(identifier):
                identifiers.remove(identifier)
                modified = True
        return modified

    def _saveConfigOrder(self, order):
        name = self._getConfigOrderName()
        self._config.replaceByName(name, order)
        self._config.commitChanges()

    def _getSavedWidths(self, datasource, table):
        widths = {}
        if self._multi:
            name = self._getDataSourceName(datasource, table)
            if name in self._widths:
                widths = self._widths[name]
        else:
            widths = self._widths
        return widths

    def _getSavedOrders(self, datasource, table=None):
        orders = (-1, True)
        if self._multi:
            name = self._getDataSourceName(datasource, table)
            if name in self._orders:
                orders = self._orders[name]
        else:
            orders = self._orders
        return orders

    def _getIdentifiers(self, widths):
        identifiers = []
        for identifier in widths:
            if identifier in self._headers:
                identifiers.append(identifier)
        if not identifiers:
            identifiers = self._getDefaultIdentifiers()
        return identifiers

    def _removeColumns(self):
        for index in range(self.Column.getColumnCount() -1, -1, -1):
            self.Column.removeColumn(index)

    def _createColumn(self, identifier):
        created = False
        if identifier in self._headers:
            column = self.Column.createColumn()
            column.Identifier = identifier
            column.Title = self._headers[identifier]
            indexes = tuple(self._headers.keys())
            column.DataColumnIndex = indexes.index(identifier)
            if identifier in self._properties:
                for property in self._properties[identifier]:
                    setattr(column, property.Name, property.Value)
            self.Column.addColumn(column)
            created = True
        return created

    def _removeIdentifier(self, identifier):
        removed = False
        for index in range(self.Column.getColumnCount() -1, -1, -1):
            column = self.Column.getColumn(index)
            if column.Identifier == identifier:
                self.Column.removeColumn(index)
                removed = True
                break
        return removed

    def _setSavedWidths(self, widths):
        for column in self.Column.getColumns():
            identifier = column.Identifier
            flex = len(column.Title)
            column.MinWidth = flex * self._factor
            column.Flexibility = 0
            if identifier in widths:
                column.ColumnWidth = widths[identifier]
            else:
                column.ColumnWidth = flex * self._factor

    def _setDefaultWidths(self):
        for column in self.Column.getColumns():
            flex = len(column.Title)
            width = flex * self._factor
            column.ColumnWidth = width
            column.MinWidth = width
            column.Flexibility = 0

    def _getColumnWidths(self):
        widths = OrderedDict()
        for column in self.Column.getColumns():
            widths[column.Identifier] = column.ColumnWidth
        return widths

    def _getColumnOrders(self):
        pair = self.Model.getCurrentSortOrder()
        return pair.First, pair.Second

    def _getDefaultIdentifiers(self):
        identifiers = tuple(self._headers.keys())
        return identifiers[slice(self._max)]

    def _getColumnTitle(self, identifier):
        if self._resolver is None or self._resource is None:
            title = identifier
        else:
            title = self._resolver.resolveString(self._resource % identifier)
        return title

    def _getConfigWidthName(self):
        return '%s%s' % (self._setting, 'Columns')

    def _getConfigOrderName(self):
        return '%s%s' % (self._setting, 'Orders')

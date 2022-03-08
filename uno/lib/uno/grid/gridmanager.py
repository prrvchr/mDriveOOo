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

from ..unotool import createService
from ..unotool import getConfiguration
from ..unotool import getResourceLocation
from ..unotool import getStringResource

from ..configuration import g_extension
from ..configuration import g_identifier

from .griddata import GridData
from .gridview import GridView

import json
from threading import Thread
from collections import OrderedDict
import traceback


class GridManager(unohelper.Base):
    def __init__(self, ctx, rowset, parent, possize, config, resource=None, maxi=None, multi=False, name='Grid1'):
        self._ctx = ctx
        self._factor = 5
        # We need to save the DataSource Name to be able to save
        # Columns Widths after DataSource is disposed
        self._name = None
        self._datasource = None
        self._query = None
        self._resource = resource
        if resource is not None:
            self._resolver = getStringResource(ctx, g_identifier, g_extension)
        self._config = config
        self._configuration = getConfiguration(ctx, g_identifier, True)
        widths = self._configuration.getByName(self._getConfigWidthName())
        self._widths = json.loads(widths, object_pairs_hook=OrderedDict)
        self._max = maxi
        self._multi = multi
        self._rowset = rowset
        self._url = getResourceLocation(ctx, g_identifier, g_extension)
        service = 'com.sun.star.awt.grid.DefaultGridColumnModel'
        self._model = createService(ctx, service)
        self._grid = GridData()
        self._columns = {}
        self._composer = None
        self._view = GridView(ctx, name, self, parent, possize)

# GridManager getter methods
    def getGridModels(self):
        return self._grid, self._model

    def getSelectedRows(self):
        return self._view.getSelectedRows()

# GridManager setter methods
    def dispose(self):
        self._model.dispose()
        self._grid.dispose()

    def addSelectionListener(self, listener):
        self._view.getGrid().addSelectionListener(listener)

    def removeSelectionListener(self, listener):
        self._view.getGrid().removeSelectionListener(listener)

    def showControls(self, state):
        self._view.setWindowPosSize(state)

    def setRowSetData(self, rowset):
        connection = rowset.ActiveConnection
        datasource = connection.Parent
        name = datasource.Name
        query = rowset.UpdateTableName
        if self._isDataSourceChanged(name, query):
            if self._isGridLoaded():
                self._saveWidths()
            # We can hide GridColumnHeader and reset GridDataModel
            # but after saving GridColumnModel Widths
            self._view.showGridColumnHeader(False)
            self._grid.resetRowSetData()
            self._composer = self._getComposer(connection, rowset)
            self._columns = self._getColumns(rowset.getMetaData())
            identifiers = self._initColumnModel(name, query)
            self._initColumns(identifiers)
            self._name = name
            self._query = query
            self._datasource = datasource
            self._view.showGridColumnHeader(True)
        self._grid.setRowSetData(rowset)

    def saveColumnWidths(self):
        self._saveWidths()
        name = self._getConfigWidthName()
        widths = json.dumps(self._widths)
        self._configuration.replaceByName(name, widths)
        self._configuration.commitChanges()

    def setColumn(self, identifier, add, reset, index):
        self._view.deselectColumn(index)
        if reset:
            modified, identifiers = self._resetColumn()
        else:
            identifiers = [column.Identifier for column in self._model.getColumns()]
            if add:
                modified = self._addColumn(identifiers, identifier)
            else:
                modified = self._removeColumn(identifiers, identifier)
        if modified:
            self._setDefaultWidths()
            self._view.setColumns(self._url, identifiers)

    def isSelected(self, image):
        return image.endswith(self._view.getSelected())

    def isUnSelected(self, image):
        return image.endswith(self._view.getUnSelected())

    def setOrder(self, identifier, add, index):
        args = self._setOrder(identifier, add, index)
        Thread(target=self._executeRowSet, args=args).start()

# GridManager private methods
    def _isDataSourceChanged(self, name, query):
        return self._name != name or self._query != query

    def _isGridLoaded(self):
        return self._composer is not None

    def _saveWidths(self):
        widths = self._getColumnWidths()
        if self._multi:
            name = self._getDataSourceName(self._name, self._query)
            self._widths[name] = widths
        else:
            self._widths = widths

    def _getDataSourceName(self, datasource, query):
        if self._multi:
            name = '%s.%s' % (datasource, query)
        else:
            name = datasource
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

    def _setOrder(self, identifier, add, index):
        self._view.deselectOrder(index)
        if add:
            self._addOrder(identifier)
        else:
            self._removeOrder(identifier)
        self._view.setOrders(self._url, self._getOrders())
        order = self._composer.getOrder()
        return (order, )

    def _executeRowSet(self, order):
        if self._query:
            self._saveQueryOrder(order)
        else:
            self._saveConfigOrder(order)
        self._rowset.Order = order
        self._rowset.execute()

    def _saveQueryOrder(self, order):
        query = self._datasource.getQueryDefinitions().getByName(self._query)
        self._composer.setQuery(query.Command)
        self._composer.setOrder(order)
        query.Command = self._composer.getQuery()
        self._datasource.DatabaseDocument.store()

    def _saveConfigOrder(self, order):
        name = self._getConfigOrderName()
        self._configuration.replaceByName(name, order)
        self._configuration.commitChanges()

    def _addOrder(self, identifier):
        ascending = self._view.getSortDirection()
        column = self._composer.getColumns().getByName(identifier)
        self._composer.appendOrderByColumn(column, ascending)

    def _removeOrder(self, identifier):
        orders = []
        enumeration = self._composer.getOrderColumns().createEnumeration()
        while enumeration.hasMoreElements():
            column = enumeration.nextElement()
            if column.Name != identifier:
                orders.append(column)
        self._composer.Order = ''
        for order in orders:
            self._composer.appendOrderByColumn(order, order.IsAscending)

    def _getOrders(self):
        orders = OrderedDict()
        enumeration = self._composer.getOrderColumns().createEnumeration()
        while enumeration.hasMoreElements():
            column = enumeration.nextElement()
            orders[column.Name] = column.IsAscending
        return orders

    def _getColumns(self, metadata):
        columns = OrderedDict()
        for index in range(metadata.getColumnCount()):
            column = metadata.getColumnLabel(index +1)
            columns[column] = self._getColumnTitle(column)
        return columns

    def _getComposer(self, connection, rowset):
        composer = connection.getComposer(rowset.CommandType, rowset.Command)
        composer.setCommand(rowset.Command, rowset.CommandType)
        if self._multi:
            composer.Order = rowset.Order
        else:
            name = self._getConfigOrderName()
            composer.Order = self._configuration.getByName(name)
        return composer

    def _initColumnModel(self, datasource, query):
        # TODO: ColumnWidth should be assigned after all columns have 
        # TODO: been added to the GridColumnModel
        self._removeColumns()
        widths = self._getSavedWidths(datasource, query)
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

    def _initColumns(self, identifiers):
        self._view.initColumns(self._url, self._columns, identifiers)
        orders = self._composer.getOrderColumns().createEnumeration()
        self._view.initOrders(self._url, self._columns, orders)

    def _getSavedWidths(self, datasource, query):
        widths = {}
        if self._multi:
            name = self._getDataSourceName(datasource, query)
            if name in self._widths:
                widths = self._widths[name]
        else:
            widths = self._widths
        return widths

    def _getIdentifiers(self, widths):
        identifiers = []
        for identifier in widths:
            if identifier in self._columns:
                identifiers.append(identifier)
        if not identifiers:
            identifiers = self._getDefaultIdentifiers()
        return identifiers

    def _removeColumns(self):
        for index in range(self._model.getColumnCount() -1, -1, -1):
            self._model.removeColumn(index)

    def _createColumn(self, identifier):
        created = False
        if identifier in self._columns:
            column = self._model.createColumn()
            column.Identifier = identifier
            column.Title = self._columns[identifier]
            indexes = tuple(self._columns.keys())
            column.DataColumnIndex = indexes.index(identifier)
            self._model.addColumn(column)
            created = True
        return created

    def _removeIdentifier(self, identifier):
        removed = False
        for index in range(self._model.getColumnCount() -1, -1, -1):
            column = self._model.getColumn(index)
            if column.Identifier == identifier:
                self._model.removeColumn(index)
                removed = True
                break
        return removed

    def _setSavedWidths(self, widths):
        for column in self._model.getColumns():
            identifier = column.Identifier
            flex = len(column.Title)
            column.MinWidth = flex * self._factor
            column.Flexibility = 0
            if identifier in widths:
                column.ColumnWidth = widths[identifier]
            else:
                column.ColumnWidth = flex * self._factor

    def _setDefaultWidths(self):
        for column in self._model.getColumns():
            flex = len(column.Title)
            width = flex * self._factor
            column.ColumnWidth = width
            column.MinWidth = width
            column.Flexibility = flex

    def _getColumnWidths(self):
        widths = OrderedDict()
        for column in self._model.getColumns():
            widths[column.Identifier] = column.ColumnWidth
        return widths

    def _getDefaultIdentifiers(self):
        identifiers = tuple(self._columns.keys())
        return identifiers[slice(self._max)]

    def _getColumnTitle(self, identifier):
        if self._resource is None:
            title = identifier
        else:
            title = self._resolver.resolveString(self._resource % identifier)
        return title

    def _getConfigWidthName(self):
        return '%s%s' % (self._config, 'Columns')

    def _getConfigOrderName(self):
        return '%s%s' % (self._config, 'Orders')

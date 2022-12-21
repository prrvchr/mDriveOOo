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

import unohelper

from com.sun.star.view.SelectionType import MULTI

from ..unotool import getContainerWindow

from ..configuration import g_extension

from .gridhandler import WindowHandler


class GridView(unohelper.Base):
    def __init__(self, ctx, name, manager, parent, possize, step=1):
        self._ctx = ctx
        self._name = name
        self._up = 20
        handler = WindowHandler(ctx, manager)
        self._window = getContainerWindow(ctx, parent, handler, g_extension, 'GridWindow')
        self._setWindow(possize, step)
        data, model = manager.getGridModels()
        self._createGrid(data, model)
        self._window.setVisible(True)

# GridView getter methods
    def getWindow(self):
        return self._window

    def getGrid(self):
        return self._getGrid()

    def getSelectedRows(self):
        return self._getGrid().getSelectedRows()

    def getSortDirection(self):
        ascending = not bool(self._getSort().Model.State)
        return ascending

    def getUnSelected(self):
        return 'column-0.png'

    def getSelected(self):
        return 'column-1.png'

    def getDescending(self):
        return 'sort-0.png'

    def getAscending(self):
        return 'sort-1.png'

# GridView setter methods
    def setWindowPosSize(self, state):
        self._setGridPosSize(state)
        self._window.Model.Step = state +1

    def showGridColumnHeader(self, state):
        self._getGrid().Model.ShowColumnHeader = state

    def initColumns(self, url, columns, identifiers):
        control = self._getColumn()
        unselected = self._getUnSelected(url)
        self._initListBox(control, columns, unselected)
        indexes = tuple(columns.keys())
        selected = self._getSelected(url)
        for identifier in identifiers:
            index = indexes.index(identifier)
            control.Model.setItemImage(index, selected)

    def deselectColumn(self, index):
        self._getColumn().selectItemPos(index, False)

    def setColumns(self, url, identifiers):
        control = self._getColumn()
        selected = self._getSelected(url)
        unselected = self._getUnSelected(url)
        for index in range(control.Model.ItemCount):
            identifier = control.Model.getItemData(index)
            if identifier in identifiers:
                control.Model.setItemImage(index, selected)
            else:
                control.Model.setItemImage(index, unselected)

    def initOrders(self, url, columns, orders):
        control = self._getOrder()
        unselected = self._getUnSelected(url)
        self._initListBox(control, columns, unselected)
        indexes = tuple(columns.keys())
        ascending = self._getAscending(url)
        descending = self._getDescending(url)
        while orders.hasMoreElements():
            order = orders.nextElement()
            index = indexes.index(order.Name)
            image = ascending if order.IsAscending else descending
            control.Model.setItemImage(index, image)

    def deselectOrder(self, index):
        self._getOrder().selectItemPos(index, False)

    def setOrders(self, url, orders):
        control = self._getOrder()
        ascending = self._getAscending(url)
        descending = self._getDescending(url)
        unselected = self._getUnSelected(url)
        for index in range(control.Model.ItemCount):
            identifier = control.Model.getItemData(index)
            if identifier in orders:
                image = ascending if orders[identifier] else descending
                control.Model.setItemImage(index, image)
            else:
                control.Model.setItemImage(index, unselected)

# GridView private setter methods
    def _setGridPosSize(self, state):
        diff = self._up if state else -self._up
        model = self._getGrid().Model
        model.PositionY = model.PositionY + diff
        model.Height = model.Height - diff

    def _initListBox(self, control, columns, image):
        control.Model.removeAllItems()
        for identifier, title in columns.items():
            index = control.Model.ItemCount
            control.Model.insertItem(index, title, image)
            control.Model.setItemData(index, identifier)

    def _setWindow(self, possize, step):
        model = self._window.Model
        model.PositionX = possize.X
        model.PositionY = possize.Y
        model.Height = possize.Height
        model.Width = possize.Width
        model.Step = step

    def _getMargin(self):
        return self._getToggle().Model.Width

    def _createGrid(self, data, column):
        model = self._getGridModel(data, column)
        self._window.Model.insertByName(self._name, model)

# GridView private getter methods
    def _getUnSelected(self, url):
        return '%s/%s' % (url, self.getUnSelected())

    def _getSelected(self, url):
        return '%s/%s' % (url,  self.getSelected())

    def _getDescending(self, url):
        return '%s/%s' % (url, self.getDescending())

    def _getAscending(self, url):
        return '%s/%s' % (url, self.getAscending())

    def _getGridModel(self, data, column):
        margin = self._getToggle().Model.Width
        service = 'com.sun.star.awt.grid.UnoControlGridModel'
        model = self._window.Model.createInstance(service)
        model.Name = self._name
        model.PositionX = margin
        model.PositionY = 0
        model.Height = self._window.Model.Height
        model.Width = self._window.Model.Width - margin
        model.GridDataModel = data
        model.ColumnModel = column
        model.SelectionModel = MULTI
        model.ShowColumnHeader = False
        model.BackgroundColor = 16777215
        return model

# GridView private control methods
    def _getGrid(self):
        return self._window.getControl(self._name)

    def _getToggle(self):
        return self._window.getControl('CommandButton1')

    def _getColumnLabel(self):
        return self._window.getControl('Label1')

    def _getOrderLabel(self):
        return self._window.getControl('Label2')

    def _getColumn(self):
        return self._window.getControl('ListBox1')

    def _getOrder(self):
        return self._window.getControl('ListBox2')

    def _getSort(self):
        return self._window.getControl('CheckBox1')

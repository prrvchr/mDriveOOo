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

import unohelper

from com.sun.star.view.SelectionType import MULTI

from ..unotool import getContainerWindow

from ..configuration import g_identifier


class GridView(unohelper.Base):
    def __init__(self, ctx, window, handler, model, selection, step=1):
        self._name = 'GridControl1'
        self._gap = 20
        self._margin = 10
        self._window = getContainerWindow(ctx, window.getPeer(), handler, g_identifier, 'GridWindow')
        self._setWindowSize(window.Model, step)
        self._createGrid(model, selection)
        self._window.setVisible(True)

# GridView getter methods
    def getWindow(self):
        return self._window

    def getGrid(self):
        return self._getGrid()

    def hasSelectedRows(self):
        return self._getGrid().hasSelectedRows()

    def getSelectedRow(self):
        index = -1
        control = self._getGrid()
        if control.hasSelectedRows():
            index = control.getSelectedRows()[-1]
        return index

    def getSelectedRows(self):
        return self._getGrid().getSelectedRows()

    def getUnSelected(self):
        return 'column-0.png'

    def getSelected(self):
        return 'column-1.png'

# GridView setter methods
    def setGridVisible(self, enabled):
        self._getGrid().setVisible(enabled)

    def showControls(self, state):
        control = self._getGrid()
        control.setVisible(False)
        self._setGridPosSize(control.Model, state)
        self._window.Model.Step = state +1
        control.setVisible(True)

    def addSelectionListener(self, listener):
        self._getGrid().addSelectionListener(listener)

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

    def deselectAllRows(self):
        self._getGrid().deselectAllRows()

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

# GridView private setter methods
    def _setGridPosSize(self, model, state):
        gap = self._gap if state else -self._gap
        model.PositionY = model.PositionY + gap
        model.Height = model.Height - gap

    def _initListBox(self, control, columns, image):
        control.Model.removeAllItems()
        for identifier, title in columns.items():
            index = control.Model.ItemCount
            control.Model.insertItem(index, title, image)
            control.Model.setItemData(index, identifier)

    def _setWindowSize(self, window, step):
        model = self._window.Model
        model.Height = window.Height
        model.Width = window.Width
        offset = self._setControlPosition(self._getColumn(), window.Width)
        self._setControlPosition(self._getColumnLabel(), offset)
        model.Step = step

    def _setControlPosition(self, control, offset):
        control.Model.PositionX = offset - control.Model.Width
        return control.Model.PositionX - self._margin

    def _createGrid(self, data, selection):
        model = self._getGridModel(data, selection)
        self._window.Model.insertByName(self._name, model)

# GridView private getter methods
    def _getUnSelected(self, url):
        return '%s/%s' % (url, self.getUnSelected())

    def _getSelected(self, url):
        return '%s/%s' % (url,  self.getSelected())

    def _getGridModel(self, data, selection):
        margin = self._getToggle().Model.Width
        service = 'com.sun.star.awt.grid.UnoControlGridModel'
        model = self._window.Model.createInstance(service)
        model.Name = self._name
        model.PositionX = margin
        model.PositionY = 0
        model.Height = self._window.Model.Height
        model.Width = self._window.Model.Width - margin
        model.GridDataModel = data
        #model.ColumnModel = column
        model.SelectionModel = selection
        model.HScroll = True
        model.VScroll = True
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

    def _getColumn(self):
        return self._window.getControl('ListBox1')


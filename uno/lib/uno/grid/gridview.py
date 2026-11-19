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

import unohelper

from com.sun.star.awt import Point

from com.sun.star.awt.PosSize import POSSIZE

from com.sun.star.util.MeasureUnit import APPFONT

from ...unotool import Layout

from ...unotool import getContainerWindow

from ...configuration import g_identifier


class GridView(unohelper.Base):
    def __init__(self, ctx, window, handler, model, size, selection, step=1):
        self._name = 'GridControl1'
        self._window = getContainerWindow(ctx, window.getPeer(), handler, g_identifier, 'GridWindow')
        self._offset = self._window.convertPointToPixel(Point(0, 20), APPFONT).Y
        self._setWindowSize(size, step)
        self._createGrid(model, selection)
        self._layout = Layout(self._window, **self._getLayouts())

# GridView getter methods
    def getGrid(self):
        return self._getGrid()

    def getLayout(self):
        return self._layout

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

    def getSelectedColumn(self, index):
        control = self._getColumn()
        control.selectItemPos(index, False)
        identifier = control.Model.getItemData(index)
        add = self._isUnSelectedUrl(control.Model.getItemImage(index))
        for i in range(control.Model.ItemCount):
            if i != index and self._isSelectedUrl(control.Model.getItemImage(i)):
                reset = False
                break
        else:
            reset = True
        return identifier, add, reset

# GridView setter methods
    def setGridVisible(self, enabled):
        self._getGrid().setVisible(enabled)

    def showColumns(self, state):
        control = self._getGrid()
        control.setVisible(False)
        self._setGridPosSize(control, state)
        self._window.Model.Step = state + 1
        control.setVisible(True)
        self._layout.updateControl(control)

    def enableColumnSelection(self, enabled):
        self._getColumn().Model.Enabled = enabled

    def addSelectionListener(self, listener):
        self._getGrid().addSelectionListener(listener)

    def showGridColumnHeader(self, state):
        self._getGrid().Model.ShowColumnHeader = state

    def initColumns(self, url, columns, identifiers):
        control = self._getColumn()
        unselected = self._getUnSelectedUrl(url)
        self._initListBox(control, columns, unselected)
        indexes = tuple(columns.keys())
        selected = self._getSelectedUrl(url)
        for identifier in identifiers:
            index = indexes.index(identifier)
            control.Model.setItemImage(index, selected)

    def deselectAllRows(self):
        self._getGrid().deselectAllRows()

    def setColumns(self, url, identifiers):
        control = self._getColumn()
        selected = self._getSelectedUrl(url)
        unselected = self._getUnSelectedUrl(url)
        for index in range(control.Model.ItemCount):
            identifier = control.Model.getItemData(index)
            if identifier in identifiers:
                control.Model.setItemImage(index, selected)
            else:
                control.Model.setItemImage(index, unselected)

# GridView private setter methods
    def _setGridPosSize(self, control, state):
        pos = control.getPosSize()
        gap = self._offset if state else -self._offset
        control.setPosSize(pos.X, pos.Y + gap, pos.Width, pos.Height - gap, POSSIZE)

    def _initListBox(self, control, columns, image):
        control.Model.removeAllItems()
        for identifier, title in columns.items():
            index = control.Model.ItemCount
            control.Model.insertItem(index, title, image)
            control.Model.setItemData(index, identifier)

    def _setWindowSize(self, size, step):
        model = self._window.Model
        x = size.Width - model.Width
        y = size.Height - model.Height
        model.Width = size.Width
        model.Height = size.Height
        frame = self._getFrame().Model
        frame.Width += x
        frame.Height += y
        self._getColumn().Model.PositionX += x
        self._getColumnLabel().Model.PositionX += x
        model.Step = step

    def _createGrid(self, data, selection):
        model = self._getGridModel(data, selection)
        self._window.Model.insertByName(self._name, model)

# GridView private getter methods
    def _getUnSelectedUrl(self, url):
        return '%s/%s' % (url, self._getUnSelectedImage())

    def _getSelectedUrl(self, url):
        return '%s/%s' % (url,  self._getSelectedImage())

    def _isUnSelectedUrl(self, url):
        return url.endswith(self._getUnSelectedImage())

    def _isSelectedUrl(self, url):
        return url.endswith(self._getSelectedImage())

    def _getUnSelectedImage(self):
        return 'column-0.png'

    def _getSelectedImage(self):
        return 'column-1.png'

    def _getGridModel(self, data, selection):
        service = 'com.sun.star.awt.grid.UnoControlGridModel'
        model = self._window.Model.createInstance(service)
        model.Name = self._name
        frame = self._getFrame().Model
        model.PositionX = frame.PositionX
        model.PositionY = frame.PositionY
        model.Width = frame.Width
        model.Height = frame.Height
        model.GridDataModel = data
        model.SelectionModel = selection
        model.HScroll = True
        model.VScroll = True
        model.ShowColumnHeader = False
        model.BackgroundColor = 16777215
        return model

    def _getLayouts(self):
        return {'controls': (self._getFrame(), self._getGrid(), ),
                'tops':     (self._getColumnLabel(), self._getColumn())}

# GridView private control methods
    def _getFrame(self):
        return self._window.getControl('FrameControl1')

    def _getGrid(self):
        return self._window.getControl(self._name)

    def _getToggle(self):
        return self._window.getControl('CommandButton1')

    def _getColumnLabel(self):
        return self._window.getControl('Label1')

    def _getColumn(self):
        return self._window.getControl('ListBox1')

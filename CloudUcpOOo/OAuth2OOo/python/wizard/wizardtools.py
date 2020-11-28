#!
# -*- coding: utf_8 -*-

'''
    Copyright (c) 2020 https://prrvchr.github.io

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the Software
    is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
    OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import uno
import unohelper


def getRowSetOrders(rowset):
    orders = [order.strip('"') for order in rowset.Order.replace(' ', '').split(',')]
    return orders

def setRowSetOrders(orders):
    rowsetorder = '%s' % '", "'.join(orders)
    if len(orders) > 0:
        rowsetorder = '"%s"' % rowsetorder
    return rowsetorder

# TODO: On OpenOffice listbox.getSelectedItems() return a "ByteSequence instance" on empty selection
def getSelectedItems(control):
    items = control.getSelectedItems() if control.getSelectedItemPos() != -1 else ()
    return items

# TODO: On OpenOffice listbox.Model.StringItemList return a "ByteSequence instance" on empty listbox
def getStringItemList(control):
    items = control.Model.StringItemList if control.ItemCount > 0 else ()
    return items

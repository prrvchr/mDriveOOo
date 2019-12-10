#!
# -*- coding: utf_8 -*-

import unohelper

from com.sun.star.awt import XDialogEventHandler


class DialogHandler(unohelper.Base,
                    XDialogEventHandler):

    # XDialogEventHandler
    def callHandlerMethod(self, dialog, event, method):
        handled = False
        if method == 'Add':
            handled = self._addItem(dialog, event.Source)
        elif method == 'Remove':
            handled = self._removeItem(dialog, event.Source)
        elif method == 'Change':
            handled = self._updateDialog(dialog, event.Source)
        return handled
    def getSupportedMethodNames(self):
        return ('Add', 'Remove', 'Change')

    def _addItem(self, dialog, control):
        item = control.Model.Tag
        if item == 'Scope':
            textfield = dialog.getControl('TextField1')
            scope = textfield.Text
            listbox = dialog.getControl('ListBox1')
            listbox.Model.insertItemText(listbox.ItemCount, scope)
            textfield.Text = ''
            self._updateDialog(dialog, textfield)
        return True

    def _removeItem(self, dialog, control):
        item = control.Model.Tag
        if item == 'Scope':
            listbox = dialog.getControl('ListBox1')
            listbox.Model.removeItem(listbox.SelectedItemPos)
            self._updateDialog(dialog, listbox)
            textfield = dialog.getControl('TextField1')
            self._updateDialog(dialog, textfield)
        return True

    def _updateDialog(self, dialog, control):
        item = control.Model.Tag
        if item == 'HttpHandler':
            dialog.getControl('Label8').Model.Enabled = True
            dialog.getControl('TextField7').Model.Enabled = True
            dialog.getControl('Label9').Model.Enabled = True
            dialog.getControl('NumericField1').Model.Enabled = True
        elif item == 'GuiHandler':
            dialog.getControl('Label8').Model.Enabled = False
            dialog.getControl('TextField7').Model.Enabled = False
            dialog.getControl('Label9').Model.Enabled = False
            dialog.getControl('NumericField1').Model.Enabled = False
        elif item == 'CodeChallenge':
            enabled = bool(control.State)
            dialog.getControl('OptionButton1').Model.Enabled = enabled
            dialog.getControl('OptionButton2').Model.Enabled = enabled
        elif item == 'Scopes':
            enabled = control.SelectedItemPos != -1
            dialog.getControl('CommandButton2').Model.Enabled = enabled
        elif item == 'Scope':
            scope = control.Text
            # TODO: OpenOffice dont return a empty <tuple> but a <ByteSequence instance ''> on
            # ListBox.Model.StringItemList if StringItemList is empty!!!
            listbox = dialog.getControl('ListBox1')
            scopes = listbox.Model.StringItemList if listbox.ItemCount else ()
            enabled = scope != '' and scope not in scopes
            dialog.getControl('CommandButton1').Model.Enabled = enabled
        elif item == 'Login':
            enabled = control.Text != ''
            dialog.getControl('CommandButton2').Model.Enabled = enabled
        return True

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

import uno
import unohelper

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from ..unotool import createService

from ..logger import getLogger

from ..configuration import g_errorlog
from ..configuration import g_basename

from collections import OrderedDict
import traceback


class AddressBooks(unohelper.Base):
    def __init__(self, ctx, metadata, new):
        self._ctx = ctx
        print("AddressBooks.__init__() 1")
        self._addressbooks = self._getAddressbooks(metadata, new)
        print("AddressBooks.__init__() 2")

    def initAddressbooks(self, database, user, addressbooks):
        count = 0
        modified = False
        for uri, name, tag, token in addressbooks:
            print("AddressBooks.initAddressbooks() 1 Name: %s - Uri: %s - Tag: %s - Token: %s" % (name, uri, tag, token))
            if self._hasAddressbook(uri):
                addressbook = self._getAddressbook(uri)
                if addressbook.hasNameChanged(name):
                    database.updateAddressbookName(addressbook.Id, name)
                    addressbook.setName(name)
                    modified = True
                    print("AddressBooks.initAddressbooks() 2 %s" % (name, ))
            else:
                aid = database.insertAddressbook(user, uri, name, tag, token)
                addressbook = AddressBook(self._ctx, aid, uri, name, tag, token, True)
                self._addressbooks[uri] = addressbook
                modified = True
                print("AddressBooks.initAddressbooks() 3 %s - %s - %s" % (aid, name, uri))
            count += 1
        print("AddressBooks.initAddressbooks() 4")
        return count, modified

    def getAddressbooks(self):
        return self._addressbooks.values()

    # Private methods
    def _hasAddressbook(self, uri):
        return uri in self._addressbooks

    def _getAddressbook(self, uri):
        return self._addressbooks[uri]

    def _getAddressbooks(self, metadata, new):
        i = 0
        addressbooks = OrderedDict()
        aids, names, tags, tokens = self._getAddressbookMetaData(metadata)
        for uri in metadata.getValue('Uris'):
            # FIXME: If url is None we don't add this addressbook
            if uri is None:
                continue
            print("AddressBook._getAddressbooks() Url: %s - Name: %s - Index: %s - Tag: %s - Token: %s" % (uri, names[i], aids[i], tags[i], tokens[i]))
            addressbooks[uri] = AddressBook(self._ctx, aids[i], uri, names[i], tags[i], tokens[i], new)
            i += 1
        return addressbooks

    def _getAddressbookMetaData(self, data):
        return data.getValue('Aids'), data.getValue('Names'), data.getValue('Tags'), data.getValue('Tokens')


class AddressBook(unohelper.Base):
    def __init__(self, ctx, aid, uri, name, tag, token, new=False):
        self._ctx = ctx
        self._aid = aid
        self._uri = uri
        self._name = name
        self._tag = tag
        self._token = token
        self._new = new

    @property
    def Id(self):
        return self._aid
    @property
    def Uri(self):
        return self._uri
    @property
    def Name(self):
        return self._name
    @property
    def Tag(self):
        return self._tag
    @property
    def Token(self):
        return self._token

    def isNew(self):
        new = self._new
        self._new = False
        return new

    def hasNameChanged(self, name):
        return self._name != name

    def setName(self, name):
        self.Name = name

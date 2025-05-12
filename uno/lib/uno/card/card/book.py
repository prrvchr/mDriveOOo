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

from .group import Group

import json


class Book():
    def __init__(self, new, **kwargs):
        self._new = new
        self._id = kwargs.get('Book')
        self._uri = kwargs.get('Uri')
        self._name = kwargs.get('Name')
        self._tag = kwargs.get('Tag')
        self._token = kwargs.get('Token')
        groups = (Group(new, *group) for group in json.loads(kwargs.get('Groups', '[]')))
        self._groups = {group.Uri: group for group in groups}

    @property
    def Id(self):
        return self._id
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
        return self._new

    def resetNew(self):
        self._new = False

    def hasGroup(self, uri):
        return uri in self._groups

    def getGroups(self):
        return self._groups.values()

    def getGroup(self, uri):
        return self._groups[uri]

    def setNewGroup(self, uri, *args):
        group = Group(True, *args)
        self._groups[uri] = group
        return group

    def isRenamed(self, name):
        return self._name != name

    def setName(self, name):
        self._name = name

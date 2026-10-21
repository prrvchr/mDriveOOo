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

import uno
import unohelper

from com.sun.star.datatransfer import UnsupportedFlavorException
from com.sun.star.datatransfer import XTransferable

from .unotool import getMimeTypeFactory
from .unotool import getPropertyValueSet
from .unotool import getStringResource
from .unotool import getSequenceInputStream
from .unotool import getStreamSequence
from .unotool import getSimpleFile
from .unotool import getTypeDetection
from .unotool import hasInterface

from ..configuration import g_identifier
from ..configuration import g_resource

import traceback


class Factory():
    def __init__(self, ctx):
        self._ctx = ctx
        self._sf = getSimpleFile(ctx)
        self._mtf = getMimeTypeFactory(ctx)
        self._detection = getTypeDetection(ctx)
        self._charset = 'charset'
        self._encode = False
        self._default = 'utf-8'
        self._encoding = self._default
        self._uiname = 'E Documents'
        self._mimetype = 'application/octet-stream'

    @property
    def Encoding(self):
        return self._encoding
    @Encoding.setter
    def Encoding(self, encoding):
        self._encode = True
        self._encoding = encoding

# XTransferableFactory
    def getBySequence(self, sequence):
        stream = getSequenceInputStream(self._ctx, sequence)
        return self._create('InputStream', stream, sequence)

    def getByUrl(self, url):
        stream = self._sf.openFileRead(url)
        return self._create('URL', url, stream, stream=stream)

    def getByStream(self, stream):
        return self._create('InputStream', stream, stream)

    def getByString(self, data):
        sequence = uno.ByteSequence(data.encode(self._encoding))
        stream = getSequenceInputStream(self._ctx, sequence)
        return self._create('InputStream', stream, data, force=True)

# Private methods
    def _create(self, key, value, data, stream=None, force=False):
        typemap = self._getTypeMap(self._encoding)
        descriptor = {key: value}
        if stream: 
            descriptor['InputStream'] = stream
        uiname, mimetype = self._getMimeValues(descriptor, self._uiname, self._mimetype)
        mimetype = self._getMimeType(mimetype, force)
        typename = self._getDataTypeName(data)
        flavors = self._getFlavors(typemap, uiname, mimetype, typename)
        return Transferable(self._ctx, typemap, flavors, typename, data)

    def _getMimeValues(self, descriptor, uiname, mimetype, deep=True):
        itype, descriptor = self._detection.queryTypeByDescriptor(getPropertyValueSet(descriptor), deep)
        if self._detection.hasByName(itype):
            for t in self._detection.getByName(itype):
                if t.Name == 'UIName':
                    uiname = t.Value
                elif t.Name == 'MediaType':
                    mimetype = t.Value
        return uiname, mimetype

    def _getMimeType(self, mimetype, force=False):
        if force or self._encode:
            mct = self._mtf.createMimeContentType(mimetype)
            if not mct.hasParameter(self._charset):
                mimetype += ';%s=%s' % (self._charset, self._encoding)
        self._encoding = self._default
        self._encode = False
        return mimetype

    def _getFlavors(self, typemap, uiname, mimetype, typename):
        flavors = []
        for input, output in typemap.keys():
            if input == typename:
                flavors.append(self._getFlavor(uiname, mimetype, output))
        return tuple(flavors)

    def _getFlavor(self, uiname, mimetype, typename):
        flavor = uno.createUnoStruct('com.sun.star.datatransfer.DataFlavor')
        flavor.HumanPresentableName = uiname
        flavor.MimeType = mimetype
        flavor.DataType = uno.getTypeByName(typename)
        return flavor

    def _getDataTypeName(self, data):
        if isinstance(data, str):
            return 'string'
        elif isinstance(data, uno.ByteSequence):
            return '[]byte'
        elif hasInterface(data, 'com.sun.star.io.XInputStream'):
            return 'com.sun.star.io.XInputStream'
        return ''

    def _getTypeMap(self, encoding):
        ipstream = 'com.sun.star.io.XInputStream'
        return {(ipstream, ipstream): lambda x: x,
                ('string', 'string'): lambda x: x,
                ('[]byte', '[]byte'): lambda x: x,
                (ipstream, '[]byte'): lambda x: getStreamSequence(x),
                (ipstream, 'string'): lambda x: getStreamSequence(x).value.decode(encoding, errors='ignore'),
                ('string', '[]byte'): lambda x: uno.ByteSequence(x.encode(encoding)),
                ('[]byte', 'string'): lambda x: x.value.decode(encoding, errors='ignore')}


class Transferable(unohelper.Base,
                   XTransferable):
    def __init__(self, ctx, typemap, flavors, typename, data):
        self._ctx = ctx
        self._typemap = typemap
        self._flavors = flavors
        self._typename = typename
        self._data = data

# XTransferable
    def getTransferData(self, flavor):
        if not self.isDataFlavorSupported(flavor):
            resolver = getStringResource(self._ctx, g_identifier, g_resource, 'Transferable')
            msg = resolver.resolveString(101) % (flavor.MimeType, flavor.DataType.typeName)
            raise UnsupportedFlavorException(msg, self)

        key = (self._typename, flavor.DataType.typeName)
        return self._typemap[key](self._data)

    def getTransferDataFlavors(self):
        return self._flavors

    def isDataFlavorSupported(self, flavor):
        return any(flavor.MimeType == f.MimeType and
                   flavor.DataType.typeName == f.DataType.typeName for f in self._flavors)


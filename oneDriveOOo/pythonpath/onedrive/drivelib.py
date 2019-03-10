#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.io import XOutputStream
from com.sun.star.io import XInputStream
from com.sun.star.io import IOException

from .drivetools import unparseDateTime
from .drivetools import g_childfields
from .drivetools import g_chunk
from .drivetools import g_pages
from .drivetools import g_timeout
from .drivetools import g_url


class IdGenerator():
    def __init__(self, session, count, space='drive'):
        print("google.IdGenerator.__init__()")
        self.ids = []
        url = '%sfiles/generateIds' % g_url
        params = {'count': count, 'space': space}
        with session.get(url, params=params, timeout=g_timeout) as r:
            print("google.IdGenerator(): %s" % r.json())
            if r.status_code == session.codes.ok:
                self.ids = r.json().get('ids', [])
        print("google.IdGenerator.__init__()")
    def __iter__(self):
        return self
    def __next__(self):
        if self.ids:
            return self.ids.pop(0)
        raise StopIteration
    # for python v2.xx
    def next(self):
        return self.__next__()


class ChildGenerator():
    def __init__(self, session, id):
        print("google.ChildGenerator.__init__()")
        self.session = session
        self.params = {'fields': g_childfields, 'pageSize': g_pages}
        self.params['q'] = "'%s' in parents" % id
        self.timestamp = unparseDateTime()
        self.url = '%sfiles' % g_url
        print("google.ChildGenerator.__init__()")
    def __iter__(self):
        self.rows, self.token = self._getChunk()
        return self
    def __next__(self):
        if self.rows:
            return self.rows.pop(0)
        elif self.token:
            self.rows, self.token = self._getChunk(self.token)
            return self.rows.pop(0)
        raise StopIteration
    # for python v2.xx
    def next(self):
        return self.__next__()
    def _getChunk(self, token=None):
        self.params['pageToken'] = token
        rows = []
        token = None
        r = self.session.get(self.url, params=self.params, timeout=g_timeout)
        print("google.ChildGenerator(): %s" % r.json())
        if r.status_code == self.session.codes.ok:
            rows = r.json().get('files', [])
            token = r.json().get('nextPageToken', None)
        return rows, token


class InputStream(unohelper.Base, XInputStream):
    def __init__(self, session, id, size, mimetype):
        self.session = session
        self.length = 32768
        url = '%sfiles/%s/export' % (g_url, id) if mimetype else '%sfiles/%s' % (g_url, id)
        params = {'mimeType': mimetype} if mimetype else {'alt': 'media'}
        self.chunks = (s for c in ChunksDownloader(self.session, url, params, size, self.length) for s in c)
        print("google.InputStream.__init__()")

    #XInputStream
    def readBytes(self, sequence, length):
        # I assume that 'length' is constant...and is multiple of 'self.length'
        sequence = uno.ByteSequence(b'')
        while length > 0:
            sequence += uno.ByteSequence(next(self.chunks, b''))
            length -= self.length
        length = len(sequence)
        return length, sequence
    def readSomeBytes(self, sequence, length):
        return self.readBytes(sequence, length)
    def skipBytes(self, length):
        pass
    def available(self):
        return g_chunk
    def closeInput(self):
        self.session.close()


class ChunksDownloader():
    def __init__(self, session, url, params, size, length):
        print("google.ChunkDownloader.__init__()")
        self.session = session
        self.url = url
        self.size = size
        self.length = length
        self.start, self.closed = 0, False
        self.headers = {'Accept-Encoding': 'gzip'}
        self.params = params 
        print("google.ChunkDownloader.__init__()")
    def __iter__(self):
        return self
    def __next__(self):
        if self.closed:
            raise StopIteration
        print("google.ChunkDownloader.__next__() 1")
        end = g_chunk
        if self.size:
            end = min(self.start + g_chunk, self.size - self.start)
            self.headers['Range'] = 'bytes=%s-%s' % (self.start, end -1)
        print("google.ChunkDownloader.__next__() 2: %s" % (self.headers, ))
        r = self.session.get(self.url, headers=self.headers, params=self.params, timeout=g_timeout, stream=True)
        print("google.ChunkDownloader.__next__() 3: %s - %s" % (r.status_code, r.headers))
        if r.status_code == self.session.codes.partial_content:
            self.start += int(r.headers.get('Content-Length', end))
            self.closed = self.start == self.size
            print("google.ChunkDownloader.__next__() 4 %s - %s" % (self.closed, self.start))
        elif  r.status_code == self.session.codes.ok:
            self.start += int(r.headers.get('Content-Length', end))
            self.closed = True
            print("google.ChunkDownloader.__next__() 5 %s - %s" % (self.closed, self.start))
        else:
            raise IOException('Error Downloading file...', self)
        return r.iter_content(self.length)
    # for python v2.xx
    def next(self):
        return self.__next__()


class OutputStream(unohelper.Base, XOutputStream):
    def __init__(self, session, url, size):
        self.session = session
        self.url = url
        self.size = size
        self.buffers = uno.ByteSequence(b'')
        self.start = 0
        self.closed, self.flushed, self.chunked = False, False, size >= g_chunk

    # XOutputStream
    def writeBytes(self, sequence):
        if self.closed:
            raise IOException('OutputStream is closed...', self)
        self.buffers += sequence
        length = len(self.buffers)
        if length >= g_chunk and not self._isWrite(length):
            raise IOException('Error Uploading file...', self)
        else:
            print("google.OutputStream.writeBytes() Bufferize: %s - %s" % (self.start, length))
        return
    def flush(self):
        print("google.OutputStream.flush()")
        if self.closed:
            raise IOException('OutputStream is closed...', self)
        if not self.flushed and not self._flush():
            raise IOException('Error Uploading file...', self)
    def closeOutput(self):
        print("google.OutputStream.closeOutput()")
        if not self.flushed and not self._flush():
            raise IOException('Error Uploading file...', self)
        #self.session.close()
        self.closed = True
    def _flush(self):
        self.flushed = True
        length = len(self.buffers)
        return self._isWrite(length)
    def _isWrite(self, length):
        print("google.OutputStream._write() 1: %s" % (self.start, ))
        headers = None
        if self.chunked:
            end = self.start + length -1
            headers = {'Content-Range': 'bytes %s-%s/%s' % (self.start, end, self.size)}
        r = self.session.put(self.url, headers=headers, data=self.buffers.value)
        print("google.OutputStream._write() 2: %s" % (r.request.headers, ))
        print("google.OutputStream._write() 3: %s - %s" % (r.status_code, r.headers))
        print("google.OutputStream._write() 4: %s" % (r.content, ))
        if r.status_code == self.session.codes.ok or r.status_code == self.session.codes.created:
            self.start += int(r.request.headers['Content-Length'])
            self.buffers = uno.ByteSequence(b'')
            return True
        elif r.status_code == self.session.codes.permanent_redirect:
            if 'Range' in r.headers:
                self.start += int(r.headers['Range'].split('-')[-1]) +1
                self.buffers = uno.ByteSequence(b'')
                return True
        return False
